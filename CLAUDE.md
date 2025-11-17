# CLAUDE.md

This file provides guidance to Claude Code when working with the Mozaic Chord Sequence Generator.

## Overview

This repository contains a modern, refactored Python toolkit for generating Mozaic chord sequence scripts. It transforms simple text-based chord files into binary .mozaic files that can be loaded into the Mozaic iOS music app.

**Version:** 2.0.0 (Refactored with Pydantic, Jinja2, Click)

## Quick Commands

### Generate Chord Sequence

```bash
# Modern CLI (recommended)
./chord-sequence generate -d songs/ -o output.mozaic -v

# Legacy interface (backward compatible)
python3 chordSequenceGenerator.py -d songs/ -o output.mozaic
```

### Run Tests

```bash
# Quick test
python3 test_chordSequenceGenerator.py

# With runner script
./run_tests.sh

# All tests MUST pass (29/29) ✅
```

### Validate Song Files

```bash
./chord-sequence validate songs/AllOfMe.txt
./chord-sequence list-songs songs/
```

## Architecture (v2.0)

### Modern Package Structure

```
src/
├── __init__.py           # Public API exports
├── models.py             # Pydantic domain models (Song, Bar, SongCollection)
├── templates.py          # Jinja2 template manager
├── generator.py          # Core chord sequence generation logic
├── cli.py                # Click-based CLI commands
└── encoders/
    ├── __init__.py
    └── archiver.py       # Pure Python & Foundation NSKeyedArchiver
```

### Key Components

#### 1. Pydantic Models (`src/models.py`)

Type-safe domain models with validation:

- **`Bar`**: Represents a single bar with chord list
- **`Song`**: Contains title, tempo, bars, with computed properties
- **`SongCollection`**: Manages multiple songs with ordering
- **`MozaicMetadata`**: Script constants and configuration
- **`EncoderConfig`**: Encoder settings (deduplication, Foundation usage)
- **`ScriptContext`**: Complete generation context

```python
from src.models import Song, Bar

song = Song.from_file(Path("song.txt"))
print(song.title, song.num_bars, song.has_tempo)
```

#### 2. Template System (`src/templates.py`)

Jinja2-based template rendering:

- **Template file**: `templates/chord_sequence.mozaic.j2`
- **TemplateManager**: Loads and renders templates
- **Convenience function**: `render_chord_sequence(songs)`

The 168-line hardcoded Mozaic script is now externalized in a Jinja2 template.

#### 3. Generator (`src/generator.py`)

Core generation logic:

- **`generate_update_block(song, index)`**: Creates `@UpdateChordsSong{n}` blocks
- **`ChordSequenceGenerator`**: Main orchestrator class
- **Song ordering functions**: `resolve_song_order()`, `read_song_index()`, `write_song_index()`

#### 4. Encoders (`src/encoders/archiver.py`)

NSKeyedArchiver implementations:

- **`NSKeyedArchiver`**: Pure Python implementation (iPad-compatible!)
- **`MozaicEncoder`**: High-level encoder with Foundation fallback
- **`create_mozaic_file()`**: Convenience function

**Critical:** Number deduplication is REQUIRED for iPad compatibility!

#### 5. CLI (`src/cli.py`)

Modern Click-based CLI with commands:

- `generate` - Main generation command
- `validate` - Validate song files
- `list-songs` - Show song order
- `generate-single` - Quick single-song generation

### Backward Compatibility

**`chordSequenceGenerator.py`** is now a compatibility wrapper that:

- Imports from new `src/` package
- Provides old function signatures
- Allows all 29 existing tests to pass unchanged
- Supports legacy scripts without modification

```python
# Old API still works!
from chordSequenceGenerator import parse_chord_file, generate_plist

title, tempo, bars = parse_chord_file(Path("song.txt"))
plist_bytes = generate_plist(script_text, "filename")
```

## Song File Format

Each `.txt` file in `songs/` directory:

```
All of Me
tempo=120
C E7 A7
Dm G7 C A7
F Fm C A7
...
```

- **Line 1**: Song title
- **Line 2 (optional)**: `tempo=120`
- **Remaining lines**: One bar per line, space-separated chords

Empty lines create empty bars. Multiple chords per bar are distributed evenly across 8 subdivisions.

## Song Ordering

The `.songs.index` file maintains persistent ordering:

- Stores filenames only (no paths)
- Preserves order between runs
- New songs appended at end
- Missing songs removed
- Use `--reset-index` to rebuild

## Dependencies

### Core Dependencies (`requirements.txt`)

```bash
pip3 install -r requirements.txt
```

- **pydantic>=2.0.0** - Data validation and type safety
- **jinja2>=3.1.0** - Template rendering
- **click>=8.1.0** - Modern CLI framework
- **coverage>=7.0.0** - Test coverage (optional)
- **mypy>=1.0.0** - Type checking (optional)

### Platform-Specific

- **PyObjC** (macOS only, optional) - For native Foundation encoding
  - Auto-detected and used if available
  - Falls back to pure Python automatically

## Testing

### Test Suite

**File:** `test_chordSequenceGenerator.py`

**Coverage:** 29 comprehensive unit tests

```bash
# Run tests
python3 test_chordSequenceGenerator.py

# Expected output:
# Ran 29 tests in 0.037s
# OK
```

### Test Categories

1. **TestParseChordFile** (5 tests) - File parsing
2. **TestGenerateUpdateFunction** (3 tests) - Update block generation
3. **TestGenerateInitializeSongBlock** (2 tests) - Initialization
4. **TestIndexFileOperations** (3 tests) - Index file I/O
5. **TestResolveSongOrder** (5 tests) - Song ordering logic
6. **TestPurePythonEncoder** (4 tests) - **CRITICAL for iPad!**
7. **TestGeneratePlistPure** (3 tests) - Plist generation
8. **TestGenerateFullScript** (2 tests) - Complete script
9. **TestIntegration** (1 test) - End-to-end workflow

### Critical Tests

**Number Deduplication Test:**

```python
def test_number_deduplication(self):
    """Test that identical numbers are deduplicated."""
    # Without this, files won't load on iPad!
    # Reduces object count from 147 to 117
```

This test MUST pass for iPad compatibility.

## Build Commands

### Development Workflow

```bash
# 1. Make changes to src/ files

# 2. Run tests
./run_tests.sh

# 3. Test CLI
./chord-sequence generate -d songs/ -v

# 4. Commit if tests pass
git add .
git commit -m "Description of changes"
```

### Testing New Features

```bash
# Test individual song
./chord-sequence validate songs/AllOfMe.txt

# Test generation
./chord-sequence generate-single songs/AllOfMe.txt -o test.mozaic

# Verify output
python3 mozaic_reader.py test.mozaic --code-only
```

## Common Tasks

### Adding a New Song

```bash
# 1. Create song file
cat > songs/NewSong.txt <<EOF
My New Song
tempo=120
C F G
Am Dm E7
EOF

# 2. Generate (automatically added to index)
./chord-sequence generate -d songs/

# 3. View order
./chord-sequence list-songs songs/
```

### Modifying Templates

```bash
# 1. Edit template
vim templates/chord_sequence.mozaic.j2

# 2. Test generation
./chord-sequence generate -d songs/ -v

# 3. Verify output
python3 mozaic_reader.py chordSequence.mozaic --code-only
```

### Adding New Validation

```python
# In src/models.py, add validators:

from pydantic import field_validator

class Song(BaseModel):
    title: str

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        if len(v) > 50:
            raise ValueError("Title too long")
        return v
```

## Refactoring History

### Version 2.0.0 - Major Refactoring

**Goal:** Modern code structure with type safety and better maintainability

**Changes:**

1. **Eliminated 500+ lines of duplicate code**
   - Consolidated 3 encoder implementations into `src/encoders/archiver.py`
   - Single source of truth for NSKeyedArchiver

2. **Extracted 168-line hardcoded template**
   - Moved to `templates/chord_sequence.mozaic.j2`
   - Jinja2-based rendering with loops and conditionals

3. **Introduced Pydantic domain models**
   - Type-safe `Song`, `Bar`, `SongCollection` classes
   - Validation and computed properties
   - Better IDE support

4. **Modern Click CLI**
   - User-friendly commands: `generate`, `validate`, `list-songs`
   - Verbose mode, help text, error handling

5. **Package structure**
   - Organized `src/` package with clear separation
   - `models.py`, `templates.py`, `generator.py`, `encoders/`, `cli.py`

6. **Backward compatibility**
   - All 29 existing tests pass unchanged
   - Old API preserved in wrapper
   - Legacy scripts continue to work

### What Stayed the Same

- ✅ Song file format (unchanged)
- ✅ .songs.index format (unchanged)
- ✅ Output .mozaic format (byte-identical)
- ✅ Pure Python encoder (critical for iPad)
- ✅ Number deduplication (critical for iPad)
- ✅ All 29 tests (100% passing)

## Pure Python Encoder Details

### Why It Matters

The pure Python NSKeyedArchiver is **critical** for:

1. **iPad compatibility** - No Foundation framework on iPad
2. **File size** - Number deduplication reduces objects (147 → 117)
3. **Cross-platform** - Works on Linux, Windows, macOS

### Implementation

**File:** `src/encoders/archiver.py`

**Key features:**
- UID-based object references
- String deduplication (prevents bloat)
- **Number deduplication** (REQUIRED for iPad!)
- NSData wrapping
- Class metadata structure

Without number deduplication, files with many `0.0` values become too large and won't load on iPad.

## Code Style

### Type Hints

Use modern Python 3.10+ type hints:

```python
from pathlib import Path
from typing import List, Optional

def load_song(path: Path) -> Song:
    """Load a song from file."""
    return Song.from_file(path)
```

### Pydantic Models

Use Pydantic for data validation:

```python
from pydantic import BaseModel, Field

class MyModel(BaseModel):
    name: str = Field(min_length=1)
    count: int = Field(ge=0)
```

### Documentation

Use comprehensive docstrings:

```python
def my_function(arg: str) -> bool:
    """
    Short description.

    Longer explanation if needed.

    Args:
        arg: Description of argument

    Returns:
        Description of return value

    Example:
        >>> my_function("test")
        True
    """
```

## Troubleshooting

### Tests Failing

```bash
# Check which tests fail
python3 test_chordSequenceGenerator.py -v

# Check for import errors
python3 -c "from src import Song, ChordSequenceGenerator"

# Verify dependencies
pip3 install -r requirements.txt
```

### CLI Not Working

```bash
# Check executable permissions
chmod +x chord-sequence

# Test Python path
python3 -c "import sys; print(sys.path)"

# Run directly
python3 -m src.cli generate --help
```

### iPad Compatibility Issues

- **ALWAYS** use pure Python encoder (default)
- **NEVER** disable number deduplication
- Test with: `test_number_deduplication()` must pass

## References

- **NSKeyedArchiver Format:** See `PURE_PYTHON_ENCODER.md`
- **Testing Guide:** See `TESTING.md`
- **Mozaic App:** iOS music production app

## License

Generated with [Claude Code](https://claude.com/claude-code)

---

**Last Updated:** 2025-01-17 (v2.0.0 refactoring)
