#!/usr/bin/env python3
"""
Backward compatibility wrapper for chordSequenceGenerator.

This module provides the old API while using the new refactored code internally.
Ensures existing tests and scripts continue to work.
"""

from pathlib import Path
from typing import Tuple, List, Optional
import plistlib
from plistlib import UID

# Import from new structure
from src.models import Song, Bar
from src.generator import (
    generate_update_block as _generate_update_block,
    read_song_index,
    write_song_index,
    resolve_song_order as _resolve_song_order,
    ChordSequenceGenerator
)
from src.templates import TemplateManager
from src.encoders.archiver import (
    PurePythonArchiver as _PurePythonArchiver,
    MozaicEncoder,
    FOUNDATION_AVAILABLE
)

# Constants for backward compatibility
DEFAULT_INDEX_FILENAME = ".songs.index"


def parse_chord_file(path: Path) -> Tuple[str, Optional[int], List[List[str]]]:
    """
    Parse a song chord file into (title, tempo, bars).

    Backward compatibility wrapper for Song.from_file().

    Args:
        path: Path to chord file

    Returns:
        Tuple of (title, tempo, bars) where bars is List[List[str]]
    """
    song = Song.from_file(path)
    bars = [bar.chords for bar in song.bars]
    return (song.title, song.tempo, bars)


def generate_update_function(song_nb: int, bars: List[List[str]]) -> Tuple[str, int]:
    """
    Generate @UpdateChordsSong{n} block.

    Backward compatibility wrapper.

    Args:
        song_nb: Song index number
        bars: List of bar chord lists

    Returns:
        Tuple of (block_text, num_bars)
    """
    # Convert to new Bar model
    bar_models = [Bar(chords=chords) for chords in bars]

    # Create temporary song
    temp_song = Song(
        title="temp",
        bars=bar_models
    )

    # Generate update block
    block_text = _generate_update_block(temp_song, song_nb)

    return (block_text, len(bars))


def generate_initialize_song_block(songs) -> str:
    """
    Generate @InitializeSong block.

    Backward compatibility - now handled by template.

    Args:
        songs: List of song tuples (title, num_bars) or dicts with 'title' and 'num_bars'

    Returns:
        Mozaic script block
    """
    lines = ["@InitializeSong"]

    for i, song in enumerate(songs):
        if_word = "if" if i == 0 else "elseif"

        # Support both tuple (old) and dict (new) formats
        if isinstance(song, tuple):
            title, num_bars = song
        else:
            title = song['title']
            num_bars = song['num_bars']

        lines.append(f"  {if_word} SongNb = {i}")
        lines.append(f"    LabelPads {{{title}}}")
        lines.append(f"    NbOfBars = {num_bars}")

    lines.append("  else")
    lines.append("    LabelPads {Unassigned}")
    lines.append("  endif")
    lines.append("@End\n")

    return "\n".join(lines)


def generate_set_song_rhythm_block(songs: List[dict]) -> str:
    """
    Generate @SetSongRhythm block.

    Backward compatibility - now handled by template.

    Args:
        songs: List of song dicts with optional 'tempo'

    Returns:
        Mozaic script block
    """
    has_tempo = any(song.get('tempo') for song in songs)

    if not has_tempo:
        return "@SetSongRhythm\n@End\n"

    lines = ["@SetSongRhythm"]
    first = True

    for i, song in enumerate(songs):
        if song.get('tempo'):
            if_word = "if" if first else "elseif"
            lines.append(f"  {if_word} SongNb = {i}")
            lines.append(f"    NewTempo = {song['tempo']}")
            lines.append("    Call @StartTempoChange")
            first = False

    if not first:  # Had at least one tempo
        lines.append("endif")

    lines.append("@End\n")

    return "\n".join(lines)


def generate_full_script(songs: List[dict]) -> str:
    """
    Generate complete Mozaic script.

    Backward compatibility wrapper using new template system.

    Args:
        songs: List of song dicts with 'title', 'num_bars', 'tempo', 'update_block'

    Returns:
        Complete Mozaic script text
    """
    manager = TemplateManager()
    return manager.render('chord_sequence.mozaic.j2', {'songs': songs})


def create_nskeyedarchiver_plist_pure(data_dict: dict) -> dict:
    """
    Pure Python NSKeyedArchiver implementation.

    Backward compatibility wrapper.

    Args:
        data_dict: Dictionary to archive

    Returns:
        Plist dictionary structure
    """
    archiver = _PurePythonArchiver(
        deduplicate_strings=True,
        deduplicate_numbers=True
    )
    return archiver.archive(data_dict)


def generate_plist_pure(script_text: str, filename: str = "chordSequence") -> bytes:
    """
    Generate Mozaic .mozaic file using pure Python.

    Backward compatibility wrapper.

    Args:
        script_text: The Mozaic script content
        filename: Filename to embed

    Returns:
        Binary plist bytes
    """
    encoder = MozaicEncoder(use_foundation=False)
    return encoder.encode(script_text, filename)


def generate_plist_native(script_text: str, filename: str = "chordSequence") -> bytes:
    """
    Generate Mozaic .mozaic file using native Foundation.

    Backward compatibility wrapper.

    Args:
        script_text: The Mozaic script content
        filename: Filename to embed

    Returns:
        Binary plist bytes
    """
    encoder = MozaicEncoder(use_foundation=True)
    return encoder.encode(script_text, filename)


def generate_plist(script_text: str, filename: str = "chordSequence",
                   use_pure: Optional[bool] = None) -> bytes:
    """
    Generate a Mozaic .mozaic plist file.

    Backward compatibility wrapper.

    Args:
        script_text: The Mozaic script content
        filename: The filename to embed in the plist
        use_pure: If True, use pure Python. If False, use native.
                  If None (default), auto-detect.

    Returns:
        Binary plist bytes
    """
    if use_pure is None:
        use_foundation = FOUNDATION_AVAILABLE
    else:
        use_foundation = not use_pure

    encoder = MozaicEncoder(use_foundation=use_foundation)
    return encoder.encode(script_text, filename)


# Backward compatibility aliases for index file functions
read_index_file = read_song_index
write_index_file = write_song_index


def resolve_song_order(index_path: Path, cli_files: List, reset: bool = False) -> List[str]:
    """
    Resolve song order using persistent index file.

    Backward compatibility wrapper with old signature.

    Args:
        index_path: Path to index file
        cli_files: List of file paths (can be Path or str)
        reset: If True, ignore existing index

    Returns:
        List of filenames (strings, not Paths)
    """
    # Convert cli_files to Paths if they aren't already
    file_paths = [Path(f) if not isinstance(f, Path) else f for f in cli_files]

    # Call new function
    ordered_paths = _resolve_song_order(
        current_files=file_paths,
        index_file=index_path,
        reset=reset
    )

    # Return filenames only (not full paths)
    return [p.name for p in ordered_paths]


__all__ = [
    'DEFAULT_INDEX_FILENAME',
    'parse_chord_file',
    'generate_update_function',
    'generate_initialize_song_block',
    'generate_set_song_rhythm_block',
    'generate_full_script',
    'create_nskeyedarchiver_plist_pure',
    'generate_plist_pure',
    'generate_plist_native',
    'generate_plist',
    'read_song_index',
    'write_song_index',
    'read_index_file',  # Backward compatibility alias
    'write_index_file',  # Backward compatibility alias
    'resolve_song_order',
    'FOUNDATION_AVAILABLE',
]


# Main function for backward compatibility
if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Generate Mozaic chord sequence script (legacy interface - use ./chord-sequence instead)"
    )
    parser.add_argument(
        'song_files',
        nargs='*',
        type=Path,
        help='Song chord text files'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('chordSequence.mozaic'),
        help='Output .mozaic file (default: chordSequence.mozaic)'
    )
    parser.add_argument(
        '--directory', '-d',
        type=Path,
        help='Load all *.txt files from this directory'
    )
    parser.add_argument(
        '--reset-index',
        action='store_true',
        help='Ignore existing index and rebuild from scratch'
    )
    parser.add_argument(
        '--use-pure',
        action='store_true',
        help='Force pure Python encoder (default: auto-detect)'
    )

    args = parser.parse_args()

    print("NOTE: This is the legacy interface. Consider using './chord-sequence' instead.\n")

    try:
        from src.models import SongCollection

        songs_list = []

        if args.directory:
            index_file = args.directory / DEFAULT_INDEX_FILENAME
            song_files = list(args.directory.glob("*.txt"))

            if not song_files:
                print(f"Error: No .txt files found in {args.directory}", file=sys.stderr)
                sys.exit(1)

            # Use internal function directly to avoid signature mismatch
            ordered_paths = _resolve_song_order(
                current_files=song_files,
                index_file=index_file,
                reset=args.reset_index
            )

            for path in ordered_paths:
                song = Song.from_file(path)
                songs_list.append(song)

        elif args.song_files:
            for path in args.song_files:
                song = Song.from_file(path)
                songs_list.append(song)
        else:
            parser.print_help()
            sys.exit(1)

        songs = SongCollection(songs=songs_list)
        generator = ChordSequenceGenerator(use_foundation=not args.use_pure)
        generator.generate_mozaic_file(songs, args.output)

        print(f"✓ Created: {args.output}")
        print(f"  {len(songs)} song(s), {sum(s.num_bars for s in songs)} total bars")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
