@echo off
REM Subtitle File Converter 빌드 스크립트

echo ====================================
echo Subtitle File Converter 빌드 시작
echo ====================================
echo.

REM 가상 환경 확인
if not exist "venv\" (
    echo 가상 환경을 생성합니다...
    python -m venv venv
    echo.
)

REM 가상 환경 활성화
call venv\Scripts\activate.bat

REM 의존성 설치
echo 의존성을 설치합니다...
pip install -r requirements.txt
echo.

REM 기존 빌드 파일 삭제
if exist "dist\" (
    echo 기존 빌드 파일을 삭제합니다...
    rmdir /s /q dist
    echo.
)

if exist "build\" (
    rmdir /s /q build
)

REM PyInstaller로 빌드
echo PyInstaller로 빌드합니다...
pyinstaller build.spec
echo.

REM 빌드 완료
if exist "dist\srt2xlsx.exe" (
    echo ====================================
    echo 빌드 완료!
    echo 실행 파일: dist\srt2xlsx.exe
    echo ====================================
) else (
    echo ====================================
    echo 빌드 실패!
    echo ====================================
)

pause
