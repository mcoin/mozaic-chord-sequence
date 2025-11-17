#!/usr/bin/env python3
"""
generate_chord_sequence.py
---------------------------------
Generates a complete chordSequence.txt script for Mozaic,
using one or more song chord text files as input.

Each song file:
- First line = song title
- Following lines = 1 bar per line, with chords separated by spaces

Persistent ordering:
- Maintains a hidden .songs.index file storing song filenames (no paths).
- Keeps the order of known songs between runs.
- Adds new songs at the end.
- Removes missing songs.
- Overwrites the index file on each run.
- You can manually reorder lines in .songs.index to adjust order.

Extra:
- --reset-index: ignores existing index and rebuilds from scratch.
"""

import argparse
import textwrap
from pathlib import Path
import sys
import os
import plistlib
from plistlib import UID

# Try to import Foundation for native encoding (macOS only)
try:
    from Foundation import (
        NSKeyedArchiver, NSMutableData, NSData, NSNumber, NSString,
        NSMutableDictionary
    )
    FOUNDATION_AVAILABLE = True
except ImportError:
    FOUNDATION_AVAILABLE = False

DEFAULT_INDEX_FILENAME = ".songs.index"


def parse_chord_file(path: Path):
    """Parse a song chord file into (title, tempo, bars)."""
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    if not lines:
        raise ValueError(f"Empty song file: {path}")

    title = lines[0]
    tempo = None
    bar_start_index = 1

    # Detect optional tempo line
    if len(lines) > 1 and lines[1].lower().startswith("tempo="):
        try:
            tempo = int(lines[1].split("=", 1)[1])
        except ValueError:
            raise ValueError(f"Invalid tempo format in file: {path}")
        bar_start_index = 2

    # Remaining lines → bars
    bars = [line.split() for line in lines[bar_start_index:]]
    if not bars:
        raise ValueError(f"No bars found in song file: {path}")

    return title, tempo, bars


def generate_update_function(song_nb: int, bars: list):
    """
    Generate @UpdateChordsSong{n} block.
    Returns (block_text, nb_bars_without_repeat).
    """
    nb_bars = len(bars)  # actual bar count (not counting appended first bar)
    bars_with_repeat = bars + [bars[0]]  # repeat first bar for lookahead

    lines = [f"@UpdateChordsSong{song_nb}"]
    pad_index = 0

    for bar_index, chords in enumerate(bars_with_repeat):
        if not chords:
            pad_index += 1
            continue
        num_chords = len(chords)
        for i, chord in enumerate(chords):
            beat_offset = i * (8 / num_chords)
            pos_val = pad_index * 8 + beat_offset
            pos_str = f"{int(pos_val)}" if pos_val.is_integer() else f"{pos_val:g}"
            lines.append(f"  LabelPad {pos_str} - bar*8, {{{chord}}}")
        pad_index += 1

    lines.append("@End\n")
    return "\n".join(lines), nb_bars


def generate_initialize_song_block(songs):
    """Generate @InitializeSong block dynamically for all songs."""
    lines = ["@InitializeSong"]
    for i, (title, nb_of_bars) in enumerate(songs):
        prefix = "if" if i == 0 else "elseif"
        lines.append(f"  {prefix} SongNb = {i}")
        lines.append(f"    LabelPads {{{title}}}")
        lines.append(f"    NbOfBars = {nb_of_bars}")
    lines.append("  else")
    lines.append("    LabelPads {Unassigned}")
    lines.append("  endif")
    lines.append("@End\n")
    return "\n".join(lines)


def generate_full_script(songs_data):
    """Assemble the full chordSequence text."""
    init_song_block = generate_initialize_song_block([
        (d['title'], d['nb_bars']) for d in songs_data
    ])
    update_blocks = "\n\n".join(d['update_block'] for d in songs_data)

    template = textwrap.dedent("""\
    @OnLoad
      Log {Chord Sequence}
      SetShortName {Chordsequence}
      ShowLayout 2
      prevPad =0
      SongNb = 0
      SetKnobValue 0, 0
      LabelKnob 0, {Bar -}
      SetKnobValue 1, SongNb
      LastKnob = 1
      Call @OnKnobChange
      Call @InitializeSong
      LabelKnob 2, {-}
      LabelKnob 3, {-}
      LabelKnobs {Chord Sequence}
      // Tap tempo settings
      TapNote = 90
      TapChannel = 16
    @End

    @StartTempoChange
    	minuteMs = 60000
    	quarterInterval = minuteMs / NewTempo
    	Log quarterInterval
    	SetTimerInterval quarterInterval
    	repeats = 0
    	StartTimer 
    @End
    
    @OnTimer
    	repeats = repeats + 1
    	Log repeats 
    	SendMIDINoteOn TapChannel, TapNote, 127
    	SendMIDINoteOff TapChannel, TapNote, 127
    	if repeats = 5
    		StopTimer 
    		repeats = 0
    	endif
    @End

    @OnPadDown
      Log {Pad }, LastPad
      if LastPad = 7
        Dec SongNb, 0
        SetKnobValue 1, SongNb
        LastKnob = 1
        Call @OnKnobChange
        Call @ClearPads
      elseif LastPad = 15
        Inc SongNb, 127
        SetKnobValue 1, SongNb
        LastKnob = 1
        Call @OnKnobChange
        Call @ClearPads
      elseif LastPad = 0
        Call @SetSongRhythm
      endif
    @End

    @OnKnobChange
      Log {Changed knob }, LastKnob
      Log (GetKnobValue LastKnob)
      
      if LastKnob = 1
        SongNb = RoundDown GetKnobValue LastKnob
        LabelKnob 1, {Song }, SongNb
        Call @InitializeSong
      endif
    @End

    {{INITIALIZE_SONG}}

    {{SET_SONG_RHYTHM}}

    @ClearPads
      for i = 0 to 15
        LabelPad i, { }
      endfor
    @End

    @Bar2PadColor
      section = RoundDown bar/8
      offset = 4
      baseColor = offset + section
      if baseColor > 7
        baseColor = baseColor - 7
      endif
      nextColor = baseColor + 1
      if nextColor > 7
        nextColor = nextColor - 7
      endif

      for pad = 8 to 15
        barInSection = bar - section*8
        if pad - 8 > barInSection
          ColorPad pad, baseColor
        else
          ColorPad pad, nextColor
        endif
      endfor
    @End

    {{UPDATE_BLOCKS}}

    @OnNewBar
      bar = HostBar % NbOfBars
      LabelKnob 0, {Bar }, bar + 1
      SetKnobValue 0, 127*bar/(NbOfBars - 1)
      Call @ClearPads
    """)

    tempo_lines = ["@SetSongRhythm"]
    tempo_entries_exist = False
    for i, d in enumerate(songs_data):
        if d["tempo"] is not None:
            tempo_entries_exist = True
            prefix = "if" if i == 0 else "elseif"
            tempo_lines.append(f"  {prefix} SongNb = {i}")
            tempo_lines.append(f"    NewTempo = {d['tempo']}")
            tempo_lines.append("    Call @StartTempoChange")
    if tempo_entries_exist:
        tempo_lines.append("endif")
    tempo_lines.append("@End")
    tempo_block = "\n".join(tempo_lines)

    # Song update logic
    song_call_lines = []
    for i, _ in enumerate(songs_data):
        prefix = "if" if i == 0 else "elseif"
        song_call_lines.append(f"  {prefix} SongNb = {i}")
        song_call_lines.append(f"    Call @UpdateChordsSong{i}")
    song_call_lines.append("  endif")

    template += "\n".join(song_call_lines) + textwrap.dedent("""
      
      Call @Bar2PadColor
    @End 

    @OnNewBeat
      ColorPad prevPad, 0
      bar = HostBar % NbOfBars
      beat = HostBeat
      
      pad = beat*2
      if beat = 0
        ColorPad pad, 1
        FlashPad pad
      else
        ColorPad pad, 3
      endif

      prevPad = pad
    @End
    """)

    return (
        template
        .replace("{{INITIALIZE_SONG}}", init_song_block)
        .replace("{{UPDATE_BLOCKS}}", update_blocks)
        .replace("{{SET_SONG_RHYTHM}}", tempo_block)
    )


def create_nskeyedarchiver_plist_pure(data_dict):
    """
    Pure Python NSKeyedArchiver implementation (no Foundation dependency).
    Works on any platform including iOS/iPad.
    """
    # Objects array - starts with $null, then root dict at position 1
    objects = ['$null', None]  # Placeholder for root dict

    # Track NSData objects that need class reference updates
    nsdata_objects = []

    # Map for deduplication (strings and numbers)
    string_map = {}
    number_map = {}

    def add_string(s):
        """Add string with deduplication."""
        if s in string_map:
            return UID(string_map[s])
        idx = len(objects)
        objects.append(s)
        string_map[s] = idx
        return UID(idx)

    def add_number(n):
        """Add number (int or float) with deduplication."""
        if n in number_map:
            return UID(number_map[n])
        idx = len(objects)
        objects.append(n)
        number_map[n] = idx
        return UID(idx)

    def add_nsdata(data_bytes):
        """Add NSData/NSMutableData object (class reference added later)."""
        # Create NSData object with placeholder class
        nsdata_obj = {
            '$class': None,  # Will be updated later
            'NS.data': data_bytes
        }
        idx = len(objects)
        objects.append(nsdata_obj)
        nsdata_objects.append(idx)  # Track for later update
        return UID(idx)

    # Build NS.keys and NS.objects arrays for root dictionary
    keys = []
    values = []

    for key, value in data_dict.items():
        # Add key (always string)
        keys.append(add_string(key))

        # Add value based on type
        if isinstance(value, str):
            values.append(add_string(value))
        elif isinstance(value, int):
            values.append(add_number(value))
        elif isinstance(value, float):
            values.append(add_number(value))
        elif isinstance(value, bytes):
            values.append(add_nsdata(value))
        else:
            raise ValueError(f"Unsupported value type: {type(value)}")

    # Add class metadata objects at the end

    # NSData/NSMutableData class metadata
    if nsdata_objects:
        nsdata_class_uid = UID(len(objects))
        nsdata_class = {
            '$classes': ['NSMutableData', 'NSData', 'NSObject'],
            '$classname': 'NSMutableData'
        }
        objects.append(nsdata_class)

        # Update all NSData objects with correct class reference
        for idx in nsdata_objects:
            objects[idx]['$class'] = nsdata_class_uid

    # NSDictionary class metadata (for root object)
    nsdict_class_uid = UID(len(objects))
    nsdict_class = {
        '$classes': ['NSMutableDictionary', 'NSDictionary', 'NSObject'],
        '$classname': 'NSMutableDictionary'
    }
    objects.append(nsdict_class)

    # Create root dictionary object (goes at position 1)
    root_dict = {
        'NS.keys': keys,
        'NS.objects': values,
        '$class': nsdict_class_uid
    }
    objects[1] = root_dict

    # Create final plist structure
    plist = {
        '$version': 100000,
        '$archiver': 'NSKeyedArchiver',
        '$top': {'root': UID(1)},
        '$objects': objects
    }

    return plist


def generate_plist_pure(script_text: str, filename: str = "chordSequence") -> bytes:
    """
    Generate Mozaic .mozaic file using pure Python (no Foundation dependency).
    Works on any platform including iOS/iPad.
    """
    # Build the data dictionary (in alphabetical order for consistency)
    data_dict = {}

    # Audio Unit values (0-7)
    au_values = [0.0, 0.0, 0.5, 0.0, 0.0, 0.5, 0.0, 0.0]
    for i, val in enumerate(au_values):
        data_dict[f'AUVALUE{i}'] = val

    # CODE - as bytes
    data_dict['CODE'] = script_text.encode('utf-8')

    # FILENAME
    data_dict['FILENAME'] = filename

    # GUI - 40 bytes
    data_dict['GUI'] = b'\x00' * 36 + b'\x02\x00\x00\x00'

    # Knob labels (0-21)
    for i in range(22):
        data_dict[f'KNOBLABEL{i}'] = f'Knob {i}'

    # KNOBTITLE
    data_dict['KNOBTITLE'] = 'Chord Sequence'

    # Knob values (0-21)
    for i in range(22):
        data_dict[f'KNOBVALUE{i}'] = 0.0

    # PADTITLE
    data_dict['PADTITLE'] = ''

    # SCALE
    data_dict['SCALE'] = 4095

    # Variables - 16-byte binary values (0-5)
    variable_bytes = b'\x00' * 16
    for i in range(6):
        data_dict[f'VARIABLE{i}'] = variable_bytes

    # XVALUE, YVALUE
    data_dict['XVALUE'] = 0.0

    # XYTITLE
    data_dict['XYTITLE'] = ''

    # YVALUE
    data_dict['YVALUE'] = 0.0

    # data field - empty bytes
    data_dict['data'] = b''

    # Integers (manufacturer, subtype, type, version)
    data_dict['manufacturer'] = 1114792301  # 'Bram'
    data_dict['subtype'] = 1836022371       # 'mozc'
    data_dict['type'] = 1635085673          # 'aumi'
    data_dict['version'] = 1

    # Create NSKeyedArchiver structure
    plist = create_nskeyedarchiver_plist_pure(data_dict)

    # Serialize to binary plist
    return plistlib.dumps(plist, fmt=plistlib.FMT_BINARY)


def generate_plist_native(script_text: str, filename: str = "chordSequence") -> bytes:
    """
    Generate a Mozaic .mozaic plist file using native NSKeyedArchiver (macOS only).
    Returns bytes that can be written to a file.
    """
    # Create the data structure using Foundation types
    plist_data = NSMutableDictionary.dictionary()

    # CODE - NSMutableData containing the script
    code_data = NSMutableData.dataWithBytes_length_(
        script_text.encode('utf-8'),
        len(script_text.encode('utf-8'))
    )
    plist_data['CODE'] = code_data

    # GUI - 40 bytes
    gui_bytes = b'\x00' * 36 + b'\x02\x00\x00\x00'
    plist_data['GUI'] = NSData.dataWithBytes_length_(gui_bytes, len(gui_bytes))

    # Strings
    plist_data['FILENAME'] = NSString.stringWithString_(filename)
    plist_data['KNOBTITLE'] = NSString.stringWithString_('Chord Sequence')
    plist_data['PADTITLE'] = NSString.stringWithString_('')
    plist_data['XYTITLE'] = NSString.stringWithString_('')

    # Integers (as NSNumber)
    plist_data['manufacturer'] = NSNumber.numberWithInt_(1114792301)  # 'Bram' as FourCC
    plist_data['subtype'] = NSNumber.numberWithInt_(1836022371)       # 'mozc' as FourCC
    plist_data['type'] = NSNumber.numberWithInt_(1635085673)          # 'aumi' as FourCC
    plist_data['version'] = NSNumber.numberWithInt_(1)
    plist_data['SCALE'] = NSNumber.numberWithInt_(4095)  # 0xFFF - all 12 scale notes

    # Knob values (0-21)
    for i in range(22):
        plist_data[f'KNOBVALUE{i}'] = NSNumber.numberWithDouble_(0.0)

    # Knob labels (0-21)
    for i in range(22):
        plist_data[f'KNOBLABEL{i}'] = NSString.stringWithString_(f'Knob {i}')

    # Audio Unit values (0-7)
    au_values = [0.0, 0.0, 0.5, 0.0, 0.0, 0.5, 0.0, 0.0]
    for i, val in enumerate(au_values):
        plist_data[f'AUVALUE{i}'] = NSNumber.numberWithDouble_(val)

    # Variables (0-5) - 16-byte binary values
    variable_bytes = b'\x00' * 16
    for i in range(6):
        plist_data[f'VARIABLE{i}'] = NSData.dataWithBytes_length_(
            variable_bytes, len(variable_bytes)
        )

    # XY Pad values
    plist_data['XVALUE'] = NSNumber.numberWithDouble_(0.0)
    plist_data['YVALUE'] = NSNumber.numberWithDouble_(0.0)

    # data field (empty NSMutableData)
    empty_data = NSMutableData.data()
    plist_data['data'] = empty_data

    # Archive using native NSKeyedArchiver
    archived_data, error = NSKeyedArchiver.archivedDataWithRootObject_requiringSecureCoding_error_(
        plist_data, False, None
    )

    if error:
        raise RuntimeError(f"NSKeyedArchiver error: {error}")

    # Convert to bytes
    return bytes(archived_data)


def generate_plist(script_text: str, filename: str = "chordSequence", use_pure: bool = None) -> bytes:
    """
    Generate a Mozaic .mozaic plist file.

    Args:
        script_text: The Mozaic script content
        filename: The filename to embed in the plist
        use_pure: If True, use pure Python implementation. If False, use native.
                  If None (default), auto-detect (use native if available, otherwise pure).

    Returns:
        Binary plist data as bytes
    """
    # Auto-detect which implementation to use
    if use_pure is None:
        use_pure = not FOUNDATION_AVAILABLE

    if use_pure:
        return generate_plist_pure(script_text, filename)
    else:
        if not FOUNDATION_AVAILABLE:
            raise RuntimeError("Native Foundation encoding requested but Foundation is not available. Use --pure-python flag.")
        return generate_plist_native(script_text, filename)


def read_index_file(index_path):
    """Return list of filenames (no paths)."""
    if not index_path.exists():
        return []
    with open(index_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def write_index_file(index_path, filenames):
    """Overwrite index with current song filenames."""
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(filenames) + "\n")


def resolve_song_order(index_path, cli_files, reset=False):
    """Preserve previous order from index and append new songs."""
    cli_names = [Path(f).name for f in cli_files]

    if reset or not index_path.exists():
        write_index_file(index_path, cli_names)
        return cli_names

    index_names = read_index_file(index_path)
    existing = [n for n in index_names if n in cli_names]
    new = [n for n in cli_names if n not in existing]
    combined = existing + new

    write_index_file(index_path, combined)
    return combined


def main():
    parser = argparse.ArgumentParser(
        description="Generate Mozaic chordSequence script from chord files."
    )
    parser.add_argument(
        "--songs",
        nargs="+",
        required=True,
        help="List of song chord files (e.g. --songs mysongs/*.txt)"
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=Path(DEFAULT_INDEX_FILENAME),
        help="Path to persistent index file (default: .songs.index)"
    )
    parser.add_argument(
        "--reset-index",
        action="store_true",
        help="Ignore existing index and rebuild song order from scratch."
    )
    parser.add_argument(
        "--plist",
        action="store_true",
        help="Generate a binary plist (.mozaic) file instead of text output"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file path (optional, writes to stdout if not specified)"
    )
    parser.add_argument(
        "--pure-python",
        action="store_true",
        help="Force use of pure Python encoder (works on iPad). Auto-detected if not specified."
    )
    parser.add_argument(
        "--native",
        action="store_true",
        help="Force use of native Foundation encoder (macOS only). Auto-detected if not specified."
    )
    args = parser.parse_args()

    # Determine which encoder to use
    if args.pure_python and args.native:
        print("Error: Cannot specify both --pure-python and --native", file=sys.stderr)
        sys.exit(1)

    use_pure = None
    if args.pure_python:
        use_pure = True
    elif args.native:
        use_pure = False

    cli_paths = [Path(p).resolve() for p in args.songs]
    ordered_filenames = resolve_song_order(args.index, cli_paths, reset=args.reset_index)

    # map filenames -> Path objects
    name_to_path = {p.name: p for p in cli_paths}

    songs_data = []
    for i, filename in enumerate(ordered_filenames):
        path = name_to_path.get(filename)
        if not path or not path.exists():
            print(f"⚠️ Skipping missing file from index: {filename}", file=sys.stderr)
            continue
        title, tempo, bars = parse_chord_file(path)
        update_block, nb_bars = generate_update_function(i, bars)
        songs_data.append({
            "title": title,
            "tempo": tempo,
            "nb_bars": nb_bars,
            "update_block": update_block,
        })

    script_text = generate_full_script(songs_data)

    # Generate output
    if args.plist:
        # Generate binary plist format
        output_filename = "chordSequence"
        if args.output:
            output_filename = args.output.stem

        # Show which encoder is being used
        encoder_type = "pure Python" if (use_pure if use_pure is not None else not FOUNDATION_AVAILABLE) else "native Foundation"
        print(f"Using {encoder_type} encoder...", file=sys.stderr)

        plist_bytes = generate_plist(script_text, output_filename, use_pure=use_pure)

        if args.output:
            # Write to file
            with open(args.output, "wb") as f:
                f.write(plist_bytes)
            print(f"✓ Generated {args.output}", file=sys.stderr)
        else:
            # Write binary to stdout
            sys.stdout.buffer.write(plist_bytes)
    else:
        # Generate text output (original behavior)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(script_text)
            print(f"✓ Generated {args.output}", file=sys.stderr)
        else:
            sys.stdout.write(script_text)


if __name__ == "__main__":
    main()

