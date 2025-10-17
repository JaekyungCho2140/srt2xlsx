"""
검증 로직 모듈
PRD 섹션 3.3, 3.4, 4.3 참조
"""

import re
import os
import psutil
from pathlib import Path
from typing import List, Dict, Optional
from tkinter import messagebox
from src.srt_parser import Subtitle, SRTParser
from src.errors import (
    LanguageCodeError,
    InvalidFilenameError,
    TimestampSyncError,
    SubtitleCountMismatchError,
    InsufficientMemoryError
)


class Validator:
    """검증 클래스"""

    # 지원 언어 코드
    SUPPORTED_LANGUAGES = [
        "KO", "EN", "CT", "CS", "JA", "TH", "ES-LATAM", "PT-BR", "RU"
    ]

    # 언어 코드 추출 정규표현식 (PRD 섹션 3.3)
    LANGUAGE_PATTERN = re.compile(
        r".*_(KO|EN|CT|CS|JA|TH|ES-LATAM|PT-BR|RU)\.srt$",
        re.IGNORECASE
    )

    # Windows 금지 문자
    INVALID_FILENAME_CHARS = r'[\\/:*?"<>|]'

    @staticmethod
    def extract_language_code(filename: str) -> str:
        """
        파일명에서 언어 코드 추출

        Args:
            filename: 파일명 (예: "subtitle_KO.srt")

        Returns:
            언어 코드 (대문자, 예: "KO")

        Raises:
            LanguageCodeError: 언어 코드 추출 실패
        """
        basename = os.path.basename(filename)
        match = Validator.LANGUAGE_PATTERN.match(basename)

        if not match:
            raise LanguageCodeError(f"파일명 형식이 올바르지 않습니다: {basename}")

        # 언어 코드 정규화 (대문자로 변환)
        lang_code = match.group(1).upper()

        if lang_code not in Validator.SUPPORTED_LANGUAGES:
            raise LanguageCodeError(lang_code)

        return lang_code

    @staticmethod
    def validate_filename_characters(filename: str) -> None:
        """
        파일명에 Windows 금지 문자가 있는지 검증

        Args:
            filename: 파일명

        Raises:
            InvalidFilenameError: 금지 문자 포함
        """
        if re.search(Validator.INVALID_FILENAME_CHARS, filename):
            raise InvalidFilenameError()

    @staticmethod
    def validate_same_directory(filepaths: List[str]) -> None:
        """
        모든 파일이 같은 폴더에 있는지 검증

        Args:
            filepaths: 파일 경로 리스트

        Raises:
            ValueError: 파일들이 서로 다른 폴더에 위치
        """
        if not filepaths:
            return

        directories = set(os.path.dirname(os.path.abspath(fp)) for fp in filepaths)

        if len(directories) > 1:
            raise ValueError("모든 파일이 같은 폴더에 있어야 합니다")

    @staticmethod
    def validate_timestamp_sync(subtitles_by_language: Dict[str, List[Subtitle]]) -> None:
        """
        파일 간 타임스탬프 동기화 검증

        Args:
            subtitles_by_language: 언어별 자막 리스트

        Raises:
            SubtitleCountMismatchError: 자막 개수 불일치
            TimestampSyncError: 타임스탬프 불일치
        """
        if not subtitles_by_language:
            return

        # 자막 개수 확인
        counts = [len(subs) for subs in subtitles_by_language.values()]
        if len(set(counts)) > 1:
            raise SubtitleCountMismatchError()

        subtitle_count = counts[0]

        # 타임스탬프 동기화 확인
        for i in range(subtitle_count):
            # 모든 언어의 i번째 자막 타임스탬프 수집
            timestamps = {}
            for lang_code, subtitles in subtitles_by_language.items():
                subtitle = subtitles[i]
                timestamps[lang_code] = (subtitle.start_time, subtitle.end_time)

            # 타임스탬프 일치 확인
            first_lang = list(timestamps.keys())[0]
            reference_timestamps = timestamps[first_lang]

            for lang_code, (start, end) in timestamps.items():
                if (start, end) != reference_timestamps:
                    raise TimestampSyncError(i + 1)

    @staticmethod
    def check_memory_availability(
        file_size: int,
        conversion_mode: str,
        show_warning: bool = True
    ) -> bool:
        """
        메모리 가용성 체크

        Args:
            file_size: 파일 크기 (바이트)
            conversion_mode: 변환 모드 ("srt_to_xlsx" 또는 "xlsx_to_srt")
            show_warning: 경고 메시지 표시 여부

        Returns:
            계속 진행 여부 (True: 진행, False: 중단)

        Raises:
            InsufficientMemoryError: 메모리 부족 (사용자가 중단 선택 시)
        """
        # 필요 메모리 계산 (PRD 섹션 3.4)
        if conversion_mode == "srt_to_xlsx":
            required_memory = file_size * 5  # 파싱 및 Excel 생성 오버헤드
        else:  # xlsx_to_srt
            required_memory = file_size * 3  # openpyxl 로딩 오버헤드

        # 가용 메모리 확인
        available_memory = psutil.virtual_memory().available

        # 메모리 경고 임계값: 필요 메모리 > (가용 메모리 × 0.7)
        threshold = available_memory * 0.7

        if required_memory > threshold:
            if show_warning:
                response = messagebox.askyesno(
                    "메모리 경고",
                    "메모리가 부족할 수 있습니다. 계속하시겠습니까?"
                )
                if not response:
                    return False

        return True

    @staticmethod
    def check_large_file_warning(filepath: str, show_warning: bool = True) -> bool:
        """
        대용량 파일 경고 (10,000행 초과)

        Args:
            filepath: 파일 경로
            show_warning: 경고 메시지 표시 여부

        Returns:
            계속 진행 여부 (True: 진행, False: 중단)
        """
        # 빠른 라인 카운트
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                line_count = sum(1 for _ in f)

            # 자막 개수 추정 (대략 4줄당 1개 자막)
            estimated_subtitle_count = line_count // 4

            if estimated_subtitle_count > 10000:
                if show_warning:
                    response = messagebox.askyesno(
                        "대용량 파일",
                        "파일이 큽니다. 처리에 시간이 걸릴 수 있습니다. 계속하시겠습니까?"
                    )
                    if not response:
                        return False
        except:
            # 파일 읽기 실패 시 무시
            pass

        return True

    @staticmethod
    def generate_output_filename(
        base_filename: str,
        output_dir: str,
        extension: str,
        max_attempts: int = 999
    ) -> str:
        """
        출력 파일명 생성 (중복 시 _N 접미사 추가)

        Args:
            base_filename: 기본 파일명 (확장자 제외)
            output_dir: 출력 디렉토리
            extension: 확장자 (예: ".xlsx", ".srt")
            max_attempts: 최대 시도 횟수

        Returns:
            최종 파일 경로

        Raises:
            FileDuplicationError: 최대 시도 횟수 초과
        """
        from src.errors import FileDuplicationError

        output_path = Path(output_dir) / f"{base_filename}{extension}"

        if not output_path.exists():
            return str(output_path)

        # 중복 파일명 처리
        for i in range(1, max_attempts + 1):
            new_filename = f"{base_filename}_{i}{extension}"
            output_path = Path(output_dir) / new_filename

            if not output_path.exists():
                return str(output_path)

        # 최대 시도 횟수 초과
        raise FileDuplicationError()
