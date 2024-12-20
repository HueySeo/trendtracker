import os
import sys
import time
import subprocess
import requests
import json
from pathlib import Path
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt, QThread, Signal, QCoreApplication, QPoint
from PySide6.QtGui import QMovie
import datetime
import warnings

# SSL 경고 무시 (테스트 목적으로만 사용)
warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

def download_script_file(url, path, progress_callback=None):
    try:
        r = requests.get(url, stream=True, allow_redirects=True, verify=False)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to download file: {e}")
        return False
    
    filename = url.split('/')[-1]
    full_file_path = os.path.join(path, filename)
    Path(path).mkdir(parents=True, exist_ok=True)
    
    total_size = int(r.headers.get('content-length', 0))
    chunk_size = 1024 * 64  # 64KB
    downloaded_size = 0
    start_time = time.time()

    with open(full_file_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                downloaded_size += len(chunk)
                if progress_callback:
                    elapsed_time = time.time() - start_time
                    if downloaded_size > 0:
                        estimated_total_time = (elapsed_time / downloaded_size) * total_size
                        remaining_time = estimated_total_time - elapsed_time
                        remaining_time_str = str(datetime.timedelta(seconds=int(remaining_time)))
                        downloaded_size_mb = downloaded_size / (1024 * 1024)
                        total_size_mb = total_size / (1024 * 1024)
                        progress_callback(downloaded_size, total_size, remaining_time_str)
                        QCoreApplication.processEvents()  # 이벤트 루프 처리
    
    # 다운로드 완료 후 100% 진행 상황 업데이트
    if progress_callback:
        progress_callback(total_size, total_size, "0:00:00")
    
    return full_file_path

class UpdateThread(QThread):
    progress = Signal(int)
    update_failed = Signal(str)
    update_completed = Signal()
    estimated_time = Signal(str)

    def __init__(self, tt_exe_local_path, tt_exe_azure_path):
        super().__init__()
        self.tt_exe_local_path = tt_exe_local_path        # local TT.exe 
        self.tt_exe_azure_path = tt_exe_azure_path        # TT.exe  Azure URL 
        # self.tt_update_exe_path = tt_update_exe_path      # local TT_update.exe

    def run(self):
        try:
            self.progress.emit(20)

            # 파일 다운로드
            def progress_callback(downloaded_size, total_size, remaining_time_str):
                progress_percentage = 20 + int((downloaded_size / total_size) * 50)
                self.progress.emit(progress_percentage)
                self.estimated_time.emit(f"Copied: {downloaded_size / (1024 * 1024):.2f} MB / {total_size / (1024 * 1024):.2f} MB\nEstimated time remaining: {remaining_time_str}")

            downloaded_file = download_script_file(self.tt_exe_azure_path, os.path.dirname(self.tt_exe_local_path), progress_callback)
            if not downloaded_file:
                raise FileNotFoundError(f"Failed to download file: {self.tt_exe_azure_path}")

            self.progress.emit(70)

            # 현재 실행 중인 프로그램 종료 대기
            time.sleep(1)
            self.progress.emit(80)

            # # 기존 실행 파일 삭제
            # os.remove(self.tt_exe_local_path)
            # self.progress.emit(90)

            # # 새로운 파일로 덮어씌우기
            # os.rename(self.tt_update_exe_path, self.tt_exe_local_path)
            # self.progress.emit(95)

            # 프로그램 재실행
            subprocess.Popen([self.tt_exe_local_path])
            self.progress.emit(100)
            self.update_completed.emit()
        except Exception as e:
            self.update_failed.emit(str(e))

class UpdateDialog(QDialog):
    def __init__(self, tt_exe_local_path, tt_exe_azure_path):
        super().__init__()
        self.setWindowTitle("Updating...")
        self.setGeometry(0, 0, 300, 200)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        layout = QVBoxLayout()

        self.estimated_time_label = QLabel("Copied: 0.00 MB / 0.00 MB\nEstimated time remaining: Calculating...", self)
        self.loading_label = QLabel(self)
        self.loading_movie = QMovie(".\\image\\loading.gif")
        self.loading_label.setMovie(self.loading_movie)
        self.loading_movie.start()

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)

        layout.addWidget(self.estimated_time_label)
        layout.addWidget(self.loading_label)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

        self.update_thread = UpdateThread(tt_exe_local_path, tt_exe_azure_path)
        self.update_thread.progress.connect(self.progress_bar.setValue)
        self.update_thread.update_failed.connect(self.on_update_failed)
        self.update_thread.update_completed.connect(self.on_update_completed)
        self.update_thread.estimated_time.connect(self.estimated_time_label.setText)
        self.update_thread.start()

        self.old_pos = self.pos()

        # 창을 화면 중앙으로 이동
        self.center()

    def center(self):
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.old_pos)
            event.accept()

    def on_update_failed(self, error_message):
        self.loading_movie.stop()
        self.loading_label.setText(f"Update failed: {error_message}")
        sys.exit()

    def on_update_completed(self):
        self.loading_movie.stop()
        self.loading_label.setText("Update completed!")
        time.sleep(1)
        self.accept()

def main():
    if len(sys.argv) > 2:
        # print("Usage: updater.exe <tt_exe_local_path> <tt_exe_azure_path> <tt_update_exe_path>")
        time.sleep(2)
        # sys.exit(1)

        tt_exe_local_path = sys.argv[1]
        tt_exe_azure_path = sys.argv[2]
        # tt_update_exe_path = sys.argv[3]
    else:
        tt_exe_local_path = os.path.join(os.getcwd(), 'TT.exe') #
        tt_exe_azure_path = "https://gemini-files.lamresearch.com/script-files/application/trend_tracker/TT.exe" #f"\\fre_filer03\2300testdata\HeLeakSPC\data\leak_log\Trend Tracker\TT.exe" 
        # tt_update_exe_path = os.path.join(os.getcwd(), 'TT_update.exe')

    app = QApplication(sys.argv)
    dialog = UpdateDialog(tt_exe_local_path, tt_exe_azure_path)
    dialog.exec()

if __name__ == "__main__":
    main()
