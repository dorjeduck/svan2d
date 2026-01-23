"""Tests for svan2d.path.parser module."""

import pytest

from svan2d.path.parser import parse_coordinates, tokenize_path


@pytest.mark.unit
class TestTokenizePath:
    """Tests for tokenize_path function."""

    def test_simple_moveto(self):
        tokens = tokenize_path("M 10 20")
        assert tokens == ["M", "10", "20"]

    def test_moveto_lineto(self):
        tokens = tokenize_path("M 10,20 L 30,40")
        assert tokens == ["M", "10", "20", "L", "30", "40"]

    def test_compressed_syntax(self):
        # SVG allows numbers to run together without spaces
        tokens = tokenize_path("M100-20L50,30")
        assert tokens == ["M", "100", "-20", "L", "50", "30"]

    def test_decimal_numbers(self):
        tokens = tokenize_path("M 10.5 20.7")
        assert tokens == ["M", "10.5", "20.7"]

    def test_scientific_notation(self):
        tokens = tokenize_path("M 1e2 2.5e-1")
        assert tokens == ["M", "1e2", "2.5e-1"]

    def test_negative_numbers(self):
        tokens = tokenize_path("M -10 -20")
        assert tokens == ["M", "-10", "-20"]

    def test_positive_sign(self):
        tokens = tokenize_path("M +10 +20")
        assert tokens == ["M", "+10", "+20"]

    def test_close_path(self):
        tokens = tokenize_path("M 0,0 L 100,100 Z")
        assert tokens == ["M", "0", "0", "L", "100", "100", "Z"]

    def test_lowercase_commands(self):
        tokens = tokenize_path("m 10 20 l 30 40")
        assert tokens == ["m", "10", "20", "l", "30", "40"]

    def test_cubic_bezier(self):
        tokens = tokenize_path("C 10,20 30,40 50,60")
        assert tokens == ["C", "10", "20", "30", "40", "50", "60"]

    def test_quadratic_bezier(self):
        tokens = tokenize_path("Q 10,20 30,40")
        assert tokens == ["Q", "10", "20", "30", "40"]

    def test_arc_command(self):
        tokens = tokenize_path("A 25 25 0 0 1 50 50")
        assert tokens == ["A", "25", "25", "0", "0", "1", "50", "50"]

    def test_horizontal_line(self):
        tokens = tokenize_path("H 100")
        assert tokens == ["H", "100"]

    def test_vertical_line(self):
        tokens = tokenize_path("V 100")
        assert tokens == ["V", "100"]

    def test_smooth_cubic_bezier(self):
        tokens = tokenize_path("S 30,40 50,60")
        assert tokens == ["S", "30", "40", "50", "60"]

    def test_smooth_quadratic_bezier(self):
        tokens = tokenize_path("T 50,60")
        assert tokens == ["T", "50", "60"]

    def test_empty_string(self):
        tokens = tokenize_path("")
        assert tokens == []

    def test_whitespace_only(self):
        tokens = tokenize_path("   ")
        assert tokens == []

    def test_mixed_separators(self):
        tokens = tokenize_path("M10,20 30 40,50")
        assert tokens == ["M", "10", "20", "30", "40", "50"]

    def test_complex_path(self):
        path = "M 0,0 L 100,0 L 100,100 L 0,100 Z"
        tokens = tokenize_path(path)
        assert tokens == ["M", "0", "0", "L", "100", "0", "L", "100", "100", "L", "0", "100", "Z"]


@pytest.mark.unit
class TestParseCoordinates:
    """Tests for parse_coordinates function."""

    def test_parse_two_coords(self):
        tokens = ["10", "20", "30", "40"]
        coords, remaining = parse_coordinates(tokens, 2)
        assert coords == [10.0, 20.0]
        assert remaining == ["30", "40"]

    def test_parse_four_coords(self):
        tokens = ["1", "2", "3", "4", "5", "6"]
        coords, remaining = parse_coordinates(tokens, 4)
        assert coords == [1.0, 2.0, 3.0, 4.0]
        assert remaining == ["5", "6"]

    def test_parse_six_coords(self):
        tokens = ["1", "2", "3", "4", "5", "6"]
        coords, remaining = parse_coordinates(tokens, 6)
        assert coords == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        assert remaining == []

    def test_parse_decimal_coords(self):
        tokens = ["10.5", "20.7"]
        coords, remaining = parse_coordinates(tokens, 2)
        assert coords == [10.5, 20.7]

    def test_parse_negative_coords(self):
        tokens = ["-10", "-20"]
        coords, remaining = parse_coordinates(tokens, 2)
        assert coords == [-10.0, -20.0]

    def test_not_enough_coords_raises(self):
        tokens = ["10"]
        with pytest.raises(ValueError) as exc_info:
            parse_coordinates(tokens, 2)
        assert "Expected 2 coordinates" in str(exc_info.value)

    def test_empty_list_raises(self):
        with pytest.raises(ValueError):
            parse_coordinates([], 2)

    def test_original_list_not_modified(self):
        original = ["10", "20", "30"]
        parse_coordinates(original, 2)
        # Original should not be modified (we use a copy)
        assert original == ["10", "20", "30"]
