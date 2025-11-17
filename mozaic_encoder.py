#!/usr/bin/env python3
"""
mozaic_encoder.py
-----------------
Converts plain text Mozaic scripts to NSKeyedArchiver .mozaic files.

Usage:
    python3 mozaic_encoder.py script.txt output.mozaic
    python3 mozaic_encoder.py script.txt  # Creates script.mozaic
    python3 mozaic_encoder.py --pure-python script.txt output.mozaic  # iPad-compatible
"""

import sys
import argparse
from pathlib import Path
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


def create_nskeyedarchiver_plist_pure(data_dict):
    """Pure Python NSKeyedArchiver implementation (no Foundation dependency)."""
    objects = ['$null', None]
    nsdata_objects = []
    string_map = {}
    number_map = {}

    def add_string(s):
        if s in string_map:
            return UID(string_map[s])
        idx = len(objects)
        objects.append(s)
        string_map[s] = idx
        return UID(idx)

    def add_number(n):
        if n in number_map:
            return UID(number_map[n])
        idx = len(objects)
        objects.append(n)
        number_map[n] = idx
        return UID(idx)

    def add_nsdata(data_bytes):
        nsdata_obj = {'$class': None, 'NS.data': data_bytes}
        idx = len(objects)
        objects.append(nsdata_obj)
        nsdata_objects.append(idx)
        return UID(idx)

    keys = []
    values = []

    for key, value in data_dict.items():
        keys.append(add_string(key))
        if isinstance(value, str):
            values.append(add_string(value))
        elif isinstance(value, (int, float)):
            values.append(add_number(value))
        elif isinstance(value, bytes):
            values.append(add_nsdata(value))
        else:
            raise ValueError(f"Unsupported value type: {type(value)}")

    if nsdata_objects:
        nsdata_class_uid = UID(len(objects))
        nsdata_class = {
            '$classes': ['NSMutableData', 'NSData', 'NSObject'],
            '$classname': 'NSMutableData'
        }
        objects.append(nsdata_class)
        for idx in nsdata_objects:
            objects[idx]['$class'] = nsdata_class_uid

    nsdict_class_uid = UID(len(objects))
    nsdict_class = {
        '$classes': ['NSMutableDictionary', 'NSDictionary', 'NSObject'],
        '$classname': 'NSMutableDictionary'
    }
    objects.append(nsdict_class)

    root_dict = {
        'NS.keys': keys,
        'NS.objects': values,
        '$class': nsdict_class_uid
    }
    objects[1] = root_dict

    return {
        '$version': 100000,
        '$archiver': 'NSKeyedArchiver',
        '$top': {'root': UID(1)},
        '$objects': objects
    }


def create_mozaic_file_pure(script_text: str, filename: str = "script") -> bytes:
    """Create .mozaic file using pure Python (iPad-compatible)."""
    data_dict = {}

    # Add fields in order
    au_values = [0.0, 0.0, 0.5, 0.0, 0.0, 0.5, 0.0, 0.0]
    for i, val in enumerate(au_values):
        data_dict[f'AUVALUE{i}'] = val

    data_dict['CODE'] = script_text.encode('utf-8')
    data_dict['FILENAME'] = filename
    data_dict['GUI'] = b'\x00' * 36 + b'\x02\x00\x00\x00'

    for i in range(22):
        data_dict[f'KNOBLABEL{i}'] = f'Knob {i}'

    data_dict['KNOBTITLE'] = 'Mozaic Script'

    for i in range(22):
        data_dict[f'KNOBVALUE{i}'] = 0.0

    data_dict['PADTITLE'] = ''
    data_dict['SCALE'] = 4095

    variable_bytes = b'\x00' * 16
    for i in range(6):
        data_dict[f'VARIABLE{i}'] = variable_bytes

    data_dict['XVALUE'] = 0.0
    data_dict['XYTITLE'] = ''
    data_dict['YVALUE'] = 0.0
    data_dict['data'] = b''
    data_dict['manufacturer'] = 1114792301
    data_dict['subtype'] = 1836022371
    data_dict['type'] = 1635085673
    data_dict['version'] = 1

    plist = create_nskeyedarchiver_plist_pure(data_dict)
    return plistlib.dumps(plist, fmt=plistlib.FMT_BINARY)


def create_mozaic_file_native(script_text: str, filename: str = "script") -> bytes:
    """Create .mozaic file using native NSKeyedArchiver (macOS only)."""
    plist_data = NSMutableDictionary.dictionary()

    code_data = NSMutableData.dataWithBytes_length_(
        script_text.encode('utf-8'),
        len(script_text.encode('utf-8'))
    )
    plist_data['CODE'] = code_data

    gui_bytes = b'\x00' * 36 + b'\x02\x00\x00\x00'
    plist_data['GUI'] = NSData.dataWithBytes_length_(gui_bytes, len(gui_bytes))

    plist_data['FILENAME'] = NSString.stringWithString_(filename)
    plist_data['KNOBTITLE'] = NSString.stringWithString_('Mozaic Script')
    plist_data['PADTITLE'] = NSString.stringWithString_('')
    plist_data['XYTITLE'] = NSString.stringWithString_('')

    plist_data['manufacturer'] = NSNumber.numberWithInt_(1114792301)
    plist_data['subtype'] = NSNumber.numberWithInt_(1836022371)
    plist_data['type'] = NSNumber.numberWithInt_(1635085673)
    plist_data['version'] = NSNumber.numberWithInt_(1)
    plist_data['SCALE'] = NSNumber.numberWithInt_(4095)

    for i in range(22):
        plist_data[f'KNOBVALUE{i}'] = NSNumber.numberWithDouble_(0.0)

    for i in range(22):
        plist_data[f'KNOBLABEL{i}'] = NSString.stringWithString_(f'Knob {i}')

    au_values = [0.0, 0.0, 0.5, 0.0, 0.0, 0.5, 0.0, 0.0]
    for i, val in enumerate(au_values):
        plist_data[f'AUVALUE{i}'] = NSNumber.numberWithDouble_(val)

    variable_bytes = b'\x00' * 16
    for i in range(6):
        plist_data[f'VARIABLE{i}'] = NSData.dataWithBytes_length_(
            variable_bytes, len(variable_bytes)
        )

    plist_data['XVALUE'] = NSNumber.numberWithDouble_(0.0)
    plist_data['YVALUE'] = NSNumber.numberWithDouble_(0.0)

    empty_data = NSMutableData.data()
    plist_data['data'] = empty_data

    archived_data, error = NSKeyedArchiver.archivedDataWithRootObject_requiringSecureCoding_error_(
        plist_data, False, None
    )

    if error:
        raise RuntimeError(f"NSKeyedArchiver error: {error}")

    return bytes(archived_data)


def create_mozaic_file(script_text: str, filename: str = "script", use_pure: bool = None) -> bytes:
    """
    Create a .mozaic file.

    Args:
        script_text: Mozaic script content
        filename: Filename to embed in the plist
        use_pure: True for pure Python, False for native, None for auto-detect

    Returns:
        Binary plist data as bytes
    """
    if use_pure is None:
        use_pure = not FOUNDATION_AVAILABLE

    if use_pure:
        return create_mozaic_file_pure(script_text, filename)
    else:
        if not FOUNDATION_AVAILABLE:
            raise RuntimeError("Native Foundation encoding not available. Use --pure-python flag.")
        return create_mozaic_file_native(script_text, filename)


def main():
    parser = argparse.ArgumentParser(
        description="Convert plain text Mozaic script to .mozaic file",
        epilog="Examples:\n"
               "  python3 mozaic_encoder.py script.txt output.mozaic\n"
               "  python3 mozaic_encoder.py script.txt  # Creates script.mozaic\n"
               "  python3 mozaic_encoder.py --pure-python script.txt output.mozaic  # iPad-compatible\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("input", type=Path, help="Input text file containing Mozaic script")
    parser.add_argument("output", type=Path, nargs='?', help="Output .mozaic file (optional)")
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

    # Check input file exists
    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Determine output filename
    if args.output:
        output_path = args.output
    else:
        # Use input filename with .mozaic extension
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

    # Get filename (without extension) for FILENAME field
    filename = output_path.stem

    # Generate .mozaic file
    encoder_type = "pure Python" if (use_pure if use_pure is not None else not FOUNDATION_AVAILABLE) else "native Foundation"
    print(f"Creating {output_path} using {encoder_type} encoder...")
    print(f"  Script length: {len(script_text)} characters")
    print(f"  Lines: {len(script_text.splitlines())}")

    try:
        mozaic_bytes = create_mozaic_file(script_text, filename, use_pure=use_pure)
    except Exception as e:
        print(f"Error creating .mozaic file: {e}", file=sys.stderr)
        sys.exit(1)

    # Write to file
    try:
        with open(output_path, 'wb') as f:
            f.write(mozaic_bytes)
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"✓ Successfully created {output_path} ({len(mozaic_bytes)} bytes)")


if __name__ == "__main__":
    main()
