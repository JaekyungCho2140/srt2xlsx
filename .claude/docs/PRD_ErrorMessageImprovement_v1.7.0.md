# Product Requirements Document (PRD)
## Error Message Improvement for Subtitle Validation

### Document Information
- **Version**: 1.7.0 (Planned)
- **Purpose**: Enhanced error reporting for LLM-generated subtitle validation
- **Target Users**: Translation workers, Content creators, LLM subtitle validators
- **Created**: 2025-10-21
- **Status**: Draft

---

## 1. Background and Motivation

### Current Usage Pattern Discovery
During actual production use, the tool has proven invaluable not only for SRT ↔ XLSX conversion but also as a **validation tool for LLM-generated subtitle files**.

### LLM Subtitle Validation Use Case
When delegating subtitle translation to LLMs:
- **Common LLM errors detected**:
  - Missing subtitle indices
  - Duplicate subtitle numbers
  - Skipped subtitle blocks
  - Mismatched subtitle counts across language files
  - Timestamp synchronization issues

### Current Problem
While the tool successfully **detects** these errors, it fails to provide **actionable error information**:
- ❌ No file identification in error messages
- ❌ No precise location information (line number, subtitle index)
- ❌ Generic error descriptions without context
- ⏱️ Users spend significant time manually locating error positions

### Success Story
> "The validation capability is extremely useful for catching LLM translation errors, but finding exactly where the problem is takes too much time."

---

## 2. Improvement Goals

### Primary Objectives
1. **Precise Error Location**: Tell users exactly WHERE the error occurred
2. **Clear Error Context**: Provide enough information to fix issues immediately
3. **Efficient Workflow**: Minimize time spent locating and fixing errors
4. **Professional Validation Tool**: Position the tool as a robust subtitle QA solution

### Success Metrics
- Users can locate and fix errors without re-reading entire files
- Error messages contain sufficient information for immediate action
- Validation workflow time reduced by 70%+

---

## 3. Functional Requirements

### 3.1 Error Detail Window

**UI Component**: Separate scrollable error details window (CustomTkinter)

**Window Specifications**:
- **Size**: 600×400 pixels (scrollable)
- **Title**: "Validation Errors Detected"
- **Components**:
  - ScrollableFrame with error list
  - Copy to Clipboard button
  - Close button
- **Font**: Monospace font for Korean text alignment
  - Preferred: D2Coding, 나눔고딕코딩
  - Fallback: Consolas (supports Korean)
- **Language**: All error messages in Korean
- **Appearance**: Consistent with main window theme

### 3.2 Error Information Format

Each error message must include:

#### Required Information
1. **File Name**: Which file contains the error
   - Format: `subtitle_KO.srt`
   - Display: Highlighted or bolded

2. **Subtitle Index**: Which subtitle block has the issue
   - Format: `Subtitle #42`
   - Must be the logical subtitle number (not line number)

3. **Error Type**: Clear categorization
   - Examples: "Missing Index", "Duplicate Number", "Timestamp Mismatch"

4. **Error Description**: Precise problem statement
   - What was expected vs what was found
   - No suggestions for fixes (as per user preference)

#### Optional Information (When Applicable)
- **Line Number**: For file-level issues
- **Timestamp**: For timestamp-related errors
- **Comparison**: For cross-file validation issues

### 3.3 Multi-File Error Handling

**Grouping Strategy**: File-based grouping

**Display Structure**:
```
=== 파일: subtitle_KO.srt ===
  • 자막 #42: 자막 번호 누락 (42를 기대했으나 43이 발견됨)
  • 자막 #58: 중복된 자막 번호 (42번이 두 번 나타남)

=== 파일: subtitle_EN.srt ===
  • 자막 #105: 타임스탬프 형식 오류 (밀리초 값이 유효하지 않음: 1234)

=== 파일 간 검증 ===
  • 자막 개수 불일치: KO(120) vs EN(118) vs JA(120)
  • 자막 #67 타임스탬프 동기화 오류: KO와 EN 파일의 타임스탬프가 다름
```

### 3.4 Error Collection Strategy

**Behavior**: Collect ALL errors before displaying

**Rationale**:
- Single validation pass provides complete error picture
- Users can fix all issues in one edit session
- Prevents multiple re-validation cycles

**Implementation**:
- Continue validation even after encountering errors
- Accumulate errors in structured list
- Display all errors grouped by file after complete validation

---

## 4. Technical Implementation

### 4.1 Error Data Structure

**Enhanced Exception Classes** (extend current error hierarchy):

```python
class DetailedValidationError(ValidationError):
    """Base class for errors with detailed location info"""

    def __init__(
        self,
        message: str,
        file_path: str = None,
        subtitle_index: int = None,
        line_number: int = None,
        timestamp: str = None,
        error_code: int = None
    ):
        super().__init__(message)
        self.file_path = file_path
        self.subtitle_index = subtitle_index
        self.line_number = line_number
        self.timestamp = timestamp
        self.error_code = error_code

    def format_location(self) -> str:
        """Format location information for display"""
        parts = []
        if self.file_path:
            parts.append(f"File: {os.path.basename(self.file_path)}")
        if self.subtitle_index:
            parts.append(f"Subtitle #{self.subtitle_index}")
        if self.line_number:
            parts.append(f"Line {self.line_number}")
        if self.timestamp:
            parts.append(f"at {self.timestamp}")
        return " | ".join(parts)
```

### 4.2 Error Collection Mechanism

**ValidationResult Class**:
```python
@dataclass
class ValidationResult:
    """Container for validation results"""
    success: bool
    errors: List[DetailedValidationError]
    warnings: List[str]
    files_checked: List[str]

    def group_by_file(self) -> Dict[str, List[DetailedValidationError]]:
        """Group errors by file for display"""
        grouped = defaultdict(list)
        for error in self.errors:
            file_key = error.file_path or "Cross-File Validation"
            grouped[file_key].append(error)
        return dict(grouped)
```

### 4.3 Modified Validation Flow

**Current Flow**:
```
Validate → Raise Exception → Show Generic Error → Stop
```

**New Flow**:
```
Validate → Collect All Errors → Group by File → Show Detailed Error Window → Return
```

**Key Changes**:
1. Validators return `ValidationResult` instead of raising exceptions
2. Parser continues on non-critical errors, collecting issues
3. Only critical failures (file not found, encoding error) stop immediately
4. All validation errors accumulated before UI display

### 4.4 Error Display Window Implementation

**ErrorDetailWindow Class** (CustomTkinter):
```python
class ErrorDetailWindow(ctk.CTkToplevel):
    def __init__(self, parent, validation_result: ValidationResult):
        super().__init__(parent)

        self.title("검증 오류 발견")
        self.geometry("600x400")

        # Scrollable frame for errors
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Display errors grouped by file
        self._display_errors(validation_result)

        # Copy to clipboard button
        self.copy_btn = ctk.CTkButton(
            self,
            text="Copy to Clipboard",
            command=lambda: self._copy_to_clipboard(validation_result)
        )
        self.copy_btn.pack(pady=5)

        # Close button
        self.close_btn = ctk.CTkButton(self, text="Close", command=self.destroy)
        self.close_btn.pack(pady=5)
```

---

## 5. Error Message Templates

### 5.1 Validation Errors (100s)

**101: Subtitle Sequence Error**
```
파일: subtitle_KO.srt | 자막 #42
자막 번호 누락 (42를 기대했으나 43이 발견됨)
```

**102: Timestamp Format Error**
```
파일: subtitle_EN.srt | 자막 #15 | 라인 61
타임스탬프 형식 오류: '00:01:65,000' (초는 60 미만이어야 함)
```

**103: Timestamp Sync Error**
```
파일 간 검증 | 자막 #67
파일 간 타임스탬프 불일치:
  - subtitle_KO.srt: 00:05:30,000 --> 00:05:32,500
  - subtitle_EN.srt: 00:05:30,100 --> 00:05:32,600
```

**104: Duplicate Subtitle Number**
```
파일: subtitle_JA.srt | 자막 #28
중복된 자막 번호 (28번이 라인 112와 140에 나타남)
```

**108: Subtitle Count Mismatch**
```
파일 간 검증
파일 간 자막 개수 불일치:
  - subtitle_KO.srt: 120개
  - subtitle_EN.srt: 118개
  - subtitle_JA.srt: 120개
```

### 5.2 File I/O Errors (200s)

**202: Encoding Detection Error**
```
파일: subtitle_RU.srt
인코딩 감지 실패 (UTF-8, CP949, 자동 감지 시도함)
신뢰도: 0.42 (임계값: 0.7)
```

**204: Language Code Error**
```
파일: subtitle.srt
파일명 형식 오류 (예상 형식: *_언어코드.srt)
지원되는 언어 코드: KO, EN, CT, CS, JA, TH, ES-LATAM, PT-BR, RU
```

---

## 6. UI/UX Design

### 6.1 User Workflow

**Before (Current)**:
```
1. Click Convert
2. See error: "Timestamp sync error"
3. Open all files
4. Manually search for mismatched timestamps
5. Fix error
6. Retry conversion
```

**After (Improved)**:
```
1. Click Convert
2. See error detail window:
   "subtitle_KO.srt | Subtitle #67 | Timestamp mismatch..."
3. Open subtitle_KO.srt
4. Jump to subtitle #67
5. Fix error
6. Retry conversion
```

### 6.2 Error Window Layout

```
┌─────────────────────────────────────────────────────┐
│ 검증 오류 발견                                   [X] │
├─────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────┐ │
│ │ === 파일: subtitle_KO.srt ===                   │ │
│ │ • 자막 #42: 자막 번호 누락                       │ │
│ │   (42를 기대했으나 43이 발견됨)                  │ │
│ │                                                  │ │
│ │ === 파일: subtitle_EN.srt ===                   │ │
│ │ • 자막 #15 | 라인 61: 타임스탬프 형식 오류       │ │
│ │   '00:01:65,000'                                │ │
│ │                                                  │ │
│ │ === 파일 간 검증 ===                             │ │
│ │ • 자막 #67: KO와 EN 파일 간 타임스탬프 불일치    │ │
│ │                                                  │ │
│ │                                                  │ │
│ │ 총 2개 파일에서 3개 오류 발견                    │ │
│ └─────────────────────────────────────────────────┘ │
│                                                       │
│        [클립보드에 복사]        [닫기]                 │
└─────────────────────────────────────────────────────┘
```

---

## 7. Implementation Phases

### Phase 1: Core Error Infrastructure (Priority: High)
**Scope**:
- Create `DetailedValidationError` hierarchy
- Create `ValidationResult` data structure
- Modify all validators to collect errors instead of raising immediately

**Files to Modify**:
- `src/errors.py`: Add detailed error classes
- `src/validator.py`: Return ValidationResult
- `src/srt_parser.py`: Collect parsing errors
- `src/converter.py`: Handle ValidationResult

**Estimated Effort**: 4-6 hours

### Phase 2: Error Display UI (Priority: High)
**Scope**:
- Create `ErrorDetailWindow` class
- Implement error grouping and formatting
- Add copy-to-clipboard functionality

**Files to Create/Modify**:
- `src/ui/error_window.py`: New file for error display window
- `main.py`: Integrate error window instead of messagebox

**Estimated Effort**: 3-4 hours

### Phase 3: Enhanced Error Messages (Priority: Medium)
**Scope**:
- Update all error message templates
- Add location information to all error types
- Implement file-based error grouping

**Files to Modify**:
- All validation logic in `src/validator.py`
- All parsing logic in `src/srt_parser.py`

**Estimated Effort**: 3-4 hours

### Phase 4: Testing and Refinement (Priority: High)
**Scope**:
- Create test cases for each error type
- Test error window UI responsiveness
- Validate error message clarity with real LLM-generated files

**Estimated Effort**: 2-3 hours

**Total Estimated Effort**: 12-17 hours

---

## 8. Testing Scenarios

### 8.1 Single File Errors

**Test Case 1: Missing Subtitle Index**
```
Input: subtitle_KO.srt with sequence 1, 2, 4, 5 (missing 3)
Expected Output:
  파일: subtitle_KO.srt | 자막 #3
  자막 번호 누락 (3을 기대했으나 4가 발견됨)
```

**Test Case 2: Duplicate Subtitle Number**
```
Input: subtitle_EN.srt with two blocks numbered 42
Expected Output:
  파일: subtitle_EN.srt | 자막 #42
  중복된 자막 번호 (라인 168과 212에 나타남)
```

**Test Case 3: Invalid Timestamp Format**
```
Input: Timestamp "00:01:65,000" (invalid seconds)
Expected Output:
  파일: subtitle_JA.srt | 자막 #15 | 라인 61
  타임스탬프 형식 오류: '00:01:65,000' (초는 60 미만이어야 함)
```

### 8.2 Multi-File Errors

**Test Case 4: Timestamp Synchronization**
```
Input:
  - subtitle_KO.srt: Subtitle #67 at 00:05:30,000
  - subtitle_EN.srt: Subtitle #67 at 00:05:30,100
Expected Output:
  파일 간 검증 | 자막 #67
  파일 간 타임스탬프 불일치:
    - subtitle_KO.srt: 00:05:30,000 --> 00:05:32,500
    - subtitle_EN.srt: 00:05:30,100 --> 00:05:32,600
```

**Test Case 5: Subtitle Count Mismatch**
```
Input:
  - subtitle_KO.srt: 120 subtitles
  - subtitle_EN.srt: 118 subtitles
Expected Output:
  파일 간 검증
  파일 간 자막 개수 불일치:
    - subtitle_KO.srt: 120개
    - subtitle_EN.srt: 118개
```

### 8.3 Multiple Errors in Single File

**Test Case 6: Multiple Issues**
```
Input: subtitle_KO.srt with:
  - Missing subtitle #10
  - Duplicate subtitle #25
  - Invalid timestamp at subtitle #42
Expected Output: All three errors listed under subtitle_KO.srt group
```

---

## 9. Non-Functional Requirements

### 9.1 Performance
- Error collection must not significantly impact validation speed
- Error window must render within 500ms even with 50+ errors
- Memory overhead for error collection: < 5MB for typical use cases

### 9.2 Usability
- Error messages must be understandable without technical knowledge
- Location information must be precise enough for quick navigation
- Error window must support keyboard navigation (Tab, Enter, Esc)

### 9.3 Compatibility
- Must maintain backward compatibility with existing error codes
- Existing error handling in converter.py should still work
- No breaking changes to public API

---

## 10. Out of Scope (v1.7.0)

The following features are explicitly **NOT** included in this version:

- ❌ Automatic error correction or suggestions
- ❌ Export error report to file (may add in v1.8.0)
- ❌ Error severity levels (all errors treated as critical)
- ❌ Warning vs Error distinction (only errors for now)
- ❌ Interactive error navigation (jump to file/line from error window)
- ❌ Error statistics or summary dashboard

---

## 11. Success Criteria

**Must Have**:
- ✅ All errors show file name and subtitle index
- ✅ Errors grouped by file in dedicated scrollable window
- ✅ Error messages are clear and actionable
- ✅ Users can copy error details to clipboard
- ✅ All existing tests pass with new error handling

**Nice to Have**:
- ⭐ Error window remembers size and position
- ⭐ Monospace font for better alignment
- ⭐ Color coding for different error types

**Success Metrics**:
- 90%+ reduction in "where is the error?" questions
- Users can locate and fix errors without re-reading files
- No increase in validation time (< 5% acceptable)

---

## 12. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.7.0 | 2025-10 (Planned) | Enhanced error reporting with detailed location info |
| 1.6.5 | 2025-01 | Current stable release |

---

**Document Status**: Draft - Ready for Implementation
**Approval Required**: User acceptance of technical approach
**Next Steps**: Begin Phase 1 implementation after approval
