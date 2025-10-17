"""
설정 파일 (settings.ini) 관리
PRD 섹션 2 참조
"""

import configparser
import os
from pathlib import Path
from typing import Tuple, Optional


class Config:
    """settings.ini 관리 클래스"""

    def __init__(self):
        # 실행 파일과 같은 디렉토리에 설정 파일 위치
        exe_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent
        self.config_file = exe_dir / "settings.ini"
        self.config = configparser.ConfigParser()
        self._load_or_create()

    def _load_or_create(self) -> None:
        """설정 파일 로드 또는 기본값으로 생성"""
        if self.config_file.exists():
            try:
                self.config.read(self.config_file, encoding='utf-8')
                # 필수 섹션 확인
                if not self.config.has_section('UI'):
                    self.config.add_section('UI')
                if not self.config.has_section('Files'):
                    self.config.add_section('Files')
            except:
                # 손상된 경우 기본값으로 재생성
                self._create_default()
        else:
            self._create_default()

    def _create_default(self) -> None:
        """기본 설정 생성"""
        self.config['UI'] = {
            'last_mode': 'srt_to_xlsx',
            'window_x': '',
            'window_y': ''
        }
        self.config['Files'] = {
            'last_directory': ''
        }
        self._save()

    def _save(self) -> None:
        """설정 파일 저장"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
        except:
            # 저장 실패 시 무시 (오류 메시지 없음)
            pass

    def get_last_mode(self) -> str:
        """마지막 사용 모드 가져오기"""
        try:
            return self.config.get('UI', 'last_mode', fallback='srt_to_xlsx')
        except:
            return 'srt_to_xlsx'

    def set_last_mode(self, mode: str) -> None:
        """마지막 사용 모드 저장"""
        self.config.set('UI', 'last_mode', mode)
        self._save()

    def get_window_position(self) -> Optional[Tuple[int, int]]:
        """창 위치 가져오기 (없으면 None 반환)"""
        try:
            x = self.config.get('UI', 'window_x', fallback='')
            y = self.config.get('UI', 'window_y', fallback='')
            if x and y:
                return (int(x), int(y))
        except:
            pass
        return None

    def set_window_position(self, x: int, y: int) -> None:
        """창 위치 저장"""
        self.config.set('UI', 'window_x', str(x))
        self.config.set('UI', 'window_y', str(y))
        self._save()

    def get_last_directory(self) -> str:
        """마지막 사용 디렉토리 가져오기"""
        try:
            directory = self.config.get('Files', 'last_directory', fallback='')
            if directory and os.path.exists(directory):
                return directory
        except:
            pass
        # 기본값: 실행 파일 위치
        return str(Path(os.path.dirname(os.path.abspath(__file__))).parent)

    def set_last_directory(self, directory: str) -> None:
        """마지막 사용 디렉토리 저장"""
        self.config.set('Files', 'last_directory', directory)
        self._save()
