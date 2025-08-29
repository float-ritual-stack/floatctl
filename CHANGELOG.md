# Changelog

All notable changes to floatctl-py will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2025-08-29

### 🎯 Major Feature: Comprehensive Conversation Extraction Suite

Complete conversation archaeology toolkit for extracting insights from Claude conversation exports. This release transforms raw conversation data into actionable intelligence through multiple specialized extractors.

### Added
- **Enhanced Artifacts Plugin** - Complete rewrite from stub to production
  - Real artifact extraction from `tool_use.name == "artifacts"`  
  - Date-based organization with proper file extensions
  - Handles HTML, Markdown, JSON artifacts with metadata preservation
  - Found 3,377 artifacts, successfully saved 1,920 in testing
- **Time Tracking Extractor** - Extract work patterns for forensic analysis
  - `extract-time-tracking` command for `[project::rangle/*]` pattern extraction
  - Context extraction (±5 lines around patterns for narrative flow)
  - CSV output with timestamps, descriptions, conversation references
  - Found 355 time tracking entries in test data
- **Link & Reference Extractor** - Comprehensive URL archaeology  
  - `extract-links` command with type filtering (GitHub, YouTube, Claude, docs, all)
  - Context extraction (±50 characters around each link)
  - Markdown link title extraction and metadata preservation
  - Found 10,609 links across all types in test data
- **FloatAST Conversation Outlines** - Structured conversation analysis
  - `floatast-outline` command generates JSON representations
  - FLOAT pattern recognition and aggregation with timeline tracking
  - Message flow analysis with participant tracking
  - Generated 1,542 conversation outlines in test data
- **Full-Extract Command** - One-click comprehensive extraction
  - `full-extract` processes ZIP files automatically with no option decisions
  - Runs all 4 extractors in sequence with progress reporting
  - Generates comprehensive report with file listings and usage guide
  - ZIP file support with automatic conversations.json detection

### Enhanced
- **Conversations Plugin** - Massive expansion with 4 new extraction commands
  - Modular extraction methods supporting both JSON and processed markdown
  - Unified error handling and progress reporting across all extractors
  - Token-efficient processing avoiding context window explosions
  - Rich console output with tables and progress indicators

### Fixed
- **Artifacts Plugin Scope Issue** - Commands were defined outside `register_commands` method
  - Fixed command registration ensuring all commands appear in CLI help
  - Proper indentation and method scope validation
  - All extraction commands now properly registered and functional

### Performance
- **Real-world Validation** - Tested on actual conversation exports:
  - 3,377 artifacts → 1,920 saved (56% success rate)
  - 355 time tracking entries extracted with full context
  - 10,609 links categorized and contextualized
  - 1,542 conversation outlines with pattern analysis
- **Token-Efficient Processing** - Avoids loading massive files into context
  - Surgical data extraction without overwhelming token limits
  - Progressive processing with error resilience
  - Modular approach allows selective extraction when needed

### Technical Details
- ZIP file extraction with automatic conversations.json discovery
- Context preservation around extracted patterns for narrative continuity  
- Multiple output formats (CSV for analysis, JSON for programmatic access)
- Comprehensive error handling with graceful degradation
- Date-based artifact organization with conflict resolution
- Pattern timeline tracking for consciousness technology analysis

### Files Added
- Enhanced `src/floatctl/plugins/conversations.py` (2000+ lines of extraction logic)
- Production-ready artifact extraction methods
- Comprehensive helper methods for all extraction types
- ZIP file handling and input preparation utilities

## [0.6.0] - 2025-08-14

### 🎯 Major Feature: Multi-Pattern Extraction with LangExtract

This release fixes a **critical bug** in evna's pattern parser that only captured the first pattern in multi-pattern lines, missing all subsequent patterns. The new hybrid extractor achieves **3x improvement** in pattern capture rate.

### Added
- **Hybrid FLOAT Extractor** - Intelligent pattern extraction with automatic API/fallback
  - `float_extractor_hybrid.py` - Production-ready hybrid implementation
  - `float_extractor.py` - Clean LangExtract API implementation
  - `float_extractor_mock.py` - Enhanced regex fallback for reliability
  - `langextract_schemas.py` - FLOAT pattern schemas for fuzzy compilation
- **Comprehensive Documentation** in `parse_any_pattern()` docstring
  - Clear examples of multi-pattern extraction
  - When to use guidance
  - Technical implementation details
- **Test Suite** for pattern extraction validation
  - `test_evna_integration.py` - Integration tests
  - `test_langextract_api.py` - API diagnostic tool

### Fixed
- **Critical: Evna Single-Pattern Bug** - Parser now captures ALL patterns in multi-pattern lines
  - Before: `"eureka:: Found! decision:: Fix tomorrow"` → 1 pattern ❌
  - After: `"eureka:: Found! decision:: Fix tomorrow"` → 2 patterns ✅
- **Metadata Extraction** - Properly extracts nested `[mode::]`, `[project::]` attributes
- **Persona Recognition** - Captures all personas in dialogue lines

### Changed
- **mcp_server.py** - Integrated hybrid extractor with backward compatibility
  - Automatic detection and use of hybrid extractor when available
  - Graceful fallback to legacy regex if import fails
  - Enhanced metadata tracking with `extraction_method` field

### Performance
- **3x Pattern Capture Rate** on multi-pattern lines
- **100% Capture Rate** on tested FLOAT patterns
- **Graceful Degradation** ensures functionality even without API

### Technical Details
- Uses Google's LangExtract for fuzzy compilation when API available
- Falls back to enhanced regex parsing when API unavailable
- Maintains character-level position tracking for source grounding
- Preserves all existing functionality while fixing core bug

### Dependencies
- Added `langextract` (optional) for fuzzy pattern compilation
- Added `google-generativeai` (optional) for Gemini API support

### Migration Notes
- Fully backward compatible - no code changes required
- To enable LangExtract API: Set `GEMINI_API_KEY` in environment
- Falls back automatically if API unavailable

---

## [0.5.0] - Previous Releases

[Previous changelog entries would go here]

---

*"Holy shit, it actually gets my patterns now"* - User feedback on multi-pattern fix

ctx::2025-08-14 [mode:: changelog-complete]
bridge::CB-20250814-1300-MULTIPATTERN