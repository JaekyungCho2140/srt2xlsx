"""
Subtitle File Converter - Main Application
SRT <-> XLSX 양방향 변환 도구
"""

import sys
import os
from pathlib import Path
from tkinter import messagebox, filedialog
import customtkinter as ctk
from src.config import Config
from src.errors import MultipleInstanceError, ConverterError
from src.converter import Converter
import time


class SubtitleConverterApp:
    """메인 애플리케이션 클래스"""

    def __init__(self):
        # 다중 인스턴스 체크
        self._check_single_instance()

        # 설정 로드
        self.config = Config()

        # CustomTkinter 설정
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # 메인 윈도우 생성
        self.root = ctk.CTk()
        self.root.title("Subtitle File Converter")
        self.root.geometry("300x170")
        self.root.resizable(False, False)

        # 창 위치 설정
        self._set_window_position()

        # 변환 모드 (False: srt_to_xlsx, True: xlsx_to_srt)
        self.mode = ctk.BooleanVar()
        last_mode = self.config.get_last_mode()
        self.mode.set(last_mode == 'xlsx_to_srt')

        # 선택된 파일 경로들
        self.selected_files = []

        # UI 컴포넌트 생성
        self._create_widgets()

        # 종료 시 정리 작업
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _check_single_instance(self) -> None:
        """다중 인스턴스 체크"""
        exe_dir = Path(os.path.dirname(os.path.abspath(sys.argv[0])))
        self.lock_file = exe_dir / "srt2xlsx.lock"

        # Stale lock 체크 (24시간 이상 된 lock 파일 삭제)
        if self.lock_file.exists():
            try:
                file_age = time.time() - self.lock_file.stat().st_mtime
                if file_age > 86400:  # 24시간
                    self.lock_file.unlink()
            except:
                pass

        # lock 파일 존재 시 오류
        if self.lock_file.exists():
            messagebox.showerror("오류", "프로그램이 이미 실행 중입니다")
            sys.exit()

        # lock 파일 생성
        self.lock_file.touch()

    def _set_window_position(self) -> None:
        """창 위치 설정"""
        # 창 업데이트하여 크기 계산
        self.root.update_idletasks()

        # 저장된 위치 가져오기
        saved_pos = self.config.get_window_position()

        if saved_pos:
            x, y = saved_pos
            self.root.geometry(f"+{x}+{y}")
        else:
            # 화면 중앙에 배치
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - 300) // 2
            y = (screen_height - 250) // 2
            self.root.geometry(f"+{x}+{y}")

    def _create_widgets(self) -> None:
        """UI 컴포넌트 생성"""
        # 토글 스위치 (x=75, y=30, 너비 150, 높이 30)
        self.mode_switch = ctk.CTkSwitch(
            self.root,
            text="SRT →  XLSX",
            command=self._on_mode_toggle,
            variable=self.mode,
            width=150,
            height=30,
            switch_width=50,
            switch_height=24,
            fg_color="#10b981",
            progress_color="#10b981",
            button_color="#ffffff",
            button_hover_color="#059669"
        )
        self.mode_switch.place(x=75, y=30, anchor='nw')

        # 초기 텍스트 설정
        self._update_mode_text()

        # Browse 버튼 (x=40, y=100, 너비 100, 높이 30)
        self.browse_button = ctk.CTkButton(
            self.root,
            text="파일 선택",
            command=self._on_browse,
            width=100,
            height=30,
            font=("맑은 고딕", 14)
        )
        self.browse_button.place(x=40, y=100, anchor='nw')

        # 파일명 레이블 (x=10, y=140, 너비 280, 높이 20)
        self.file_label = ctk.CTkLabel(
            self.root,
            text="",
            width=280,
            height=20,
            anchor='center',
            font=("맑은 고딕", 14)
        )
        self.file_label.place(x=10, y=140, anchor='nw')

        # Convert 버튼 (x=160, y=100, 너비 100, 높이 30)
        self.convert_button = ctk.CTkButton(
            self.root,
            text="변환",
            command=self._on_convert,
            width=100,
            height=30,
            state="disabled",
            font=("맑은 고딕", 14)
        )
        self.convert_button.place(x=160, y=100, anchor='nw')

    def _on_mode_toggle(self) -> None:
        """모드 토글 이벤트"""
        self._update_mode_text()

        # 모드 저장
        mode_str = 'xlsx_to_srt' if self.mode.get() else 'srt_to_xlsx'
        self.config.set_last_mode(mode_str)

        # 파일 선택 초기화
        self.selected_files = []
        self.file_label.configure(text="")
        self.convert_button.configure(state="disabled")

    def _update_mode_text(self) -> None:
        """모드 텍스트 업데이트"""
        if self.mode.get():
            self.mode_switch.configure(text="XLSX →   SRT")
        else:
            self.mode_switch.configure(text="SRT →   XLSX")

    def _on_browse(self) -> None:
        """파일 선택 이벤트"""
        initial_dir = self.config.get_last_directory()

        if self.mode.get():
            # XLSX → SRT 모드: 단일 파일 선택
            filename = filedialog.askopenfilename(
                title="분할할 Excel 파일을 선택하세요",
                initialdir=initial_dir,
                filetypes=[("Excel files", "*.xlsx")]
            )
            if filename:
                self.selected_files = [filename]
                self.file_label.configure(text=os.path.basename(filename))
                self.convert_button.configure(state="normal")

                # 디렉토리 저장
                directory = os.path.dirname(filename)
                self.config.set_last_directory(directory)

                # 임시 파일 정리 (출력 파일이 저장될 디렉토리)
                self._cleanup_temp_files(directory)
        else:
            # SRT → XLSX 모드: 다중 파일 선택
            filenames = filedialog.askopenfilenames(
                title="병합할 SRT 파일을 선택하세요 (다중 선택 가능)",
                initialdir=initial_dir,
                filetypes=[("SRT files", "*.srt")]
            )
            if filenames:
                self.selected_files = list(filenames)

                # 파일 표시
                if len(filenames) == 1:
                    self.file_label.configure(text=os.path.basename(filenames[0]))
                else:
                    self.file_label.configure(text=f"{len(filenames)}개 파일 선택됨")

                self.convert_button.configure(state="normal")

                # 디렉토리 저장
                directory = os.path.dirname(filenames[0])
                self.config.set_last_directory(directory)

                # 임시 파일 정리 (출력 파일이 저장될 디렉토리)
                self._cleanup_temp_files(directory)

    def _cleanup_temp_files(self, directory: str) -> None:
        """임시 파일 정리 (*.tmp.* 패턴)"""
        try:
            dir_path = Path(directory)
            for temp_file in dir_path.glob("*.tmp.*"):
                try:
                    temp_file.unlink()
                except:
                    # 실패 시 무시
                    pass
        except:
            # 실패 시 무시 (사용자에게 알리지 않음)
            pass

    def _on_convert(self) -> None:
        """변환 버튼 이벤트"""
        if not self.selected_files:
            return

        # 처리 중 표시
        self.convert_button.configure(state="disabled")
        self.root.configure(cursor="wait")
        self.root.update()

        try:
            if self.mode.get():
                # XLSX → SRT 변환
                self._convert_xlsx_to_srt()
            else:
                # SRT → XLSX 변환
                self._convert_srt_to_xlsx()
        except Exception as e:
            messagebox.showerror("오류", str(e))
        finally:
            # 처리 완료
            self.root.configure(cursor="")
            self.convert_button.configure(state="normal")

    def _convert_srt_to_xlsx(self) -> None:
        """SRT → XLSX 변환"""
        try:
            output_path = Converter.srt_to_xlsx(self.selected_files)
            messagebox.showinfo("변환 완료", f"Excel 파일이 생성되었습니다:\n{os.path.basename(output_path)}")

            # 파일 선택 초기화
            self.selected_files = []
            self.file_label.configure(text="")
            self.convert_button.configure(state="disabled")

        except ConverterError as e:
            messagebox.showerror("오류", str(e))
        except Exception as e:
            messagebox.showerror("오류", f"변환 중 오류가 발생했습니다:\n{str(e)}")

    def _convert_xlsx_to_srt(self) -> None:
        """XLSX → SRT 변환"""
        try:
            output_paths = Converter.xlsx_to_srt(self.selected_files[0])

            # 생성된 파일 목록 메시지
            file_list = "\n".join([os.path.basename(p) for p in output_paths])
            messagebox.showinfo("변환 완료", f"{len(output_paths)}개의 SRT 파일이 생성되었습니다:\n\n{file_list}")

            # 파일 선택 초기화
            self.selected_files = []
            self.file_label.configure(text="")
            self.convert_button.configure(state="disabled")

        except ConverterError as e:
            messagebox.showerror("오류", str(e))
        except Exception as e:
            messagebox.showerror("오류", f"변환 중 오류가 발생했습니다:\n{str(e)}")

    def _on_closing(self) -> None:
        """프로그램 종료 시"""
        # 창 위치 저장
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        self.config.set_window_position(x, y)

        # lock 파일 삭제
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
        except:
            pass

        # 프로그램 종료
        self.root.destroy()

    def run(self) -> None:
        """애플리케이션 실행"""
        self.root.mainloop()


def main():
    """메인 함수"""
    try:
        app = SubtitleConverterApp()
        app.run()
    except MultipleInstanceError as e:
        messagebox.showerror("오류", str(e))
        sys.exit(1)
    except Exception as e:
        messagebox.showerror("오류", f"예상치 못한 오류가 발생했습니다:\n{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
