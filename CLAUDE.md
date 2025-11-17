# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository contains a Python generator (`chordSequenceGenerator.py`) that creates Mozaic scripts for interactive chord sequence playback on iOS music production apps. It transforms simple text-based chord files into either Mozaic script text (.txt) or binary plist format (.mozaic) that can be loaded into Mozaic.

## Dependencies

- **Python 3.8+**: Standard library modules (argparse, textwrap, pathlib, plistlib)
- **bpylist2**: Required for generating NSKeyedArchiver format .mozaic files
  - Install: `pip3 install bpylist2`
  - Used for: Creating iOS-compatible binary plist files

## Core Architecture

### Code Generation Pipeline

1. **Song Files** (`songs/*.txt`) → 2. **Python Generator** → 3. **Mozaic Script Output** (.txt or .mozaic)

The generator reads multiple chord files and produces a single unified Mozaic script that can switch between songs using MIDI controller knobs and pads.

### Song File Format

Song files in `songs/` directory follow this structure:
- **Line 1**: Song title (displayed in Mozaic)
- **Line 2** (optional): `tempo=<BPM>` (e.g., `tempo=120`)
- **Remaining lines**: One bar per line, chords separated by spaces

Example:
```
All of Me
tempo=120

C6
E7
A7 D-7
CMaj7 E-7b5/Bb A7
```

Empty lines are treated as empty bars. Multiple chords per bar are distributed evenly across beats (8 subdivisions per bar).

### Song Ordering System

The `.songs.index` file maintains persistent song ordering:
- Stores filenames only (no paths)
- Preserves order between generator runs
- New songs appended to end
- Missing songs removed automatically
- Can be manually edited to reorder songs
- Use `--reset-index` to rebuild from scratch

### Mozaic Script Structure

Generated scripts contain:
- `@OnLoad`: Initialization, defaults, tap tempo setup
- `@InitializeSong`: Dynamic song selector (if/elseif chain based on SongNb)
- `@SetSongRhythm`: Tempo changes per song (only for songs with tempo= line)
- `@UpdateChordsSong{N}`: One function per song containing all chord/pad label mappings
- `@OnNewBar`, `@OnNewBeat`: DAW sync handlers that call appropriate update function
- `@Bar2PadColor`: Visual feedback system using pad colors

Key Mozaic concepts:
- Pads are labeled with chord names at specific beat positions
- Position calculation: `pad_index * 8 + beat_offset` where 8 = subdivisions per bar
- Multiple chords per bar: distributed using `i * (8 / num_chords)`
- First bar is repeated at end for lookahead during playback

## Development Commands

### Generate Mozaic Script (Text Format)

```bash
python3 chordSequenceGenerator.py --songs songs/*.txt --output chordSequence.txt
```

### Generate Binary Plist Format (.mozaic)

```bash
python3 chordSequenceGenerator.py --songs songs/*.txt --plist --output chordSequence.mozaic
```

### Reset Song Order

```bash
python3 chordSequenceGenerator.py --songs songs/*.txt --reset-index --output chordSequence.txt
```

### Custom Index File Location

```bash
python3 chordSequenceGenerator.py --songs songs/*.txt --index /path/to/custom.index
```

## Key Functions

- `parse_chord_file(path)`: Parses song file into (title, tempo, bars). Returns tempo as int or None.
- `generate_update_function(song_nb, bars)`: Creates `@UpdateChordsSong{N}` block with LabelPad commands. Returns (block_text, nb_bars).
- `generate_initialize_song_block(songs)`: Creates dynamic `@InitializeSong` with if/elseif chain for all songs.
- `generate_full_script(songs_data)`: Assembles complete Mozaic script by replacing template placeholders.
- `generate_plist(script_text, filename)`: Converts script text to binary plist with all required Mozaic metadata.
- `resolve_song_order(index_path, cli_files, reset)`: Handles persistent ordering logic via `.songs.index`.

## File Naming Conventions

- Generated output files: `chordSequence*.txt` or `chordSequence*.mozaic`
- Song source files: `songs/*.txt` (descriptive names like `all_of_me.txt`)
- Backup directory: `bckp/` (not part of build process)
- Index file: `.songs.index` (hidden, auto-managed)

## Mozaic-Specific Details

### Pad Mapping
- Pads 0-7: Lower row (pad 0 triggers tempo change, pad 7 = prev song)
- Pads 8-15: Upper row (visual progress indicators, pad 15 = next song)

### Knob Mapping
- Knob 0: Current bar display (read-only)
- Knob 1: Song selector (0-127 maps to song index)
- Knobs 2-3: Unused (labeled "-")

### Tap Tempo
- Note: 90 (MIDI note number)
- Channel: 16
- Sends 5 taps on tempo change to sync external devices

### Binary Plist Structure (NSKeyedArchiver Format)
The `.mozaic` format uses Apple's NSKeyedArchiver serialization:
- **Format**: NSKeyedArchiver (not simple binary plist)
- **CODE**: NSMutableData object wrapping UTF-8 encoded script text
- **FILENAME**: Base filename without extension (string)
- **GUI**: 40-byte binary value (value 2 at byte 36 indicates XY Pad layout)
- **manufacturer**: 1114792301 (FourCC: 'Bram')
- **subtype**: 1836022371 (FourCC: 'mozc')
- **type**: 1635085673 (FourCC: 'aumi')
- **SCALE**: 4095 (0xFFF - all 12 chromatic notes enabled)
- **KNOBVALUE0-21**: Float values (default 0.0)
- **PADLABEL0-15**, **PADCOLOR4-15**: Pad UI state (strings/ints)
- **AUVALUE0-7**: Audio Unit parameters (floats)
- **VARIABLE0-14**: 16-byte binary values (runtime state)
- **data**: NSMutableData (runtime state, empty on generation)

## Common Workflow

1. Create/edit song files in `songs/` directory
2. Run generator with `--songs songs/*.txt --plist --output chordSequence.mozaic`
3. Transfer `.mozaic` file to iOS device
4. Load in Mozaic app
5. Use knob 1 to select songs, pads 7/15 to navigate
