# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
**Subtitle File Converter Tool** - A Windows-only portable tool for bidirectional conversion between multiple .srt subtitle files and a single .xlsx Excel file.

## Documentation Structure
- **CLAUDE.md** (this file): High-level guidance and quick reference for Claude
- **PRD.md** (.claude/docs/Completed/PRD.md): Complete product requirements, specifications, and technical details - **PRIMARY REFERENCE** (archived)

## Core Development Principles

### 1. Zero Arbitrary Decisions
All implementation details must strictly follow the PRD.md specifications. If any detail is not specified in the PRD, stop development and seek clarification first.

### 2. Implementation Priorities
1. **Correctness over Speed**: Ensure accurate conversion and data integrity
2. **Stability over Features**: Focus on reliable core functionality
3. **Simplicity over Complexity**: Choose straightforward solutions

### 3. PRD.md is the Source of Truth
For all technical specifications, constraints, and implementation details, refer to:
- **📋 PRD v1.6.5**: `.claude/docs/Completed/PRD.md` (archived reference)

## Development Workflow

### Test-First Development
- Write tests before implementing features
- All non-GUI logic must have automated tests
- GUI components require manual testing as specified in Testing Strategy
- Tests must validate both happy paths and edge cases

### Verification Requirements
- After any code modification, pytest results must be provided
- Never report "Modified successfully" or "Fixed" without showing verification
- Execute code at each step to validate changes
- Show actual test output, not assumptions about test results

### Prohibited Practices
- Implementing features without tests
- Reporting "Tests passed" without showing pytest execution results
- Speculative responses like "This should work" or "Probably correct"
- Committing code that fails tests
- Skipping validation steps to save time

### Documentation Requirements
- Add docstrings to all functions and classes (follow PEP 257)
- Include type hints for all function parameters and return values
- Handle edge cases explicitly (file not found, invalid format, encoding errors, etc.)
- Provide clear, actionable error messages to users
- Document why decisions were made, not just what was done

## Common Commands

### Development Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Running the Application
```bash
# Run from source
python main.py
```

### Testing
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_srt_parser.py

# Run tests with coverage
pytest --cov=src tests/
```

### Building
```bash
# Build using batch script (Windows)
build.bat

# Or manually with PyInstaller
pyinstaller build.spec

# Output location: dist/srt2xlsx.exe
```

## Architecture Overview

### Code Structure Reference

For current code structure, use **Serena MCP**:
- **Directory structure**: `list_dir('src', recursive=False)`
- **Module symbols**: `get_symbols_overview('<module_path>')`
- **Error hierarchy**: `find_symbol('ConverterError', 'src/errors.py', depth=2)`
- **Class methods**: `find_symbol('<ClassName>', '<file_path>', depth=1)`

Detailed module information is maintained in project memory: `read_memory('project_overview')`

### Key Architectural Patterns

**Two-Phase Commit (XLSX → SRT)**
- **Purpose**: Guarantee atomic multi-file creation
- **Phase 1**: Create all temporary files (*.tmp.YYYYMMDDHHMMSS)
- **Phase 2**: Atomic rename all files to final names
- **On error**: Complete rollback of all temporary and partially created files
- **Why**: Prevents partial file sets that would break conversion reversibility

**Encoding Detection Strategy**
- **Purpose**: Handle diverse subtitle file encodings
- **Chain**: UTF-8 BOM → UTF-8 decode → CP949 decode → chardet (≥ 0.7) → Error 202
- **Why this order**: BOM is instant, UTF-8 most common, CP949 for Korean legacy, chardet as fallback
- **Implementation**: See `SRTParser.detect_encoding()`

**Memory Management**
- **Purpose**: Prevent OOM crashes on large files
- **Pre-flight check**: Estimate required memory before conversion
- **Multipliers**: SRT→XLSX: filesize × 5, XLSX→SRT: filesize × 3
- **Warning threshold**: Required > (available × 0.7)
- **Why**: Excel/openpyxl has significant memory overhead
- **Implementation**: See `Validator.check_memory_availability()`

**Timestamp Synchronization**
- **Purpose**: Ensure all language tracks remain in perfect sync
- **Requirements**: Identical subtitle counts, exact timestamp matches across all languages
- **Precision**: Millisecond-level validation
- **Why**: Single-frame desyncs break video playback
- **Implementation**: See `Validator.validate_timestamp_sync()`

### UI Architecture Decisions

- **CustomTkinter choice**: Native toggle switch (CTkSwitch), modern UI components, no mixed widget styles
- **Fixed window size**: Simplified layout management, no responsive design complexity, predictable UX
- **Settings persistence**: User preferences (mode, position, directory) saved in settings.ini for session continuity
- **Why no resizing**: 300×250 pixels sufficient for all content, avoids layout complexity

For specific coordinates and component details, see `SubtitleConverterApp` in `main.py`.

### Critical Business Rules

1. **Language Code Format**: Files must follow `*_(LANG-CODE).srt` naming convention
   - Supported languages: KO, EN, CT, CS, JA, TH, ES-LATAM, PT-BR, RU
   - Implementation: See `Validator.LANGUAGE_PATTERN` and `extract_language_code()`

2. **Subtitle Requirements**:
   - Numbers must start at 1, sequential with no gaps
   - Timestamp format: `HH:MM:SS,mmm` (millisecond precision required)
   - All language files must have identical timestamps for proper synchronization

3. **File Organization**:
   - All SRT files must be in the same directory for SRT→XLSX conversion
   - Empty columns/cells detected via whitespace stripping
   - Why: Simplifies file selection, prevents path complexity

For validation implementation details, see `src/validator.py`.

### File Safety Patterns

- **Temporary file strategy**: All writes use temporary files to prevent corruption during failures
- **Single instance lock**: Lock file (srt2xlsx.lock) prevents multiple instances from conflicting writes
- **Automatic cleanup**: Stale temporary files and locks removed on startup
- **Atomic operations**: All-or-Nothing rollback on errors (Two-Phase Commit for multi-file operations)
- **Why**: Data integrity is prioritized over performance

For specific timeout values and file naming patterns, see `converter.py` and `main.py`.

## Development Notes

### DO NOT Implement
- Threading or multiprocessing (single-threaded only)
- Progress bars or status text during conversion
- Drag-and-drop file selection
- Auto-correction of subtitle numbers or timestamps
- External SRT parsing libraries (manual parsing required)

### Must Follow
- PEP 8 style guide with type hints
- Error codes from PRD section 5.1
- Exact header validation for Excel files
- Memory pre-checks before conversion
- Two-Phase Commit pattern for multi-file output

### Testing Strategy
- Core logic: 100% pytest coverage
- GUI testing: Manual only (no automation)
- Focus: Timestamp sync, encoding detection, validation logic
