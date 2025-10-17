"""
오류 코드 및 예외 정의
PRD 섹션 5.1 참조
"""

from typing import Optional


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


class SubtitleSequenceError(ValidationError):
    """자막 번호 순차 오류 (101)"""
    def __init__(self, missing_number: int):
        super().__init__(101, f"자막 번호가 순차적이지 않습니다. (누락: #{missing_number})")


class TimestampFormatError(ValidationError):
    """타임스탬프 형식 오류 (102)"""
    def __init__(self, detail: str = ""):
        super().__init__(102, "타임스탬프 형식이 올바르지 않습니다", detail)


class TimestampSyncError(ValidationError):
    """타임스탬프 동기화 오류 (103)"""
    def __init__(self, subtitle_number: int):
        super().__init__(103, f"파일 간 타임스탬프가 일치하지 않습니다 (자막 #{subtitle_number})")


class SubtitleDuplicateError(ValidationError):
    """자막 번호 중복 (104)"""
    def __init__(self, number: int):
        super().__init__(104, f"자막 번호가 중복되었습니다: #{number}")


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


class SubtitleCountMismatchError(ValidationError):
    """자막 개수 불일치 (108)"""
    def __init__(self):
        super().__init__(108, "파일 간 자막 개수가 다릅니다")


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
