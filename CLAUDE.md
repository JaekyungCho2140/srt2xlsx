# CLAUDE.md

This file provides high-level guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
- **📋 PRD v1.6.4**: `.claude/docs/PRD.md`