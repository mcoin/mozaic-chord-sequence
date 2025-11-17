"""
NSKeyedArchiver implementation for Mozaic file encoding.

This module provides both pure Python and native Foundation implementations
for encoding Mozaic scripts into the .mozaic file format.

The pure Python implementation is critical for iPad compatibility and works
on any platform without dependencies.
"""

import plistlib
from pathlib import Path
from typing import Dict, Any, Optional
from plistlib import UID

# Try to import Foundation for native encoding (macOS only)
try:
    from Foundation import (
        NSKeyedArchiver as FoundationNSKeyedArchiver,
        NSMutableData, NSData, NSNumber, NSString,
        NSMutableDictionary
    )
    FOUNDATION_AVAILABLE = True
except ImportError:
    FOUNDATION_AVAILABLE = False
    FoundationNSKeyedArchiver = None


# FourCC constants (Four Character Codes)
FOURCC_MANUFACTURER = 1114792301  # 'Bram'
FOURCC_SUBTYPE = 1836022371       # 'mozc'
FOURCC_TYPE = 1635085673          # 'aumi'

# Default values
DEFAULT_SCALE = 4095  # 0xFFF - all 12 scale notes enabled
DEFAULT_VERSION = 1
DEFAULT_GUI_BYTES = b'\x00' * 36 + b'\x02\x00\x00\x00'  # 40 bytes
DEFAULT_VARIABLE_BYTES = b'\x00' * 16
DEFAULT_AU_VALUES = [0.0, 0.0, 0.5, 0.0, 0.0, 0.5, 0.0, 0.0]
NUM_KNOBS = 22
NUM_VARIABLES = 6
NUM_AU_VALUES = 8


class PurePythonArchiver:
    """
    Pure Python implementation of NSKeyedArchiver for Mozaic files.

    This implementation is critical for iPad compatibility. The key feature
    is proper deduplication of strings AND numbers - without number
    deduplication, files won't load on iPad.

    The archiver builds a plist structure that matches what Apple's
    NSKeyedArchiver produces, with UIDs referencing deduplicated objects.
    """

    def __init__(self, deduplicate_strings: bool = True,
                 deduplicate_numbers: bool = True):
        """
        Initialize the archiver.

        Args:
            deduplicate_strings: Whether to deduplicate string objects
            deduplicate_numbers: Whether to deduplicate number objects
                                (REQUIRED for iPad compatibility!)
        """
        self.deduplicate_strings = deduplicate_strings
        self.deduplicate_numbers = deduplicate_numbers

        # Objects array - starts with $null, then root dict at position 1
        self.objects = ['$null', None]  # Placeholder for root dict

        # Track NSData objects that need class reference updates
        self.nsdata_objects = []

        # Maps for deduplication
        self.string_map = {} if deduplicate_strings else None
        self.number_map = {} if deduplicate_numbers else None

    def add_string(self, s: str) -> UID:
        """
        Add a string to the archive with optional deduplication.

        Args:
            s: String to add

        Returns:
            UID referencing the string in the objects array
        """
        if self.string_map is not None and s in self.string_map:
            return UID(self.string_map[s])

        idx = len(self.objects)
        self.objects.append(s)

        if self.string_map is not None:
            self.string_map[s] = idx

        return UID(idx)

    def add_number(self, n: float) -> UID:
        """
        Add a number (int or float) to the archive with optional deduplication.

        Critical for iPad compatibility - without deduplication, files
        with many 0.0 values will be too large and won't load.

        Args:
            n: Number to add

        Returns:
            UID referencing the number in the objects array
        """
        if self.number_map is not None and n in self.number_map:
            return UID(self.number_map[n])

        idx = len(self.objects)
        self.objects.append(n)

        if self.number_map is not None:
            self.number_map[n] = idx

        return UID(idx)

    def add_nsdata(self, data_bytes: bytes) -> UID:
        """
        Add NSData/NSMutableData object to the archive.

        The class reference is added later after all objects are collected.

        Args:
            data_bytes: Binary data to wrap

        Returns:
            UID referencing the NSData object
        """
        # Create NSData object with placeholder class
        nsdata_obj = {
            '$class': None,  # Will be updated later
            'NS.data': data_bytes
        }
        idx = len(self.objects)
        self.objects.append(nsdata_obj)
        self.nsdata_objects.append(idx)  # Track for later update
        return UID(idx)

    def archive(self, data_dict: Dict[str, Any]) -> dict:
        """
        Create NSKeyedArchiver plist structure from a dictionary.

        Args:
            data_dict: Dictionary to archive

        Returns:
            Plist dictionary structure
        """
        # Build NS.keys and NS.objects arrays for root dictionary
        keys = []
        values = []

        for key, value in data_dict.items():
            # Add key (always string)
            keys.append(self.add_string(key))

            # Add value based on type
            if isinstance(value, str):
                values.append(self.add_string(value))
            elif isinstance(value, (int, float)):
                values.append(self.add_number(float(value)))
            elif isinstance(value, bytes):
                values.append(self.add_nsdata(value))
            else:
                raise ValueError(f"Unsupported value type: {type(value)}")

        # Add class metadata objects at the end

        # NSData/NSMutableData class metadata
        if self.nsdata_objects:
            nsdata_class_uid = UID(len(self.objects))
            nsdata_class = {
                '$classes': ['NSMutableData', 'NSData', 'NSObject'],
                '$classname': 'NSMutableData'
            }
            self.objects.append(nsdata_class)

            # Update all NSData objects with correct class reference
            for idx in self.nsdata_objects:
                self.objects[idx]['$class'] = nsdata_class_uid

        # NSDictionary class metadata (for root object)
        nsdict_class_uid = UID(len(self.objects))
        nsdict_class = {
            '$classes': ['NSMutableDictionary', 'NSDictionary', 'NSObject'],
            '$classname': 'NSMutableDictionary'
        }
        self.objects.append(nsdict_class)

        # Create root dictionary object (goes at position 1)
        root_dict = {
            'NS.keys': keys,
            'NS.objects': values,
            '$class': nsdict_class_uid
        }
        self.objects[1] = root_dict

        # Create final plist structure
        plist = {
            '$version': 100000,
            '$archiver': 'NSKeyedArchiver',
            '$top': {'root': UID(1)},
            '$objects': self.objects
        }

        return plist


class MozaicEncoder:
    """
    High-level encoder for creating Mozaic .mozaic files.

    Handles both pure Python and native Foundation encoding,
    with automatic fallback to pure Python if Foundation is unavailable.
    """

    def __init__(self, use_foundation: bool = False,
                 deduplicate_strings: bool = True,
                 deduplicate_numbers: bool = True):
        """
        Initialize the encoder.

        Args:
            use_foundation: Whether to use native Foundation (macOS only)
            deduplicate_strings: Whether to deduplicate strings
            deduplicate_numbers: Whether to deduplicate numbers (critical!)
        """
        self.use_foundation = use_foundation and FOUNDATION_AVAILABLE
        self.deduplicate_strings = deduplicate_strings
        self.deduplicate_numbers = deduplicate_numbers

    def create_data_dict(self, script_text: str, filename: str = "chordSequence") -> Dict[str, Any]:
        """
        Create the data dictionary for a Mozaic file.

        This contains all the metadata and the script code.

        Args:
            script_text: The Mozaic script content
            filename: Filename to embed in the file

        Returns:
            Dictionary with all Mozaic file data
        """
        data_dict = {}

        # Audio Unit values (0-7)
        for i, val in enumerate(DEFAULT_AU_VALUES):
            data_dict[f'AUVALUE{i}'] = val

        # CODE - script as bytes
        data_dict['CODE'] = script_text.encode('utf-8')

        # FILENAME
        data_dict['FILENAME'] = filename

        # GUI - 40 bytes
        data_dict['GUI'] = DEFAULT_GUI_BYTES

        # Knob labels (0-21)
        for i in range(NUM_KNOBS):
            data_dict[f'KNOBLABEL{i}'] = f'Knob {i}'

        # KNOBTITLE
        data_dict['KNOBTITLE'] = 'Chord Sequence'

        # Knob values (0-21)
        for i in range(NUM_KNOBS):
            data_dict[f'KNOBVALUE{i}'] = 0.0

        # PADTITLE
        data_dict['PADTITLE'] = ''

        # SCALE
        data_dict['SCALE'] = DEFAULT_SCALE

        # Variables - 16-byte binary values (0-5)
        for i in range(NUM_VARIABLES):
            data_dict[f'VARIABLE{i}'] = DEFAULT_VARIABLE_BYTES

        # XVALUE, YVALUE
        data_dict['XVALUE'] = 0.0

        # XYTITLE
        data_dict['XYTITLE'] = ''

        # YVALUE
        data_dict['YVALUE'] = 0.0

        # data field - empty bytes
        data_dict['data'] = b''

        # Integers (manufacturer, subtype, type, version)
        data_dict['manufacturer'] = FOURCC_MANUFACTURER
        data_dict['subtype'] = FOURCC_SUBTYPE
        data_dict['type'] = FOURCC_TYPE
        data_dict['version'] = DEFAULT_VERSION

        return data_dict

    def encode_pure_python(self, script_text: str, filename: str = "chordSequence") -> bytes:
        """
        Encode using pure Python NSKeyedArchiver implementation.

        Works on any platform including iOS/iPad.

        Args:
            script_text: The Mozaic script content
            filename: Filename to embed

        Returns:
            Binary plist bytes
        """
        # Create data dictionary
        data_dict = self.create_data_dict(script_text, filename)

        # Create archiver and encode
        archiver = PurePythonArchiver(
            deduplicate_strings=self.deduplicate_strings,
            deduplicate_numbers=self.deduplicate_numbers
        )
        plist = archiver.archive(data_dict)

        # Serialize to binary plist
        return plistlib.dumps(plist, fmt=plistlib.FMT_BINARY)

    def encode_foundation(self, script_text: str, filename: str = "chordSequence") -> bytes:
        """
        Encode using native Foundation NSKeyedArchiver (macOS only).

        Args:
            script_text: The Mozaic script content
            filename: Filename to embed

        Returns:
            Binary plist bytes

        Raises:
            RuntimeError: If Foundation is not available or archiving fails
        """
        if not FOUNDATION_AVAILABLE:
            raise RuntimeError("Foundation framework not available (macOS only)")

        # Create the data structure using Foundation types
        plist_data = NSMutableDictionary.dictionary()

        # CODE - NSMutableData containing the script
        code_bytes = script_text.encode('utf-8')
        code_data = NSMutableData.dataWithBytes_length_(code_bytes, len(code_bytes))
        plist_data['CODE'] = code_data

        # GUI - 40 bytes
        plist_data['GUI'] = NSData.dataWithBytes_length_(
            DEFAULT_GUI_BYTES, len(DEFAULT_GUI_BYTES)
        )

        # Strings
        plist_data['FILENAME'] = NSString.stringWithString_(filename)
        plist_data['KNOBTITLE'] = NSString.stringWithString_('Chord Sequence')
        plist_data['PADTITLE'] = NSString.stringWithString_('')
        plist_data['XYTITLE'] = NSString.stringWithString_('')

        # Integers (as NSNumber)
        plist_data['manufacturer'] = NSNumber.numberWithInt_(FOURCC_MANUFACTURER)
        plist_data['subtype'] = NSNumber.numberWithInt_(FOURCC_SUBTYPE)
        plist_data['type'] = NSNumber.numberWithInt_(FOURCC_TYPE)
        plist_data['version'] = NSNumber.numberWithInt_(DEFAULT_VERSION)
        plist_data['SCALE'] = NSNumber.numberWithInt_(DEFAULT_SCALE)

        # Knob values (0-21)
        for i in range(NUM_KNOBS):
            plist_data[f'KNOBVALUE{i}'] = NSNumber.numberWithDouble_(0.0)

        # Knob labels (0-21)
        for i in range(NUM_KNOBS):
            plist_data[f'KNOBLABEL{i}'] = NSString.stringWithString_(f'Knob {i}')

        # Audio Unit values (0-7)
        for i, val in enumerate(DEFAULT_AU_VALUES):
            plist_data[f'AUVALUE{i}'] = NSNumber.numberWithDouble_(val)

        # Variables (0-5) - 16-byte binary values
        for i in range(NUM_VARIABLES):
            plist_data[f'VARIABLE{i}'] = NSData.dataWithBytes_length_(
                DEFAULT_VARIABLE_BYTES, len(DEFAULT_VARIABLE_BYTES)
            )

        # XY Pad values
        plist_data['XVALUE'] = NSNumber.numberWithDouble_(0.0)
        plist_data['YVALUE'] = NSNumber.numberWithDouble_(0.0)

        # data field (empty NSMutableData)
        empty_data = NSMutableData.data()
        plist_data['data'] = empty_data

        # Archive using native NSKeyedArchiver
        archived_data, error = FoundationNSKeyedArchiver.archivedDataWithRootObject_requiringSecureCoding_error_(
            plist_data, False, None
        )

        if error:
            raise RuntimeError(f"NSKeyedArchiver error: {error}")

        # Convert to bytes
        return bytes(archived_data)

    def encode(self, script_text: str, filename: str = "chordSequence") -> bytes:
        """
        Encode a Mozaic script to .mozaic file bytes.

        Automatically selects the appropriate encoder based on configuration.

        Args:
            script_text: The Mozaic script content
            filename: Filename to embed

        Returns:
            Binary .mozaic file bytes
        """
        if self.use_foundation:
            return self.encode_foundation(script_text, filename)
        else:
            return self.encode_pure_python(script_text, filename)


def create_mozaic_file(script_text: str,
                       output_path: Path,
                       filename: Optional[str] = None,
                       use_foundation: bool = False,
                       deduplicate_strings: bool = True,
                       deduplicate_numbers: bool = True) -> None:
    """
    Create a .mozaic file from script text.

    Convenience function that combines encoding and writing to file.

    Args:
        script_text: The Mozaic script content
        output_path: Path where the .mozaic file will be written
        filename: Optional filename to embed (defaults to stem of output_path)
        use_foundation: Whether to use native Foundation encoding
        deduplicate_strings: Whether to deduplicate strings
        deduplicate_numbers: Whether to deduplicate numbers (REQUIRED for iPad!)

    Example:
        >>> script = "@OnLoad\\n  Log {Hello}\\n@End"
        >>> create_mozaic_file(script, Path("test.mozaic"))
    """
    if filename is None:
        filename = output_path.stem

    encoder = MozaicEncoder(
        use_foundation=use_foundation,
        deduplicate_strings=deduplicate_strings,
        deduplicate_numbers=deduplicate_numbers
    )

    mozaic_bytes = encoder.encode(script_text, filename)

    with open(output_path, 'wb') as f:
        f.write(mozaic_bytes)
