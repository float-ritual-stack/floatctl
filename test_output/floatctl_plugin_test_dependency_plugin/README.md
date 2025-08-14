# FloatCtl Test_Dependency_Plugin Plugin

A FloatCtl plugin for test_dependency_plugin

## Installation

```bash
pip install floatctl-plugin-test_dependency_plugin
```

## Usage

After installation, the plugin will be automatically available in FloatCtl:

```bash
floatctl test-dependency-plugin --help
```

### Commands

- `floatctl test-dependency-plugin hello` - Say hello from the plugin
- `floatctl test-dependency-plugin echo <message>` - Echo a message

## Configuration

Create a configuration file at `~/.floatctl/config.yaml`:

```yaml
test_dependency_plugin:
  # Add your configuration options here
```

## Development

### Setup

```bash
git clone <your-repo>
cd floatctl-plugin-test_dependency_plugin
pip install -e ".[dev]"
```

### Testing

```bash
pytest
```

### Code Quality

```bash
ruff check .
mypy .
```

## License

MIT License - see LICENSE file for details.
