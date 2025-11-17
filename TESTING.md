# Testing Guide

## Overview

The chordSequence project includes comprehensive unit tests to ensure code quality and prevent regressions.

## Test Suite

### Test File
- `test_chordSequenceGenerator.py` - 29 unit tests covering all major functionality

### Test Coverage

```
TestParseChordFile (5 tests)
├── Simple song parsing
├── Song with tempo
├── Empty file error handling
├── No bars error handling
└── Invalid tempo error handling

TestGenerateUpdateFunction (3 tests)
├── Single bar generation
├── Multiple bars generation
└── First bar repetition for lookahead

TestGenerateInitializeSongBlock (2 tests)
├── Single song initialization
└── Multiple songs initialization

TestIndexFileOperations (3 tests)
├── Read non-existent index
├── Write and read index
└── Empty index handling

TestResolveSongOrder (5 tests)
├── First run creates index
├── Preserves existing order
├── Adds new songs at end
├── Removes missing songs
└── Reset flag ignores existing index

TestPurePythonEncoder (4 tests)
├── NSKeyedArchiver plist structure
├── String deduplication
├── Number deduplication (critical for iPad compatibility!)
└── NSData wrapping and class metadata

TestGeneratePlistPure (3 tests)
├── Valid plist bytes generation
├── Script text encoding
└── Filename embedding

TestGenerateFullScript (2 tests)
├── Complete script generation
└── Multiple songs in script

TestIntegration (1 test)
└── End-to-end workflow with pure Python encoder
```

## Running Tests

### Quick Test
```bash
python3 test_chordSequenceGenerator.py
```

### With Test Runner
```bash
./run_tests.sh
```

### With Coverage
```bash
pip3 install coverage
coverage run --source=chordSequenceGenerator test_chordSequenceGenerator.py
coverage report -m
coverage html
open htmlcov/index.html  # View detailed coverage report
```

### Expected Output
```
Ran 29 tests in 0.019s

OK
```

## Continuous Integration

### GitHub Actions
Automated tests run on:
- **Every push to main/develop**
- **Every pull request to main**

Test matrix:
- Python 3.8, 3.9, 3.10, 3.11, 3.12
- Ubuntu Latest & macOS Latest
- Pure Python mode (no PyObjC)
- Code linting with flake8

### View Test Results
Once pushed to GitHub, view test results at:
```
https://github.com/YOUR_USERNAME/mozaic-chord-sequence/actions
```

## Writing New Tests

### Test Structure
```python
class TestYourFeature(unittest.TestCase):
    """Test your feature."""

    def setUp(self):
        """Setup before each test."""
        # Create temporary resources
        pass

    def tearDown(self):
        """Cleanup after each test."""
        # Clean up resources
        pass

    def test_specific_behavior(self):
        """Test a specific behavior."""
        # Arrange
        input_data = ...

        # Act
        result = your_function(input_data)

        # Assert
        self.assertEqual(result, expected_value)
```

### Running Specific Tests
```bash
# Run specific test class
python3 -m unittest test_chordSequenceGenerator.TestParseChordFile

# Run specific test method
python3 -m unittest test_chordSequenceGenerator.TestParseChordFile.test_parse_simple_song
```

## Key Test Insights

### Critical Tests for iPad Compatibility

1. **Number Deduplication** (`test_number_deduplication`)
   - Ensures 0.0 values are deduplicated
   - Prevents bloated files that won't load on iPad
   - Reduces object count from 147 to 117

2. **Pure Python Encoder** (`test_end_to_end_pure_python`)
   - Validates complete workflow without Foundation
   - Ensures iPad compatibility

3. **NSData Wrapping** (`test_nsdata_wrapping`)
   - Verifies binary data is properly wrapped
   - Ensures correct class metadata structure

### Edge Cases Covered

- Empty song files
- Songs without tempo
- Invalid tempo formats
- Missing bars
- Index file persistence
- Song order management
- String/number deduplication

## Test Data

Tests use temporary directories and files created with `tempfile.mkdtemp()` to ensure:
- No interference with actual project files
- Automatic cleanup after tests
- Isolation between test runs

## Best Practices

1. **Run tests before committing**
   ```bash
   ./run_tests.sh
   ```

2. **Check coverage regularly**
   ```bash
   coverage run --source=chordSequenceGenerator test_chordSequenceGenerator.py
   coverage report -m
   ```

3. **Add tests for new features**
   - Write test first (TDD)
   - Ensure test fails without implementation
   - Implement feature
   - Verify test passes

4. **Keep tests fast**
   - Current suite runs in ~0.02 seconds
   - Use mocks for slow operations
   - Avoid network/disk I/O when possible

## Troubleshooting

### Tests fail on macOS but pass on Ubuntu
- Check if test relies on Foundation-specific behavior
- Use pure Python mode for cross-platform compatibility

### Coverage tool not found
```bash
pip3 install coverage
```

### Permission denied on run_tests.sh
```bash
chmod +x run_tests.sh
```
