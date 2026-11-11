"""
TRACE Desktop (Linux Client) - User Authentication Dialog Wrapper
FILE: trace-linux/ui/login_dialog.py
VERSION: 1.2.0
ROLE: Wraps the Material 3 LoginScreen in a modal dialog container.
"""

try:
    from PyQt6.QtWidgets import QDialog, QVBoxLayout
    from PyQt6.QtCore import Qt, pyqtSignal as Signal
except ImportError:
    from PySide6.QtWidgets import QDialog, QVBoxLayout
    from PySide6.QtCore import Qt, Signal

from ui.login_screen import LoginScreen
from config import APP_DISPLAY_NAME


class LoginDialog(QDialog):
    """
    Modal dialog wrapping LoginScreen for seamless authentication.
    """
    loginSuccessful = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edu-AI Trace - Authentication")
        self.resize(520, 720)
        self.setMinimumSize(480, 640)
        self.setModal(True)
        self.user_session = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.screen = LoginScreen(self)
        self.screen.loginSuccessful.connect(self.on_login_success)
        layout.addWidget(self.screen)

    def on_login_success(self, session: dict):
        self.user_session = session
        self.loginSuccessful.emit(session)
        self.accept()
