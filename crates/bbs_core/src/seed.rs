use crate::model::*;

pub fn seed_model() -> DataModel {
    DataModel {
        title: "SysOp BBS".to_string(),
        subtitle: "Operator console for FLOAT".to_string(),
        active_view: ViewId::Boot,
        tabs: vec![
            Tab {
                id: ViewId::Boot,
                label: "Boot".to_string(),
                hint: "^1".to_string(),
            },
            Tab {
                id: ViewId::Digest,
                label: "Digest".to_string(),
                hint: "^2".to_string(),
            },
            Tab {
                id: ViewId::ProjectsGrid,
                label: "Projects".to_string(),
                hint: "^3".to_string(),
            },
            Tab {
                id: ViewId::Boards,
                label: "Boards".to_string(),
                hint: "^4".to_string(),
            },
            Tab {
                id: ViewId::Daily,
                label: "Daily".to_string(),
                hint: "^5".to_string(),
            },
            Tab {
                id: ViewId::Essays,
                label: "Essays".to_string(),
                hint: "^6".to_string(),
            },
            Tab {
                id: ViewId::Devtools,
                label: "Dev".to_string(),
                hint: "^7".to_string(),
            },
        ],
        overlays: vec![Overlay {
            title: "Keymap".to_string(),
            body: vec![
                "q: quit".to_string(),
                "tab/shift+tab: cycle tabs".to_string(),
                "g: toggle grid/list".to_string(),
                "/: search projects".to_string(),
                "enter: log link stub".to_string(),
            ],
        }],
        views: vec![
            ViewState {
                id: ViewId::Boot,
                title: "Boot Sequence".to_string(),
                summary: "Brain boot rituals and activation sequences".to_string(),
                tags: vec!["boot".to_string(), "ritual".to_string()],
                kind: ViewData::Boot {
                    phases: vec![
                        BootPhase {
                            label: "Initialize sensors".to_string(),
                            details: vec![
                                "Collect overnight drift".to_string(),
                                "Align autopilot heuristics".to_string(),
                            ],
                        },
                        BootPhase {
                            label: "Focus lens".to_string(),
                            details: vec![
                                "Select persona: sysop".to_string(),
                                "Queue pipeline warmups".to_string(),
                            ],
                        },
                    ],
                },
            },
            ViewState {
                id: ViewId::Digest,
                title: "Telemetry Digest".to_string(),
                summary: "Cross-system telemetry for morning awareness".to_string(),
                tags: vec!["digest".to_string(), "telemetry".to_string()],
                kind: ViewData::Digest {
                    entries: vec![
                        DigestEntry {
                            headline: "Bridge uplink stable".to_string(),
                            context: "Latency under 30ms across floats".to_string(),
                            timestamp: "06:30".to_string(),
                        },
                        DigestEntry {
                            headline: "Dream capture backlog cleared".to_string(),
                            context: "Evna processed 12 new transcripts".to_string(),
                            timestamp: "06:42".to_string(),
                        },
                    ],
                },
            },
            ViewState {
                id: ViewId::ProjectsGrid,
                title: "Projects".to_string(),
                summary: "Active explorations under sysop lens".to_string(),
                tags: vec!["projects".to_string(), "grid".to_string()],
                kind: ViewData::ProjectsGrid {
                    default_layout: LayoutMode::Grid,
                    projects: vec![
                        Project {
                            name: "Ghostline viewer".to_string(),
                            description: "Surface latent thread residues".to_string(),
                            tags: vec!["ghostline".to_string(), "viz".to_string()],
                            status: ProjectStatus::Active,
                            links: vec!["float://ghostline".to_string()],
                        },
                        Project {
                            name: "Concept explorer".to_string(),
                            description: "Navigate sensemaking graph".to_string(),
                            tags: vec!["concept".to_string(), "graph".to_string()],
                            status: ProjectStatus::Exploring,
                            links: vec!["float://concept".to_string()],
                        },
                        Project {
                            name: "Sysop rituals".to_string(),
                            description: "Document boot + shutdown".to_string(),
                            tags: vec!["ops".to_string()],
                            status: ProjectStatus::Maintenance,
                            links: vec!["float://rituals".to_string()],
                        },
                    ],
                },
            },
            ViewState {
                id: ViewId::Boards,
                title: "Boards".to_string(),
                summary: "Shared boards overview".to_string(),
                tags: vec!["boards".to_string()],
                kind: ViewData::Boards {
                    boards: vec![
                        BoardSummary {
                            name: "Ops".to_string(),
                            description: "Operational updates".to_string(),
                            unread: 3,
                        },
                        BoardSummary {
                            name: "Experiments".to_string(),
                            description: "Active experiments + data".to_string(),
                            unread: 0,
                        },
                    ],
                },
            },
            ViewState {
                id: ViewId::Board,
                title: "Ops Board".to_string(),
                summary: "Detailed board threads".to_string(),
                tags: vec!["threads".to_string()],
                kind: ViewData::Board {
                    board: BoardDetail {
                        name: "Ops".to_string(),
                        description: "Mission-critical updates".to_string(),
                        threads: vec![
                            ThreadEntry {
                                subject: "Deploy new float".to_string(),
                                author: "sysop".to_string(),
                                replies: 2,
                                last_updated: "05:22".to_string(),
                            },
                            ThreadEntry {
                                subject: "Schedule downtime".to_string(),
                                author: "evna".to_string(),
                                replies: 5,
                                last_updated: "04:55".to_string(),
                            },
                        ],
                    },
                },
            },
            ViewState {
                id: ViewId::Daily,
                title: "Daily Flow".to_string(),
                summary: "Ritual actions for the day".to_string(),
                tags: vec!["daily".to_string()],
                kind: ViewData::Daily {
                    entries: vec![
                        DailyEntry {
                            title: "Warm caches".to_string(),
                            status: "ready".to_string(),
                            actions: vec![
                                "Check embeddings".to_string(),
                                "Ping GPT nodes".to_string(),
                            ],
                        },
                        DailyEntry {
                            title: "Sync rituals".to_string(),
                            status: "pending".to_string(),
                            actions: vec!["Update boot doc".to_string()],
                        },
                    ],
                },
            },
            ViewState {
                id: ViewId::Essays,
                title: "Essay drafts".to_string(),
                summary: "In-flight longform".to_string(),
                tags: vec!["writing".to_string()],
                kind: ViewData::Essays {
                    essays: vec![
                        EssayEntry {
                            title: "Boring core".to_string(),
                            abstract_text: "Why maintenance is liberation".to_string(),
                            ready: false,
                        },
                        EssayEntry {
                            title: "Liminal ops".to_string(),
                            abstract_text: "Holding the weirdness without burning out".to_string(),
                            ready: true,
                        },
                    ],
                },
            },
            ViewState {
                id: ViewId::Architecture,
                title: "Architecture".to_string(),
                summary: "System schematics".to_string(),
                tags: vec!["architecture".to_string()],
                kind: ViewData::Architecture {
                    sections: vec![
                        ArchitectureSection {
                            name: "Edge routers".to_string(),
                            notes: vec!["Route floats to stable lanes".to_string()],
                        },
                        ArchitectureSection {
                            name: "Memory lattice".to_string(),
                            notes: vec!["Temporal braiding across personas".to_string()],
                        },
                    ],
                },
            },
            ViewState {
                id: ViewId::ConceptExplorer,
                title: "Concept explorer".to_string(),
                summary: "Navigate concepts by energy".to_string(),
                tags: vec!["concept".to_string()],
                kind: ViewData::ConceptExplorer {
                    concepts: vec![
                        ConceptCard {
                            name: "Ops compassion".to_string(),
                            description: "Holding failure states gently".to_string(),
                            energy: 7,
                            category: "ethos".to_string(),
                        },
                        ConceptCard {
                            name: "Bridge weather".to_string(),
                            description: "Ambient sense of cross-float traffic".to_string(),
                            energy: 5,
                            category: "telemetry".to_string(),
                        },
                    ],
                },
            },
            ViewState {
                id: ViewId::GhostlineViewer,
                title: "Ghostline".to_string(),
                summary: "Trace faint conversation residues".to_string(),
                tags: vec!["ghostline".to_string()],
                kind: ViewData::GhostlineViewer {
                    streams: vec![
                        GhostlineEntry {
                            channel: "#ops".to_string(),
                            payload: "[sysop] noticing pattern drift".to_string(),
                            hint: "Tag for retro".to_string(),
                        },
                        GhostlineEntry {
                            channel: "#concept".to_string(),
                            payload: "[evna] exploring new rituals".to_string(),
                            hint: "Link to essay".to_string(),
                        },
                    ],
                },
            },
            ViewState {
                id: ViewId::Devtools,
                title: "Devtools".to_string(),
                summary: "Commands & instrumentation".to_string(),
                tags: vec!["tools".to_string()],
                kind: ViewData::Devtools {
                    commands: vec![
                        DevtoolCommand {
                            name: "Warm caches".to_string(),
                            synopsis: "Preload embeddings".to_string(),
                            command: "floatctl ops warm".to_string(),
                        },
                        DevtoolCommand {
                            name: "Reindex".to_string(),
                            synopsis: "Refresh float index".to_string(),
                            command: "floatctl ops reindex".to_string(),
                        },
                    ],
                },
            },
            ViewState {
                id: ViewId::Ast,
                title: "AST".to_string(),
                summary: "Bridge parser tree".to_string(),
                tags: vec!["ast".to_string()],
                kind: ViewData::Ast {
                    nodes: vec![
                        AstNode {
                            label: "root".to_string(),
                            depth: 0,
                            details: "dispatch".to_string(),
                        },
                        AstNode {
                            label: "persona".to_string(),
                            depth: 1,
                            details: "sysop".to_string(),
                        },
                        AstNode {
                            label: "command".to_string(),
                            depth: 2,
                            details: "boot".to_string(),
                        },
                    ],
                },
            },
            ViewState {
                id: ViewId::MultisiteTiles,
                title: "Multisite".to_string(),
                summary: "Linked float surfaces".to_string(),
                tags: vec!["multisite".to_string()],
                kind: ViewData::MultisiteTiles {
                    sites: vec![
                        SiteTile {
                            handle: "home".to_string(),
                            url: "https://float.city".to_string(),
                            status: "healthy".to_string(),
                        },
                        SiteTile {
                            handle: "lab".to_string(),
                            url: "https://lab.float.city".to_string(),
                            status: "maintenance".to_string(),
                        },
                    ],
                },
            },
            ViewState {
                id: ViewId::Unknown,
                title: "Unknown".to_string(),
                summary: "Placeholder for unconfigured views".to_string(),
                tags: vec!["unknown".to_string()],
                kind: ViewData::Unknown {
                    note: "No renderer available".to_string(),
                },
            },
        ],
    }
}
