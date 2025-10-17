# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
**Subtitle File Converter Tool** - A Windows-only portable tool for bidirectional conversion between multiple .srt subtitle files and a single .xlsx Excel file.

## Documentation Structure
- **CLAUDE.md** (this file): High-level guidance and quick reference for Claude
- **PRD.md** (.claude/docs/PRD.md): Complete product requirements, specifications, and technical details - **PRIMARY REFERENCE**
- **design_draft.html** (.claude/docs/design_draft.html): UI design mockup

## Core Development Principles

### 1. Zero Arbitrary Decisions
All implementation details must strictly follow the PRD.md specifications. If any detail is not specified in the PRD, stop development and seek clarification first.

### 2. Implementation Priorities
1. **Correctness over Speed**: Ensure accurate conversion and data integrity
2. **Stability over Features**: Focus on reliable core functionality
3. **Simplicity over Complexity**: Choose straightforward solutions

### 3. PRD.md is the Source of Truth
For all technical specifications, constraints, and implementation details, refer to:
- **📋 PRD v1.6.5**: `.claude/docs/PRD.md`

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

### Module Structure
```
src/
├── config.py          # Settings.ini management (window position, last mode, last directory)
├── errors.py          # Custom exception hierarchy (100/200/300 error codes)
├── srt_parser.py      # SRT parsing with encoding detection (UTF-8 → CP949 → chardet)
├── excel_generator.py # Excel creation/reading with openpyxl (formatting, headers)
├── validator.py       # All validation logic (timestamps, language codes, memory checks)
└── converter.py       # Main conversion orchestration (Two-Phase Commit for XLSX→SRT)
```

### Key Architectural Patterns

**Two-Phase Commit (XLSX → SRT)**
- Phase 1: Create all temporary files (*.tmp.YYYYMMDDHHMMSS)
- Phase 2: Atomic rename all files to final names
- On error: Complete rollback of all temporary and partially created files

**Encoding Detection Strategy**
1. UTF-8 BOM check (immediate success)
2. UTF-8 decode attempt
3. CP949 decode attempt
4. chardet auto-detection (confidence ≥ 0.7)
5. Error 202 if all fail

**Memory Management**
- Pre-flight memory check using psutil
- SRT→XLSX: filesize × 5 multiplier
- XLSX→SRT: filesize × 3 multiplier
- Warning threshold: required > (available × 0.7)

**Timestamp Synchronization**
- All language files must have identical subtitle counts
- Each subtitle number must have exact timestamp match across all languages
- Millisecond-level precision required
- Error 103 on any mismatch

### Error Code System
- **100s**: Validation errors (sequence, timestamp format, sync)
- **200s**: File I/O errors (encoding, lock, language code)
- **300s**: System errors (multi-instance, memory, disk space)

### UI Coordination
- CustomTkinter for all UI components (no tkinter widgets)
- Fixed window size: 300×250 pixels
- Component placement: absolute coordinates using `place(anchor='nw')`
- CTkSwitch for mode toggle with dynamic text updates
- Settings persistence via settings.ini (ConfigParser)

### Critical Validation Rules
1. **Language Code Extraction**: Regex pattern `.*_(LANG-CODE)\.srt$` (case-insensitive)
2. **Subtitle Numbering**: Must start at 1, sequential with no gaps
3. **Timestamp Format**: Strict `HH:MM:SS,mmm` validation
4. **Same Directory Rule**: All SRT files must be in same folder for SRT→XLSX
5. **Empty Column Detection**: Strip whitespace, check for None/""/whitespace-only

### File Operations
- All writes use temporary files with timestamp suffix
- Temporary file cleanup on app start in output directory
- Lock file (srt2xlsx.lock) prevents multiple instances
- Stale lock auto-removal after 24 hours
- All-or-Nothing rollback on any error

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
