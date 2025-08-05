# FloatCtl Test_Example Plugin

A FloatCtl plugin for test_example

## Installation

```bash
pip install floatctl-plugin-test_example
```

## Usage

After installation, the plugin will be automatically available in FloatCtl:

```bash
floatctl test-example --help
```

### Commands

- `floatctl test-example hello` - Say hello from the plugin
- `floatctl test-example echo <message>` - Echo a message

## Configuration

Create a configuration file at `~/.floatctl/config.yaml`:

```yaml
test_example:
  # Add your configuration options here
```

## Development

### Setup

```bash
git clone <your-repo>
cd floatctl-plugin-test_example
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
