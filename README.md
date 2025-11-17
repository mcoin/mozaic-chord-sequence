# Mozaic Chord Sequence Generator

A Python toolset for creating and managing Mozaic chord sequence scripts for the Mozaic iOS music app.

## Features

- **Pure Python NSKeyedArchiver encoder** - Works on iPad without macOS dependencies
- **Multi-song chord sequence generator** - Combine multiple songs into one Mozaic script
- **Persistent song ordering** - Maintains song order between runs
- **Cross-platform** - Works on macOS, iPad, and any Python 3.7+ environment

## Tools

### 1. chordSequenceGenerator.py

Generate complete chord sequence Mozaic scripts from multiple song files.

```bash
# Generate with auto-detected encoder
python3 chordSequenceGenerator.py --songs songs/*.txt --plist --output chordSequence.mozaic

# Force pure Python (iPad-compatible)
python3 chordSequenceGenerator.py --songs songs/*.txt --plist --pure-python --output chordSequence.mozaic

# Generate text output
python3 chordSequenceGenerator.py --songs songs/*.txt --output chordSequence.txt
```

### 2. mozaic_encoder.py

Convert plain text Mozaic scripts to .mozaic binary files.

```bash
# Auto-detect encoder
python3 mozaic_encoder.py script.txt output.mozaic

# Force pure Python
python3 mozaic_encoder.py --pure-python script.txt output.mozaic
```

### 3. mozaic_pure_encoder.py

Standalone pure Python encoder (no Foundation dependency).

```bash
python3 mozaic_pure_encoder.py script.txt output.mozaic
```

### 4. mozaic_reader.py

Read and display contents of .mozaic files.

```bash
# Summary view
python3 mozaic_reader.py file.mozaic

# Show code only
python3 mozaic_reader.py --code-only file.mozaic

# Full plist dump
python3 mozaic_reader.py --full file.mozaic
```

## Song File Format

Each song file should have:
- First line: Song title
- Optional second line: `tempo=120` (BPM)
- Remaining lines: One bar per line, chords separated by spaces

Example:

```
All of Me
tempo=120
C E7 A7
Dm G7 C A7
F Fm C A7
D7 G7 C G7
```

## Installation

### macOS

```bash
# Install PyObjC for native encoding (optional, pure Python works too)
pip3 install pyobjc
```

### iPad

Use any Python environment (Pythonista, Pyto, a-Shell). Only pure Python mode available (no additional dependencies needed).

## Dependencies

- **Pure Python mode**: Python 3.7+ (standard library only)
- **Native mode**: macOS with PyObjC/Foundation

## Architecture

### Encoding Methods

1. **Pure Python** - Cross-platform NSKeyedArchiver implementation using plistlib
2. **Native** - Uses macOS Foundation framework (faster, but macOS-only)

Both methods produce identical output that works in the Mozaic app.

### Key Implementation Details

- String and number deduplication for optimal file size
- Proper NSData wrapping for binary data
- NSMutableData and NSDictionary class metadata
- Binary plist format (FMT_BINARY)

## Documentation

- [CLAUDE.md](CLAUDE.md) - Build commands and architecture overview
- [PURE_PYTHON_ENCODER.md](PURE_PYTHON_ENCODER.md) - Pure Python implementation details

## License

This project is for personal use with the Mozaic iOS app.

## Mozaic App

Mozaic is a MIDI processor and scripting environment for iOS by Bram Bos.
Learn more at: https://www.mosaic-app.com/
