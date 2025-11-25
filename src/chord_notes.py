"""
Chord to MIDI note conversion using pychord library.

This module provides functionality to convert chord symbols (e.g., "Cmaj7", "Dm7")
into MIDI note numbers for playback.
"""

import re
from typing import List
from pychord import Chord
from pychord.utils import note_to_val
from pychord.constants.qualities import DEFAULT_QUALITIES


class QualityManager:
    """
    Manages custom chord qualities for pychord.

    This class registers missing chord qualities that are common in jazz
    notation but not included in pychord by default.
    """

    _initialized = False

    @classmethod
    def _get_quality_components(cls, quality_name: str):
        """Get components for a quality from DEFAULT_QUALITIES."""
        for name, components in DEFAULT_QUALITIES:
            if name == quality_name:
                return components
        return None

    @classmethod
    def _quality_exists(cls, quality_name: str) -> bool:
        """Check if a quality already exists in DEFAULT_QUALITIES."""
        return any(name == quality_name for name, _ in DEFAULT_QUALITIES)

    @classmethod
    def initialize(cls):
        """
        Initialize and register custom chord qualities with pychord.

        This method is idempotent - it can be called multiple times safely.
        """
        if cls._initialized:
            return

        # Register jazz notation variants
        # '-7' is jazz notation for minor 7th (same as 'm7')
        if not cls._quality_exists('-7'):
            m7_components = cls._get_quality_components('m7')
            if m7_components:
                DEFAULT_QUALITIES.append(('-7', m7_components))

        # '-6' is jazz notation for minor 6th (same as 'm6')
        if not cls._quality_exists('-6'):
            m6_components = cls._get_quality_components('m6')
            if m6_components:
                DEFAULT_QUALITIES.append(('-6', m6_components))

        # 'Maj7' is alternative notation for maj7 (capital M)
        if not cls._quality_exists('Maj7'):
            maj7_components = cls._get_quality_components('maj7')
            if maj7_components:
                DEFAULT_QUALITIES.append(('Maj7', maj7_components))

        # '-7b5' is jazz notation for half-diminished (same as 'm7b5')
        if not cls._quality_exists('-7b5'):
            m7b5_components = cls._get_quality_components('m7b5')
            if m7b5_components:
                DEFAULT_QUALITIES.append(('-7b5', m7b5_components))

        # '-' alone is jazz notation for minor (same as 'm')
        if not cls._quality_exists('-'):
            m_components = cls._get_quality_components('m')
            if m_components:
                DEFAULT_QUALITIES.append(('-', m_components))

        cls._initialized = True


def parse_note_with_octave(note_string: str) -> tuple[str, int]:
    """
    Parse a note string with octave into note name and octave number.

    Args:
        note_string: Note with octave (e.g., "C4", "F#3", "Bb5")

    Returns:
        Tuple of (note_name, octave_number)

    Example:
        >>> parse_note_with_octave("C4")
        ("C", 4)
        >>> parse_note_with_octave("F#3")
        ("F#", 3)
    """
    # Match note name (letter + optional sharp/flat) and octave number
    match = re.match(r'^([A-G][#b]?)(\d+)$', note_string)
    if not match:
        raise ValueError(f"Invalid note format: {note_string}")

    note_name = match.group(1)
    octave = int(match.group(2))

    return note_name, octave


def note_to_midi(note_string: str) -> int:
    """
    Convert a note string with octave to MIDI note number.

    MIDI note numbers range from 0 (C-1) to 127 (G9).
    Middle C (C4) = 60.

    Args:
        note_string: Note with octave (e.g., "C4", "F#3")

    Returns:
        MIDI note number (0-127)

    Example:
        >>> note_to_midi("C4")
        60
        >>> note_to_midi("A3")
        57
    """
    note_name, octave = parse_note_with_octave(note_string)

    # Get note value (C=0, C#=1, D=2, ..., B=11)
    note_val = note_to_val(note_name)

    # Calculate MIDI note number
    # MIDI C4 (middle C) = 60
    # Formula: (octave + 1) * 12 + note_value
    midi_number = (octave + 1) * 12 + note_val

    return midi_number


def midi_to_note_name(midi_number: int) -> str:
    """
    Convert a MIDI note number to a human-readable note name with octave.

    Args:
        midi_number: MIDI note number (0-127)

    Returns:
        Note name with octave (e.g., "C4", "F#3", "Bb5")

    Example:
        >>> midi_to_note_name(60)
        'C4'
        >>> midi_to_note_name(57)
        'A3'
        >>> midi_to_note_name(63)
        'Eb4'
    """
    # MIDI notes: C-1 = 0, C0 = 12, ..., C4 = 60
    # Reverse formula: octave = (midi / 12) - 1, note = midi % 12
    octave = (midi_number // 12) - 1
    note_index = midi_number % 12

    # Note names
    note_names = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
    note_name = note_names[note_index]

    return f"{note_name}{octave}"


def chord_to_midi_notes(chord_symbol: str, octave: int = 3) -> List[int]:
    """
    Convert a chord symbol to a list of MIDI note numbers.

    Uses the pychord library to parse chord symbols and extract note components.
    Supports 105+ chord qualities including maj7, m7, dim, aug, sus4, 9, 11, 13, etc.
    Also supports jazz notation variants like -7, -6, Maj7, etc.

    Args:
        chord_symbol: Chord symbol (e.g., "Cmaj7", "Dm7", "G7sus4", "F#m7b5", "D-7")
        octave: Base octave for the chord (default: 3, which gives C3=48)

    Returns:
        List of MIDI note numbers sorted from lowest to highest.
        Returns empty list if chord symbol is invalid or unknown.

    Example:
        >>> chord_to_midi_notes("C")
        [48, 52, 55]  # C3, E3, G3
        >>> chord_to_midi_notes("Cmaj7", octave=4)
        [60, 64, 67, 71]  # C4, E4, G4, B4
        >>> chord_to_midi_notes("D-7")  # Jazz notation for Dm7
        [50, 53, 57, 60]  # D3, F3, A3, C4
        >>> chord_to_midi_notes("InvalidChord")
        []
    """
    try:
        # Initialize custom chord qualities
        QualityManager.initialize()

        # Parse chord symbol
        chord = Chord(chord_symbol)

        # Get note components with octave
        notes_with_octave = chord.components_with_pitch(octave)

        # Convert each note to MIDI number
        midi_notes = [note_to_midi(note) for note in notes_with_octave]

        # Sort notes (should already be sorted, but ensure it)
        midi_notes.sort()

        return midi_notes

    except Exception as e:
        # Handle unknown chord qualities or parsing errors
        # Return empty list for graceful degradation
        import warnings
        warnings.warn(f"Could not parse chord '{chord_symbol}': {e}", UserWarning)
        return []


def simplify_chord_symbol(chord_symbol: str) -> str:
    """
    Simplify a chord symbol to basic triad for simplified voicing.

    Converts extended chords to their basic triad equivalents.
    Currently handles:
    - 6 chords (C6, D6, etc.) -> major triad (C, D, etc.)

    Args:
        chord_symbol: Original chord symbol (e.g., "C6", "Dm7", "G7")

    Returns:
        Simplified chord symbol (e.g., "C" for "C6", "Dm" for "Dm7")

    Example:
        >>> simplify_chord_symbol("C6")
        'C'
        >>> simplify_chord_symbol("D6")
        'D'
        >>> simplify_chord_symbol("F#6")
        'F#'
    """
    # Handle 6 chords - strip the '6' to get major triad
    # Match: root note (letter + optional sharp/flat) + '6' + optional bass
    # Examples: C6, F#6, Bb6, C6/E
    match = re.match(r'^([A-G][#b]?)6(.*)$', chord_symbol)
    if match:
        root = match.group(1)
        bass = match.group(2)  # Could be empty or something like '/E'
        return root + bass

    # For other chords, return as-is for now
    return chord_symbol


def chord_to_simplified_midi_notes(chord_symbol: str, octave: int = 3) -> List[int]:
    """
    Convert a chord symbol to simplified MIDI notes (basic triads).

    This function simplifies extended chords before converting to MIDI.
    For example, C6 becomes C (major triad: C, E, G).

    Args:
        chord_symbol: Chord symbol (e.g., "C6", "Dm7", "G7sus4")
        octave: Base octave for the chord (default: 3)

    Returns:
        List of MIDI note numbers for simplified voicing.
        Returns empty list if chord symbol is invalid.

    Example:
        >>> chord_to_simplified_midi_notes("C6")
        [48, 52, 55]  # C3, E3, G3 (same as "C")
        >>> chord_to_simplified_midi_notes("D6")
        [50, 54, 57]  # D3, F#3, A3 (same as "D")
    """
    # Simplify the chord symbol first
    simplified = simplify_chord_symbol(chord_symbol)

    # Convert simplified chord to MIDI notes
    return chord_to_midi_notes(simplified, octave)
