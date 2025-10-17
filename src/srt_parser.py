"""
SRT 파일 파싱 모듈
PRD 섹션 3.1 참조
"""

import re
import chardet
from typing import List, Tuple
from dataclasses import dataclass
from src.errors import (
    EncodingDetectionError,
    SubtitleSequenceError,
    SubtitleDuplicateError,
    SubtitleZeroStartError,
    TimestampFormatError,
    TimeRangeError
)


@dataclass
class Subtitle:
    """자막 데이터 클래스"""
    number: int
    start_time: str
    end_time: str
    text: str


class SRTParser:
    """SRT 파일 파서"""

    # 타임스탬프 정규표현식 (HH:MM:SS,mmm)
    TIMESTAMP_PATTERN = re.compile(
        r'^(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})$'
    )

    @staticmethod
    def detect_encoding(filepath: str) -> str:
        """
        파일 인코딩 감지
        PRD 섹션 3.1 인코딩 감지 순서에 따라 구현
        """
        # 1. UTF-8 BOM 체크
        try:
            with open(filepath, 'rb') as f:
                first_bytes = f.read(3)
                if first_bytes == b'\xef\xbb\xbf':
                    return 'utf-8-sig'
        except:
            pass

        # 2. UTF-8로 디코딩 시도
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                f.read()
            return 'utf-8'
        except UnicodeDecodeError:
            pass

        # 3. CP949로 디코딩 시도
        try:
            with open(filepath, 'r', encoding='cp949') as f:
                f.read()
            return 'cp949'
        except UnicodeDecodeError:
            pass

        # 4. chardet로 자동 감지
        try:
            with open(filepath, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                if result['confidence'] >= 0.7:
                    return result['encoding']
        except:
            pass

        # 모두 실패 시 오류
        raise EncodingDetectionError(filepath)

    @staticmethod
    def parse_file(filepath: str) -> List[Subtitle]:
        """
        SRT 파일 파싱

        Args:
            filepath: SRT 파일 경로

        Returns:
            Subtitle 객체 리스트

        Raises:
            EncodingDetectionError: 인코딩 감지 실패
            SubtitleSequenceError: 자막 번호 순차 오류
            SubtitleDuplicateError: 자막 번호 중복
            SubtitleZeroStartError: 자막 번호 0 시작
            TimestampFormatError: 타임스탬프 형식 오류
            TimeRangeError: 시간 범위 역전
        """
        # 인코딩 감지
        encoding = SRTParser.detect_encoding(filepath)

        # 파일 읽기
        with open(filepath, 'r', encoding=encoding) as f:
            content = f.read()

        # 파싱
        return SRTParser.parse_content(content)

    @staticmethod
    def parse_content(content: str) -> List[Subtitle]:
        """
        SRT 내용 파싱

        Args:
            content: SRT 파일 내용

        Returns:
            Subtitle 객체 리스트
        """
        subtitles = []
        lines = content.strip().split('\n')
        i = 0
        expected_number = 1
        seen_numbers = set()

        while i < len(lines):
            # 빈 줄 건너뛰기
            while i < len(lines) and not lines[i].strip():
                i += 1

            if i >= len(lines):
                break

            # 자막 번호 파싱
            try:
                number = int(lines[i].strip())
            except ValueError:
                raise TimestampFormatError(f"자막 번호를 찾을 수 없습니다: {lines[i]}")

            # 자막 번호 검증
            if number == 0:
                raise SubtitleZeroStartError()

            if number in seen_numbers:
                raise SubtitleDuplicateError(number)

            if number != expected_number:
                raise SubtitleSequenceError(expected_number)

            seen_numbers.add(number)
            i += 1

            # 타임스탬프 파싱
            if i >= len(lines):
                raise TimestampFormatError("타임스탬프를 찾을 수 없습니다")

            timestamp_line = lines[i].strip()
            match = SRTParser.TIMESTAMP_PATTERN.match(timestamp_line)

            if not match:
                raise TimestampFormatError(f"잘못된 타임스탬프 형식: {timestamp_line}")

            # 타임스탬프 추출
            start_h, start_m, start_s, start_ms = match.groups()[:4]
            end_h, end_m, end_s, end_ms = match.groups()[4:]

            start_time = f"{start_h}:{start_m}:{start_s},{start_ms}"
            end_time = f"{end_h}:{end_m}:{end_s},{end_ms}"

            # 시간 범위 검증
            start_total_ms = (int(start_h) * 3600 + int(start_m) * 60 + int(start_s)) * 1000 + int(start_ms)
            end_total_ms = (int(end_h) * 3600 + int(end_m) * 60 + int(end_s)) * 1000 + int(end_ms)

            if end_total_ms <= start_total_ms:
                raise TimeRangeError(number)

            # 24시간 이내 검증
            if start_total_ms >= 24 * 3600 * 1000 or end_total_ms >= 24 * 3600 * 1000:
                raise TimestampFormatError(f"타임스탬프가 24시간을 초과합니다 (자막 #{number})")

            i += 1

            # 자막 텍스트 파싱
            text_lines = []
            while i < len(lines) and lines[i].strip():
                text_lines.append(lines[i])
                i += 1

            # 자막 텍스트 (빈 텍스트 허용)
            text = '\n'.join(text_lines)

            # Subtitle 객체 생성
            subtitle = Subtitle(
                number=number,
                start_time=start_time,
                end_time=end_time,
                text=text
            )
            subtitles.append(subtitle)

            expected_number += 1

        return subtitles

    @staticmethod
    def parse_timestamp_to_ms(timestamp: str) -> int:
        """
        타임스탬프를 밀리초로 변환

        Args:
            timestamp: HH:MM:SS,mmm 형식의 타임스탬프

        Returns:
            밀리초 단위 시간
        """
        match = re.match(r'^(\d{2}):(\d{2}):(\d{2}),(\d{3})$', timestamp)
        if not match:
            raise TimestampFormatError(f"잘못된 타임스탬프 형식: {timestamp}")

        h, m, s, ms = map(int, match.groups())
        return (h * 3600 + m * 60 + s) * 1000 + ms
