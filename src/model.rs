use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Meta {
    pub title: String,
    pub subtitle: String,
    pub version: String,
    pub context: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Entry {
    pub pattern: String,
    pub description: String,
    pub signals: Vec<String>,
    pub protocol: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Section {
    pub id: String,
    pub title: String,
    pub icon: String,
    pub color: String,
    pub entries: Vec<Entry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FieldGuide {
    pub meta: Meta,
    pub sections: Vec<Section>,
}

impl FieldGuide {
    pub fn sample() -> Self {
        serde_json::from_value(serde_json::json!({
            "meta": {
                "title": "PATTERN DISPATCH EVOLUTION",
                "subtitle": "From mIRC Scripts to Claude Tools",
                "version": "v1.0.2025.09.25",
                "context": "ctx:: 2025-09-25 @ 02:02AM → 03:02AM"
            },
            "sections": [
                {
                    "id": "mirc-patterns",
                    "title": "mIRC Script Architecture",
                    "icon": "circle",
                    "color": "cyan",
                    "entries": [
                        {
                            "pattern": "Event-Driven Triggers",
                            "description": "Pattern matching on message content, user masks, channel context",
                            "signals": [
                                "on *:TEXT:",
                                "pattern matching",
                                "multi-condition dispatch",
                                "contextual routing"
                            ],
                            "protocol": "Route to appropriate handler based on semantic patterns, not rigid types"
                        },
                        {
                            "pattern": "Store & Forward",
                            "description": "Message tossing between channels, context preservation",
                            "signals": [
                                "floatctl toss",
                                "cross-channel routing",
                                "state persistence",
                                "BBS door vibes"
                            ],
                            "protocol": "Maintain conversation continuity across interface boundaries"
                        }
                    ]
                },
                {
                    "id": "redux-evolution",
                    "title": "Redux Beyond action.type",
                    "icon": "square",
                    "color": "purple",
                    "entries": [
                        {
                            "pattern": "Semantic Routing",
                            "description": "Pattern matching on payload content, user context, operational semantics",
                            "signals": [
                                "action.payload patterns",
                                "context-aware dispatch",
                                "multi-field matching",
                                "flexible categorization"
                            ],
                            "protocol": "Examine payload content, user context, channel patterns, temporal conditions"
                        }
                    ]
                }
            ]
        }))
        .expect("static sample data is valid")
    }
}
