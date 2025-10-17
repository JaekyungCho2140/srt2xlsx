"""
변환 로직 모듈
PRD 섹션 4.1, 4.2 참조
"""

import os
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from src.srt_parser import SRTParser, Subtitle
from src.excel_generator import ExcelGenerator
from src.validator import Validator
from src.errors import FileLockError, InsufficientDiskSpaceError


class Converter:
    """변환 클래스"""

    @staticmethod
    def srt_to_xlsx(filepaths: List[str]) -> str:
        """
        SRT → XLSX 변환

        Args:
            filepaths: SRT 파일 경로 리스트

        Returns:
            생성된 Excel 파일 경로

        Raises:
            ValueError: 같은 폴더에 없음
            LanguageCodeError: 언어 코드 오류
            SubtitleCountMismatchError: 자막 개수 불일치
            TimestampSyncError: 타임스탬프 불일치
            FileDuplicationError: 파일명 중복 초과
        """
        if not filepaths:
            raise ValueError("파일이 선택되지 않았습니다")

        # 같은 폴더 검증
        Validator.validate_same_directory(filepaths)

        # 메모리 체크
        total_size = sum(os.path.getsize(fp) for fp in filepaths)
        if not Validator.check_memory_availability(total_size, "srt_to_xlsx"):
            raise ValueError("사용자가 변환을 중단했습니다")

        # 대용량 파일 경고
        for filepath in filepaths:
            if not Validator.check_large_file_warning(filepath):
                raise ValueError("사용자가 변환을 중단했습니다")

        # 언어별 자막 파싱
        subtitles_by_language = {}

        for filepath in filepaths:
            # 언어 코드 추출
            lang_code = Validator.extract_language_code(filepath)

            # SRT 파일 파싱
            subtitles = SRTParser.parse_file(filepath)

            subtitles_by_language[lang_code] = subtitles

        # 타임스탬프 동기화 검증
        Validator.validate_timestamp_sync(subtitles_by_language)

        # Excel 생성
        wb = ExcelGenerator.create_workbook(subtitles_by_language)

        # 출력 파일 경로 결정
        output_dir = os.path.dirname(filepaths[0])

        # 기본 파일명 (첫 번째 파일의 언어 코드 제거)
        first_filename = os.path.basename(filepaths[0])
        base_filename = first_filename.rsplit('_', 1)[0]  # 마지막 언더스코어 이전까지

        # 중복 파일명 처리
        output_path = Validator.generate_output_filename(
            base_filename, output_dir, ".xlsx"
        )

        # 임시 파일 생성
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        temp_path = f"{output_path}.tmp.{timestamp}"

        try:
            # Excel 파일 저장 (임시 파일)
            wb.save(temp_path)

            # 임시 파일을 최종 위치로 이동
            if os.path.exists(output_path):
                os.remove(output_path)
            os.rename(temp_path, output_path)

        except PermissionError:
            # Excel 파일이 이미 열려 있는 경우
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            raise FileLockError(os.path.basename(output_path))

        except OSError as e:
            # 디스크 공간 부족
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            raise InsufficientDiskSpaceError()

        finally:
            # 임시 파일 정리
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass

        return output_path

    @staticmethod
    def xlsx_to_srt(filepath: str) -> List[str]:
        """
        XLSX → SRT 변환 (Two-Phase Commit)

        Args:
            filepath: Excel 파일 경로

        Returns:
            생성된 SRT 파일 경로 리스트

        Raises:
            ExcelHeaderError: 헤더 오류
            FileLockError: 파일 잠금
            InsufficientDiskSpaceError: 디스크 공간 부족
        """
        if not filepath:
            raise ValueError("파일이 선택되지 않았습니다")

        # 메모리 체크
        file_size = os.path.getsize(filepath)
        if not Validator.check_memory_availability(file_size, "xlsx_to_srt"):
            raise ValueError("사용자가 변환을 중단했습니다")

        # 대용량 파일 경고
        if not Validator.check_large_file_warning(filepath):
            raise ValueError("사용자가 변환을 중단했습니다")

        # Excel 파일 읽기
        try:
            subtitles_by_language = ExcelGenerator.read_workbook(filepath)
        except PermissionError:
            raise FileLockError(os.path.basename(filepath))

        # 빈 언어 열 제외
        non_empty_languages = {}
        for lang_code, subtitles in subtitles_by_language.items():
            if not ExcelGenerator.is_language_column_empty(subtitles):
                non_empty_languages[lang_code] = subtitles

        if not non_empty_languages:
            raise ValueError("변환할 자막이 없습니다 (모든 언어 열이 비어있습니다)")

        # 출력 디렉토리
        output_dir = os.path.dirname(filepath)

        # 기본 파일명 (Excel 파일명에서 확장자 제거)
        excel_filename = os.path.basename(filepath)
        base_filename = os.path.splitext(excel_filename)[0]

        # Phase 1: 모든 언어의 임시 파일 생성
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        temp_files = {}
        created_temp_files = []

        try:
            for lang_code, subtitles in non_empty_languages.items():
                # 출력 파일명
                output_filename = f"{base_filename}_{lang_code}.srt"
                output_path = Validator.generate_output_filename(
                    f"{base_filename}_{lang_code}", output_dir, ".srt"
                )

                # 임시 파일 경로
                temp_path = f"{output_path}.tmp.{timestamp}"

                # SRT 내용 생성
                srt_content = Converter._generate_srt_content(subtitles)

                # 임시 파일에 쓰기 (UTF-8 BOM)
                with open(temp_path, 'w', encoding='utf-8-sig') as f:
                    f.write(srt_content)

                temp_files[lang_code] = (temp_path, output_path)
                created_temp_files.append(temp_path)

            # Phase 2: 모든 임시 파일을 최종 위치로 일괄 이동
            created_output_files = []

            for lang_code, (temp_path, output_path) in temp_files.items():
                try:
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    os.rename(temp_path, output_path)
                    created_output_files.append(output_path)
                except Exception as e:
                    # 이동 실패 시 롤백
                    Converter._rollback(created_temp_files, created_output_files)
                    raise e

            # 성공 시 임시 파일 정리
            for temp_path in created_temp_files:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass

            return created_output_files

        except PermissionError:
            Converter._rollback(created_temp_files, [])
            raise FileLockError(base_filename)

        except OSError:
            Converter._rollback(created_temp_files, [])
            raise InsufficientDiskSpaceError()

        except Exception as e:
            Converter._rollback(created_temp_files, [])
            raise e

    @staticmethod
    def _generate_srt_content(subtitles: List[Subtitle]) -> str:
        """
        자막 리스트로부터 SRT 내용 생성

        Args:
            subtitles: Subtitle 객체 리스트

        Returns:
            SRT 파일 내용
        """
        lines = []

        for subtitle in subtitles:
            lines.append(str(subtitle.number))
            lines.append(f"{subtitle.start_time} --> {subtitle.end_time}")
            lines.append(subtitle.text)
            lines.append("")  # 빈 줄

        return '\n'.join(lines)

    @staticmethod
    def _rollback(temp_files: List[str], output_files: List[str]) -> None:
        """
        롤백: 생성된 임시 파일 및 출력 파일 삭제

        Args:
            temp_files: 임시 파일 경로 리스트
            output_files: 출력 파일 경로 리스트
        """
        # 임시 파일 삭제
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

        # 부분적으로 생성된 출력 파일 삭제
        for output_file in output_files:
            if os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except:
                    pass
