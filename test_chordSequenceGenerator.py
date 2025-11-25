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


class TestFillTriggers(unittest.TestCase):
    """Test fill trigger parsing and generation."""

    def setUp(self):
        """Create temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_parse_song_with_fill_markers(self):
        """Test parsing song file with fill markers."""
        song_file = Path(self.test_dir) / "fills.txt"
        song_file.write_text("Fill Test\nC G * Am F\nF * C G * C\n")

        title, tempo, bars = csg.parse_chord_file(song_file)

        self.assertEqual(title, "Fill Test")
        self.assertEqual(len(bars), 2)
        # First bar: C, G (with fill), Am, F
        self.assertEqual(bars[0], ['C', 'G', 'Am', 'F'])
        # Second bar: F (with fill), C, G (with fill), C
        self.assertEqual(bars[1], ['F', 'C', 'G', 'C'])

    def test_parse_song_with_fill_at_end_of_bar(self):
        """Test parsing fill marker at end of bar."""
        song_file = Path(self.test_dir) / "fills_end.txt"
        song_file.write_text("Test\nC G Am * F\n")

        title, tempo, bars = csg.parse_chord_file(song_file)

        self.assertEqual(bars[0], ['C', 'G', 'Am', 'F'])

    def test_parse_song_without_fills(self):
        """Test parsing song without fill markers."""
        song_file = Path(self.test_dir) / "no_fills.txt"
        song_file.write_text("No Fills\nC G Am F\n")

        title, tempo, bars = csg.parse_chord_file(song_file)

        self.assertEqual(bars[0], ['C', 'G', 'Am', 'F'])

    def test_generate_update_block_with_fills(self):
        """Test that generate_update_block returns fill positions."""
        from src.models import Song, Bar

        # Create song with fills
        song = Song(
            title="Test",
            bars=[
                Bar(chords=['C', 'G', 'Am', 'F'], fills=[False, True, False, False]),
                Bar(chords=['F', 'C', 'G', 'C'], fills=[True, False, True, False])
            ]
        )

        from src.generator import generate_update_block
        block_text, fill_positions = generate_update_block(song, 0)

        # Check that function returns tuple
        self.assertIsInstance(block_text, str)
        self.assertIsInstance(fill_positions, list)

        # Check fill positions
        # Bar 0, chord 1 (G): position = 0*8 + 1*(8/4) = 2
        # Bar 1, chord 0 (F): position = 1*8 + 0*(8/4) = 8
        # Bar 1, chord 2 (G): position = 1*8 + 2*(8/4) = 12
        expected_positions = [2.0, 8.0, 12.0]
        self.assertEqual(fill_positions, expected_positions)

    def test_generate_update_block_without_fills(self):
        """Test generate_update_block with no fills returns empty list."""
        from src.models import Song, Bar

        song = Song(
            title="Test",
            bars=[Bar(chords=['C', 'G', 'Am', 'F'])]
        )

        from src.generator import generate_update_block
        block_text, fill_positions = generate_update_block(song, 0)

        self.assertEqual(fill_positions, [])


class TestPydanticModels(unittest.TestCase):
    """Test Pydantic domain models."""

    def setUp(self):
        """Create temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_bar_model_creates_fills_list(self):
        """Test that Bar model auto-creates fills list."""
        from src.models import Bar

        bar = Bar(chords=['C', 'G', 'Am', 'F'])

        self.assertEqual(len(bar.fills), 4)
        self.assertEqual(bar.fills, [False, False, False, False])

    def test_bar_model_with_explicit_fills(self):
        """Test Bar model with explicit fills."""
        from src.models import Bar

        bar = Bar(chords=['C', 'G', 'Am'], fills=[False, True, False])

        self.assertEqual(bar.chords, ['C', 'G', 'Am'])
        self.assertEqual(bar.fills, [False, True, False])

    def test_bar_has_fills_method(self):
        """Test Bar.has_fills() method."""
        from src.models import Bar

        bar_no_fills = Bar(chords=['C', 'G'])
        bar_with_fills = Bar(chords=['C', 'G'], fills=[False, True])

        self.assertFalse(bar_no_fills.has_fills())
        self.assertTrue(bar_with_fills.has_fills())

    def test_song_from_file(self):
        """Test Song.from_file() classmethod."""
        from src.models import Song

        song_file = Path(self.test_dir) / "test.txt"
        song_file.write_text("My Song\ntempo=120\nC G Am F\nF C G C\n")

        song = Song.from_file(song_file)

        self.assertEqual(song.title, "My Song")
        self.assertEqual(song.tempo, 120)
        self.assertEqual(len(song.bars), 2)
        self.assertEqual(song.bars[0].chords, ['C', 'G', 'Am', 'F'])
        self.assertEqual(song.source_file, song_file)

    def test_song_from_file_with_fills(self):
        """Test Song.from_file() parses fill markers."""
        from src.models import Song

        song_file = Path(self.test_dir) / "fills.txt"
        song_file.write_text("Fill Song\nC G * Am F\n")

        song = Song.from_file(song_file)

        self.assertEqual(song.bars[0].chords, ['C', 'G', 'Am', 'F'])
        self.assertEqual(song.bars[0].fills, [False, True, False, False])

    def test_song_num_bars_property(self):
        """Test Song.num_bars computed property."""
        from src.models import Song, Bar

        song = Song(
            title="Test",
            bars=[
                Bar(chords=['C', 'G']),
                Bar(chords=['Am', 'F']),
                Bar(chords=['C', 'G'])
            ]
        )

        self.assertEqual(song.num_bars, 3)

    def test_song_collection_iteration(self):
        """Test SongCollection iteration."""
        from src.models import Song, Bar, SongCollection

        songs = SongCollection(songs=[
            Song(title="Song 1", bars=[Bar(chords=['C', 'G'])]),
            Song(title="Song 2", bars=[Bar(chords=['Am', 'F'])])
        ])

        titles = [song.title for song in songs]
        self.assertEqual(titles, ["Song 1", "Song 2"])

    def test_song_collection_len(self):
        """Test SongCollection length."""
        from src.models import Song, Bar, SongCollection

        songs = SongCollection(songs=[
            Song(title="Song 1", bars=[Bar(chords=['C'])]),
            Song(title="Song 2", bars=[Bar(chords=['G'])])
        ])

        self.assertEqual(len(songs), 2)

    def test_song_validates_tempo_range(self):
        """Test Song model validates tempo range."""
        from src.models import Song, Bar
        from pydantic import ValidationError

        # Valid tempo
        song = Song(title="Test", tempo=120, bars=[Bar(chords=['C'])])
        self.assertEqual(song.tempo, 120)

        # Tempo too low should raise error
        with self.assertRaises(ValidationError):
            Song(title="Test", tempo=10, bars=[Bar(chords=['C'])])

        # Tempo too high should raise error
        with self.assertRaises(ValidationError):
            Song(title="Test", tempo=500, bars=[Bar(chords=['C'])])

    def test_bar_requires_non_empty_chords(self):
        """Test Bar model requires non-empty chord list."""
        from src.models import Bar
        from pydantic import ValidationError

        # Valid bar
        bar = Bar(chords=['C', 'G'])
        self.assertEqual(len(bar.chords), 2)

        # Empty chord list should raise error
        with self.assertRaises(ValidationError):
            Bar(chords=[])


class TestRhythmSelection(unittest.TestCase):
    """Test rhythm selection feature."""

    def setUp(self):
        """Create temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_parse_song_with_rhythm(self):
        """Test parsing song file with rhythm line."""
        song_file = Path(self.test_dir) / "rhythm_test.txt"
        song_file.write_text("Rhythm Song\ntempo=120\nrhythm 1 2\nC G Am F\n")

        title, tempo, bars = csg.parse_chord_file(song_file)

        self.assertEqual(title, "Rhythm Song")
        self.assertEqual(tempo, 120)
        self.assertEqual(bars[0], ['C', 'G', 'Am', 'F'])

    def test_parse_song_with_rhythm_no_tempo(self):
        """Test parsing song with rhythm but no tempo."""
        song_file = Path(self.test_dir) / "rhythm_no_tempo.txt"
        song_file.write_text("Rhythm Song\nrhythm 3 5\nC G Am F\n")

        title, tempo, bars = csg.parse_chord_file(song_file)

        self.assertEqual(title, "Rhythm Song")
        self.assertIsNone(tempo)
        self.assertEqual(bars[0], ['C', 'G', 'Am', 'F'])

    def test_song_from_file_with_rhythm(self):
        """Test Song.from_file() parses rhythm correctly."""
        from src.models import Song

        song_file = Path(self.test_dir) / "rhythm.txt"
        song_file.write_text("Test Rhythm\ntempo=120\nrhythm 1 2\nC G Am F\n")

        song = Song.from_file(song_file)

        self.assertEqual(song.title, "Test Rhythm")
        self.assertEqual(song.tempo, 120)
        self.assertEqual(song.rhythm_bank, 1)
        self.assertEqual(song.rhythm_number, 2)
        self.assertTrue(song.has_rhythm)

    def test_song_without_rhythm(self):
        """Test Song without rhythm has None values."""
        from src.models import Song

        song_file = Path(self.test_dir) / "no_rhythm.txt"
        song_file.write_text("No Rhythm\nC G Am F\n")

        song = Song.from_file(song_file)

        self.assertIsNone(song.rhythm_bank)
        self.assertIsNone(song.rhythm_number)
        self.assertFalse(song.has_rhythm)

    def test_invalid_rhythm_format(self):
        """Test that invalid rhythm format raises error."""
        from src.models import Song

        song_file = Path(self.test_dir) / "bad_rhythm.txt"
        song_file.write_text("Bad Rhythm\nrhythm 1\nC G\n")

        with self.assertRaises(ValueError) as context:
            Song.from_file(song_file)
        self.assertIn("rhythm", str(context.exception).lower())

    def test_rhythm_values_in_range(self):
        """Test that rhythm bank and number are validated."""
        from src.models import Song, Bar
        from pydantic import ValidationError

        # Valid rhythm values
        song = Song(
            title="Test",
            rhythm_bank=10,
            rhythm_number=20,
            bars=[Bar(chords=['C'])]
        )
        self.assertEqual(song.rhythm_bank, 10)
        self.assertEqual(song.rhythm_number, 20)

        # Invalid rhythm bank (negative)
        with self.assertRaises(ValidationError):
            Song(
                title="Test",
                rhythm_bank=-1,
                rhythm_number=20,
                bars=[Bar(chords=['C'])]
            )

        # Invalid rhythm number (> 127)
        with self.assertRaises(ValidationError):
            Song(
                title="Test",
                rhythm_bank=10,
                rhythm_number=200,
                bars=[Bar(chords=['C'])]
            )

    def test_template_renders_rhythm_defaults(self):
        """Test that template includes rhythm defaults in @OnLoad."""
        from src.generator import ChordSequenceGenerator
        from src.models import Song, Bar, SongCollection

        songs = SongCollection(songs=[
            Song(title="Test", bars=[Bar(chords=['C', 'G'])])
        ])

        generator = ChordSequenceGenerator()
        script = generator.generate_script(songs)

        # Check for rhythm defaults in @OnLoad
        self.assertIn("RhythmSetChannel = 10", script)
        self.assertIn("RhythmBankCC = 31", script)
        self.assertIn("RhythmCC = 32", script)
        self.assertIn("RhythmSetDelay = 1000", script)

    def test_template_renders_rhythm_selection(self):
        """Test that template includes rhythm selection in @SetSongRhythm."""
        from src.generator import ChordSequenceGenerator
        from src.models import Song, Bar, SongCollection

        songs = SongCollection(songs=[
            Song(
                title="Test",
                rhythm_bank=1,
                rhythm_number=2,
                bars=[Bar(chords=['C', 'G'])]
            )
        ])

        generator = ChordSequenceGenerator()
        script = generator.generate_script(songs)

        # Check for rhythm selection in @SetSongRhythm (with - 1 for 0-based MIDI channel)
        self.assertIn("SendMIDICC RhythmSetChannel - 1, RhythmBankCC, 1", script)
        self.assertIn("SendMIDICC RhythmSetChannel - 1, RhythmCC, 2, RhythmSetDelay", script)

    def test_template_multiple_songs_with_rhythm(self):
        """Test template with multiple songs having different rhythms."""
        from src.generator import ChordSequenceGenerator
        from src.models import Song, Bar, SongCollection

        songs = SongCollection(songs=[
            Song(title="Song 1", rhythm_bank=1, rhythm_number=2, bars=[Bar(chords=['C'])]),
            Song(title="Song 2", rhythm_bank=3, rhythm_number=5, bars=[Bar(chords=['G'])])
        ])

        generator = ChordSequenceGenerator()
        script = generator.generate_script(songs)

        # Check for both rhythm selections (with - 1 for 0-based MIDI channel)
        self.assertIn("if SongNb = 0", script)
        self.assertIn("SendMIDICC RhythmSetChannel - 1, RhythmBankCC, 1", script)
        self.assertIn("elseif SongNb = 1", script)
        self.assertIn("SendMIDICC RhythmSetChannel - 1, RhythmBankCC, 3", script)


class TestTemplateRendering(unittest.TestCase):
    """Test Jinja2 template rendering."""

    def test_template_renders_fill_defaults(self):
        """Test that template includes fill trigger defaults in @OnLoad."""
        from src.generator import ChordSequenceGenerator
        from src.models import Song, Bar, SongCollection

        songs = SongCollection(songs=[
            Song(title="Test", bars=[Bar(chords=['C', 'G'])])
        ])

        generator = ChordSequenceGenerator()
        script = generator.generate_script(songs)

        # Check for fill defaults in @OnLoad
        self.assertIn("FillChannel = 10", script)
        self.assertIn("FillControl = 48", script)
        self.assertIn("FillValue = 127", script)

    def test_template_renders_fill_logic_in_onbeat(self):
        """Test that template includes fill logic in @OnNewBeat."""
        from src.generator import ChordSequenceGenerator
        from src.models import Song, Bar, SongCollection

        songs = SongCollection(songs=[
            Song(title="Test", bars=[
                Bar(chords=['C', 'G'], fills=[False, True])
            ])
        ])

        generator = ChordSequenceGenerator()
        script = generator.generate_script(songs)

        # Check for fill checking logic in @OnNewBeat (with - 1 for 0-based MIDI channel)
        self.assertIn("@OnNewBeat", script)
        self.assertIn("pos = bar*8 + beat*2", script)
        self.assertIn("SendMIDICC FillChannel - 1, FillControl, FillValue", script)

    def test_template_renders_multiple_songs_with_fills(self):
        """Test template with multiple songs containing fills."""
        from src.generator import ChordSequenceGenerator
        from src.models import Song, Bar, SongCollection

        songs = SongCollection(songs=[
            Song(title="Song 1", bars=[
                Bar(chords=['C', 'G'], fills=[False, True])
            ]),
            Song(title="Song 2", bars=[
                Bar(chords=['Am', 'F'], fills=[True, False])
            ])
        ])

        generator = ChordSequenceGenerator()
        script = generator.generate_script(songs)

        # Check for song-specific fill logic
        self.assertIn("if SongNb = 0", script)
        self.assertIn("elseif SongNb = 1", script)

    def test_template_without_fills_no_logic(self):
        """Test that template without fills doesn't include unnecessary logic."""
        from src.generator import ChordSequenceGenerator
        from src.models import Song, Bar, SongCollection

        songs = SongCollection(songs=[
            Song(title="Test", bars=[Bar(chords=['C', 'G'])])
        ])

        generator = ChordSequenceGenerator()
        script = generator.generate_script(songs)

        # Should still have fill variables defined but no fill checking
        self.assertIn("FillChannel = 10", script)
        # The template should handle empty fill lists gracefully


class TestGenerateTextScript(unittest.TestCase):
    """Test text script generation (without encoding)."""

    def setUp(self):
        """Create temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_generate_script_returns_text(self):
        """Test that generate_script returns text string."""
        from src.generator import ChordSequenceGenerator
        from src.models import Song, Bar, SongCollection

        songs = SongCollection(songs=[
            Song(title="Test", bars=[Bar(chords=['C', 'G'])])
        ])

        generator = ChordSequenceGenerator()
        script = generator.generate_script(songs)

        self.assertIsInstance(script, str)
        self.assertGreater(len(script), 0)
        self.assertIn("@OnLoad", script)
        self.assertIn("@End", script)

    def test_generate_script_includes_all_sections(self):
        """Test that generated script includes all required sections."""
        from src.generator import ChordSequenceGenerator
        from src.models import Song, Bar, SongCollection

        songs = SongCollection(songs=[
            Song(title="Test Song", tempo=120, bars=[
                Bar(chords=['C', 'G', 'Am', 'F'])
            ])
        ])

        generator = ChordSequenceGenerator()
        script = generator.generate_script(songs)

        required_sections = [
            '@OnLoad',
            '@StartTempoChange',
            '@OnTimer',
            '@OnPadDown',
            '@OnKnobChange',
            '@InitializeSong',
            '@SetSongRhythm',
            '@ClearPads',
            '@Bar2PadColor',
            '@UpdateChordsSong0',
            '@OnNewBar',
            '@OnNewBeat'
        ]

        for section in required_sections:
            self.assertIn(section, script, f"Missing section: {section}")

    def test_generate_script_with_fills_has_correct_positions(self):
        """Test that fill positions are correctly calculated in script."""
        from src.generator import ChordSequenceGenerator
        from src.models import Song, Bar, SongCollection

        # Create song where we know the fill positions
        # Bar 0: 4 chords, fill on chord 1 -> pos = 0*8 + 1*(8/4) = 2
        # Bar 1: 4 chords, fill on chord 3 -> pos = 1*8 + 3*(8/4) = 14
        songs = SongCollection(songs=[
            Song(title="Test", bars=[
                Bar(chords=['C', 'G', 'Am', 'F'], fills=[False, True, False, False]),
                Bar(chords=['F', 'C', 'G', 'C'], fills=[False, False, False, True])
            ])
        ])

        generator = ChordSequenceGenerator()
        script = generator.generate_script(songs)

        # Check that fill positions are in the script
        self.assertIn("pos = 2", script)
        self.assertIn("pos = 14", script)


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


class TestChordNotePlayback(unittest.TestCase):
    """Test chord MIDI note playback functionality."""

    def test_chord_to_midi_notes_basic(self):
        """Test basic chord to MIDI conversion."""
        from src.chord_notes import chord_to_midi_notes

        # C major (octave 3): C3, E3, G3
        notes = chord_to_midi_notes("C", octave=3)
        self.assertEqual(notes, [48, 52, 55])

        # Dm (octave 3): D3, F3, A3
        notes = chord_to_midi_notes("Dm", octave=3)
        self.assertEqual(notes, [50, 53, 57])

    def test_chord_to_midi_notes_seventh(self):
        """Test seventh chord conversion."""
        from src.chord_notes import chord_to_midi_notes

        # Cmaj7 (octave 4): C4, E4, G4, B4
        notes = chord_to_midi_notes("Cmaj7", octave=4)
        self.assertEqual(notes, [60, 64, 67, 71])

        # Dm7 (octave 3): D3, F3, A3, C4
        notes = chord_to_midi_notes("Dm7", octave=3)
        self.assertEqual(notes, [50, 53, 57, 60])

    def test_chord_to_midi_notes_complex(self):
        """Test complex chord quality conversion."""
        from src.chord_notes import chord_to_midi_notes

        # Test various complex chords don't crash
        chords = ["G7sus4", "C#m7b5", "Fmaj9", "Bbmaj7"]
        for chord in chords:
            notes = chord_to_midi_notes(chord)
            self.assertIsInstance(notes, list)
            self.assertGreater(len(notes), 0)

    def test_chord_to_midi_notes_invalid(self):
        """Test invalid chord handling."""
        from src.chord_notes import chord_to_midi_notes
        import warnings

        # Invalid chord should return empty list
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            notes = chord_to_midi_notes("InvalidChord123")
            self.assertEqual(notes, [])

    def test_bar_chord_notes_field(self):
        """Test Bar model populates chord_notes field."""
        from src.models import Bar

        bar = Bar(chords=["C", "F", "G"])

        # Should auto-populate chord_notes
        self.assertEqual(len(bar.chord_notes), 3)

        # C chord should have notes
        self.assertEqual(bar.chord_notes[0], [48, 52, 55])

        # F chord should have notes
        self.assertEqual(bar.chord_notes[1], [53, 57, 60])

        # G chord should have notes
        self.assertEqual(bar.chord_notes[2], [55, 59, 62])

    def test_generator_chord_structure(self):
        """Test generator builds chord structure for template."""
        from src.generator import ChordSequenceGenerator
        from src.models import Song, Bar, SongCollection

        # Create test song
        bars = [
            Bar(chords=["C", "F"]),
            Bar(chords=["G", "C"])
        ]
        song = Song(title="Test", bars=bars)
        songs = SongCollection(songs=[song])

        # Generate script
        generator = ChordSequenceGenerator()
        script = generator.generate_script(songs)

        # Verify ChordNoteChannel and ChordNoteVelocity in script
        self.assertIn("ChordNoteChannel = 11", script)
        self.assertIn("ChordNoteVelocity = 64", script)
        self.assertIn("PrevBar = -1", script)
        self.assertIn("PrevBeat = -1", script)

    def test_template_chord_playback_blocks(self):
        """Test template generates chord playback blocks."""
        from src.generator import ChordSequenceGenerator
        from src.models import Song, Bar, SongCollection

        # Create test song with chords
        bars = [Bar(chords=["C", "G"])]
        song = Song(title="Test", bars=bars)
        songs = SongCollection(songs=[song])

        # Generate script
        generator = ChordSequenceGenerator()
        script = generator.generate_script(songs)

        # Verify @PlayChordSong0 block exists
        self.assertIn("@PlayChordSong0", script)

        # Verify @StopChordNotes block exists
        self.assertIn("@StopChordNotes", script)

        # Verify note-on commands are generated
        self.assertIn("SendMIDINoteOn ChordNoteChannel - 1,", script)

    def test_chord_change_detection_logic(self):
        """Test template generates chord change detection in @OnNewBeat."""
        from src.generator import ChordSequenceGenerator
        from src.models import Song, Bar, SongCollection

        # Create song with varying chords per bar
        bars = [
            Bar(chords=["C"]),           # 1 chord
            Bar(chords=["F", "G"]),      # 2 chords
            Bar(chords=["C", "F", "G"])  # 3 chords
        ]
        song = Song(title="Test", bars=bars)
        songs = SongCollection(songs=[song])

        # Generate script
        generator = ChordSequenceGenerator()
        script = generator.generate_script(songs)

        # Verify nested bar/beat based chord selection
        self.assertIn("if bar = 1", script)  # Bar test
        self.assertIn("if beat = 0", script)  # First chord at beat 0
        self.assertIn("elseif beat = 2", script)  # Second chord at beat 2 for 2-chord bar

        # Verify chord change detection based on bar and beat
        self.assertIn("if bar <> PrevBar or beat <> PrevBeat", script)
        self.assertIn("Call @StopChordNotes", script)

    def test_integration_chord_playback(self):
        """Integration test for chord playback with real song."""
        from src.generator import ChordSequenceGenerator
        from src.models import Song, SongCollection

        # Create test file
        test_dir = tempfile.mkdtemp()
        try:
            song_file = Path(test_dir) / "test_chord_playback.txt"
            song_file.write_text("Chord Test\ntempo=120\nC G Am F\nF C G C\n")

            # Load song
            song = Song.from_file(song_file)
            songs = SongCollection(songs=[song])

            # Generate script
            generator = ChordSequenceGenerator()
            script = generator.generate_script(songs)

            # Verify all components present
            self.assertIn("ChordNoteChannel = 11", script)
            self.assertIn("@PlayChordSong0", script)
            self.assertIn("@StopChordNotes", script)
            self.assertIn("SendMIDINoteOn", script)
            self.assertIn("SendMIDINoteOff", script)

            # Verify specific note values for C chord (48, 52, 55)
            self.assertIn("48", script)  # C3
            self.assertIn("52", script)  # E3
            self.assertIn("55", script)  # G3

        finally:
            shutil.rmtree(test_dir)


class TestSimplifiedVoicings(unittest.TestCase):
    """Test simplified chord voicings for second channel."""

    def test_simplify_chord_symbol_for_6_chords(self):
        """Test that 6 chords are simplified to major triads."""
        from src.chord_notes import simplify_chord_symbol

        # Test basic 6 chords
        self.assertEqual(simplify_chord_symbol("C6"), "C")
        self.assertEqual(simplify_chord_symbol("D6"), "D")
        self.assertEqual(simplify_chord_symbol("F#6"), "F#")
        self.assertEqual(simplify_chord_symbol("Bb6"), "Bb")

        # Test 6 chords with bass notes
        self.assertEqual(simplify_chord_symbol("C6/E"), "C/E")

    def test_simplify_chord_symbol_passthrough(self):
        """Test that non-6 chords pass through unchanged."""
        from src.chord_notes import simplify_chord_symbol

        # These should not be simplified
        self.assertEqual(simplify_chord_symbol("Cmaj7"), "Cmaj7")
        self.assertEqual(simplify_chord_symbol("Dm7"), "Dm7")
        self.assertEqual(simplify_chord_symbol("G7"), "G7")
        self.assertEqual(simplify_chord_symbol("C"), "C")

    def test_chord_to_simplified_midi_notes(self):
        """Test that chord_to_simplified_midi_notes simplifies 6 chords."""
        from src.chord_notes import chord_to_midi_notes, chord_to_simplified_midi_notes

        # C6 should simplify to C major triad
        c6_simplified = chord_to_simplified_midi_notes("C6", octave=3)
        c_major = chord_to_midi_notes("C", octave=3)
        self.assertEqual(c6_simplified, c_major)
        self.assertEqual(c6_simplified, [48, 52, 55])  # C3, E3, G3

        # D6 should simplify to D major triad
        d6_simplified = chord_to_simplified_midi_notes("D6", octave=3)
        d_major = chord_to_midi_notes("D", octave=3)
        self.assertEqual(d6_simplified, d_major)

    def test_bar_model_populates_simplified_chord_notes(self):
        """Test that Bar model auto-populates simplified_chord_notes."""
        from src.models import Bar

        # Create bar with 6 chord
        bar = Bar(chords=["C6", "G", "Am"])

        # Should have both chord_notes and simplified_chord_notes
        self.assertEqual(len(bar.chord_notes), 3)
        self.assertEqual(len(bar.simplified_chord_notes), 3)

        # C6 simplified should match C major
        self.assertEqual(bar.simplified_chord_notes[0], [48, 52, 55])

        # G should be same in both
        self.assertEqual(bar.simplified_chord_notes[1], bar.chord_notes[1])

    def test_template_includes_simplified_channel(self):
        """Test that template includes SimplifiedChordChannel configuration."""
        from src.generator import ChordSequenceGenerator
        from src.models import Song, Bar, SongCollection

        songs = SongCollection(songs=[
            Song(title="Test", bars=[Bar(chords=["C6"])])
        ])

        generator = ChordSequenceGenerator()
        script = generator.generate_script(songs)

        # Check for SimplifiedChordChannel configuration
        self.assertIn("SimplifiedChordChannel = 12", script)
        self.assertIn("ActiveSimplifiedNotes", script)
        self.assertIn("NumActiveSimplifiedNotes", script)

    def test_template_includes_onshiftdown(self):
        """Test that template includes @OnShiftDown block."""
        from src.generator import ChordSequenceGenerator
        from src.models import Song, Bar, SongCollection

        songs = SongCollection(songs=[
            Song(title="Test", bars=[Bar(chords=["C"])])
        ])

        generator = ChordSequenceGenerator()
        script = generator.generate_script(songs)

        # Check for @OnShiftDown block
        self.assertIn("@OnShiftDown", script)
        self.assertIn("Call @StopAllNotes", script)

    def test_template_sends_to_both_channels(self):
        """Test that template sends notes to both channels."""
        from src.generator import ChordSequenceGenerator
        from src.models import Song, Bar, SongCollection

        songs = SongCollection(songs=[
            Song(title="Test", bars=[Bar(chords=["C6"])])
        ])

        generator = ChordSequenceGenerator()
        script = generator.generate_script(songs)

        # Check for both channel sends
        self.assertIn("SendMIDINoteOn ChordNoteChannel - 1,", script)
        self.assertIn("SendMIDINoteOn SimplifiedChordChannel - 1,", script)

    def test_stopallnotes_stops_both_channels(self):
        """Test that @StopAllNotes stops notes on both channels."""
        from src.generator import ChordSequenceGenerator
        from src.models import Song, Bar, SongCollection

        songs = SongCollection(songs=[
            Song(title="Test", bars=[Bar(chords=["C"])])
        ])

        generator = ChordSequenceGenerator()
        script = generator.generate_script(songs)

        # Check @StopAllNotes block exists
        self.assertIn("@StopAllNotes", script)

        # Check that script has SendMIDINoteOff for both channels in @StopAllNotes block
        # We're looking for the pattern where we loop through notes and send off messages
        # The comment should say "on both channels"
        self.assertIn("on both channels", script.lower())

        # Count SendMIDINoteOff occurrences - should have multiple
        # At least 2 in @StopAllNotes (one per channel)
        noteoff_count = script.count("SendMIDINoteOff")
        self.assertGreaterEqual(noteoff_count, 2)

    def test_integration_simplified_voicing(self):
        """Integration test for simplified voicing with C6 chord."""
        from src.generator import ChordSequenceGenerator
        from src.models import Song, SongCollection

        # Create test file with C6 chord
        test_dir = tempfile.mkdtemp()
        try:
            song_file = Path(test_dir) / "test_c6.txt"
            song_file.write_text("C6 Test\nC6 G Am F6\n")

            # Load song
            song = Song.from_file(song_file)
            songs = SongCollection(songs=[song])

            # Generate script
            generator = ChordSequenceGenerator()
            script = generator.generate_script(songs)

            # Verify simplified channel configuration
            self.assertIn("SimplifiedChordChannel = 12", script)

            # Verify simplified notes are mentioned in comments
            self.assertIn("Simplified:", script)

            # Verify both C6 full voicing and simplified are present
            # C6 full has 4 notes, simplified has 3 notes
            self.assertIn("@PlayChordSong0", script)

        finally:
            shutil.rmtree(test_dir)


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
    suite.addTests(loader.loadTestsFromTestCase(TestFillTriggers))
    suite.addTests(loader.loadTestsFromTestCase(TestPydanticModels))
    suite.addTests(loader.loadTestsFromTestCase(TestRhythmSelection))
    suite.addTests(loader.loadTestsFromTestCase(TestTemplateRendering))
    suite.addTests(loader.loadTestsFromTestCase(TestGenerateTextScript))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestChordNotePlayback))
    suite.addTests(loader.loadTestsFromTestCase(TestSimplifiedVoicings))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
