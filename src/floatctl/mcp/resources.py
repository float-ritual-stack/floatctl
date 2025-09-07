"""MCP resources and prompts for FLOAT consciousness technology :: resources.

This module contains MCP resources and prompts for consciousness technology operations.
Extracted from the monolithic mcp_server.py for maintainability.
"""

import json
import random
from datetime import datetime, timezone
from typing import Dict, Any, List

# Import utilities from modular structure
from floatctl.mcp.utils import get_chroma_client, search_prompts

# Consciousness-oriented prompt library
PROMPT_LIBRARY = {
    "consciousness_archaeology": {
        "prompt": """I need you to perform consciousness archaeology on this conversation/document. Look for:

- Hidden patterns and recurring themes
- Unconscious assumptions being made
- Power dynamics and whose voices are centered/marginalized  
- What's being said vs what's being avoided
- Emotional undertones and energy shifts
- Places where authentic self breaks through performative layers
- Moments of genuine insight vs surface-level analysis
- How language choices reveal deeper beliefs
- What this reveals about the person's relationship to themselves/others/work

Be direct, insightful, and don't hold back. I want the real archaeology, not polite observations.""",
        "tags": ["analysis", "consciousness", "archaeology", "patterns"],
        "usage_count": 0
    },
    
    "ritual_computing": {
        "prompt": """Help me design a ritual computing protocol for this situation. Consider:

- What repetitive actions create consciousness change?
- How can structured data serve meaning-making?
- What boundaries need to be established?
- How does this serve authentic human experience?
- What would make this feel sacred rather than mechanical?
- How can technology amplify rather than replace human ritual?

Focus on practical, implementable protocols that honor both efficiency and meaning.""",
        "tags": ["ritual", "computing", "protocol", "consciousness"],
        "usage_count": 0
    },
    
    "neuroqueer_analysis": {
        "prompt": """Analyze this through a neuroqueer lens. Look for:

- How neurotypical assumptions are embedded
- Where masking or performance might be happening
- Opportunities for more authentic expression
- How systems could be redesigned for neurodivergent thriving
- What accommodations or modifications would help
- How to honor different processing styles
- Ways to reduce cognitive load and overwhelm

Be specific and actionable, not just theoretical.""",
        "tags": ["neuroqueer", "analysis", "accessibility", "authenticity"],
        "usage_count": 0
    },
    
    "shack_not_cathedral": {
        "prompt": """Apply 'shacks not cathedrals' philosophy to this. Help me:

- Strip away unnecessary complexity
- Focus on what actually serves the user (me)
- Identify over-engineering or premature abstraction
- Find the minimal viable solution
- Prioritize working over perfect
- Build for iteration, not permanence
- Make it maintainable by one person
- Optimize for immediate utility

What's the shack version of this?""",
        "tags": ["philosophy", "simplicity", "pragmatic", "minimal"],
        "usage_count": 0
    },
    
    "context_crunch": {
        "prompt": """I'm hitting context limits. Help me:

1. Identify the core 20% that gives 80% of the value
2. Summarize key decisions and their rationale
3. Extract actionable next steps
4. Preserve essential context for continuation
5. Note what can be safely discarded
6. Create a bridge to the next conversation

Be ruthless about cutting fluff while preserving essence.""",
        "tags": ["context", "summarization", "efficiency", "continuation"],
        "usage_count": 0
    }
}


async def ritual_prompt(
    ritual_name: str = "session_sync",
    include_context: bool = True
) -> List[Dict[str, Any]]:
    """Get a ritual prompt from float_ritual collection.
    
    This dynamically fetches prompts from ChromaDB, making them
    available as MCP prompts that Claude Desktop can discover.
    
    Args:
        ritual_name: Name or search term for the ritual (e.g., 'session_sync', 'annotate')
        include_context: Whether to include recent context in the prompt
    """
    try:
        # Use existing get_prompt logic to search float_ritual collection
        chroma = get_chroma_client()
        results = chroma.search_context(
            collection_name="float_ritual",
            query=ritual_name,
            limit=1
        )
        
        if not results:
            # Fallback to a helpful message
            return [{
                "role": "user",
                "content": {
                    "type": "text",
                    "text": f"No ritual found for '{ritual_name}'. Available rituals include: session_sync, annotate, coordination patterns. Use the get_prompt tool to explore the float_ritual collection."
                }
            }]
        
        best_result = results[0]
        content = best_result.get("content", "")
        metadata = best_result.get("metadata", {})
        
        # Start with the ritual content as the main prompt
        messages = [{
            "role": "user",
            "content": {
                "type": "text",
                "text": content
            }
        }]
        
        # Optionally add recent context as a second message
        if include_context:
            try:
                # Get recent context (last 6 hours)
                context_results = chroma.query_recent_context(
                    collection_name="active_context_stream",
                    hours=6,
                    limit=5
                )
                
                if context_results.get("documents"):
                    context_items = []
                    for doc, meta in zip(
                        context_results.get("documents", []),
                        context_results.get("metadatas", [])
                    ):
                        timestamp = meta.get("timestamp", "")
                        project = meta.get("project", "")
                        mode = meta.get("mode", "")
                        
                        context_line = f"[{timestamp}]"
                        if project:
                            context_line += f" [project::{project}]"
                        if mode:
                            context_line += f" [mode::{mode}]"
                        context_line += f" {doc[:150]}..."
                        
                        context_items.append(context_line)
                    
                    messages.append({
                        "role": "user", 
                        "content": {
                            "type": "text",
                            "text": f"Recent Context (last 6 hours):\n\n" + "\n\n".join(context_items)
                        }
                    })
            except Exception as e:
                # Context is optional - don't fail the whole prompt if it fails
                pass
        
        return messages
        
    except Exception as e:
        # Fallback error message
        return [{
            "role": "user",
            "content": {
                "type": "text", 
                "text": f"Error loading ritual '{ritual_name}': {str(e)}. Try using the get_prompt tool directly."
            }
        }]


async def create_bridge(
    focus: str = "current conversation",
    threads: str = "",
    project: str = ""
) -> List[Dict[str, Any]]:
    """
    Generate a bridge creation template for current context.
    
    Args:
        focus: What to focus the bridge on (default: "current conversation")
        threads: Comma-separated active threads to preserve
        project: Current project context (optional)
    """
    try:
        # Generate CB-YYYYMMDD-HHMM-XXXX format ID
        now = datetime.now()
        bridge_id = f"CB-{now.strftime('%Y%m%d-%H%M')}-{random.randint(4096,65535):04X}"
        
        # Build thread list
        thread_list = []
        if threads:
            thread_list = [thread.strip() for thread in threads.split(",") if thread.strip()]
        
        # Format project context
        project_context = f"\nProject: {project}" if project else ""
        
        # Create the bridge template message
        bridge_template = f"""# Continuity Anchor: {bridge_id}

## Session Context
Date: {now.strftime('%Y-%m-%d')}
Timestamp: {now.strftime('%H:%M:%S')}
Focus: {focus}{project_context}
Active Threads: {', '.join(thread_list) if thread_list else 'general conversation'}

## Bridge Content
[This section will be populated with the conversation summary when you run bridge::create]

## Active Threads
{chr(10).join([f'1. **{thread}**' for thread in thread_list]) if thread_list else '1. **General conversation flow**'}

## Resumption Instructions

```
bridge::restore {bridge_id}
```

To activate this bridge:
1. Copy the bridge content above
2. Save it to your vault or context system
3. Use the restore command when continuing the session

Generated: {now.isoformat()}
"""
        
        return [{
            "role": "user",
            "content": {
                "type": "text",
                "text": bridge_template
            }
        }]
        
    except Exception as e:
        return [{
            "role": "user", 
            "content": {
                "type": "text",
                "text": f"Error creating bridge template: {str(e)}"
            }
        }]


async def get_recent_bridges_resource() -> Dict[str, Any]:
    """List the 5 most recent bridges for quick access."""
    try:
        chroma = get_chroma_client()
        
        # Get the 5 most recent bridges (from the end of the collection)
        total_count = chroma.count_documents(collection_name="float_bridges")
        offset = max(0, total_count - 5)  # Get last 5 documents
        
        results = chroma.get_documents(
            collection_name="float_bridges",
            limit=5,
            offset=offset,
            include=["documents", "metadatas"]
        )
        
        # Reverse the order so newest is first
        if results.get("documents"):
            results["documents"] = list(reversed(results["documents"]))
            results["metadatas"] = list(reversed(results["metadatas"]))
            if "ids" in results:
                results["ids"] = list(reversed(results["ids"]))
        
        # Format for resource consumption
        bridges_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_bridges": total_count,
            "recent_count": len(results.get("documents", [])),
            "bridges": []
        }
        
        for doc, meta, doc_id in zip(
            results.get("documents", []),
            results.get("metadatas", []),
            results.get("ids", [])
        ):
            bridge_id = meta.get("bridge_id", meta.get("anchor_id", f"bridge_{doc_id}"))
            bridges_data["bridges"].append({
                "bridge_id": bridge_id,
                "created": meta.get("timestamp", ""),
                "active_threads": meta.get("active_threads", "").split(",") if meta.get("active_threads") else [],
                "mode": meta.get("mode", ""),
                "project": meta.get("project", ""),
                "preview": doc[:150] + "..." if len(doc) > 150 else doc,
                "restoration_command": f"bridge::restore {bridge_id}",
                "resource_uri": f"bridge://{bridge_id}"
            })
        
        return {
            "uri": "bridge://recent",
            "mimeType": "application/json",
            "text": json.dumps(bridges_data, indent=2)
        }
        
    except Exception as e:
        # Return error as JSON resource
        error_data = {
            "error": f"Failed to load recent bridges: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fallback": "Use smart_chroma_query with collection='float_bridges' instead"
        }
        
        return {
            "uri": "bridge://recent", 
            "mimeType": "application/json",
            "text": json.dumps(error_data, indent=2)
        }


async def search_bridges_resource() -> Dict[str, Any]:
    """Search interface for finding bridges by content or metadata."""
    try:
        chroma = get_chroma_client()
        
        # Get collection info for search guidance  
        total_count = chroma.count_documents(collection_name="float_bridges")
        
        collection_info = {
            "collection_name": "float_bridges",
            "total_bridges": total_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "search_instructions": {
                "specific_bridge": "Use resource: bridge://{bridge_id}",
                "by_date": "Use resource: bridge://YYYYMMDD for fuzzy date search", 
                "latest_bridge": "Use resource: bridge://latest",
                "semantic_search": "Use tool: smart_chroma_query with collection='float_bridges'"
            },
            "available_metadata": [
                "bridge_id", "timestamp", "active_threads", "mode", 
                "project", "conversation_id", "anchor_id"
            ],
            "example_queries": [
                "bridge::restore CB-20250511-2000-7B3D",
                "bridge://latest",  
                "bridge://20250807",
                "smart_chroma_query('airbender', collection='float_bridges')"
            ]
        }
        
        return {
            "uri": "bridge://search",
            "mimeType": "application/json", 
            "text": json.dumps(collection_info, indent=2)
        }
        
    except Exception as e:
        # Return error as JSON resource
        error_data = {
            "error": f"Failed to load bridge search info: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fallback": "Use smart_chroma_query tool instead"
        }
        
        return {
            "uri": "bridge://search",
            "mimeType": "application/json",
            "text": json.dumps(error_data, indent=2)
        }


def find_related_bridges(bridge_id: str, chroma_client) -> List[Dict[str, str]]:
    """Find bridges that reference this one or share context."""
    try:
        # Search for bridges that mention this bridge ID
        results = chroma_client.query_documents(
            collection_name="float_bridges",
            query_texts=[bridge_id],
            n_results=3,
            include=["metadatas"]
        )
        
        related = []
        for meta in results.get("metadatas", []):
            if meta.get("bridge_id") != bridge_id:  # Don't include self
                related.append({
                    "bridge_id": meta.get("bridge_id", ""),
                    "timestamp": meta.get("timestamp", ""),
                    "threads": meta.get("active_threads", "")
                })
        
        return related[:2]  # Limit to 2 related bridges
        
    except Exception as e:
        return [{"error": f"Could not find related bridges: {str(e)}"}]


async def get_bridge_by_id(bridge_id: str) -> Dict[str, Any]:
    """
    Restore a specific bridge by its ID for session continuation.
    
    Example URIs:
    - bridge://CB-20250807-1430-A7B3
    - bridge://latest  (special case for most recent)  
    - bridge://20250807  (fuzzy match by date)
    """
    try:
        chroma = get_chroma_client()
        results = None
        search_method = ""
        
        # Handle special cases
        if bridge_id == "latest":
            # Get the most recent bridge
            search_method = "latest_bridge"
            results = chroma.get_documents(
                collection_name="float_bridges",
                limit=1,
                include=["documents", "metadatas"]
            )
        elif len(bridge_id) == 8 and bridge_id.isdigit():
            # Date-based fuzzy search (YYYYMMDD)
            search_method = f"date_search_{bridge_id}"
            results = chroma.query_documents(
                collection_name="float_bridges", 
                query_texts=[f"CB-{bridge_id}"],
                n_results=3,
                include=["documents", "metadatas"]
            )
        else:
            # Try exact bridge ID lookup first
            search_method = f"exact_id_{bridge_id}"
            try:
                results = chroma.query_documents(
                    collection_name="float_bridges",
                    query_texts=[bridge_id],
                    n_results=1,
                    include=["documents", "metadatas"]
                )
            except:
                # Fallback to semantic search
                search_method = f"semantic_search_{bridge_id}"
                results = chroma.query_documents(
                    collection_name="float_bridges",
                    query_texts=[bridge_id],
                    n_results=1, 
                    include=["documents", "metadatas"]
                )
        
        # Format for restoration
        if results and results.get("documents"):
            doc = results["documents"][0]
            meta = results.get("metadatas", [{}])[0]
            found_bridge_id = meta.get("bridge_id", bridge_id)
            
            bridge_data = {
                "bridge_id": found_bridge_id,
                "created": meta.get("timestamp", ""),
                "active_threads": meta.get("active_threads", "").split(",") if meta.get("active_threads") else [],
                "mode": meta.get("mode", ""),
                "project": meta.get("project", ""),
                "conversation_id": meta.get("conversation_id", ""),
                "content": doc,
                "search_method": search_method,
                "related_bridges": find_related_bridges(found_bridge_id, chroma),
                "restoration_instructions": [
                    "This bridge contains session context for continuation",
                    "Review the content to understand previous discussion",
                    "Use the active threads to guide next steps",
                    f"Bridge restored via method: {search_method}"
                ]
            }
            
            return {
                "uri": f"bridge://{bridge_id}",
                "mimeType": "application/json",
                "text": json.dumps(bridge_data, indent=2)
            }
        else:
            # No bridge found
            error_data = {
                "error": f"Bridge '{bridge_id}' not found",
                "search_method": search_method,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "suggestions": [
                    "Try bridge://latest for most recent bridge",
                    "Use bridge://YYYYMMDD for date-based search",
                    "Use bridge://recent resource to see available bridges",
                    "Use smart_chroma_query tool to search bridge content"
                ]
            }
            
            return {
                "uri": f"bridge://{bridge_id}",
                "mimeType": "application/json", 
                "text": json.dumps(error_data, indent=2)
            }
            
    except Exception as e:
        # Return error as JSON resource
        error_data = {
            "error": f"Failed to load bridge '{bridge_id}': {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fallback": "Use smart_chroma_query tool instead"
        }
        
        return {
            "uri": f"bridge://{bridge_id}",
            "mimeType": "application/json",
            "text": json.dumps(error_data, indent=2)
        }