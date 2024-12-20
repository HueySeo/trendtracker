from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton
from PySide6.QtGui import QIcon
import os

class AboutDialog(QDialog):
    def __init__(self, parent=None, version = ''):
        super().__init__(parent)
        self.setWindowTitle("About")
        self.setGeometry(400, 300, 400, 300)
        self.setWindowIcon(QIcon(os.path.join(os.getcwd(), 'ico', 'tt.ico')))

        layout = QVBoxLayout()

        developer_label = QLabel("seohu")
        version_label = QLabel(f"Version: {version}")

        # changelog = QTextEdit()
        # changelog.setReadOnly(True)
        # changelog.setPlainText("Version 1.0v")

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)

        layout.addWidget(developer_label)
        layout.addWidget(version_label)
        # layout.addWidget(changelog)
        layout.addWidget(close_button)

        self.setLayout(layout)
