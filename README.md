# Mozaic Chord Sequence Generator

A modern, type-safe Python toolkit for creating and managing Mozaic chord sequence scripts for the Mozaic iOS music app.

## Features

- **🎹 Modern CLI** - User-friendly command-line interface with Click
- **📦 Pure Python NSKeyedArchiver** - Works on iPad without macOS dependencies
- **🎵 Multi-song support** - Combine multiple songs into one Mozaic script
- **📊 Type-safe models** - Pydantic-based data validation
- **🔄 Persistent ordering** - Maintains song order between runs
- **🌐 Cross-platform** - Works on macOS, Linux, Windows, and any Python 3.10+ environment
- **✅ Fully tested** - 29 comprehensive unit tests with CI/CD

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/mcoin/mozaic-chord-sequence.git
cd mozaic-chord-sequence

# Install dependencies
pip3 install -r requirements.txt
```

### Generate Your First Chord Sequence

```bash
# From a directory of song files
./chord-sequence generate -d songs/ -o output.mozaic

# From specific files
./chord-sequence generate song1.txt song2.txt -o output.mozaic

# With verbose output
./chord-sequence generate -d songs/ -v
```

## Modern CLI Commands

### Main Commands

#### `generate` - Create Mozaic files

```bash
# Generate from directory
./chord-sequence generate -d songs/

# Specify output file
./chord-sequence generate -d songs/ -o myChords.mozaic

# Reset song order
./chord-sequence generate -d songs/ --reset-index

# Use native Foundation encoder (macOS only)
./chord-sequence generate -d songs/ --use-foundation
```

#### `validate` - Check song file format

```bash
./chord-sequence validate songs/AllOfMe.txt
```

#### `list-songs` - Show song order

```bash
./chord-sequence list-songs songs/
```

#### `generate-single` - Quick single-song generation

```bash
./chord-sequence generate-single song.txt
```

### Get Help

```bash
./chord-sequence --help
./chord-sequence generate --help
```

## Song File Format

Each song file should contain:
- **Line 1:** Song title
- **Line 2 (optional):** `tempo=120` (BPM)
- **Remaining lines:** One bar per line, chords separated by spaces

### Example

```
All of Me
tempo=120
C E7 A7
Dm G7 C A7
F Fm C A7
D7 G7 C G7
C E7 A7
...
```

## Project Structure

```
chordSequence/
├── chord-sequence           # Main CLI entry point
├── src/                     # Source package
│   ├── __init__.py         # Public API exports
│   ├── models.py           # Pydantic domain models
│   ├── templates.py        # Jinja2 template management
│   ├── generator.py        # Core generation logic
│   ├── cli.py              # Click CLI commands
│   └── encoders/           # NSKeyedArchiver implementations
│       ├── __init__.py
│       └── archiver.py     # Pure Python & Foundation encoders
├── templates/              # Jinja2 templates
│   └── chord_sequence.mozaic.j2
├── songs/                  # Example song files
├── chordSequenceGenerator.py  # Legacy compatibility wrapper
└── test_chordSequenceGenerator.py  # 29 unit tests
```

## Architecture

### Modern Features (v2.0+)

- **Pydantic Models:** Type-safe `Song`, `Bar`, `SongCollection` models
- **Template Engine:** Jinja2-based script generation
- **Encoder Package:** Shared NSKeyedArchiver with proper deduplication
- **Click CLI:** Modern, user-friendly command interface

### Legacy Compatibility

The old `chordSequenceGenerator.py` API is preserved for backward compatibility:

```python
from chordSequenceGenerator import parse_chord_file, generate_plist

title, tempo, bars = parse_chord_file(Path("song.txt"))
mozaic_bytes = generate_plist(script_text, "filename")
```

All existing tests pass without modification.

## Python API

### High-Level API

```python
from src import ChordSequenceGenerator, Song

# Load songs
songs = [Song.from_file(Path("song1.txt")), Song.from_file(Path("song2.txt"))]

# Generate .mozaic file
generator = ChordSequenceGenerator()
generator.generate_mozaic_file(songs, Path("output.mozaic"))
```

### Low-Level API

```python
from src.models import Song, Bar
from src.encoders import create_mozaic_file

# Create song programmatically
song = Song(
    title="Test Song",
    tempo=120,
    bars=[
        Bar(chords=["C", "F", "G"]),
        Bar(chords=["Am", "Dm", "E7"])
    ]
)

# Generate script
generator = ChordSequenceGenerator()
script = generator.generate_script([song])

# Encode to .mozaic
create_mozaic_file(script, Path("output.mozaic"))
```

## Testing

```bash
# Run all tests
python3 test_chordSequenceGenerator.py

# Or use test runner
./run_tests.sh

# With coverage
pip3 install coverage
coverage run --source=chordSequenceGenerator test_chordSequenceGenerator.py
coverage report -m
```

**Test Results:** 29 tests, 100% passing ✅

See [TESTING.md](TESTING.md) for detailed testing documentation.

## Why Pure Python Encoder?

The pure Python NSKeyedArchiver implementation is **critical for iPad compatibility**:

- ✅ Number deduplication reduces file size (147 → 117 objects)
- ✅ Works without macOS Foundation framework
- ✅ Identical output to native encoder
- ✅ Files load correctly on iPad

Without number deduplication, files won't load on iPad!

## Development

### Dependencies

```bash
pip3 install -r requirements.txt
```

**Core:**
- `pydantic>=2.0.0` - Data validation
- `jinja2>=3.1.0` - Template rendering
- `click>=8.1.0` - CLI framework

**Development:**
- `coverage>=7.0.0` - Code coverage
- `mypy>=1.0.0` - Type checking

### Running from Source

```bash
# Main CLI
./chord-sequence generate -d songs/

# Legacy interface
python3 chordSequenceGenerator.py -d songs/
```

## Additional Tools

### Legacy Tools (Still Available)

These older tools are still included for compatibility:

```bash
# Standalone encoder
python3 mozaic_pure_encoder.py script.txt output.mozaic

# Mozaic file reader
python3 mozaic_reader.py file.mozaic

# Binary editor
python3 mozaic_edit.py file.mozaic
```

## Documentation

- **[README.md](README.md)** - This file
- **[CLAUDE.md](CLAUDE.md)** - Build commands and architecture details
- **[TESTING.md](TESTING.md)** - Comprehensive testing guide
- **[PURE_PYTHON_ENCODER.md](PURE_PYTHON_ENCODER.md)** - Pure Python encoder details

## Contributing

This project uses:
- **Python 3.10+** for modern type hints
- **Pydantic** for data validation
- **Click** for CLI
- **Jinja2** for templates
- **Unit tests** for all features

Run tests before committing:

```bash
./run_tests.sh
```

## License

Generated with [Claude Code](https://claude.com/claude-code)

## Version History

- **v2.0.0** - Modern refactoring with Pydantic, Jinja2, Click
- **v1.0.0** - Original implementation with pure Python encoder

---

🎵 Happy chord sequencing!
