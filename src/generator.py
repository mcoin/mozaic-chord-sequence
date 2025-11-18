"""
Chord sequence script generator for Mozaic.

This module provides the core functionality for generating Mozaic chord
sequence scripts from song files.
"""

from pathlib import Path
from typing import List, Optional
from .models import Song, SongCollection, Bar, ScriptContext
from .templates import TemplateManager
from .encoders import MozaicEncoder, create_mozaic_file


def generate_update_block(song: Song, song_index: int) -> tuple[str, list[float]]:
    """
    Generate the @UpdateChordsSong{n} block for a song.

    This creates the Mozaic script that labels pads with chord names
    at the appropriate beat positions.

    Args:
        song: Song instance with bars of chords
        song_index: Zero-based index of the song

    Returns:
        Tuple of (block_text, fill_positions)
        - block_text: Mozaic script block as string
        - fill_positions: List of positions where fills should trigger

    Example:
        >>> song = Song(title="Test", bars=[Bar(chords=["C", "F", "G"])])
        >>> block, fills = generate_update_block(song, 0)
        >>> "@UpdateChordsSong0" in block
        True
    """
    # Add first bar at end for lookahead
    bars_with_repeat = list(song.bars) + [song.bars[0]]

    lines = [f"@UpdateChordsSong{song_index}"]

    # Collect fill positions for this song
    fill_positions = []
    pad_index = 0

    for bar_idx, bar in enumerate(song.bars):
        if not bar.chords:
            pad_index += 1
            continue

        num_chords = len(bar)
        for i, (chord, has_fill) in enumerate(zip(bar.chords, bar.fills)):
            if has_fill:
                # Calculate beat offset within the bar
                beat_offset = i * (8 / num_chords)
                pos_val = pad_index * 8 + beat_offset
                fill_positions.append(pos_val)

        pad_index += 1

    # Generate chord labels
    pad_index = 0
    for bar in bars_with_repeat:
        if not bar.chords:
            pad_index += 1
            continue

        num_chords = len(bar)
        for i, chord in enumerate(bar.chords):
            # Calculate beat offset within the bar
            beat_offset = i * (8 / num_chords)
            pos_val = pad_index * 8 + beat_offset

            # Format position (integer if whole, float otherwise)
            if pos_val.is_integer():
                pos_str = f"{int(pos_val)}"
            else:
                pos_str = f"{pos_val:g}"

            lines.append(f"  LabelPad {pos_str} - bar*8, {{{chord}}}")

        pad_index += 1

    lines.append("@End\n")
    return "\n".join(lines), fill_positions


class ChordSequenceGenerator:
    """
    Main generator for Mozaic chord sequence scripts.

    This class orchestrates the entire process of generating a Mozaic
    chord sequence script from song files, rendering it with a template,
    and encoding it to a .mozaic file.

    Attributes:
        template_manager: TemplateManager for rendering scripts
        encoder: MozaicEncoder for creating .mozaic files
    """

    def __init__(self,
                 template_dir: Optional[Path] = None,
                 use_foundation: bool = False):
        """
        Initialize the generator.

        Args:
            template_dir: Optional custom template directory
            use_foundation: Whether to use Foundation encoding (macOS only)
        """
        self.template_manager = TemplateManager(template_dir)
        self.encoder = MozaicEncoder(use_foundation=use_foundation)

    def generate_script(self, songs: SongCollection) -> str:
        """
        Generate complete Mozaic script from song collection.

        Args:
            songs: SongCollection with songs to include

        Returns:
            Complete Mozaic script text

        Example:
            >>> songs = SongCollection(songs=[
            ...     Song.from_file(Path("test.txt"))
            ... ])
            >>> generator = ChordSequenceGenerator()
            >>> script = generator.generate_script(songs)
            >>> "@OnLoad" in script
            True
        """
        # Build context for template rendering
        template_songs = []

        for idx, song in enumerate(songs):
            # Generate update block and get fill positions
            update_block, fill_positions = generate_update_block(song, idx)

            template_songs.append({
                'title': song.title,
                'num_bars': song.num_bars,
                'tempo': song.tempo,
                'update_block': update_block,
                'fill_positions': fill_positions,
                'song_index': idx
            })

        # Render template
        context = {'songs': template_songs}
        script = self.template_manager.render('chord_sequence.mozaic.j2', context)

        return script

    def generate_mozaic_file(self,
                            songs: SongCollection,
                            output_path: Path,
                            filename: Optional[str] = None) -> None:
        """
        Generate complete .mozaic file from song collection.

        This is the high-level method that combines script generation
        and file encoding.

        Args:
            songs: SongCollection with songs to include
            output_path: Path where .mozaic file will be written
            filename: Optional filename to embed (defaults to output_path stem)

        Example:
            >>> songs = SongCollection(songs=[Song.from_file(Path("song.txt"))])
            >>> generator = ChordSequenceGenerator()
            >>> generator.generate_mozaic_file(songs, Path("output.mozaic"))
        """
        # Generate script text
        script_text = self.generate_script(songs)

        # Determine embedded filename
        if filename is None:
            filename = output_path.stem

        # Encode and write
        mozaic_bytes = self.encoder.encode(script_text, filename)

        with open(output_path, 'wb') as f:
            f.write(mozaic_bytes)


def load_songs_from_directory(directory: Path,
                              pattern: str = "*.txt",
                              index_file: Optional[Path] = None) -> SongCollection:
    """
    Load all song files from a directory.

    Args:
        directory: Directory containing song files
        pattern: Glob pattern for song files (default: *.txt)
        index_file: Optional path to song order index file

    Returns:
        SongCollection with all loaded songs

    Raises:
        ValueError: If no song files are found

    Example:
        >>> songs = load_songs_from_directory(Path("songs/"))
        >>> len(songs) > 0
        True
    """
    song_files = sorted(directory.glob(pattern))

    if not song_files:
        raise ValueError(f"No song files found in {directory} matching {pattern}")

    songs = []
    for song_file in song_files:
        try:
            song = Song.from_file(song_file)
            songs.append(song)
        except Exception as e:
            print(f"Warning: Failed to load {song_file}: {e}")

    if not songs:
        raise ValueError(f"No valid songs loaded from {directory}")

    return SongCollection(songs=songs, index_file=index_file)


def read_song_index(index_file: Path) -> List[str]:
    """
    Read song order from index file.

    Args:
        index_file: Path to .songs.index file

    Returns:
        List of song filenames (basenames only)
    """
    if not index_file.exists():
        return []

    with open(index_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    return lines


def write_song_index(index_file: Path, filenames: List[str]) -> None:
    """
    Write song order to index file.

    Args:
        index_file: Path to .songs.index file
        filenames: List of song filenames (basenames only)
    """
    with open(index_file, 'w', encoding='utf-8') as f:
        for filename in filenames:
            f.write(f"{filename}\n")


def resolve_song_order(current_files: List[Path],
                       index_file: Optional[Path] = None,
                       reset: bool = False) -> List[Path]:
    """
    Resolve song order using persistent index file.

    Maintains user's preferred song order across runs by:
    - Reading existing order from index file
    - Preserving order of known songs
    - Adding new songs at the end
    - Removing songs that no longer exist

    Args:
        current_files: List of currently available song files
        index_file: Path to index file (None = no persistence)
        reset: If True, ignore existing index and rebuild

    Returns:
        List of song files in the correct order

    Example:
        >>> files = [Path("song1.txt"), Path("song2.txt")]
        >>> ordered = resolve_song_order(files, Path(".songs.index"))
        >>> len(ordered) == 2
        True
    """
    if index_file is None or reset or not index_file.exists():
        # No index or reset requested - use alphabetical order
        ordered_files = sorted(current_files, key=lambda p: p.name)
        if index_file is not None:
            write_song_index(index_file, [f.name for f in ordered_files])
        return ordered_files

    # Read existing index
    indexed_names = read_song_index(index_file)

    # Build map of filename -> Path for current files
    current_map = {f.name: f for f in current_files}

    # Build ordered list:
    # 1. Songs from index that still exist
    ordered_files = []
    for name in indexed_names:
        if name in current_map:
            ordered_files.append(current_map[name])
            del current_map[name]  # Remove from map

    # 2. New songs not in index (alphabetically sorted)
    new_files = sorted(current_map.values(), key=lambda p: p.name)
    ordered_files.extend(new_files)

    # Update index file
    write_song_index(index_file, [f.name for f in ordered_files])

    return ordered_files
