#!/usr/bin/env python3
"""
mozaic_pure_encoder.py
----------------------
Pure Python NSKeyedArchiver encoder (no Foundation dependency).
Works on any platform including iOS/iPad.

Usage:
    python3 mozaic_pure_encoder.py script.txt output.mozaic
"""

import sys
import argparse
from pathlib import Path
import plistlib
from plistlib import UID


def create_nskeyedarchiver_plist(data_dict):
    """
    Create NSKeyedArchiver plist structure from a dictionary.
    Returns a plist-compatible dictionary.
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


def create_mozaic_file_pure(script_text: str, filename: str = "script") -> bytes:
    """
    Create a .mozaic file using pure Python (no Foundation dependency).
    Returns bytes that can be written to a file.
    """
    # Build the data dictionary (must be in consistent order)
    data_dict = {}

    # Add fields in alphabetical order (to match native encoder behavior)
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
    plist = create_nskeyedarchiver_plist(data_dict)

    # Serialize to binary plist
    return plistlib.dumps(plist, fmt=plistlib.FMT_BINARY)


def main():
    parser = argparse.ArgumentParser(
        description="Convert text Mozaic script to .mozaic file (pure Python, no Foundation)"
    )
    parser.add_argument("input", type=Path, help="Input text file containing Mozaic script")
    parser.add_argument("output", type=Path, nargs='?', help="Output .mozaic file (optional)")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Determine output filename
    if args.output:
        output_path = args.output
    else:
        output_path = args.input.with_suffix('.mozaic')

    # Read the script text
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            script_text = f.read()
    except Exception as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(1)

    if not script_text.strip():
        print("Error: Input file is empty", file=sys.stderr)
        sys.exit(1)

    # Get filename
    filename = output_path.stem

    # Generate .mozaic file
    print(f"Creating {output_path} using pure Python NSKeyedArchiver...")
    print(f"  Script length: {len(script_text)} characters")
    print(f"  Lines: {len(script_text.splitlines())}")

    try:
        mozaic_bytes = create_mozaic_file_pure(script_text, filename)
    except Exception as e:
        print(f"Error creating .mozaic file: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Write to file
    try:
        with open(output_path, 'wb') as f:
            f.write(mozaic_bytes)
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"✓ Successfully created {output_path} ({len(mozaic_bytes)} bytes)")
    print(f"✓ Pure Python implementation - works on any platform including iPad!")


if __name__ == "__main__":
    main()
