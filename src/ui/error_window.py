"""
오류 상세 표시 윈도우
PRD v1.7.0 섹션 3.1, 4.4 참조
"""

import customtkinter as ctk
from typing import Optional
from src.errors import ValidationResult


class ErrorDetailWindow(ctk.CTkToplevel):
    """
    오류 상세 정보를 표시하는 스크롤 가능한 윈도우

    Attributes:
        parent: 부모 윈도우
        validation_result: 검증 결과
    """

    def __init__(self, parent, validation_result: ValidationResult):
        """
        ErrorDetailWindow 생성자

        Args:
            parent: 부모 윈도우 (CTk 또는 CTkToplevel)
            validation_result: 표시할 검증 결과
        """
        super().__init__(parent)

        self.validation_result = validation_result

        # 윈도우 설정
        self.title("검증 오류 발견")
        self.geometry("600x400")

        # 부모 윈도우 중앙에 배치
        self.transient(parent)
        self.grab_set()  # 모달 동작

        # 윈도우가 닫힐 때까지 대기하도록 설정
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        # UI 생성
        self._create_ui()

    def _create_ui(self) -> None:
        """UI 컴포넌트 생성"""

        # 스크롤 가능한 프레임
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            width=560,
            height=300
        )
        self.scrollable_frame.pack(fill="both", expand=True, padx=20, pady=(20, 10))

        # 오류 표시
        self._display_errors()

        # 버튼 프레임
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        # 클립보드 복사 버튼
        self.copy_btn = ctk.CTkButton(
            button_frame,
            text="클립보드에 복사",
            command=self._copy_to_clipboard,
            width=140,
            height=35
        )
        self.copy_btn.pack(side="left", padx=(0, 10))

        # 닫기 버튼
        self.close_btn = ctk.CTkButton(
            button_frame,
            text="닫기",
            command=self.destroy,
            width=100,
            height=35
        )
        self.close_btn.pack(side="left")

    def _display_errors(self) -> None:
        """
        오류를 파일별로 그룹핑하여 표시
        """
        grouped = self.validation_result.group_by_file()

        # 한글 지원 폰트 설정
        # D2Coding, 나눔고딕코딩이 없으면 Consolas 폴백
        font_family = self._get_monospace_font()

        for file_key in sorted(grouped.keys()):
            errors = grouped[file_key]

            # 파일 헤더
            if file_key == "파일 간 검증":
                header_text = f"=== {file_key} ==="
            else:
                import os
                filename = os.path.basename(file_key)
                header_text = f"=== 파일: {filename} ==="

            header_label = ctk.CTkLabel(
                self.scrollable_frame,
                text=header_text,
                font=(font_family, 13, "bold"),
                anchor="w"
            )
            header_label.pack(fill="x", pady=(10, 5))

            # 오류 목록
            for error in errors:
                location = error.format_location()

                if location:
                    # 위치 정보 레이블
                    location_label = ctk.CTkLabel(
                        self.scrollable_frame,
                        text=f"  • {location}",
                        font=(font_family, 11),
                        anchor="w",
                        text_color="#d97706"  # 주황색
                    )
                    location_label.pack(fill="x", padx=(10, 0))

                    # 오류 메시지 레이블
                    message_label = ctk.CTkLabel(
                        self.scrollable_frame,
                        text=f"    {error.message}",
                        font=(font_family, 10),
                        anchor="w",
                        wraplength=520,
                        justify="left"
                    )
                    message_label.pack(fill="x", padx=(10, 0), pady=(0, 5))
                else:
                    # 위치 정보 없는 경우 메시지만 표시
                    message_label = ctk.CTkLabel(
                        self.scrollable_frame,
                        text=f"  • {error.message}",
                        font=(font_family, 10),
                        anchor="w",
                        wraplength=520,
                        justify="left"
                    )
                    message_label.pack(fill="x", padx=(10, 0), pady=(0, 5))

        # 요약
        total_files = len(grouped)
        total_errors = len(self.validation_result.errors)

        summary_label = ctk.CTkLabel(
            self.scrollable_frame,
            text=f"\n총 {total_files}개 파일에서 {total_errors}개 오류 발견",
            font=(font_family, 12, "bold"),
            anchor="w",
            text_color="#dc2626"  # 빨간색
        )
        summary_label.pack(fill="x", pady=(15, 10))

    def _get_monospace_font(self) -> str:
        """
        사용 가능한 고정폭 한글 폰트 반환

        우선순위:
        1. D2Coding
        2. 나눔고딕코딩
        3. Consolas (Windows 기본, 한글 지원)

        Returns:
            폰트 패밀리 이름
        """
        import tkinter.font as tkfont

        # 사용 가능한 폰트 목록
        available_fonts = tkfont.families()

        # 우선순위대로 확인
        preferred_fonts = ["D2Coding", "나눔고딕코딩", "NanumGothicCoding", "Consolas"]

        for font in preferred_fonts:
            if font in available_fonts:
                return font

        # 폴백: 시스템 기본 고정폭 폰트
        return "Courier New"

    def _copy_to_clipboard(self) -> None:
        """클립보드에 오류 리포트 복사"""
        text = self._format_clipboard_text(self.validation_result)

        # 클립보드에 복사
        self.clipboard_clear()
        self.clipboard_append(text)

        # 피드백 메시지 (버튼 텍스트 임시 변경)
        original_text = self.copy_btn.cget("text")
        self.copy_btn.configure(text="✓ 복사됨")

        # 1초 후 원래 텍스트로 복원
        self.after(1000, lambda: self.copy_btn.configure(text=original_text))

    @staticmethod
    def _format_clipboard_text(validation_result: ValidationResult) -> str:
        """
        클립보드용 텍스트 포맷팅 (일반 텍스트)

        Args:
            validation_result: 검증 결과

        Returns:
            포맷된 텍스트
        """
        # ValidationResult의 format_error_report() 메서드 재사용
        return validation_result.format_error_report()
