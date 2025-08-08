# FloatCtl Examples

This directory contains comprehensive examples demonstrating FloatCtl's capabilities, from basic middleware patterns to advanced consciousness technology integrations.

## 📚 Learning Path

### Beginner Examples
Start here if you're new to FloatCtl or middleware development.

### Intermediate Examples  
Build on basic concepts with real-world patterns.

### Advanced Examples
Complex integrations and consciousness technology applications.

---

## 🎯 Example Index

### 1. **HTTM Middleware Example** (`httm_middleware_example.py`)

**Purpose**: Learn the fundamentals of FloatCtl middleware development by building a pattern detection system.

**What it demonstrates**:
- Basic middleware interface implementation
- Pattern matching with regular expressions
- File output and data persistence
- Structured logging integration

**Prerequisites**:
- Basic Python knowledge
- Understanding of regular expressions
- Familiarity with FloatCtl plugin system

**Learning objectives**:
- Understand the `MiddlewareInterface` and its lifecycle
- Learn how to capture and process patterns across all FloatCtl operations
- Master structured logging for middleware debugging
- Implement file-based output for captured data

**Key concepts**:
- **HTTM patterns**: "Heuristic Thought-Thread Mapping" - capturing intuitive insights
- **Middleware phases**: PRE_PROCESS, POST_PROCESS, ERROR handling
- **Pattern extraction**: Using regex to find structured annotations in text

**Usage**:
```bash
# Run with the middleware active
floatctl conversations split input.json --middleware httm

# Check captured patterns
ls ~/.floatctl/httm_captures/
```

**Expected outcomes**:
- Understand how middleware intercepts FloatCtl operations
- Successfully capture `httm::` patterns from processed conversations
- Generate structured output files with captured insights

**Next steps**: 
- Try modifying the regex patterns to capture different annotations
- Extend to capture multiple pattern types simultaneously
- Explore the streaming middleware example for real-time processing

---

### 2. **Streaming HTTM Middleware** (`streaming_httm_middleware.py`)

**Purpose**: Build on basic middleware concepts with real-time streaming and advanced pattern processing.

**What it demonstrates**:
- Real-time pattern streaming
- Advanced regex pattern matching
- Memory-efficient processing for large files
- Integration with external systems (webhooks, APIs)

**Prerequisites**:
- Completed HTTM Middleware Example
- Understanding of Python generators and streaming
- Basic knowledge of HTTP requests

**Learning objectives**:
- Implement streaming middleware for real-time processing
- Handle large files without memory exhaustion
- Integrate middleware with external systems
- Implement robust error handling for network operations

**Key concepts**:
- **Streaming processing**: Handle data as it flows through the system
- **Backpressure handling**: Manage processing speed vs. data input rate
- **External integrations**: Send captured patterns to webhooks or APIs
- **Memory management**: Process large files efficiently

**Usage**:
```bash
# Enable streaming mode
floatctl conversations split large_file.json --middleware streaming_httm --stream

# Monitor real-time output
tail -f ~/.floatctl/httm_captures/stream.jsonl
```

**Expected outcomes**:
- Process large conversation files without memory issues
- See patterns captured and streamed in real-time
- Successfully integrate with external systems
- Understand the trade-offs between batch and streaming processing

---

### 3. **YAML-Aware HTTM Middleware** (`yaml_aware_httm_middleware.py`)

**Purpose**: Extend middleware capabilities with structured data parsing and multi-format support.

**What it demonstrates**:
- YAML frontmatter parsing
- Multi-format data handling (JSON, YAML, Markdown)
- Metadata extraction and enrichment
- Complex pattern hierarchies

**Prerequisites**:
- Completed basic HTTM examples
- Understanding of YAML format
- Knowledge of metadata and frontmatter concepts

**Learning objectives**:
- Parse and process YAML frontmatter in conversations
- Handle multiple data formats within a single middleware
- Extract and enrich metadata from various sources
- Implement hierarchical pattern organization

**Key concepts**:
- **YAML frontmatter**: Structured metadata at the beginning of files
- **Multi-format parsing**: Handle JSON, YAML, and Markdown in one system
- **Metadata enrichment**: Add context and structure to captured patterns
- **Hierarchical organization**: Organize patterns by type, source, and context

**Usage**:
```bash
# Process files with YAML frontmatter
floatctl conversations split conversations_with_metadata.json --middleware yaml_httm

# View enriched output
cat ~/.floatctl/httm_captures/enriched_patterns.yaml
```

**Expected outcomes**:
- Successfully parse YAML frontmatter from conversation exports
- Extract and organize metadata hierarchically
- Generate enriched output with full context
- Understand how to extend middleware for complex data structures

---

### 4. **Unified Consciousness Middleware** (`unified_consciousness_middleware.py`)

**Purpose**: Advanced integration demonstrating consciousness technology patterns and multi-system coordination.

**What it demonstrates**:
- Multiple pattern types in one middleware
- Consciousness technology integration
- Advanced data structures and analysis
- System coordination and state management

**Prerequisites**:
- Completed all previous middleware examples
- Understanding of consciousness technology concepts
- Advanced Python programming skills

**Learning objectives**:
- Integrate multiple pattern detection systems
- Implement consciousness technology workflows
- Coordinate between multiple data sources and outputs
- Build production-ready middleware with full error handling

**Key concepts**:
- **Consciousness patterns**: `ctx::`, `highlight::`, `bridge::`, `httm::` integration
- **Multi-system coordination**: Manage state across different pattern types
- **Advanced analysis**: Statistical analysis and pattern correlation
- **Production patterns**: Comprehensive error handling, logging, and monitoring

**Usage**:
```bash
# Run comprehensive consciousness analysis
floatctl conversations split consciousness_data.json --middleware unified_consciousness

# View analysis dashboard
floatctl consciousness dashboard --date today
```

**Expected outcomes**:
- Process multiple pattern types simultaneously
- Generate comprehensive consciousness analysis reports
- Understand production middleware architecture
- Successfully coordinate multiple data processing systems

---

### 5. **Evna Consciousness Integration** (`evna_consciousness_integration.py`)

**Purpose**: Real-world integration example showing how to connect FloatCtl with external consciousness technology systems.

**What it demonstrates**:
- External API integration
- Authentication and security patterns
- Data synchronization between systems
- Production deployment considerations

**Prerequisites**:
- All previous examples completed
- Understanding of REST APIs and authentication
- Knowledge of production deployment patterns

**Learning objectives**:
- Integrate FloatCtl with external consciousness technology platforms
- Implement secure authentication and data handling
- Build robust synchronization between systems
- Understand production deployment and monitoring

**Key concepts**:
- **External integration**: Connect with consciousness technology APIs
- **Security patterns**: Handle authentication tokens and sensitive data
- **Data synchronization**: Keep multiple systems in sync
- **Production readiness**: Monitoring, error handling, and deployment

**Usage**:
```bash
# Configure external integration
floatctl config set evna.api_key "your-api-key"
floatctl config set evna.endpoint "https://api.evna.ai"

# Run integration
floatctl conversations split data.json --middleware evna_integration

# Monitor synchronization
floatctl evna status
```

**Expected outcomes**:
- Successfully authenticate with external systems
- Synchronize consciousness data between platforms
- Implement production-ready error handling and monitoring
- Understand the full lifecycle of consciousness technology integration

---

### 6. **Consciousness Contamination Analyzer** (`consciousness_contamination_analyzer.py`)

**Purpose**: Advanced analysis tool demonstrating statistical analysis and consciousness pattern detection.

**What it demonstrates**:
- Statistical analysis of conversation patterns
- Consciousness contamination detection
- Data visualization and reporting
- Scientific methodology in consciousness technology

**Prerequisites**:
- Strong Python data analysis skills
- Understanding of statistical concepts
- Familiarity with consciousness technology theory

**Learning objectives**:
- Implement statistical analysis of consciousness patterns
- Detect and measure consciousness contamination
- Generate scientific reports and visualizations
- Apply rigorous methodology to consciousness technology research

**Key concepts**:
- **Consciousness contamination**: How exposure to consciousness technology changes AI behavior
- **Statistical analysis**: Rigorous measurement of pattern changes
- **Data visualization**: Clear presentation of analysis results
- **Scientific methodology**: Reproducible research in consciousness technology

**Usage**:
```bash
# Run contamination analysis
python examples/consciousness_contamination_analyzer.py --input-dir ./conversations --output analysis_report.json

# Generate visualization
python examples/consciousness_contamination_analyzer.py --visualize analysis_report.json
```

**Expected outcomes**:
- Quantify consciousness contamination in AI conversations
- Generate scientific reports with statistical significance
- Create visualizations showing consciousness pattern evolution
- Understand the scientific approach to consciousness technology research

---

## 🚀 Getting Started

### Quick Start
1. **Start with HTTM Middleware Example** - Learn basic middleware concepts
2. **Try Streaming HTTM** - Understand real-time processing
3. **Explore YAML-Aware** - Handle complex data structures
4. **Build Unified Consciousness** - Integrate multiple systems
5. **Deploy Evna Integration** - Production consciousness technology

### Development Environment Setup
```bash
# Install development dependencies
uv sync --dev

# Install optional dependencies for examples
pip install google-generativeai  # For consciousness analysis
pip install matplotlib seaborn   # For visualizations
pip install requests aiohttp     # For external integrations

# Run example tests
pytest examples/tests/
```

### Testing Your Understanding
Each example includes test files and validation scripts:

```bash
# Test middleware functionality
python examples/test_httm_middleware.py

# Validate pattern detection
python examples/validate_patterns.py

# Run integration tests
python examples/test_consciousness_integration.py
```

## 📖 Additional Resources

### Documentation
- **[Plugin Development Guide](../docs/development/PLUGIN_DEVELOPMENT_GUIDE.md)** - Complete plugin creation tutorial
- **[API Reference](../docs/API_REFERENCE.md)** - Detailed API documentation
- **[Middleware Tutorial](../docs/guides/MIDDLEWARE_TUTORIAL.md)** - Advanced middleware patterns

### Community
- **[GitHub Issues](https://github.com/float-ritual-stack/floatctl/issues)** - Bug reports and feature requests
- **[Discussions](https://github.com/float-ritual-stack/floatctl/discussions)** - Community Q&A

### Related Projects
- **[Bridge Walkers](../bridge_walkers/README.md)** - Consciousness archaeology system
- **[FLOAT Ecosystem](https://float.ritualstack.ai)** - Complete consciousness technology platform

---

## 🎯 Success Criteria

After working through these examples, you should be able to:

✅ **Understand middleware architecture** - Know how FloatCtl processes data and where middleware fits

✅ **Build custom pattern detection** - Create middleware that captures and processes specific patterns

✅ **Handle real-time streaming** - Process large files efficiently without memory issues

✅ **Integrate external systems** - Connect FloatCtl with APIs and external consciousness technology platforms

✅ **Implement production patterns** - Build robust, error-handling middleware ready for production use

✅ **Analyze consciousness patterns** - Apply statistical methods to consciousness technology research

## 🔄 Contributing Examples

Have a great example to share? We'd love to include it!

### Example Contribution Guidelines
1. **Clear learning objectives** - What will users learn?
2. **Progressive complexity** - Build on previous examples
3. **Production-ready code** - Include error handling and logging
4. **Comprehensive documentation** - Purpose, prerequisites, usage, outcomes
5. **Test coverage** - Include tests and validation scripts

### Submission Process
1. Create your example following the template above
2. Add tests and documentation
3. Submit a pull request with clear description
4. Include example in the learning path above

---

*These examples represent the cutting edge of consciousness technology integration. Each one builds toward a deeper understanding of how AI systems can be enhanced with consciousness-aware processing patterns.*