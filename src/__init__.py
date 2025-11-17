"""
chordSequence - Mozaic Chord Sequence Generator

A pure Python toolkit for creating and managing Mozaic chord sequence scripts.
"""

__version__ = "2.0.0"
__author__ = "Generated with Claude Code"

# Public API exports
from .models import Song, Bar, SongCollection, ScriptContext, MozaicMetadata, EncoderConfig
from .generator import ChordSequenceGenerator, generate_update_block
from .templates import TemplateManager, render_chord_sequence
from .encoders import NSKeyedArchiver, MozaicEncoder, create_mozaic_file

__all__ = [
    # Version
    '__version__',
    '__author__',

    # Models
    'Song',
    'Bar',
    'SongCollection',
    'ScriptContext',
    'MozaicMetadata',
    'EncoderConfig',

    # Generator
    'ChordSequenceGenerator',
    'generate_update_block',

    # Templates
    'TemplateManager',
    'render_chord_sequence',

    # Encoders
    'NSKeyedArchiver',
    'MozaicEncoder',
    'create_mozaic_file',
]
