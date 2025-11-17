#!/usr/bin/env python3
"""
Unit tests for chordSequenceGenerator.py
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Import the module to test
import chordSequenceGenerator as csg


class TestParseChordFile(unittest.TestCase):
    """Test parse_chord_file function."""

    def setUp(self):
        """Create temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_parse_simple_song(self):
        """Test parsing a simple song file without tempo."""
        song_file = Path(self.test_dir) / "simple.txt"
        song_file.write_text("Test Song\nC G Am F\nF C G C\n")

        title, tempo, bars = csg.parse_chord_file(song_file)

        self.assertEqual(title, "Test Song")
        self.assertIsNone(tempo)
        self.assertEqual(bars, [['C', 'G', 'Am', 'F'], ['F', 'C', 'G', 'C']])

    def test_parse_song_with_tempo(self):
        """Test parsing a song file with tempo."""
        song_file = Path(self.test_dir) / "with_tempo.txt"
        song_file.write_text("Blues Song\ntempo=120\nC7 F7 C7 C7\nF7 F7 C7 C7\n")

        title, tempo, bars = csg.parse_chord_file(song_file)

        self.assertEqual(title, "Blues Song")
        self.assertEqual(tempo, 120)
        self.assertEqual(len(bars), 2)
        self.assertEqual(bars[0], ['C7', 'F7', 'C7', 'C7'])

    def test_parse_empty_file_raises_error(self):
        """Test that empty file raises ValueError."""
        song_file = Path(self.test_dir) / "empty.txt"
        song_file.write_text("")

        with self.assertRaises(ValueError) as context:
            csg.parse_chord_file(song_file)
        self.assertIn("Empty", str(context.exception))

    def test_parse_no_bars_raises_error(self):
        """Test that file with only title raises ValueError."""
        song_file = Path(self.test_dir) / "no_bars.txt"
        song_file.write_text("Just Title\n")

        with self.assertRaises(ValueError) as context:
            csg.parse_chord_file(song_file)
        self.assertIn("No bars", str(context.exception))

    def test_parse_invalid_tempo(self):
        """Test that invalid tempo format raises ValueError."""
        song_file = Path(self.test_dir) / "bad_tempo.txt"
        song_file.write_text("Song\ntempo=abc\nC G\n")

        with self.assertRaises(ValueError) as context:
            csg.parse_chord_file(song_file)
        self.assertIn("tempo", str(context.exception).lower())


class TestGenerateUpdateFunction(unittest.TestCase):
    """Test generate_update_function."""

    def test_generate_single_bar(self):
        """Test generating update function for single bar."""
        bars = [['C', 'G', 'Am', 'F']]
        block_text, nb_bars = csg.generate_update_function(0, bars)

        self.assertEqual(nb_bars, 1)
        self.assertIn("@UpdateChordsSong0", block_text)
        self.assertIn("@End", block_text)
        self.assertIn("LabelPad 0 - bar*8, {C}", block_text)
        self.assertIn("LabelPad 2 - bar*8, {G}", block_text)
        self.assertIn("LabelPad 4 - bar*8, {Am}", block_text)
        self.assertIn("LabelPad 6 - bar*8, {F}", block_text)

    def test_generate_multiple_bars(self):
        """Test generating update function for multiple bars."""
        bars = [['C', 'G'], ['F', 'C']]
        block_text, nb_bars = csg.generate_update_function(1, bars)

        self.assertEqual(nb_bars, 2)
        self.assertIn("@UpdateChordsSong1", block_text)
        self.assertIn("LabelPad 0 - bar*8, {C}", block_text)
        self.assertIn("LabelPad 8 - bar*8, {F}", block_text)

    def test_generate_with_repeating_first_bar(self):
        """Test that first bar is repeated at end for lookahead."""
        bars = [['C'], ['G']]
        block_text, nb_bars = csg.generate_update_function(0, bars)

        # Should have 3 chord labels: C at 0, G at 8, C at 16
        self.assertEqual(block_text.count("LabelPad"), 3)


class TestGenerateInitializeSongBlock(unittest.TestCase):
    """Test generate_initialize_song_block."""

    def test_generate_single_song(self):
        """Test generating initialization block for single song."""
        songs = [("Test Song", 4)]
        block = csg.generate_initialize_song_block(songs)

        self.assertIn("@InitializeSong", block)
        self.assertIn("if SongNb = 0", block)
        self.assertIn("LabelPads {Test Song}", block)
        self.assertIn("NbOfBars = 4", block)
        self.assertIn("@End", block)

    def test_generate_multiple_songs(self):
        """Test generating initialization block for multiple songs."""
        songs = [("Song One", 4), ("Song Two", 8), ("Song Three", 12)]
        block = csg.generate_initialize_song_block(songs)

        self.assertIn("if SongNb = 0", block)
        self.assertIn("elseif SongNb = 1", block)
        self.assertIn("elseif SongNb = 2", block)
        self.assertIn("LabelPads {Song One}", block)
        self.assertIn("LabelPads {Song Two}", block)
        self.assertIn("LabelPads {Song Three}", block)
        self.assertIn("else", block)
        self.assertIn("LabelPads {Unassigned}", block)


class TestIndexFileOperations(unittest.TestCase):
    """Test index file read/write operations."""

    def setUp(self):
        """Create temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_read_nonexistent_index_returns_empty(self):
        """Test reading non-existent index file returns empty list."""
        index_path = Path(self.test_dir) / "nonexistent.index"
        result = csg.read_index_file(index_path)
        self.assertEqual(result, [])

    def test_write_and_read_index(self):
        """Test writing and reading index file."""
        index_path = Path(self.test_dir) / "test.index"
        filenames = ["song1.txt", "song2.txt", "song3.txt"]

        csg.write_index_file(index_path, filenames)
        result = csg.read_index_file(index_path)

        self.assertEqual(result, filenames)

    def test_write_index_with_empty_list(self):
        """Test writing empty index file."""
        index_path = Path(self.test_dir) / "empty.index"
        csg.write_index_file(index_path, [])

        result = csg.read_index_file(index_path)
        self.assertEqual(result, [])


class TestResolveSongOrder(unittest.TestCase):
    """Test resolve_song_order function."""

    def setUp(self):
        """Create temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()
        self.index_path = Path(self.test_dir) / ".test.index"

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_first_run_creates_index(self):
        """Test that first run creates index with all songs."""
        cli_files = [
            Path(self.test_dir) / "song1.txt",
            Path(self.test_dir) / "song2.txt",
            Path(self.test_dir) / "song3.txt"
        ]

        result = csg.resolve_song_order(self.index_path, cli_files)

        self.assertEqual(result, ["song1.txt", "song2.txt", "song3.txt"])
        self.assertTrue(self.index_path.exists())

    def test_preserves_existing_order(self):
        """Test that existing order is preserved."""
        # Write initial index
        csg.write_index_file(self.index_path, ["song2.txt", "song1.txt", "song3.txt"])

        cli_files = [
            Path(self.test_dir) / "song1.txt",
            Path(self.test_dir) / "song2.txt",
            Path(self.test_dir) / "song3.txt"
        ]

        result = csg.resolve_song_order(self.index_path, cli_files)

        # Should preserve the order from index
        self.assertEqual(result, ["song2.txt", "song1.txt", "song3.txt"])

    def test_adds_new_songs_at_end(self):
        """Test that new songs are added at the end."""
        csg.write_index_file(self.index_path, ["song1.txt", "song2.txt"])

        cli_files = [
            Path(self.test_dir) / "song1.txt",
            Path(self.test_dir) / "song2.txt",
            Path(self.test_dir) / "song3.txt",
            Path(self.test_dir) / "song4.txt"
        ]

        result = csg.resolve_song_order(self.index_path, cli_files)

        self.assertEqual(result, ["song1.txt", "song2.txt", "song3.txt", "song4.txt"])

    def test_removes_missing_songs(self):
        """Test that missing songs are removed from index."""
        csg.write_index_file(self.index_path, ["song1.txt", "song2.txt", "song3.txt", "song4.txt"])

        cli_files = [
            Path(self.test_dir) / "song1.txt",
            Path(self.test_dir) / "song3.txt"
        ]

        result = csg.resolve_song_order(self.index_path, cli_files)

        # song2.txt and song4.txt should be removed
        self.assertEqual(result, ["song1.txt", "song3.txt"])

    def test_reset_ignores_existing_index(self):
        """Test that reset flag ignores existing index."""
        csg.write_index_file(self.index_path, ["song3.txt", "song1.txt", "song2.txt"])

        cli_files = [
            Path(self.test_dir) / "song1.txt",
            Path(self.test_dir) / "song2.txt",
            Path(self.test_dir) / "song3.txt"
        ]

        result = csg.resolve_song_order(self.index_path, cli_files, reset=True)

        # Should use CLI order, not index order
        self.assertEqual(result, ["song1.txt", "song2.txt", "song3.txt"])


class TestPurePythonEncoder(unittest.TestCase):
    """Test pure Python NSKeyedArchiver encoder."""

    def test_create_nskeyedarchiver_plist_structure(self):
        """Test that plist has correct structure."""
        data_dict = {
            'test_string': 'hello',
            'test_int': 42,
            'test_float': 3.14,
            'test_bytes': b'binary'
        }

        plist = csg.create_nskeyedarchiver_plist_pure(data_dict)

        # Check top-level structure
        self.assertIn('$version', plist)
        self.assertIn('$archiver', plist)
        self.assertIn('$top', plist)
        self.assertIn('$objects', plist)

        self.assertEqual(plist['$version'], 100000)
        self.assertEqual(plist['$archiver'], 'NSKeyedArchiver')

        # Check objects array
        objects = plist['$objects']
        self.assertEqual(objects[0], '$null')
        self.assertIsNotNone(objects[1])  # Root dict

        # Check root dict structure
        root = objects[1]
        self.assertIn('NS.keys', root)
        self.assertIn('NS.objects', root)
        self.assertIn('$class', root)

    def test_string_deduplication(self):
        """Test that identical strings are deduplicated."""
        data_dict = {
            'key1': 'hello',
            'key2': 'hello',
            'key3': 'world'
        }

        plist = csg.create_nskeyedarchiver_plist_pure(data_dict)
        objects = plist['$objects']

        # Count occurrences of 'hello' in objects
        hello_count = sum(1 for obj in objects if obj == 'hello')
        self.assertEqual(hello_count, 1, "String 'hello' should appear only once")

    def test_number_deduplication(self):
        """Test that identical numbers are deduplicated."""
        data_dict = {
            'val1': 0.0,
            'val2': 0.0,
            'val3': 0.0,
            'val4': 1.0
        }

        plist = csg.create_nskeyedarchiver_plist_pure(data_dict)
        objects = plist['$objects']

        # Count occurrences of 0.0 in objects
        zero_count = sum(1 for obj in objects if obj == 0.0)
        self.assertEqual(zero_count, 1, "Number 0.0 should appear only once")

    def test_nsdata_wrapping(self):
        """Test that bytes are wrapped in NSData objects."""
        data_dict = {'test_data': b'binary data'}

        plist = csg.create_nskeyedarchiver_plist_pure(data_dict)
        objects = plist['$objects']

        # Find NSData wrapper object
        nsdata_objects = [obj for obj in objects if isinstance(obj, dict) and 'NS.data' in obj]
        self.assertGreater(len(nsdata_objects), 0, "Should have NSData wrapper objects")

        # Check NSData object has correct structure
        nsdata_obj = nsdata_objects[0]
        self.assertIn('$class', nsdata_obj)
        self.assertIn('NS.data', nsdata_obj)
        self.assertEqual(nsdata_obj['NS.data'], b'binary data')

    def test_class_metadata_present(self):
        """Test that class metadata objects are present."""
        data_dict = {
            'string_val': 'test',
            'bytes_val': b'data'
        }

        plist = csg.create_nskeyedarchiver_plist_pure(data_dict)
        objects = plist['$objects']

        # Find class metadata objects
        class_objects = [obj for obj in objects
                        if isinstance(obj, dict) and '$classes' in obj]

        self.assertEqual(len(class_objects), 2, "Should have 2 class metadata objects")

        # Check for NSMutableData class
        nsdata_class = [obj for obj in class_objects
                       if 'NSMutableData' in obj.get('$classes', [])]
        self.assertEqual(len(nsdata_class), 1)

        # Check for NSMutableDictionary class
        nsdict_class = [obj for obj in class_objects
                       if 'NSMutableDictionary' in obj.get('$classes', [])]
        self.assertEqual(len(nsdict_class), 1)


class TestGeneratePlistPure(unittest.TestCase):
    """Test generate_plist_pure function."""

    def test_generates_valid_plist_bytes(self):
        """Test that function returns bytes."""
        script_text = "@OnLoad\n  Log {Test}\n@End"
        result = csg.generate_plist_pure(script_text, "test")

        self.assertIsInstance(result, bytes)
        self.assertGreater(len(result), 0)

    def test_script_text_is_encoded(self):
        """Test that script text is properly encoded in output."""
        script_text = "@OnLoad\n  Log {Test Script}\n@End"
        result = csg.generate_plist_pure(script_text, "test")

        # The script text should be somewhere in the binary plist
        self.assertIn(b'@OnLoad', result)
        self.assertIn(b'Log {Test Script}', result)

    def test_filename_is_embedded(self):
        """Test that filename is embedded in plist."""
        script_text = "@OnLoad\n@End"
        filename = "my_test_script"
        result = csg.generate_plist_pure(script_text, filename)

        self.assertIn(filename.encode('utf-8'), result)


class TestGenerateFullScript(unittest.TestCase):
    """Test generate_full_script function."""

    def test_generates_complete_script(self):
        """Test that full script is generated with all required sections."""
        songs_data = [
            {
                'title': 'Test Song',
                'tempo': 120,
                'nb_bars': 4,
                'update_block': '@UpdateChordsSong0\n  LabelPad 0 - bar*8, {C}\n@End'
            }
        ]

        script = csg.generate_full_script(songs_data)

        # Check for required sections
        self.assertIn('@OnLoad', script)
        self.assertIn('@OnKnobChange', script)
        self.assertIn('@OnPadDown', script)
        self.assertIn('@OnNewBar', script)
        self.assertIn('@OnNewBeat', script)
        self.assertIn('@InitializeSong', script)
        self.assertIn('@UpdateChordsSong0', script)
        self.assertIn('@SetSongRhythm', script)
        self.assertIn('NewTempo = 120', script)

    def test_multiple_songs_in_script(self):
        """Test script generation with multiple songs."""
        songs_data = [
            {
                'title': 'Song 1',
                'tempo': None,
                'nb_bars': 4,
                'update_block': '@UpdateChordsSong0\n@End'
            },
            {
                'title': 'Song 2',
                'tempo': 140,
                'nb_bars': 8,
                'update_block': '@UpdateChordsSong1\n@End'
            }
        ]

        script = csg.generate_full_script(songs_data)

        self.assertIn('if SongNb = 0', script)
        self.assertIn('elseif SongNb = 1', script)
        self.assertIn('LabelPads {Song 1}', script)
        self.assertIn('LabelPads {Song 2}', script)
        self.assertIn('@UpdateChordsSong0', script)
        self.assertIn('@UpdateChordsSong1', script)
        self.assertIn('NewTempo = 140', script)


class TestIntegration(unittest.TestCase):
    """Integration tests for end-to-end functionality."""

    def setUp(self):
        """Create temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_end_to_end_pure_python(self):
        """Test complete workflow with pure Python encoder."""
        # Create test song files
        song1 = Path(self.test_dir) / "song1.txt"
        song1.write_text("Test Song 1\ntempo=120\nC G Am F\nF C G C\n")

        song2 = Path(self.test_dir) / "song2.txt"
        song2.write_text("Test Song 2\nC7 F7 C7 C7\n")

        # Parse songs
        title1, tempo1, bars1 = csg.parse_chord_file(song1)
        title2, tempo2, bars2 = csg.parse_chord_file(song2)

        # Generate update functions
        update1, nb_bars1 = csg.generate_update_function(0, bars1)
        update2, nb_bars2 = csg.generate_update_function(1, bars2)

        # Create songs data
        songs_data = [
            {'title': title1, 'tempo': tempo1, 'nb_bars': nb_bars1, 'update_block': update1},
            {'title': title2, 'tempo': tempo2, 'nb_bars': nb_bars2, 'update_block': update2}
        ]

        # Generate full script
        script = csg.generate_full_script(songs_data)

        # Generate plist
        plist_bytes = csg.generate_plist_pure(script, "test_output")

        # Verify output
        self.assertIsInstance(plist_bytes, bytes)
        self.assertGreater(len(plist_bytes), 1000)  # Should be reasonable size
        self.assertIn(b'Test Song 1', plist_bytes)
        self.assertIn(b'Test Song 2', plist_bytes)


def run_tests():
    """Run all tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestParseChordFile))
    suite.addTests(loader.loadTestsFromTestCase(TestGenerateUpdateFunction))
    suite.addTests(loader.loadTestsFromTestCase(TestGenerateInitializeSongBlock))
    suite.addTests(loader.loadTestsFromTestCase(TestIndexFileOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestResolveSongOrder))
    suite.addTests(loader.loadTestsFromTestCase(TestPurePythonEncoder))
    suite.addTests(loader.loadTestsFromTestCase(TestGeneratePlistPure))
    suite.addTests(loader.loadTestsFromTestCase(TestGenerateFullScript))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
