"""
Encoders for Mozaic file format.

This package provides NSKeyedArchiver implementations for encoding
Mozaic scripts into the .mozaic file format.
"""

from .archiver import (
    PurePythonArchiver,
    create_mozaic_file,
    MozaicEncoder
)

# Backward compatibility alias
NSKeyedArchiver = PurePythonArchiver

__all__ = [
    'PurePythonArchiver',
    'NSKeyedArchiver',  # Backward compatibility
    'create_mozaic_file',
    'MozaicEncoder'
]
