"""Forest management plugin for FloatCtl."""

import json
import os
import subprocess
import concurrent.futures
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import rich_click as click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from floatctl.plugin_manager import PluginBase

console = Console()


class ForestPlugin(PluginBase):
    """Plugin for managing FLOAT Forest deployments and artifacts."""
    
    name = "forest"
    description = "Manage FLOAT Forest deployments and artifact catalog"
    version = "0.1.0"
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize forest plugin."""
        super().__init__(config)
        self.artifacts_path = Path.home() / "projects" / "float-workspace" / "artifacts"
        self.forest_path = self.artifacts_path / "float-forest-navigator"
        
    def register_commands(self, cli_group: click.Group) -> None:
        """Register forest commands with the CLI."""
        
        @cli_group.group(name="forest", help="Manage FLOAT Forest deployments")
        def forest_group():
            """Forest management commands."""
            pass
        
        @forest_group.command(name="status")
        def status_cmd():
            """Check deployment status of all forest artifacts."""
            self.check_deployment_status()
        
        @forest_group.command(name="update")
        @click.option(
            "--check-only",
            is_flag=True,
            help="Only check status without updating catalog"
        )
        def update_cmd(check_only: bool):
            """Update forest catalog with working deployments."""
            self.update_forest_catalog(check_only)
        
        @forest_group.command(name="stats")
        def stats_cmd():
            """Show forest deployment statistics."""
            self.show_deployment_stats()
        
        @forest_group.command(name="fix")
        @click.option(
            "--limit",
            "-n",
            type=int,
            default=5,
            help="Number of deployments to fix"
        )
        @click.option(
            "--dry-run",
            is_flag=True,
            help="Show what would be fixed without making changes"
        )
        def fix_cmd(limit: int, dry_run: bool):
            """Fix broken deployments."""
            self.fix_broken_deployments(limit, dry_run)
        
        @forest_group.command(name="list")
        @click.option(
            "--status",
            type=click.Choice(["working", "broken", "all"]),
            default="all",
            help="Filter by deployment status"
        )
        @click.option(
            "--format",
            type=click.Choice(["table", "json", "csv"]),
            default="table",
            help="Output format"
        )
        @click.option(
            "--cached",
            is_flag=True,
            default=True,
            help="Use cached deployment status (faster)"
        )
        @click.option(
            "--show-vercel",
            is_flag=True,
            help="Show Vercel project links"
        )
        def list_cmd(status: str, format: str, cached: bool, show_vercel: bool):
            """List forest artifacts with their deployment status."""
            self.list_artifacts(status, format, cached, show_vercel)
        
        @forest_group.command(name="scan")
        @click.option(
            "--add-missing",
            is_flag=True,
            help="Add missing projects to Vercel"
        )
        @click.option(
            "--inject-toolbar",
            is_flag=True,
            help="Inject FLOAT toolbar and re-deploy existing projects"
        )
        def scan_cmd(add_missing: bool, inject_toolbar: bool):
            """Scan for new artifacts and add to deployment."""
            self.scan_for_new_artifacts(add_missing, inject_toolbar)
        
        @forest_group.command(name="update-toolbar")
        @click.option(
            "--limit",
            "-n",
            type=int,
            default=10,
            help="Number of sites to update (default: 10)"
        )
        @click.option(
            "--all",
            is_flag=True,
            help="Update all sites"
        )
        @click.option(
            "--filter",
            type=str,
            help="Only update sites matching pattern"
        )
        @click.option(
            "--parallel",
            "-p",
            type=int,
            default=3,
            help="Number of parallel deployments (default: 3)"
        )
        @click.option(
            "--force",
            is_flag=True,
            help="Force update even if toolbar already present"
        )
        @click.option(
            "--dry-run",
            is_flag=True,
            help="Show what would be done without doing it"
        )
        def update_toolbar_cmd(limit: int, all: bool, filter: str, parallel: int, force: bool, dry_run: bool):
            """Fast toolbar update for existing sites using Python."""
            if all:
                limit = 1000
            self.fast_toolbar_update(limit, filter, parallel, force, dry_run)
    
    def check_deployment_status(self) -> Dict[str, List[Dict]]:
        """Check deployment status of all artifacts."""
        console.print(Panel.fit(
            "[bold blue]🌲 Checking Forest Deployment Status[/bold blue]",
            border_style="blue"
        ))
        
        # Run the check-all-deployments script
        script_path = self.forest_path / "check-all-deployments.sh"
        
        if not script_path.exists():
            console.print("[red]❌ Deployment check script not found![/red]")
            return {"working": [], "broken": [], "no_domain": []}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Checking deployments...", total=None)
            
            try:
                # Run the script
                result = subprocess.run(
                    ["bash", str(script_path)],
                    cwd=str(self.forest_path),
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                progress.update(task, completed=True)
                
                # Parse the CSV output
                csv_path = self.forest_path / "deployment-status.csv"
                if csv_path.exists():
                    return self._parse_deployment_csv(csv_path)
                else:
                    console.print("[yellow]⚠️  No deployment status file generated[/yellow]")
                    return {"working": [], "broken": [], "no_domain": []}
                    
            except subprocess.TimeoutExpired:
                progress.update(task, completed=True)
                console.print("[yellow]⚠️  Deployment check timed out[/yellow]")
                return {"working": [], "broken": [], "no_domain": []}
            except Exception as e:
                progress.update(task, completed=True)
                console.print(f"[red]❌ Error checking deployments: {e}[/red]")
                return {"working": [], "broken": [], "no_domain": []}
    
    def _parse_deployment_csv(self, csv_path: Path) -> Dict[str, List[Dict]]:
        """Parse deployment status CSV file."""
        import csv
        
        results = {"working": [], "broken": [], "no_domain": []}
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                status = row.get("Status", "")
                project = {
                    "name": row.get("Project", ""),
                    "domain": row.get("CustomDomain", ""),
                    "status": status,
                    "deployment": row.get("LastDeployment", ""),
                    "issues": row.get("Issues", "")
                }
                
                if status == "OK":
                    results["working"].append(project)
                elif status == "404":
                    results["broken"].append(project)
                elif status == "NO_DOMAIN":
                    results["no_domain"].append(project)
        
        return results
    
    def update_forest_catalog(self, check_only: bool = False):
        """Update the forest catalog with only working deployments."""
        # First check status
        status = self.check_deployment_status()
        
        # Show summary
        console.print("\n[bold]📊 Deployment Summary:[/bold]")
        console.print(f"  ✅ Working: {len(status['working'])}")
        console.print(f"  🚨 Broken (404): {len(status['broken'])}")
        console.print(f"  📍 No Domain: {len(status['no_domain'])}")
        
        if check_only:
            return
        
        # Run the filter script
        console.print("\n[bold blue]🔄 Updating production catalog...[/bold blue]")
        
        script_path = self.forest_path / "generate-working-artifacts.js"
        if not script_path.exists():
            console.print("[red]❌ Filter script not found![/red]")
            return
        
        try:
            result = subprocess.run(
                ["node", str(script_path)],
                cwd=str(self.forest_path),
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                console.print("[green]✅ Production catalog updated successfully![/green]")
                console.print(result.stdout)
            else:
                console.print(f"[red]❌ Error updating catalog: {result.stderr}[/red]")
                
        except Exception as e:
            console.print(f"[red]❌ Failed to update catalog: {e}[/red]")
    
    def show_deployment_stats(self):
        """Show detailed deployment statistics."""
        status = self.check_deployment_status()
        
        # Create summary table
        table = Table(title="🌲 Forest Deployment Statistics", show_header=True)
        table.add_column("Status", style="bold")
        table.add_column("Count", justify="right")
        table.add_column("Percentage", justify="right")
        
        total = len(status["working"]) + len(status["broken"]) + len(status["no_domain"])
        
        if total > 0:
            table.add_row(
                "[green]Working[/green]",
                str(len(status["working"])),
                f"{len(status['working']) / total * 100:.1f}%"
            )
            table.add_row(
                "[red]Broken (404)[/red]",
                str(len(status["broken"])),
                f"{len(status['broken']) / total * 100:.1f}%"
            )
            table.add_row(
                "[yellow]No Domain[/yellow]",
                str(len(status["no_domain"])),
                f"{len(status['no_domain']) / total * 100:.1f}%"
            )
            table.add_section()
            table.add_row(
                "[bold]Total[/bold]",
                f"[bold]{total}[/bold]",
                "100.0%"
            )
        
        console.print(table)
        
        # Show some working sites
        if status["working"]:
            console.print("\n[bold green]✅ Working Sites:[/bold green]")
            for site in status["working"][:10]:
                console.print(f"  • {site['name']} → {site['domain']}")
            if len(status["working"]) > 10:
                console.print(f"  ... and {len(status['working']) - 10} more")
    
    def fix_broken_deployments(self, limit: int, dry_run: bool):
        """Fix broken deployments."""
        status = self.check_deployment_status()
        broken = status["broken"][:limit]
        
        if not broken:
            console.print("[green]✨ No broken deployments to fix![/green]")
            return
        
        console.print(f"\n[bold]🔧 Fixing {len(broken)} broken deployments...[/bold]")
        
        if dry_run:
            console.print("[yellow]DRY RUN - No changes will be made[/yellow]\n")
        
        for project in broken:
            console.print(f"\n[bold]{project['name']}[/bold]")
            console.print(f"  Domain: {project['domain']}")
            
            if not dry_run:
                # Run fix script for this project
                fix_script = self.forest_path / "fix-single-404.sh"
                if fix_script.exists():
                    try:
                        result = subprocess.run(
                            ["bash", str(fix_script), project['name']],
                            cwd=str(self.forest_path),
                            capture_output=True,
                            text=True,
                            timeout=120
                        )
                        if result.returncode == 0:
                            console.print("  [green]✅ Fixed successfully[/green]")
                        else:
                            console.print(f"  [red]❌ Fix failed: {result.stderr}[/red]")
                    except Exception as e:
                        console.print(f"  [red]❌ Error: {e}[/red]")
                else:
                    console.print("  [red]❌ Fix script not found[/red]")
    
    def list_artifacts(self, status_filter: str, output_format: str, use_cached: bool = True, show_vercel: bool = False):
        """List artifacts with filtering and formatting options."""
        # Load the artifacts JSON
        artifacts_file = self.forest_path / "public" / "artifacts-production.json"
        if not artifacts_file.exists():
            artifacts_file = self.forest_path / "public" / "artifacts.json"
        
        if not artifacts_file.exists():
            console.print("[red]❌ No artifacts catalog found![/red]")
            return
        
        with open(artifacts_file) as f:
            data = json.load(f)
        
        artifacts = data.get("artifacts", [])
        
        # Apply filtering
        if status_filter != "all":
            if use_cached and (self.forest_path / "deployment-status.csv").exists():
                # Use cached status from CSV
                status = self._parse_deployment_csv(self.forest_path / "deployment-status.csv")
            else:
                # Check live status
                status = self.check_deployment_status()
            
            if status_filter == "working":
                working_names = {p["name"] for p in status["working"]}
                artifacts = [a for a in artifacts if a["name"] in working_names]
            elif status_filter == "broken":
                broken_names = {p["name"] for p in status["broken"]}
                artifacts = [a for a in artifacts if a["name"] in broken_names]
        
        # Check for toolbar presence in each artifact
        for artifact in artifacts:
            artifact["hasToolbar"] = self._check_has_toolbar(artifact)
            if show_vercel:
                artifact["vercelProjectUrl"] = self._get_vercel_project_url(artifact)
        
        # Format output
        if output_format == "json":
            console.print_json(data=artifacts)
        elif output_format == "csv":
            import csv
            import sys
            fieldnames = ["name", "type", "customDomain", "deployedUrl", "hasToolbar"]
            if show_vercel:
                fieldnames.append("vercelProjectUrl")
            writer = csv.DictWriter(
                sys.stdout,
                fieldnames=fieldnames,
                extrasaction='ignore'
            )
            writer.writeheader()
            writer.writerows(artifacts)
        else:  # table
            table = Table(title=f"🌲 Forest Artifacts ({status_filter})")
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Toolbar", style="yellow", justify="center")
            table.add_column("Domain", style="green")
            if show_vercel:
                table.add_column("Vercel Project", style="blue")
            
            for artifact in artifacts[:20]:  # Limit table output
                toolbar_icon = "✓" if artifact.get("hasToolbar", False) else "✗"
                toolbar_style = "green" if artifact.get("hasToolbar", False) else "red"
                
                row = [
                    artifact.get("name", ""),
                    artifact.get("type", ""),
                    f"[{toolbar_style}]{toolbar_icon}[/{toolbar_style}]",
                    artifact.get("customDomain", artifact.get("deployedUrl", ""))
                ]
                
                if show_vercel:
                    # Generate Vercel project URL
                    vercel_project_url = self._get_vercel_project_url(artifact)
                    row.append(vercel_project_url)
                
                table.add_row(*row)
            
            console.print(table)
            
            if len(artifacts) > 20:
                console.print(f"\n... and {len(artifacts) - 20} more")
    
    def scan_for_new_artifacts(self, add_missing: bool = False, inject_toolbar: bool = False):
        """Scan for new artifacts and optionally add them to deployment."""
        console.print(Panel.fit(
            "[bold blue]🔍 Scanning for New Artifacts[/bold blue]",
            border_style="blue"
        ))
        
        # Get all directories in artifacts path
        all_dirs = [d for d in self.artifacts_path.iterdir() if d.is_dir()]
        
        # Load current catalog
        artifacts_file = self.forest_path / "public" / "artifacts.json"
        if artifacts_file.exists():
            with open(artifacts_file) as f:
                catalog = json.load(f)
                existing_names = {a["name"] for a in catalog.get("artifacts", [])}
        else:
            existing_names = set()
        
        # Find new artifacts
        new_artifacts = []
        for dir_path in all_dirs:
            dir_name = dir_path.name
            
            # Skip system directories
            if dir_name.startswith('.') or dir_name == 'float-forest-navigator':
                continue
            
            # Check if it's a potential artifact
            has_marker = any((
                (dir_path / "index.html").exists(),
                (dir_path / "package.json").exists(),
                (dir_path / "README.md").exists(),
                (dir_path / "vercel.json").exists(),
            ))
            
            if has_marker and dir_name not in existing_names:
                new_artifacts.append({
                    "name": dir_name,
                    "path": str(dir_path),
                    "has_package": (dir_path / "package.json").exists(),
                    "has_vercel": (dir_path / "vercel.json").exists(),
                })
        
        if not new_artifacts:
            console.print("[green]✅ No new artifacts found![/green]")
            return
        
        # Display results
        console.print(f"\n[bold]Found {len(new_artifacts)} new artifacts:[/bold]")
        
        table = Table(show_header=True)
        table.add_column("Name", style="cyan")
        table.add_column("Has package.json", style="yellow")
        table.add_column("Has vercel.json", style="green")
        
        for artifact in new_artifacts[:20]:
            table.add_row(
                artifact["name"],
                "✓" if artifact["has_package"] else "✗",
                "✓" if artifact["has_vercel"] else "✗"
            )
        
        console.print(table)
        
        if len(new_artifacts) > 20:
            console.print(f"\n... and {len(new_artifacts) - 20} more")
        
        if add_missing:
            console.print("\n[bold yellow]🚀 Adding new artifacts to deployment...[/bold yellow]")
            self._deploy_missing_artifacts(new_artifacts)
        elif inject_toolbar:
            console.print("\n[bold yellow]🔧 Injecting toolbar and re-deploying artifacts...[/bold yellow]")
            self._inject_toolbar_and_deploy(new_artifacts)
        else:
            console.print("\n[dim]To add these to deployment, run with --add-missing flag[/dim]")
            console.print("[dim]To inject toolbar into existing deployments, run with --inject-toolbar flag[/dim]")
    
    def _deploy_missing_artifacts(self, artifacts: List[Dict]):
        """Deploy missing artifacts to Vercel."""
        # First check if Vercel CLI is available
        try:
            subprocess.run(["vercel", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            console.print("[red]❌ Vercel CLI not found! Please install it first:[/red]")
            console.print("[dim]npm install -g vercel[/dim]")
            return
        
        # Ask for confirmation
        console.print(f"\n[yellow]⚠️  This will deploy {len(artifacts)} new projects to Vercel.[/yellow]")
        if not click.confirm("Continue?"):
            console.print("[dim]Deployment cancelled[/dim]")
            return
        
        # Deploy each artifact
        deployed = []
        failed = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            for artifact in artifacts:
                task = progress.add_task(f"Deploying {artifact['name']}...", total=None)
                
                try:
                    # Run vercel deployment
                    result = subprocess.run(
                        ["vercel", "--prod", "--yes"],
                        cwd=artifact["path"],
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minute timeout per project
                    )
                    
                    if result.returncode == 0:
                        # Extract URL from output
                        import re
                        url_match = re.search(r'https://[^\s]+\.vercel\.app', result.stdout)
                        url = url_match.group(0) if url_match else "Unknown URL"
                        
                        deployed.append({
                            "name": artifact["name"],
                            "url": url
                        })
                        progress.update(task, description=f"[green]✓[/green] {artifact['name']}")
                    else:
                        failed.append({
                            "name": artifact["name"],
                            "error": result.stderr or "Unknown error"
                        })
                        progress.update(task, description=f"[red]✗[/red] {artifact['name']}")
                        
                except subprocess.TimeoutExpired:
                    failed.append({
                        "name": artifact["name"],
                        "error": "Deployment timed out"
                    })
                    progress.update(task, description=f"[yellow]⚠[/yellow] {artifact['name']}")
                except Exception as e:
                    failed.append({
                        "name": artifact["name"],
                        "error": str(e)
                    })
                    progress.update(task, description=f"[red]✗[/red] {artifact['name']}")
                
                progress.update(task, completed=True)
        
        # Show results
        console.print(f"\n[bold]Deployment Results:[/bold]")
        console.print(f"  [green]✅ Deployed: {len(deployed)}[/green]")
        console.print(f"  [red]❌ Failed: {len(failed)}[/red]")
        
        if deployed:
            console.print("\n[bold green]Successfully Deployed:[/bold green]")
            for item in deployed:
                console.print(f"  • {item['name']} → {item['url']}")
        
        if failed:
            console.print("\n[bold red]Failed Deployments:[/bold red]")
            for item in failed:
                console.print(f"  • {item['name']}: {item['error']}")
        
        # Update catalog
        if deployed:
            console.print("\n[bold]Updating forest catalog...[/bold]")
            self._update_artifacts_catalog(deployed)
    
    def _update_artifacts_catalog(self, deployed_items: List[Dict]):
        """Update the artifacts catalog with newly deployed items."""
        artifacts_file = self.forest_path / "public" / "artifacts.json"
        
        try:
            # Load existing catalog
            if artifacts_file.exists():
                with open(artifacts_file, 'r') as f:
                    catalog = json.load(f)
            else:
                catalog = {
                    "generated": "",
                    "totalArtifacts": 0,
                    "artifacts": []
                }
            
            # Add new artifacts
            for item in deployed_items:
                # Create artifact entry
                artifact_path = Path(item['name'])
                new_artifact = {
                    "id": item['name'],
                    "path": str(self.artifacts_path / item['name']),
                    "name": item['name'],
                    "type": "unknown",  # Will be determined by discovery
                    "framework": "unknown",
                    "hasJson": (artifact_path / "package.json").exists(),
                    "hasBuildProcess": (artifact_path / "package.json").exists(),
                    "deployedUrl": item['url'],
                    "isDeployed": True,
                    "staticMode": True
                }
                
                # Check if already exists
                exists = False
                for i, existing in enumerate(catalog['artifacts']):
                    if existing['name'] == item['name']:
                        catalog['artifacts'][i] = new_artifact
                        exists = True
                        break
                
                if not exists:
                    catalog['artifacts'].append(new_artifact)
            
            # Update metadata
            catalog['generated'] = datetime.now().isoformat()
            catalog['totalArtifacts'] = len(catalog['artifacts'])
            
            # Save updated catalog
            with open(artifacts_file, 'w') as f:
                json.dump(catalog, f, indent=2)
            
            console.print(f"[green]✅ Updated catalog with {len(deployed_items)} new deployments[/green]")
            
            # Also run the discovery script to properly categorize
            console.print("[dim]Running discovery to update artifact metadata...[/dim]")
            try:
                subprocess.run(
                    ["npm", "run", "discover"],
                    cwd=str(self.forest_path),
                    capture_output=True,
                    timeout=60
                )
            except Exception as e:
                console.print(f"[yellow]⚠️  Discovery update failed: {e}[/yellow]")
                
        except Exception as e:
            console.print(f"[red]❌ Failed to update catalog: {e}[/red]")
    
    def _inject_toolbar_and_deploy(self, artifacts: List[Dict]):
        """Inject FLOAT toolbar into existing projects and re-deploy them."""
        # First check if Vercel CLI is available
        try:
            subprocess.run(["vercel", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            console.print("[red]❌ Vercel CLI not found! Please install it first:[/red]")
            console.print("[dim]npm install -g vercel[/dim]")
            return
        
        # Ask for confirmation
        console.print(f"\n[yellow]⚠️  This will inject the FLOAT toolbar and re-deploy {len(artifacts)} projects.[/yellow]")
        if not click.confirm("Continue?"):
            console.print("[dim]Operation cancelled[/dim]")
            return
        
        # Copy inject-toolbar.sh to each project
        inject_script = self.forest_path / "inject-toolbar.sh"
        if not inject_script.exists():
            console.print("[red]❌ inject-toolbar.sh not found![/red]")
            return
        
        deployed = []
        failed = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            for artifact in artifacts:
                task = progress.add_task(f"Processing {artifact['name']}...", total=None)
                
                try:
                    artifact_path = Path(artifact["path"])
                    
                    # Check if it has a vercel.json
                    vercel_json_path = artifact_path / "vercel.json"
                    has_vercel_json = vercel_json_path.exists()
                    
                    if has_vercel_json:
                        # Read existing vercel.json
                        with open(vercel_json_path, 'r') as f:
                            vercel_config = json.load(f)
                    else:
                        # Create minimal vercel.json
                        vercel_config = {}
                    
                    # Add or update buildCommand to inject toolbar
                    original_build = vercel_config.get("buildCommand", "")
                    
                    # Copy inject script to project
                    project_inject_script = artifact_path / "inject-toolbar.sh"
                    import shutil
                    shutil.copy2(inject_script, project_inject_script)
                    
                    # Update build command
                    # For Next.js apps, inject BEFORE build
                    is_nextjs = any((
                        (artifact_path / "next.config.js").exists(),
                        (artifact_path / "next.config.mjs").exists(),
                        (artifact_path / "next.config.ts").exists(),
                        vercel_config.get("framework") == "nextjs"
                    ))
                    
                    if is_nextjs:
                        # For Next.js, run injection before build
                        if original_build:
                            vercel_config["buildCommand"] = f"bash inject-toolbar.sh && {original_build}"
                        else:
                            vercel_config["buildCommand"] = "bash inject-toolbar.sh && next build"
                    else:
                        # For other frameworks, run after build
                        if original_build:
                            vercel_config["buildCommand"] = f"{original_build} && bash inject-toolbar.sh"
                        else:
                            # Check if it's a framework project
                            package_json_path = artifact_path / "package.json"
                            if package_json_path.exists():
                                with open(package_json_path, 'r') as f:
                                    package_data = json.load(f)
                                    scripts = package_data.get("scripts", {})
                                    if "build" in scripts:
                                        vercel_config["buildCommand"] = "npm run build && bash inject-toolbar.sh"
                                    else:
                                        vercel_config["buildCommand"] = "bash inject-toolbar.sh"
                            else:
                                vercel_config["buildCommand"] = "bash inject-toolbar.sh"
                    
                    # Write updated vercel.json
                    with open(vercel_json_path, 'w') as f:
                        json.dump(vercel_config, f, indent=2)
                    
                    # Deploy with Vercel
                    result = subprocess.run(
                        ["vercel", "--prod", "--yes"],
                        cwd=str(artifact_path),
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    
                    if result.returncode == 0:
                        # Extract URL
                        import re
                        url_match = re.search(r'https://[^\s]+\.vercel\.app', result.stdout)
                        url = url_match.group(0) if url_match else "Unknown URL"
                        
                        deployed.append({
                            "name": artifact["name"],
                            "url": url
                        })
                        progress.update(task, description=f"[green]✓[/green] {artifact['name']}")
                    else:
                        failed.append({
                            "name": artifact["name"],
                            "error": result.stderr or "Unknown error"
                        })
                        progress.update(task, description=f"[red]✗[/red] {artifact['name']}")
                    
                    # Clean up inject script copy
                    if project_inject_script.exists():
                        project_inject_script.unlink()
                        
                except subprocess.TimeoutExpired:
                    failed.append({
                        "name": artifact["name"],
                        "error": "Deployment timed out"
                    })
                    progress.update(task, description=f"[yellow]⚠[/yellow] {artifact['name']}")
                except Exception as e:
                    failed.append({
                        "name": artifact["name"],
                        "error": str(e)
                    })
                    progress.update(task, description=f"[red]✗[/red] {artifact['name']}")
                
                progress.update(task, completed=True)
        
        # Show results
        console.print(f"\n[bold]Toolbar Injection & Deployment Results:[/bold]")
        console.print(f"  [green]✅ Deployed with toolbar: {len(deployed)}[/green]")
        console.print(f"  [red]❌ Failed: {len(failed)}[/red]")
        
        if deployed:
            console.print("\n[bold green]Successfully Deployed with Toolbar:[/bold green]")
            for item in deployed:
                console.print(f"  • {item['name']} → {item['url']}")
        
        if failed:
            console.print("\n[bold red]Failed Deployments:[/bold red]")
            for item in failed:
                console.print(f"  • {item['name']}: {item['error']}")
        
        # Update catalog
        if deployed:
            console.print("\n[bold]Updating forest catalog...[/bold]")
            self._update_artifacts_catalog(deployed)
    
    def _check_has_toolbar(self, artifact: Dict) -> bool:
        """Check if an artifact has the FLOAT toolbar injected."""
        artifact_path = Path(artifact.get("path", self.artifacts_path / artifact["name"]))
        
        # Check vercel.json for inject-toolbar.sh in buildCommand
        vercel_json_path = artifact_path / "vercel.json"
        if vercel_json_path.exists():
            try:
                with open(vercel_json_path, 'r') as f:
                    vercel_config = json.load(f)
                    build_command = vercel_config.get("buildCommand", "")
                    if "inject-toolbar.sh" in build_command:
                        return True
            except Exception:
                pass
        
        # Check for presence of inject-toolbar.sh file
        if (artifact_path / "inject-toolbar.sh").exists():
            return True
        
        # Check package.json scripts for toolbar injection
        package_json_path = artifact_path / "package.json"
        if package_json_path.exists():
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                    scripts = package_data.get("scripts", {})
                    # Check various script fields
                    for script_name in ["build", "postbuild", "vercel-build"]:
                        if script_name in scripts and "inject-toolbar" in scripts[script_name]:
                            return True
            except Exception:
                pass
        
        # Check if project has a custom build script that might inject toolbar
        build_files = ["build.sh", "build.js", "build.ts"]
        for build_file in build_files:
            build_path = artifact_path / build_file
            if build_path.exists():
                try:
                    with open(build_path, 'r') as f:
                        content = f.read()
                        if "float-toolbar" in content.lower() or "inject-toolbar" in content.lower():
                            return True
                except Exception:
                    pass
        
        return False
    
    def _get_vercel_project_url(self, artifact: Dict) -> str:
        """Generate Vercel project dashboard URL for an artifact."""
        # Try to get Vercel team/username from environment or config
        vercel_team = os.environ.get("VERCEL_TEAM", "evan-schultzs-projects")
        
        # Get the project name - use the artifact name directly
        # Vercel keeps the original project name in the dashboard
        project_name = artifact.get("name", "")
        
        # Generate the project URL
        return f"https://vercel.com/{vercel_team}/{project_name}"
    
    def fast_toolbar_update(self, limit: int, filter_pattern: Optional[str], parallel: int, force: bool, dry_run: bool):
        """Fast toolbar update using Python for existing sites."""
        console.print(Panel.fit(
            "[bold blue]⚡ Fast Toolbar Update[/bold blue]",
            border_style="blue"
        ))
        
        # Load artifacts catalog
        artifacts_file = self.forest_path / "public" / "artifacts.json"
        if not artifacts_file.exists():
            console.print("[red]❌ No artifacts catalog found![/red]")
            return
        
        with open(artifacts_file) as f:
            data = json.load(f)
        
        artifacts = data.get("artifacts", [])
        
        # Filter artifacts
        if filter_pattern:
            import fnmatch
            artifacts = [a for a in artifacts if fnmatch.fnmatch(a.get("name", ""), filter_pattern)]
        
        # Skip artifacts that already have toolbar (unless force)
        if not force:
            artifacts_to_update = []
            for artifact in artifacts:
                if not self._check_has_toolbar(artifact):
                    artifacts_to_update.append(artifact)
                elif dry_run:
                    console.print(f"[dim]Skipping {artifact['name']} - already has toolbar[/dim]")
            artifacts = artifacts_to_update
        
        # Limit the number of artifacts
        artifacts = artifacts[:limit]
        
        if not artifacts:
            console.print("[green]✅ No artifacts need toolbar update![/green]")
            return
        
        console.print(f"\n[bold]Processing {len(artifacts)} artifacts:[/bold]")
        
        if dry_run:
            table = Table(show_header=True)
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Framework", style="yellow")
            
            for artifact in artifacts:
                table.add_row(
                    artifact.get("name", ""),
                    artifact.get("type", "unknown"),
                    self._detect_framework(Path(artifact.get("path", "")))
                )
            
            console.print(table)
            console.print("\n[yellow]DRY RUN - No changes will be made[/yellow]")
            return
        
        # Download inject-toolbar.sh once
        inject_script_content = self._download_inject_script()
        if not inject_script_content:
            console.print("[red]❌ Failed to download inject-toolbar.sh[/red]")
            return
        
        # Process artifacts in parallel
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
                # Submit all tasks
                future_to_artifact = {}
                for artifact in artifacts:
                    task = progress.add_task(f"Updating {artifact['name']}...", total=None)
                    future = executor.submit(
                        self._update_single_artifact,
                        artifact,
                        inject_script_content,
                        task,
                        progress
                    )
                    future_to_artifact[future] = (artifact, task)
                
                # Process results as they complete
                succeeded = []
                failed = []
                
                for future in concurrent.futures.as_completed(future_to_artifact):
                    artifact, task = future_to_artifact[future]
                    try:
                        success, message = future.result()
                        if success:
                            succeeded.append(artifact)
                            progress.update(task, description=f"[green]✓[/green] {artifact['name']}")
                        else:
                            failed.append((artifact, message))
                            progress.update(task, description=f"[red]✗[/red] {artifact['name']}")
                    except Exception as e:
                        failed.append((artifact, str(e)))
                        progress.update(task, description=f"[red]✗[/red] {artifact['name']}")
                    
                    progress.update(task, completed=True)
        
        # Show results
        console.print(f"\n[bold]Update Results:[/bold]")
        console.print(f"  [green]✅ Updated: {len(succeeded)}[/green]")
        console.print(f"  [red]❌ Failed: {len(failed)}[/red]")
        
        if succeeded:
            console.print("\n[bold green]Successfully Updated:[/bold green]")
            for item in succeeded[:10]:
                console.print(f"  • {item['name']}")
            if len(succeeded) > 10:
                console.print(f"  ... and {len(succeeded) - 10} more")
        
        if failed:
            console.print("\n[bold red]Failed Updates:[/bold red]")
            for item, error in failed[:10]:
                console.print(f"  • {item['name']}: {error}")
            if len(failed) > 10:
                console.print(f"  ... and {len(failed) - 10} more")
    
    def _download_inject_script(self) -> Optional[str]:
        """Download the inject-toolbar.sh script once."""
        try:
            import urllib.request
            with urllib.request.urlopen("https://forest.ritualstack.ai/inject-toolbar.sh") as response:
                return response.read().decode('utf-8')
        except Exception as e:
            console.print(f"[red]Failed to download inject script: {e}[/red]")
            return None
    
    def _detect_framework(self, artifact_path: Path) -> str:
        """Detect the framework of an artifact."""
        if (artifact_path / "next.config.js").exists() or \
           (artifact_path / "next.config.mjs").exists() or \
           (artifact_path / "next.config.ts").exists():
            return "nextjs"
        
        package_json = artifact_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    
                    if "react-scripts" in deps:
                        return "create-react-app"
                    elif "vite" in deps:
                        return "vite"
                    elif "react" in deps:
                        return "react-other"
            except:
                pass
        
        return "unknown"
    
    def _update_single_artifact(self, artifact: Dict, inject_script: str, task_id: int, progress) -> Tuple[bool, str]:
        """Update a single artifact with toolbar injection."""
        try:
            artifact_path = Path(artifact.get("path", self.artifacts_path / artifact["name"]))
            
            if not artifact_path.exists():
                return False, "Artifact path not found"
            
            # Write inject script to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(inject_script)
                inject_script_path = f.name
            
            try:
                # Make script executable
                os.chmod(inject_script_path, 0o755)
                
                # Run inject script
                progress.update(task_id, description=f"Injecting toolbar for {artifact['name']}...")
                
                result = subprocess.run(
                    ["bash", inject_script_path],
                    cwd=str(artifact_path),
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode != 0:
                    return False, f"Injection failed: {result.stderr}"
                
                # Deploy with Vercel
                progress.update(task_id, description=f"Deploying {artifact['name']}...")
                
                deploy_result = subprocess.run(
                    ["vercel", "--prod", "--yes"],
                    cwd=str(artifact_path),
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if deploy_result.returncode != 0:
                    return False, f"Deploy failed: {deploy_result.stderr}"
                
                # Extract URL from output
                url_match = re.search(r'https://[^\s]+\.vercel\.app', deploy_result.stdout)
                if url_match:
                    artifact['deployedUrl'] = url_match.group(0)
                
                return True, "Success"
                
            finally:
                # Clean up temp file
                if os.path.exists(inject_script_path):
                    os.unlink(inject_script_path)
                
        except subprocess.TimeoutExpired:
            return False, "Operation timed out"
        except Exception as e:
            return False, str(e)