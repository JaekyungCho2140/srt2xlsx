"""
오류 코드 및 예외 정의
PRD 섹션 5.1 참조
"""

import os
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
from collections import defaultdict


class ConverterError(Exception):
    """변환 도구 기본 예외"""
    def __init__(self, code: int, message: str, detail: Optional[str] = None):
        self.code = code
        self.message = message
        self.detail = detail
        super().__init__(f"[오류 {code}] {message}" + (f": {detail}" if detail else ""))


# 검증 오류 (100번대)
class ValidationError(ConverterError):
    """검증 오류"""
    pass


class DetailedValidationError(ValidationError):
    """
    상세 위치 정보를 포함한 검증 오류

    Attributes:
        message: 오류 메시지
        file_path: 오류가 발생한 파일 경로 (선택)
        subtitle_index: 오류가 발생한 자막 번호 (선택)
        line_number: 오류가 발생한 라인 번호 (선택)
        timestamp: 오류가 발생한 타임스탬프 (선택)
        error_code: 오류 코드 (선택)
    """

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        subtitle_index: Optional[int] = None,
        line_number: Optional[int] = None,
        timestamp: Optional[str] = None,
        error_code: Optional[int] = None
    ):
        """
        DetailedValidationError 생성자

        Args:
            message: 오류 메시지
            file_path: 파일 경로
            subtitle_index: 자막 인덱스 번호
            line_number: 라인 번호
            timestamp: 타임스탬프
            error_code: 에러 코드
        """
        self.file_path = file_path
        self.subtitle_index = subtitle_index
        self.line_number = line_number
        self.timestamp = timestamp
        self.error_code = error_code or 100  # 기본값

        super().__init__(self.error_code, message)

    def format_location(self) -> str:
        """
        위치 정보를 포맷팅하여 반환

        Returns:
            포맷된 위치 정보 문자열
        """
        parts = []

        if self.file_path:
            filename = os.path.basename(self.file_path)
            parts.append(f"파일: {filename}")

        if self.subtitle_index is not None:
            parts.append(f"자막 #{self.subtitle_index}")

        if self.line_number is not None:
            parts.append(f"라인 {self.line_number}")

        if self.timestamp:
            parts.append(f"at {self.timestamp}")

        return " | ".join(parts) if parts else ""


@dataclass
class ValidationResult:
    """
    검증 결과를 담는 컨테이너 클래스

    Attributes:
        success: 검증 성공 여부
        errors: 발견된 오류 리스트
        warnings: 경고 리스트
        files_checked: 검증한 파일 리스트
    """
    success: bool
    errors: List[DetailedValidationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    files_checked: List[str] = field(default_factory=list)

    def group_by_file(self) -> Dict[str, List[DetailedValidationError]]:
        """
        오류를 파일별로 그룹핑

        Returns:
            파일명을 키로 하는 오류 리스트 딕셔너리
        """
        grouped: Dict[str, List[DetailedValidationError]] = defaultdict(list)

        for error in self.errors:
            if error.file_path:
                key = error.file_path
            else:
                key = "파일 간 검증"
            grouped[key].append(error)

        return dict(grouped)

    def format_error_report(self) -> str:
        """
        오류 리포트를 포맷팅하여 반환

        Returns:
            포맷된 오류 리포트 문자열
        """
        if not self.errors:
            return "오류가 없습니다."

        report_lines = []
        grouped = self.group_by_file()

        for file_key in sorted(grouped.keys()):
            errors = grouped[file_key]

            # 파일별 헤더
            if file_key == "파일 간 검증":
                report_lines.append(f"\n=== {file_key} ===")
            else:
                filename = os.path.basename(file_key)
                report_lines.append(f"\n=== 파일: {filename} ===")

            # 오류 목록
            for error in errors:
                location = error.format_location()
                if location:
                    report_lines.append(f"  • {location}")
                    report_lines.append(f"    {error.message}")
                else:
                    report_lines.append(f"  • {error.message}")

        # 요약
        total_files = len(grouped)
        total_errors = len(self.errors)
        report_lines.append(f"\n총 {total_files}개 파일에서 {total_errors}개 오류 발견")

        return "\n".join(report_lines)

    def save_to_log_file(self, log_path: str) -> None:
        """
        오류 리포트를 로그 파일로 저장

        Args:
            log_path: 로그 파일 경로
        """
        report = self.format_error_report()

        with open(log_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("Subtitle Validation Error Report\n")
            f.write("=" * 60 + "\n")
            f.write(report)
            f.write("\n" + "=" * 60 + "\n")


class SubtitleSequenceError(DetailedValidationError):
    """자막 번호 순차 오류 (101)"""
    def __init__(
        self,
        expected: int = None,
        found: int = None,
        missing_number: int = None,  # 하위 호환성
        file_path: Optional[str] = None,
        subtitle_index: Optional[int] = None
    ):
        # 하위 호환성: missing_number가 제공되면 그것을 사용
        if missing_number is not None:
            expected = missing_number
            message = f"자막 번호가 순차적이지 않습니다. (누락: #{missing_number})"
        elif expected is not None and found is not None:
            message = f"자막 번호 누락 ({expected}를 기대했으나 {found}가 발견됨)"
            if subtitle_index is None:
                subtitle_index = expected
        else:
            message = "자막 번호가 순차적이지 않습니다"

        super().__init__(
            message=message,
            file_path=file_path,
            subtitle_index=subtitle_index,
            error_code=101
        )


class TimestampFormatError(DetailedValidationError):
    """타임스탬프 형식 오류 (102)"""
    def __init__(
        self,
        invalid_timestamp: str = None,
        detail: str = "",  # 하위 호환성
        file_path: Optional[str] = None,
        subtitle_index: Optional[int] = None,
        line_number: Optional[int] = None
    ):
        if invalid_timestamp:
            message = f"타임스탬프 형식 오류: '{invalid_timestamp}' (초는 60 미만이어야 함)"
        elif detail:
            message = f"타임스탬프 형식이 올바르지 않습니다: {detail}"
        else:
            message = "타임스탬프 형식이 올바르지 않습니다"

        super().__init__(
            message=message,
            file_path=file_path,
            subtitle_index=subtitle_index,
            line_number=line_number,
            error_code=102
        )


class TimestampSyncError(DetailedValidationError):
    """타임스탬프 동기화 오류 (103)"""
    def __init__(
        self,
        subtitle_number: int = None,  # 하위 호환성
        subtitle_index: int = None,
        file_timestamps: Optional[Dict[str, Tuple[str, str]]] = None
    ):
        # 하위 호환성
        if subtitle_number is not None and subtitle_index is None:
            subtitle_index = subtitle_number

        if file_timestamps:
            message = "파일 간 타임스탬프 불일치:\n"
            for filename, (start, end) in file_timestamps.items():
                message += f"  - {filename}: {start} --> {end}\n"
            message = message.rstrip()
        else:
            message = f"파일 간 타임스탬프가 일치하지 않습니다 (자막 #{subtitle_index})"

        super().__init__(
            message=message,
            subtitle_index=subtitle_index,
            error_code=103
        )
        self.file_timestamps = file_timestamps


class SubtitleDuplicateError(DetailedValidationError):
    """자막 번호 중복 (104)"""
    def __init__(
        self,
        number: int = None,  # 하위 호환성
        duplicate_number: int = None,
        line_numbers: Optional[List[int]] = None,
        file_path: Optional[str] = None
    ):
        # 하위 호환성
        if number is not None and duplicate_number is None:
            duplicate_number = number

        if line_numbers and len(line_numbers) >= 2:
            lines_str = "과 ".join(str(ln) for ln in line_numbers)
            message = f"중복된 자막 번호 ({duplicate_number}번이 라인 {lines_str}에 나타남)"
        else:
            message = f"자막 번호가 중복되었습니다: #{duplicate_number}"

        super().__init__(
            message=message,
            file_path=file_path,
            subtitle_index=duplicate_number,
            error_code=104
        )
        self.line_numbers = line_numbers


class SubtitleZeroStartError(ValidationError):
    """자막 번호 0 시작 (105)"""
    def __init__(self):
        super().__init__(105, "자막 번호는 1부터 시작해야 합니다")


class ExcelHeaderError(ValidationError):
    """Excel 헤더 불일치 (106)"""
    def __init__(self):
        super().__init__(106, "Excel 헤더가 올바르지 않습니다")


class TimeRangeError(ValidationError):
    """시간 범위 역전 (107)"""
    def __init__(self, subtitle_number: int):
        super().__init__(107, f"종료 시간이 시작 시간보다 빠릅니다 (자막 #{subtitle_number})")


class SubtitleCountMismatchError(DetailedValidationError):
    """자막 개수 불일치 (108)"""
    def __init__(self, file_counts: Optional[Dict[str, int]] = None):
        if file_counts:
            message = "파일 간 자막 개수 불일치:\n"
            for filename, count in file_counts.items():
                message += f"  - {filename}: {count}개\n"
            message = message.rstrip()
        else:
            message = "파일 간 자막 개수가 다릅니다"

        super().__init__(
            message=message,
            error_code=108
        )
        self.file_counts = file_counts


# 파일 I/O 오류 (200번대)
class FileIOError(ConverterError):
    """파일 I/O 오류"""
    pass


class EncodingDetectionError(FileIOError):
    """인코딩 감지 실패 (202)"""
    def __init__(self, filename: str):
        super().__init__(202, f"파일 인코딩을 감지할 수 없습니다: {filename}")


class FileLockError(FileIOError):
    """Excel 파일 잠금 (203)"""
    def __init__(self, filename: str):
        super().__init__(203, f"파일이 이미 열려 있습니다: {filename}")


class LanguageCodeError(FileIOError):
    """언어 코드 오류 (204)"""
    def __init__(self, code: str):
        super().__init__(204, f"지원되지 않는 언어 코드: {code}")


class InvalidFilenameError(FileIOError):
    """특수문자 파일명 (205)"""
    def __init__(self):
        super().__init__(205, "파일명에 사용할 수 없는 문자가 포함되어 있습니다")


class FileDuplicationError(FileIOError):
    """파일명 중복 초과 (206)"""
    def __init__(self):
        super().__init__(206, "출력 파일을 생성할 수 없습니다 (파일명 중복)")


# 시스템 오류 (300번대)
class SystemError(ConverterError):
    """시스템 오류"""
    pass


class MultipleInstanceError(SystemError):
    """다중 인스턴스 (301)"""
    def __init__(self):
        super().__init__(301, "프로그램이 이미 실행 중입니다")


class InsufficientMemoryError(SystemError):
    """메모리 부족 (302)"""
    def __init__(self):
        super().__init__(302, "메모리가 부족합니다. 파일 개수를 줄여주세요")


class InsufficientDiskSpaceError(SystemError):
    """디스크 공간 부족 (303)"""
    def __init__(self):
        super().__init__(303, "디스크 공간이 부족합니다")
