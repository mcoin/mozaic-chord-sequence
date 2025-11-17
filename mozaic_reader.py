#!/usr/bin/env python3
"""
mozaic_reader.py
-----------------
Reads and displays NSKeyedArchiver .mozaic files in human-readable format.

Usage:
    python3 mozaic_reader.py <file.mozaic>
    python3 mozaic_reader.py --code-only <file.mozaic>  # Show only the script
    python3 mozaic_reader.py --full <file.mozaic>       # Show all content (no truncation)
"""

import sys
import argparse
from pathlib import Path
from bpylist2 import archiver
from bpylist2.archive_types import NSMutableData


def format_value(value, truncate=True):
    """Format a value for display."""
    if isinstance(value, NSMutableData):
        data_len = len(value.NSdata)
        # Try to decode as UTF-8 text
        try:
            text = value.NSdata.decode('utf-8')
            if truncate and len(text) > 200:
                return f"NSMutableData({data_len} bytes, text preview):\n{text[:200]}..."
            return f"NSMutableData({data_len} bytes):\n{text}"
        except:
            if truncate:
                return f"NSMutableData({data_len} bytes, binary)"
            else:
                return f"NSMutableData({data_len} bytes, hex):\n{value.NSdata.hex()}"
    elif isinstance(value, bytes):
        if truncate and len(value) > 16:
            return f"bytes({len(value)}): {value[:16].hex()}..."
        return f"bytes: {value.hex()}"
    elif isinstance(value, float):
        return f"{value:.2f}"
    elif isinstance(value, int):
        # Check if it looks like a FourCC code
        if 1000000000 <= value <= 2000000000:
            try:
                import struct
                fourcc = struct.pack('>I', value).decode('ascii', errors='replace')
                return f"{value} (FourCC: '{fourcc}')"
            except:
                pass
        return str(value)
    elif isinstance(value, str):
        if truncate and len(value) > 100:
            return f'"{value[:100]}..."'
        return f'"{value}"'
    return str(value)


def read_mozaic(filepath, code_only=False, full=False):
    """Read and display mozaic file contents."""
    with open(filepath, 'rb') as f:
        data = archiver.unarchive(f.read())

    if code_only:
        # Just show the CODE field
        if 'CODE' in data:
            code = data['CODE']
            if isinstance(code, NSMutableData):
                print(code.NSdata.decode('utf-8'))
            else:
                print(code)
        else:
            print("No CODE field found!")
        return

    if full:
        # Show all fields without truncation
        print(f"{'='*70}")
        print(f"Mozaic File: {filepath.name} (FULL DUMP)")
        print(f"{'='*70}\n")

        for key in sorted(data.keys()):
            print(f"{key}:")
            print(f"  {format_value(data[key], truncate=False)}")
            print()

        print(f"{'='*70}")
        print(f"Total fields: {len(data.keys())}")
        print(f"{'='*70}")
        return

    # Show all fields in organized groups
    print(f"{'='*70}")
    print(f"Mozaic File: {filepath.name}")
    print(f"{'='*70}\n")

    # Metadata
    print("=== METADATA ===")
    for key in ['FILENAME', 'manufacturer', 'subtype', 'type', 'version']:
        if key in data:
            print(f"  {key:20} = {format_value(data[key])}")

    # UI Configuration
    print("\n=== UI CONFIGURATION ===")
    for key in ['KNOBTITLE', 'PADTITLE', 'XYTITLE', 'SCALE']:
        if key in data:
            print(f"  {key:20} = {format_value(data[key])}")

    # XY Pad
    print("\n=== XY PAD ===")
    for key in ['XVALUE', 'YVALUE']:
        if key in data:
            print(f"  {key:20} = {format_value(data[key])}")

    # Knobs (only show non-default values)
    print("\n=== KNOBS (non-zero values) ===")
    for i in range(22):
        key = f'KNOBVALUE{i}'
        if key in data and data[key] != 0.0:
            label_key = f'KNOBLABEL{i}'
            label = data.get(label_key, '')
            print(f"  Knob {i:2} = {data[key]:7.2f}  (label: {label})")

    # Pad Labels (only show non-empty)
    print("\n=== PAD LABELS (non-empty) ===")
    for i in range(16):
        key = f'PADLABEL{i}'
        if key in data and data[key]:
            print(f"  Pad {i:2} = {data[key]}")

    # Audio Unit Values
    print("\n=== AUDIO UNIT VALUES ===")
    for i in range(8):
        key = f'AUVALUE{i}'
        if key in data:
            print(f"  {key:20} = {format_value(data[key])}")

    # Variables
    print("\n=== VARIABLES ===")
    for i in range(15):
        key = f'VARIABLE{i}'
        if key in data:
            value = data[key]
            # Only show if not all zeros
            if isinstance(value, bytes) and value != b'\x00' * len(value):
                print(f"  {key:20} = {format_value(value)}")

    # CODE
    print("\n=== CODE ===")
    if 'CODE' in data:
        code = data['CODE']
        if isinstance(code, NSMutableData):
            code_text = code.NSdata.decode('utf-8')
            lines = code_text.split('\n')
            print(f"  Script length: {len(code_text)} characters, {len(lines)} lines")
            print(f"  First 10 lines:")
            for line in lines[:10]:
                print(f"    {line}")
            print(f"  ... (use --code-only to see full script)")

    # Data field
    print("\n=== RUNTIME DATA ===")
    if 'data' in data:
        data_field = data['data']
        if isinstance(data_field, NSMutableData):
            print(f"  data field: {len(data_field.NSdata)} bytes")

    # GUI bytes
    print("\n=== GUI CONFIGURATION ===")
    if 'GUI' in data:
        gui = data['GUI']
        if isinstance(gui, bytes):
            print(f"  GUI bytes: {gui.hex()}")
            print(f"  (40 bytes, value at byte 36 indicates layout)")

    print(f"\n{'='*70}")
    print(f"Total fields: {len(data.keys())}")
    print(f"{'='*70}")


def main():
    parser = argparse.ArgumentParser(description="Read and display Mozaic .mozaic files")
    parser.add_argument("file", type=Path, help="Path to .mozaic file")
    parser.add_argument("--code-only", action="store_true",
                       help="Show only the CODE script content")
    parser.add_argument("--full", action="store_true",
                       help="Show all fields with full content (no truncation)")
    args = parser.parse_args()

    if not args.file.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    read_mozaic(args.file, code_only=args.code_only, full=args.full)


if __name__ == "__main__":
    main()
