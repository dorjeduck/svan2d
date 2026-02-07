# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Updated documentation to reflect current builder API

## [0.5.0-alpha] - 2026-01-23

### Added
- Rounded corners for `RectangleState` and `SquareState` via `corner_radius` parameter
- `VertexRectangle` now supports `corner_radius` for morphing rounded shapes

### Added
- VScene and VSceneExporter tests
- Path module tests (parser, svg_path)
- Converter tests with mocking
- Server, CLI, and font module tests
- Completed `transition_and_keystates.md` documentation

### Changed
- Improved test coverage for core modules (color, point2d, scalar_functions)
- Pylance-compliance improvements
- Synchronized version numbers across project files

### Fixed
- Bare except clauses in `config.py` and `flubber_morpher.py`

## [0.4.2] - 2026-01-11

### Added
- Z-index support for element layering

## [0.4.0] - 2025-12-17

### Added
- State collections (`StateCollectionState`)

## [0.3.0] - 2025-12-16

### Added
- Builder pattern for VElement construction
- Segment functions for common animation patterns

### Changed
- Complete API refactoring

## [0.2.0] - 2025-12-11

### Changed
- States now use `Point2D` for position fields

## [0.1.0] - 2025-12-08

### Added
- Initial release
