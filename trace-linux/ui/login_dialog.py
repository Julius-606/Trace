"""
TRACE Desktop (Linux Client) - User Authentication & Cloud Sync Dialog
FILE: trace-linux/ui/login_dialog.py
VERSION: 1.0.0
ROLE: Modern dark-themed login modal supporting authentication with the
      central FastAPI backend and graceful offline fallback to local SQLite.
"""

import sys
try:
    from PyQt6.QtWidgets import (
        QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QFrame, QMessageBox, QApplication
    )
    from PyQt6.QtCore import Qt, pyqtSignal as Signal
    from PyQt6.QtGui import QFont, QIcon
except ImportError:
    from PySide6.QtWidgets import (
        QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QFrame, QMessageBox, QApplication
    )
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QFont, QIcon

from repository import TraceRepository
from config import DEFAULT_BACKEND_URL, APP_DISPLAY_NAME


class LoginDialog(QDialog):
    """
    Modal authentication dialog that connects to the central backend
    or allows offline workstation access with local cached credentials.
    """
    loginSuccessful = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Authentication - {APP_DISPLAY_NAME}")
        self.setFixedSize(460, 560)
        self.setModal(True)
        self.user_session = None
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0b0f19;
                color: #f8fafc;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        # Brand & Header
        brand_layout = QHBoxLayout()
        logo = QLabel("⚡", self)
        logo.setStyleSheet("font-size: 26px;")
        brand_layout.addWidget(logo)

        title = QLabel("TRACE", self)
        title.setStyleSheet("font-size: 22px; font-weight: 900; letter-spacing: 2px; color: #6366f1;")
        brand_layout.addWidget(title)

        badge = QLabel("LINUX WORKSTATION", self)
        badge.setStyleSheet("font-size: 10px; font-weight: bold; background: #312e81; color: #a5b4fc; padding: 3px 8px; border-radius: 4px;")
        brand_layout.addWidget(badge)
        brand_layout.addStretch()
        layout.addLayout(brand_layout)

        subtitle = QLabel("Sign in to sync your active units, Neurons wallet, and progress with the central cloud vault.", self)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 12px; color: #94a3b8; line-height: 1.4;")
        layout.addWidget(subtitle)

        # Form Fields Container
        form_frame = QFrame(self)
        form_frame.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(12)

        # Backend URL Field
        url_label = QLabel("CENTRAL BACKEND URL", form_frame)
        url_label.setStyleSheet("font-size: 10px; font-weight: bold; color: #64748b; letter-spacing: 0.5px;")
        form_layout.addWidget(url_label)

        self.url_input = QLineEdit(DEFAULT_BACKEND_URL, form_frame)
        self.url_input.setPlaceholderText("http://127.0.0.1:7860")
        self.url_input.setStyleSheet("""
            QLineEdit {
                background-color: #0b0f19;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #e2e8f0;
                padding: 8px 12px;
                font-size: 12px;
                font-family: monospace;
            }
            QLineEdit:focus { border-color: #6366f1; }
        """)
        form_layout.addWidget(self.url_input)

        # Email / Username
        email_label = QLabel("EMAIL OR USERNAME", form_frame)
        email_label.setStyleSheet("font-size: 10px; font-weight: bold; color: #64748b; letter-spacing: 0.5px;")
        form_layout.addWidget(email_label)

        self.email_input = QLineEdit(form_frame)
        self.email_input.setPlaceholderText("candidate@trace.edu or username")
        self.email_input.setStyleSheet("""
            QLineEdit {
                background-color: #0b0f19;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #ffffff;
                padding: 10px 12px;
                font-size: 13px;
            }
            QLineEdit:focus { border-color: #6366f1; }
        """)
        form_layout.addWidget(self.email_input)

        # Password
        pass_label = QLabel("PASSWORD", form_frame)
        pass_label.setStyleSheet("font-size: 10px; font-weight: bold; color: #64748b; letter-spacing: 0.5px;")
        form_layout.addWidget(pass_label)

        self.pass_input = QLineEdit(form_frame)
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setPlaceholderText("••••••••")
        self.pass_input.setStyleSheet("""
            QLineEdit {
                background-color: #0b0f19;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #ffffff;
                padding: 10px 12px;
                font-size: 13px;
            }
            QLineEdit:focus { border-color: #6366f1; }
        """)
        self.pass_input.returnPressed.connect(self.handle_online_login)
        form_layout.addWidget(self.pass_input)

        layout.addWidget(form_frame)

        # Status / Feedback label
        self.status_label = QLabel("", self)
        self.status_label.setStyleSheet("font-size: 11px; color: #f59e0b;")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Primary Action: Cloud Sign-In
        self.btn_login = QPushButton("🔐 Sign In & Sync Cloud Vault", self)
        self.btn_login.setStyleSheet("""
            QPushButton {
                background-color: #4f46e5;
                color: #ffffff;
                font-weight: 800;
                font-size: 13px;
                padding: 12px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover { background-color: #4338ca; }
            QPushButton:disabled { background-color: #312e81; color: #64748b; }
        """)
        self.btn_login.clicked.connect(self.handle_online_login)
        layout.addWidget(self.btn_login)

        # Secondary Action: Offline Mode
        self.btn_offline = QPushButton("⚡ Continue in Offline Mode (Local SQLite)", self)
        self.btn_offline.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #334155;
                color: #cbd5e1;
                font-weight: 600;
                font-size: 12px;
                padding: 10px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #ffffff;
            }
        """)
        self.btn_offline.clicked.connect(self.handle_offline_login)
        layout.addWidget(self.btn_offline)

        layout.addStretch()

        # Footer security note
        footer = QLabel("🔒 TRACE dual-source architecture caches data in ~/.local/share/trace/ for zero-latency offline drills.", self)
        footer.setWordWrap(True)
        footer.setStyleSheet("font-size: 10px; color: #64748b; line-height: 1.3;")
        layout.addWidget(footer)

    def handle_online_login(self):
        email = self.email_input.text().strip()
        pwd = self.pass_input.text()
        backend_url = self.url_input.text().strip() or DEFAULT_BACKEND_URL

        if not email or not pwd:
            self.status_label.setText("⚠️ Please enter both email/username and password.")
            return

        self.btn_login.setEnabled(False)
        self.status_label.setText("Connecting to central backend...")
        QApplication.processEvents()

        success, msg, session = TraceRepository.login(email, pwd, backend_url)
        self.btn_login.setEnabled(True)

        if success and session:
            self.status_label.setStyleSheet("font-size: 11px; color: #10b981;")
            self.status_label.setText(f"✅ {msg}")
            self.user_session = session
            self.loginSuccessful.emit(session)
            self.accept()
        else:
            self.status_label.setStyleSheet("font-size: 11px; color: #ef4444;")
            self.status_label.setText(f"❌ {msg}")

    def handle_offline_login(self):
        """Allows instant access via local SQLite session or offline candidate profile."""
        email = self.email_input.text().strip() or "student"
        pwd = self.pass_input.text() or "offline"
        backend_url = self.url_input.text().strip()

        success, msg, session = TraceRepository.login(email, pwd, backend_url)
        if success and session:
            self.user_session = session
            self.loginSuccessful.emit(session)
            self.accept()
        else:
            # Force create an offline candidate profile
            success, msg, session = TraceRepository.login("student", "offline", backend_url)
            if session:
                self.user_session = session
                self.loginSuccessful.emit(session)
                self.accept()
            else:
                self.status_label.setText("Could not initialize local offline session.")
