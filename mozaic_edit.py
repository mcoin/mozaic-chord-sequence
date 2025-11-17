#!/usr/bin/env python3
"""
mozaic_edit.py
--------------
Edit Mozaic scripts by binary replacement (NO decode/encode).
This preserves the exact binary format that Mozaic expects.

Usage:
    # Extract script for editing
    python3 mozaic_edit.py extract input.mozaic script.txt

    # Replace script (MUST be same byte length!)
    python3 mozaic_edit.py replace input.mozaic script.txt output.mozaic
"""

import sys
import argparse
from pathlib import Path


def extract_script(mozaic_path: Path, output_path: Path):
    """Extract script from .mozaic file."""
    with open(mozaic_path, 'rb') as f:
        data = f.read()

    # Find script boundaries
    start_marker = b'@OnLoad'
    start = data.find(start_marker)
    if start == -1:
        print("Error: Cannot find @OnLoad in file", file=sys.stderr)
        sys.exit(1)

    # Find last @End
    end_marker = b'@End\n'
    end = data.rfind(end_marker)
    if end == -1:
        end_marker = b'@End'  # Try without newline
        end = data.rfind(end_marker)

    if end == -1:
        print("Error: Cannot find @End in file", file=sys.stderr)
        sys.exit(1)

    # Extract script
    script_bytes = data[start:end + len(end_marker)]
    script = script_bytes.decode('utf-8')

    # Save
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(script)

    print(f"✓ Extracted script to {output_path}")
    print(f"  Length: {len(script)} characters ({len(script_bytes)} bytes)")


def replace_script(template_path: Path, script_path: Path, output_path: Path):
    """Replace script in .mozaic file."""
    # Read template
    with open(template_path, 'rb') as f:
        data = f.read()

    # Read new script
    with open(script_path, 'r', encoding='utf-8') as f:
        new_script = f.read()

    # Find old script
    start_marker = b'@OnLoad'
    start = data.find(start_marker)
    if start == -1:
        print("Error: Cannot find @OnLoad in template", file=sys.stderr)
        sys.exit(1)

    end_marker = b'@End\n'
    end = data.rfind(end_marker)
    if end == -1:
        end_marker = b'@End'
        end = data.rfind(end_marker)

    if end == -1:
        print("Error: Cannot find @End in template", file=sys.stderr)
        sys.exit(1)

    old_script_bytes = data[start:end + len(end_marker)]
    old_script = old_script_bytes.decode('utf-8')
    new_script_bytes = new_script.encode('utf-8')

    print(f"Old script: {len(old_script_bytes)} bytes")
    print(f"New script: {len(new_script_bytes)} bytes")

    if len(old_script_bytes) != len(new_script_bytes):
        diff = len(new_script_bytes) - len(old_script_bytes)
        print(f"\n⚠ WARNING: Length mismatch ({diff:+d} bytes)")
        print("  The file WILL be corrupted!")
        print("\nTo fix: pad your script with comments to match the exact length:")
        print(f"  Target length: {len(old_script_bytes)} bytes")
        print(f"  Current length: {len(new_script_bytes)} bytes")
        if diff > 0:
            print(f"  Remove {diff} bytes (characters)")
        else:
            print(f"  Add {-diff} bytes, e.g.:")
            print(f"    // {' ' * ((-diff) - 4)}")

        response = input("\nContinue anyway? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted")
            sys.exit(1)

    # Replace
    new_data = data[:start] + new_script_bytes + data[end + len(end_marker):]

    # Save
    with open(output_path, 'wb') as f:
        f.write(new_data)

    print(f"\n✓ Created {output_path}")
    print(f"  Size: {len(data)} → {len(new_data)} bytes ({len(new_data) - len(data):+d})")

    if len(data) == len(new_data):
        print("  ✓ Size preserved - should work in Mozaic!")
    else:
        print("  ⚠ Size changed - file may be corrupted!")


def main():
    parser = argparse.ArgumentParser(description="Edit Mozaic scripts without decode/encode")
    subparsers = parser.add_subparsers(dest='command', help='Command')

    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract script from .mozaic file')
    extract_parser.add_argument('input', type=Path, help='Input .mozaic file')
    extract_parser.add_argument('output', type=Path, help='Output script .txt file')

    # Replace command
    replace_parser = subparsers.add_parser('replace', help='Replace script in .mozaic file')
    replace_parser.add_argument('template', type=Path, help='Template .mozaic file')
    replace_parser.add_argument('script', type=Path, help='New script .txt file')
    replace_parser.add_argument('output', type=Path, help='Output .mozaic file')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'extract':
        if not args.input.exists():
            print(f"Error: File not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        extract_script(args.input, args.output)

    elif args.command == 'replace':
        if not args.template.exists():
            print(f"Error: Template not found: {args.template}", file=sys.stderr)
            sys.exit(1)
        if not args.script.exists():
            print(f"Error: Script not found: {args.script}", file=sys.stderr)
            sys.exit(1)
        replace_script(args.template, args.script, args.output)


if __name__ == "__main__":
    main()
