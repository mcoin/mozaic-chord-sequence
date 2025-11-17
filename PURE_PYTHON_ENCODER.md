# Pure Python Mozaic Encoder

## Overview

Successfully implemented a pure Python NSKeyedArchiver encoder that works on iPad and any Python platform without requiring macOS Foundation framework.

## What Was Fixed

The key issue was **number deduplication**. The initial pure Python implementation wasn't deduplicating numeric values (especially the many 0.0 values used in knobs), resulting in:
- Too many objects in the $objects array (147 vs 117)
- Larger file sizes
- Files that wouldn't load in Mozaic app

### Solution

Added number deduplication with a `number_map` dictionary, matching the native NSKeyedArchiver behavior:

```python
def add_number(n):
    """Add number (int or float) with deduplication."""
    if n in number_map:
        return UID(number_map[n])
    idx = len(objects)
    objects.append(n)
    number_map[n] = idx
    return UID(idx)
```

## Updated Tools

All three encoding tools now support pure Python encoding:

### 1. mozaic_pure_encoder.py
Standalone pure Python encoder (no Foundation dependency).

```bash
# Works on iPad!
python3 mozaic_pure_encoder.py script.txt output.mozaic
```

### 2. mozaic_encoder.py  
General-purpose encoder with auto-detection.

```bash
# Auto-detects which encoder to use
python3 mozaic_encoder.py script.txt output.mozaic

# Force pure Python (iPad-compatible)
python3 mozaic_encoder.py --pure-python script.txt output.mozaic

# Force native (macOS only)
python3 mozaic_encoder.py --native script.txt output.mozaic
```

### 3. chordSequenceGenerator.py
Multi-song chord sequence generator.

```bash
# Auto-detects encoder
python3 chordSequenceGenerator.py --songs songs/*.txt --plist --output chordSequence.mozaic

# Force pure Python
python3 chordSequenceGenerator.py --songs songs/*.txt --plist --pure-python --output chordSequence.mozaic

# Force native
python3 chordSequenceGenerator.py --songs songs/*.txt --plist --native --output chordSequence.mozaic
```

## Testing Results

✅ **simple_test.mozaic** - Loaded successfully on iPad  
✅ **chordSequence10_pure_v2.mozaic** - Loaded successfully on iPad  
✅ **test_gen_pure.mozaic** - Generated successfully with all songs  

## File Size Comparison

Pure Python encoder now produces files nearly identical in size to native encoder:

| File | Native | Pure Python |
|------|--------|-------------|
| simple_test.mozaic | 2914 bytes | 2867 bytes |
| chordSequence10.mozaic | 9751 bytes | 9708 bytes |

## Technical Details

### NSKeyedArchiver Structure

The encoder creates the following object graph:

```
- Object 0: "$null"
- Object 1: root NSDictionary with NS.keys and NS.objects arrays
- Objects 2-N: data values (strings, numbers, NSData wrappers)
- Object N+1: NSMutableData class metadata
- Object N+2: NSMutableDictionary class metadata
```

### Key Features

1. **String deduplication**: Identical strings share the same UID
2. **Number deduplication**: Identical numbers share the same UID (critical fix!)
3. **NSData wrapping**: Binary data wrapped in NSMutableData objects
4. **Class metadata**: Proper $class references with $classes and $classname
5. **Binary plist**: Uses plistlib.FMT_BINARY for output

## Dependencies

- **Pure Python mode**: Only requires standard library (`plistlib`)
- **Native mode**: Requires PyObjC/Foundation (macOS only)

## Usage on iPad

All scripts with `--pure-python` flag or `mozaic_pure_encoder.py` can run directly on iPad using:
- Pythonista
- Pyto
- a-Shell
- Or any Python 3.7+ environment

No macOS-specific dependencies required!
