"""
Command-line interface for Mozaic Chord Sequence Generator.

This module provides Click-based CLI commands for generating and managing
Mozaic chord sequence files.
"""

import sys
from pathlib import Path
from typing import Optional

import click

from . import __version__
from .models import Song, SongCollection
from .generator import (
    ChordSequenceGenerator,
    load_songs_from_directory,
    resolve_song_order
)


DEFAULT_INDEX_FILE = ".songs.index"


@click.group()
@click.version_option(version=__version__, prog_name="chord-sequence")
def cli():
    """
    Mozaic Chord Sequence Generator

    Generate Mozaic chord sequence scripts from simple text files.
    """
    pass


@cli.command()
@click.argument('song_files', nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option(
    '--output', '-o',
    type=click.Path(path_type=Path),
    default=Path('chordSequence.mozaic'),
    help='Output .mozaic file path',
    show_default=True
)
@click.option(
    '--directory', '-d',
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help='Load all song files from directory (*.txt)'
)
@click.option(
    '--index-file',
    type=click.Path(path_type=Path),
    help=f'Song order index file (default: {DEFAULT_INDEX_FILE} in song directory)'
)
@click.option(
    '--reset-index',
    is_flag=True,
    help='Ignore existing index and rebuild from scratch'
)
@click.option(
    '--use-foundation',
    is_flag=True,
    help='Use native Foundation encoder (macOS only, default: pure Python)'
)
@click.option(
    '--filename',
    type=str,
    help='Filename to embed in .mozaic file (default: output filename stem)'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Verbose output'
)
def generate(song_files, output, directory, index_file, reset_index,
             use_foundation, filename, verbose):
    """
    Generate a Mozaic chord sequence file.

    Reads song files in simple text format and generates a complete
    .mozaic file for use in Mozaic app.

    Song file format:
    \b
    - Line 1: Song title
    - Line 2 (optional): tempo=120
    - Remaining lines: One bar per line, chords space-separated

    Examples:
    \b
        # Generate from specific files
        chord-sequence generate song1.txt song2.txt

        # Generate from all files in directory
        chord-sequence generate -d songs/

        # Specify output file
        chord-sequence generate -d songs/ -o output.mozaic

        # Reset song order
        chord-sequence generate -d songs/ --reset-index
    """
    try:
        songs_list = []

        # Load from directory if specified
        if directory:
            if verbose:
                click.echo(f"Loading songs from directory: {directory}")

            # Determine index file path
            if index_file is None:
                index_file = directory / DEFAULT_INDEX_FILE

            # Get all song files
            song_file_paths = list(directory.glob("*.txt"))

            if not song_file_paths:
                click.echo(f"Error: No .txt files found in {directory}", err=True)
                sys.exit(1)

            # Resolve order using index
            ordered_paths = resolve_song_order(
                song_file_paths,
                index_file=index_file,
                reset=reset_index
            )

            if verbose:
                click.echo(f"Found {len(ordered_paths)} song file(s)")
                if index_file.exists() and not reset_index:
                    click.echo(f"Using song order from: {index_file}")

            # Load songs
            for path in ordered_paths:
                try:
                    song = Song.from_file(path)
                    songs_list.append(song)
                    if verbose:
                        tempo_str = f" (tempo={song.tempo})" if song.tempo else ""
                        click.echo(f"  ✓ {song.title}: {song.num_bars} bars{tempo_str}")
                except Exception as e:
                    click.echo(f"  ✗ Failed to load {path.name}: {e}", err=True)

        # Load from individual files
        elif song_files:
            if verbose:
                click.echo(f"Loading {len(song_files)} song file(s)")

            for path in song_files:
                try:
                    song = Song.from_file(Path(path))
                    songs_list.append(song)
                    if verbose:
                        tempo_str = f" (tempo={song.tempo})" if song.tempo else ""
                        click.echo(f"  ✓ {song.title}: {song.num_bars} bars{tempo_str}")
                except Exception as e:
                    click.echo(f"  ✗ Failed to load {path}: {e}", err=True)

        else:
            click.echo("Error: Specify either song files or --directory", err=True)
            click.echo("Try 'chord-sequence generate --help' for more information.")
            sys.exit(1)

        # Check if we loaded any songs
        if not songs_list:
            click.echo("Error: No valid songs loaded", err=True)
            sys.exit(1)

        # Create song collection
        songs = SongCollection(songs=songs_list)

        # Generate .mozaic file
        if verbose:
            click.echo(f"\nGenerating Mozaic script...")

        generator = ChordSequenceGenerator(use_foundation=use_foundation)
        generator.generate_mozaic_file(songs, output, filename=filename)

        click.echo(f"✓ Created: {output}")
        click.echo(f"  {len(songs)} song(s), {sum(s.num_bars for s in songs)} total bars")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument('song_file', type=click.Path(exists=True, path_type=Path))
def validate(song_file):
    """
    Validate a song file format.

    Checks if a song file is properly formatted and can be loaded.

    Example:
    \b
        chord-sequence validate song.txt
    """
    try:
        song = Song.from_file(song_file)

        click.echo(f"✓ Valid song file: {song_file}")
        click.echo(f"  Title: {song.title}")
        if song.tempo:
            click.echo(f"  Tempo: {song.tempo} BPM")
        click.echo(f"  Bars: {song.num_bars}")

        # Show first few bars
        click.echo("\n  Chord progression:")
        for i, bar in enumerate(song.bars[:4]):
            chords = " ".join(bar.chords)
            click.echo(f"    Bar {i+1}: {chords}")

        if len(song.bars) > 4:
            click.echo(f"    ... ({len(song.bars) - 4} more bars)")

    except Exception as e:
        click.echo(f"✗ Invalid song file: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    '--index-file',
    type=click.Path(path_type=Path),
    help=f'Index file path (default: {DEFAULT_INDEX_FILE} in directory)'
)
def list_songs(directory, index_file):
    """
    List songs in a directory with their current order.

    Shows the order that songs will appear in the generated Mozaic file.

    Example:
    \b
        chord-sequence list-songs songs/
    """
    try:
        if index_file is None:
            index_file = directory / DEFAULT_INDEX_FILE

        # Get all song files
        song_files = list(directory.glob("*.txt"))

        if not song_files:
            click.echo(f"No .txt files found in {directory}")
            return

        # Resolve order
        ordered_files = resolve_song_order(song_files, index_file=index_file)

        click.echo(f"Songs in {directory}:")
        if index_file.exists():
            click.echo(f"(Order from: {index_file})\n")
        else:
            click.echo("(Alphabetical order)\n")

        for i, path in enumerate(ordered_files):
            try:
                song = Song.from_file(path)
                tempo_str = f", {song.tempo} BPM" if song.tempo else ""
                click.echo(f"  {i}. {song.title} ({song.num_bars} bars{tempo_str})")
            except Exception as e:
                click.echo(f"  {i}. {path.name} (error: {e})")

        click.echo(f"\nTotal: {len(ordered_files)} song(s)")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('song_file', type=click.Path(exists=True, path_type=Path))
@click.option(
    '--output', '-o',
    type=click.Path(path_type=Path),
    help='Output .mozaic file (default: based on song filename)'
)
def generate_single(song_file, output):
    """
    Generate a .mozaic file from a single song.

    Quick command for testing individual songs.

    Example:
    \b
        chord-sequence generate-single song.txt
        chord-sequence generate-single song.txt -o test.mozaic
    """
    try:
        song = Song.from_file(song_file)

        if output is None:
            output = Path(song_file).with_suffix('.mozaic')

        songs = SongCollection(songs=[song])
        generator = ChordSequenceGenerator()
        generator.generate_mozaic_file(songs, output)

        click.echo(f"✓ Created: {output}")
        click.echo(f"  {song.title}: {song.num_bars} bars")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('song_files', nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option(
    '--output', '-o',
    type=click.Path(path_type=Path),
    default=Path('chordSequence.txt'),
    help='Output text file',
    show_default=True
)
@click.option(
    '--directory', '-d',
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help='Load all song files from directory (*.txt)'
)
@click.option(
    '--index-file',
    type=click.Path(path_type=Path),
    help=f'Song order index file (default: {DEFAULT_INDEX_FILE} in song directory)'
)
@click.option(
    '--reset-index',
    is_flag=True,
    help='Ignore existing index and rebuild from scratch'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Verbose output'
)
def generate_text(song_files, output, directory, index_file, reset_index, verbose):
    """
    Generate a text Mozaic script (without encoding to .mozaic).

    Outputs just the script text from @OnLoad to the last @End,
    suitable for viewing, debugging, or manual copy-paste into Mozaic.

    Examples:
    \b
        # Generate from directory
        chord-sequence generate-text -d songs/ -o script.txt

        # Generate from specific files
        chord-sequence generate-text song1.txt song2.txt

        # Output to stdout
        chord-sequence generate-text -d songs/ -o -
    """
    try:
        songs_list = []

        # Load from directory if specified
        if directory:
            if verbose:
                click.echo(f"Loading songs from directory: {directory}")

            # Determine index file path
            if index_file is None:
                index_file = directory / DEFAULT_INDEX_FILE

            # Get all song files
            song_file_paths = list(directory.glob("*.txt"))

            if not song_file_paths:
                click.echo(f"Error: No .txt files found in {directory}", err=True)
                sys.exit(1)

            # Resolve order using index
            ordered_paths = resolve_song_order(
                song_file_paths,
                index_file=index_file,
                reset=reset_index
            )

            if verbose:
                click.echo(f"Found {len(ordered_paths)} song file(s)")

            # Load songs
            for path in ordered_paths:
                try:
                    song = Song.from_file(path)
                    songs_list.append(song)
                    if verbose:
                        tempo_str = f" (tempo={song.tempo})" if song.tempo else ""
                        click.echo(f"  ✓ {song.title}: {song.num_bars} bars{tempo_str}")
                except Exception as e:
                    click.echo(f"  ✗ Failed to load {path.name}: {e}", err=True)

        # Load from individual files
        elif song_files:
            if verbose:
                click.echo(f"Loading {len(song_files)} song file(s)")

            for path in song_files:
                try:
                    song = Song.from_file(Path(path))
                    songs_list.append(song)
                    if verbose:
                        tempo_str = f" (tempo={song.tempo})" if song.tempo else ""
                        click.echo(f"  ✓ {song.title}: {song.num_bars} bars{tempo_str}")
                except Exception as e:
                    click.echo(f"  ✗ Failed to load {path}: {e}", err=True)

        else:
            click.echo("Error: Specify either song files or --directory", err=True)
            click.echo("Try 'chord-sequence generate-text --help' for more information.")
            sys.exit(1)

        # Check if we loaded any songs
        if not songs_list:
            click.echo("Error: No valid songs loaded", err=True)
            sys.exit(1)

        # Create song collection
        songs = SongCollection(songs=songs_list)

        # Generate script text
        if verbose:
            click.echo(f"\nGenerating Mozaic script text...")

        generator = ChordSequenceGenerator()
        script_text = generator.generate_script(songs)

        # Output to file or stdout
        if str(output) == '-':
            click.echo(script_text)
        else:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(script_text)
            click.echo(f"✓ Created: {output}")
            click.echo(f"  {len(songs)} song(s), {sum(s.num_bars for s in songs)} total bars")
            click.echo(f"  {len(script_text.splitlines())} lines")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point for CLI."""
    cli()


if __name__ == '__main__':
    main()
