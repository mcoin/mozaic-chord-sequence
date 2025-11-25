"""
Domain models for Mozaic chord sequence generation.

This module provides Pydantic models for type-safe data handling throughout
the application, replacing dictionary-based data structures.
"""

from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, computed_field
from .chord_notes import chord_to_midi_notes, chord_to_simplified_midi_notes


class Bar(BaseModel):
    """
    Represents a single bar of chords.

    A bar contains one or more chords that will be displayed across
    the bar's duration. Chords can be marked with fills for triggering
    MIDI CC messages.

    Attributes:
        chords: List of chord symbols (e.g., ['Cmaj7', 'Dm7', 'G7'])
        fills: List of boolean flags indicating which chords trigger fills
        chord_notes: List of MIDI note lists for each chord (auto-populated)
        simplified_chord_notes: List of simplified MIDI note lists for each chord (auto-populated)
    """
    chords: List[str] = Field(min_length=1, description="Chord symbols in the bar")
    fills: List[bool] = Field(default_factory=list, description="Fill markers for each chord")
    chord_notes: List[List[int]] = Field(default_factory=list, description="MIDI notes for each chord")
    simplified_chord_notes: List[List[int]] = Field(default_factory=list, description="Simplified MIDI notes for each chord")

    @field_validator('chords')
    @classmethod
    def validate_chords(cls, v: List[str]) -> List[str]:
        """Validate that all chords are non-empty strings."""
        if not all(isinstance(chord, str) and chord.strip() for chord in v):
            raise ValueError("All chords must be non-empty strings")
        return [chord.strip() for chord in v]

    def model_post_init(self, __context):
        """Ensure fills, chord_notes, and simplified_chord_notes lists match chords list length."""
        if not self.fills:
            self.fills = [False] * len(self.chords)
        elif len(self.fills) != len(self.chords):
            raise ValueError("fills list must match chords list length")

        # Populate chord_notes from chord symbols if not already set
        if not self.chord_notes:
            self.chord_notes = [chord_to_midi_notes(chord) for chord in self.chords]
        elif len(self.chord_notes) != len(self.chords):
            raise ValueError("chord_notes list must match chords list length")

        # Populate simplified_chord_notes from chord symbols if not already set
        if not self.simplified_chord_notes:
            self.simplified_chord_notes = [chord_to_simplified_midi_notes(chord) for chord in self.chords]
        elif len(self.simplified_chord_notes) != len(self.chords):
            raise ValueError("simplified_chord_notes list must match chords list length")

    def __len__(self) -> int:
        """Return the number of chords in the bar."""
        return len(self.chords)

    def __getitem__(self, index: int) -> str:
        """Allow indexing into the bar's chords."""
        return self.chords[index]

    def has_fills(self) -> bool:
        """Check if this bar has any fill markers."""
        return any(self.fills)


class Song(BaseModel):
    """
    Represents a song with chord sequences.

    A song contains metadata (title, tempo) and the chord progression
    organized by bars.

    Attributes:
        title: Song title
        tempo: Optional tempo in BPM (beats per minute)
        rhythm_bank: Optional rhythm bank number (0-127)
        rhythm_number: Optional rhythm pattern number (0-127)
        bars: List of bars, each containing chord symbols
        source_file: Optional source file path
    """
    title: str = Field(min_length=1, description="Song title")
    tempo: Optional[int] = Field(
        default=None,
        ge=20,
        le=300,
        description="Tempo in BPM (20-300)"
    )
    rhythm_bank: Optional[int] = Field(
        default=None,
        ge=0,
        le=127,
        description="Rhythm bank (0-127)"
    )
    rhythm_number: Optional[int] = Field(
        default=None,
        ge=0,
        le=127,
        description="Rhythm pattern number (0-127)"
    )
    bars: List[Bar] = Field(min_length=1, description="Bars of chord sequences")
    source_file: Optional[Path] = Field(
        default=None,
        description="Source file path"
    )

    @computed_field
    @property
    def num_bars(self) -> int:
        """Return the number of bars in the song."""
        return len(self.bars)

    @computed_field
    @property
    def has_tempo(self) -> bool:
        """Check if the song has a tempo defined."""
        return self.tempo is not None

    @computed_field
    @property
    def has_rhythm(self) -> bool:
        """Check if the song has rhythm bank and number defined."""
        return self.rhythm_bank is not None and self.rhythm_number is not None

    def get_update_block_name(self, song_index: int) -> str:
        """
        Get the Mozaic update block name for this song.

        Args:
            song_index: Zero-based index of the song

        Returns:
            Update block name (e.g., '@UpdateChordsSong0')
        """
        return f"@UpdateChordsSong{song_index}"

    @classmethod
    def from_file(cls, path: Path) -> "Song":
        """
        Create a Song from a chord file.

        File format:
        - Line 1: Song title
        - Line 2 (optional): tempo=120
        - Line 3 (optional): rhythm <bank> <number>
        - Remaining lines: One bar per line, chords space-separated
        - Chord followed by ' *' triggers a fill (e.g., "Cmaj7 *")

        Args:
            path: Path to the song chord file

        Returns:
            Song instance

        Raises:
            ValueError: If file is empty or has no bars
        """
        with open(path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        if not lines:
            raise ValueError(f"Empty song file: {path}")

        title = lines[0]
        tempo = None
        rhythm_bank = None
        rhythm_number = None
        bar_start_index = 1

        # Detect optional tempo line
        if len(lines) > 1 and lines[1].lower().startswith("tempo="):
            try:
                tempo = int(lines[1].split("=", 1)[1])
            except ValueError:
                raise ValueError(f"Invalid tempo format in file: {path}")
            bar_start_index = 2

        # Detect optional rhythm line
        if len(lines) > bar_start_index and lines[bar_start_index].lower().startswith("rhythm "):
            try:
                parts = lines[bar_start_index].split()
                if len(parts) != 3:
                    raise ValueError(f"Invalid rhythm format (expected 'rhythm <bank> <number>'): {path}")
                rhythm_bank = int(parts[1])
                rhythm_number = int(parts[2])
            except ValueError as e:
                raise ValueError(f"Invalid rhythm format in file: {path} - {e}")
            bar_start_index += 1

        # Parse bars with fill markers
        bar_lines = lines[bar_start_index:]
        if not bar_lines:
            raise ValueError(f"No bars found in song file: {path}")

        bars = []
        for line in bar_lines:
            tokens = line.split()
            chords = []
            fills = []

            i = 0
            while i < len(tokens):
                token = tokens[i]

                # Check if next token is a fill marker
                if i + 1 < len(tokens) and tokens[i + 1] == '*':
                    chords.append(token)
                    fills.append(True)
                    i += 2  # Skip the '*'
                elif token == '*':
                    # Standalone '*' - attach to previous chord
                    if chords and not fills[-1]:
                        fills[-1] = True
                    i += 1
                else:
                    chords.append(token)
                    fills.append(False)
                    i += 1

            if chords:  # Only create bar if it has chords
                bars.append(Bar(chords=chords, fills=fills))

        return cls(
            title=title,
            tempo=tempo,
            rhythm_bank=rhythm_bank,
            rhythm_number=rhythm_number,
            bars=bars,
            source_file=path
        )


class SongCollection(BaseModel):
    """
    Represents a collection of songs with persistent ordering.

    The collection maintains song order using an index file and handles
    adding/removing songs while preserving the user's preferred order.

    Attributes:
        songs: List of Song instances
        index_file: Path to the persistent index file
    """
    songs: List[Song] = Field(default_factory=list, description="Songs in the collection")
    index_file: Optional[Path] = Field(
        default=None,
        description="Path to persistent song order index"
    )

    def __len__(self) -> int:
        """Return the number of songs in the collection."""
        return len(self.songs)

    def __getitem__(self, index: int) -> Song:
        """Allow indexing into the song collection."""
        return self.songs[index]

    def __iter__(self):
        """Allow iteration over songs."""
        return iter(self.songs)

    @computed_field
    @property
    def has_tempo_songs(self) -> bool:
        """Check if any songs have tempo defined."""
        return any(song.has_tempo for song in self.songs)

    def add_song(self, song: Song) -> None:
        """
        Add a song to the collection.

        Args:
            song: Song to add
        """
        self.songs.append(song)

    def get_song_filenames(self) -> List[str]:
        """
        Get list of source filenames for all songs.

        Returns:
            List of filenames (no paths)
        """
        return [
            song.source_file.name
            for song in self.songs
            if song.source_file is not None
        ]


class MozaicMetadata(BaseModel):
    """
    Mozaic script metadata and constants.

    Contains all the constant values and metadata needed for
    generating Mozaic scripts and encoding them.

    Attributes:
        script_name: Name of the Mozaic script
        short_name: Short name displayed in Mozaic
        tap_note: MIDI note for tap tempo
        tap_channel: MIDI channel for tap tempo
        layout: Layout number to display
        fill_channel: MIDI channel for fill triggers
        fill_control: MIDI CC number for fill triggers
        fill_value: MIDI CC value for fill triggers
        rhythm_set_channel: MIDI channel for rhythm selection
        rhythm_bank_cc: MIDI CC number for rhythm bank
        rhythm_cc: MIDI CC number for rhythm pattern
        rhythm_set_delay: Delay in ms before sending rhythm CC
    """
    script_name: str = Field(
        default="Chord Sequence",
        description="Full script name"
    )
    short_name: str = Field(
        default="Chordsequence",
        description="Short name for display"
    )
    tap_note: int = Field(
        default=90,
        ge=0,
        le=127,
        description="MIDI note for tap tempo (0-127)"
    )
    tap_channel: int = Field(
        default=16,
        ge=1,
        le=16,
        description="MIDI channel for tap tempo (1-16)"
    )
    layout: int = Field(
        default=2,
        ge=0,
        le=7,
        description="Layout number (0-7)"
    )
    fill_channel: int = Field(
        default=10,
        ge=1,
        le=16,
        description="MIDI channel for fill triggers (1-16)"
    )
    fill_control: int = Field(
        default=48,
        ge=0,
        le=127,
        description="MIDI CC number for fill triggers (0-127)"
    )
    fill_value: int = Field(
        default=127,
        ge=0,
        le=127,
        description="MIDI CC value for fill triggers (0-127)"
    )
    rhythm_set_channel: int = Field(
        default=10,
        ge=1,
        le=16,
        description="MIDI channel for rhythm selection (1-16)"
    )
    rhythm_bank_cc: int = Field(
        default=31,
        ge=0,
        le=127,
        description="MIDI CC number for rhythm bank (0-127)"
    )
    rhythm_cc: int = Field(
        default=32,
        ge=0,
        le=127,
        description="MIDI CC number for rhythm pattern (0-127)"
    )
    rhythm_set_delay: int = Field(
        default=1000,
        ge=0,
        description="Delay in ms before sending rhythm CC (0+)"
    )


class EncoderConfig(BaseModel):
    """
    Configuration for Mozaic file encoding.

    Controls how the script text is encoded into the .mozaic file format
    using NSKeyedArchiver.

    Attributes:
        use_foundation: Whether to use native Foundation framework (macOS only)
        filename: Output filename for the .mozaic file
        deduplicate_strings: Whether to deduplicate string objects
        deduplicate_numbers: Whether to deduplicate number objects (critical for iPad!)
    """
    use_foundation: bool = Field(
        default=False,
        description="Use native Foundation framework (macOS only)"
    )
    filename: str = Field(
        default="chordSequence.mozaic",
        description="Output .mozaic filename"
    )
    deduplicate_strings: bool = Field(
        default=True,
        description="Deduplicate string objects in archive"
    )
    deduplicate_numbers: bool = Field(
        default=True,
        description="Deduplicate number objects (REQUIRED for iPad compatibility!)"
    )

    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Ensure filename has .mozaic extension."""
        if not v.endswith('.mozaic'):
            return f"{v}.mozaic"
        return v


class ScriptContext(BaseModel):
    """
    Complete context for generating a Mozaic script.

    This model brings together all the components needed to generate
    a complete Mozaic chord sequence script.

    Attributes:
        songs: Collection of songs to include
        metadata: Mozaic script metadata
        encoder_config: Encoder configuration
    """
    songs: SongCollection = Field(
        default_factory=SongCollection,
        description="Song collection"
    )
    metadata: MozaicMetadata = Field(
        default_factory=MozaicMetadata,
        description="Script metadata"
    )
    encoder_config: EncoderConfig = Field(
        default_factory=EncoderConfig,
        description="Encoder configuration"
    )

    @computed_field
    @property
    def song_count(self) -> int:
        """Return the number of songs in the context."""
        return len(self.songs)

    def to_template_context(self) -> dict:
        """
        Convert to dictionary suitable for template rendering.

        Returns:
            Dictionary with 'songs' list containing dicts with:
            - title: str
            - num_bars: int
            - tempo: Optional[int]
            - update_block: str (to be generated)
        """
        return {
            'songs': [
                {
                    'title': song.title,
                    'num_bars': song.num_bars,
                    'tempo': song.tempo,
                    'update_block': ''  # Will be filled by generator
                }
                for song in self.songs
            ]
        }
