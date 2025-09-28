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
        Self {
            meta: Meta {
                title: "PATTERN DISPATCH EVOLUTION".to_string(),
                subtitle: "From mIRC Scripts to Claude Tools".to_string(),
                version: "v1.0.2025.09.25".to_string(),
                context: "ctx:: 2025-09-25 @ 02:02AM → 03:02AM".to_string(),
            },
            sections: vec![
                Section {
                    id: "mirc-patterns".to_string(),
                    title: "mIRC Script Architecture".to_string(),
                    icon: "circle".to_string(),
                    color: "cyan".to_string(),
                    entries: vec![
                        Entry {
                            pattern: "Event-Driven Triggers".to_string(),
                            description: "Pattern matching on message content, user masks, channel context".to_string(),
                            signals: vec![
                                "on *:TEXT:".to_string(),
                                "pattern matching".to_string(),
                                "multi-condition dispatch".to_string(),
                                "contextual routing".to_string(),
                            ],
                            protocol: "Route to appropriate handler based on semantic patterns, not rigid types".to_string(),
                        },
                        Entry {
                            pattern: "Store & Forward".to_string(),
                            description: "Message tossing between channels, context preservation".to_string(),
                            signals: vec![
                                "floatctl toss".to_string(),
                                "cross-channel routing".to_string(),
                                "state persistence".to_string(),
                                "BBS door vibes".to_string(),
                            ],
                            protocol: "Maintain conversation continuity across interface boundaries".to_string(),
                        },
                    ],
                },
                Section {
                    id: "redux-evolution".to_string(),
                    title: "Redux Beyond action.type".to_string(),
                    icon: "square".to_string(),
                    color: "purple".to_string(),
                    entries: vec![Entry {
                        pattern: "Semantic Routing".to_string(),
                        description: "Pattern matching on payload content, user context, operational semantics".to_string(),
                        signals: vec![
                            "action.payload patterns".to_string(),
                            "context-aware dispatch".to_string(),
                            "multi-field matching".to_string(),
                            "flexible categorization".to_string(),
                        ],
                        protocol: "Examine payload content, user context, channel patterns, temporal conditions".to_string(),
                    }],
                },
            ],
        }
    }
}
