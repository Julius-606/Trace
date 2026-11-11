"""
TRACE Desktop (Linux Client) - Login & Enrollment Screen
FILE: trace-linux/ui/login_screen.py
VERSION: 1.2.0
ROLE: Full-window authentication and enrollment view matching Android's LoginScreen.kt.
      Provides Material 3 Dark Slate aesthetics, dual tab navigation, in-app signup
      with OTP verification, password reset, and gateway target switching.
"""

import sys
import webbrowser
try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
        QFrame, QScrollArea, QComboBox, QMessageBox, QApplication, QDialog
    )
    from PyQt6.QtCore import Qt, pyqtSignal as Signal
    from PyQt6.QtGui import QFont, QCursor
except ImportError:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
        QFrame, QScrollArea, QComboBox, QMessageBox, QApplication, QDialog
    )
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QFont, QCursor

from repository import TraceRepository, http_post
from config import DEFAULT_BACKEND_URL, CLOUD_BACKEND_URL, APP_DISPLAY_NAME, ENDPOINT_SIGNUP, ENDPOINT_REQUEST_OTP, ENDPOINT_VERIFY_OTP


class LoginScreen(QWidget):
    """
    Dedicated full-window authentication and enrollment view.
    Faithfully replicates Android com.example.edu_ai.ui.screens.LoginScreen.
    """
    loginSuccessful = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("loginScreen")
        self.is_signup_mode = False
        self.is_password_visible = False
        self.is_signup_password_visible = False
        self.backend_url = DEFAULT_BACKEND_URL

        self.init_ui()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Main background scroll area
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: #020617; border: none;")

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(24, 40, 24, 40)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # Center Card Shell (Constrained to max-width 480px)
        self.card_shell = QFrame(container)
        self.card_shell.setFixedWidth(480)
        self.card_shell.setStyleSheet("background: transparent; border: none;")
        card_layout = QVBoxLayout(self.card_shell)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(16)

        # ----------------------------------------------------------------------
        # 1. BRAND HEADER (Matching Android Rounded Badge & Logo)
        # ----------------------------------------------------------------------
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.setSpacing(8)

        # Logo Icon Surface
        logo_frame = QFrame(self.card_shell)
        logo_frame.setFixedSize(68, 68)
        logo_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(99, 102, 241, 0.35), stop:1 rgba(49, 46, 129, 0.6));
                border: 1.5px solid rgba(99, 102, 241, 0.6);
                border-radius: 20px;
            }
        """)
        logo_box = QVBoxLayout(logo_frame)
        logo_box.setContentsMargins(0, 0, 0, 0)
        logo_icon = QLabel("⚡", logo_frame)
        logo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_icon.setStyleSheet("font-size: 30px; background: transparent; border: none;")
        logo_box.addWidget(logo_icon)
        header_layout.addWidget(logo_frame, alignment=Qt.AlignmentFlag.AlignCenter)

        # App Title
        self.title_label = QLabel("Edu-AI Trace", self.card_shell)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 26px; font-weight: 900; letter-spacing: -0.5px; color: #6366f1;")
        header_layout.addWidget(self.title_label)

        # Subtitle
        self.subtitle_label = QLabel("Sign in to access your workspace", self.card_shell)
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setStyleSheet("font-size: 13px; color: #94a3b8;")
        header_layout.addWidget(self.subtitle_label)

        card_layout.addLayout(header_layout)

        # ----------------------------------------------------------------------
        # 2. NAVIGATION TOGGLE TABS ([ SIGN IN ] vs [ SIGN UP (WEB) ↗ ])
        # ----------------------------------------------------------------------
        tab_surface = QFrame(self.card_shell)
        tab_surface.setFixedHeight(48)
        tab_surface.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 14px;
                padding: 3px;
            }
        """)
        tab_layout = QHBoxLayout(tab_surface)
        tab_layout.setContentsMargins(4, 4, 4, 4)
        tab_layout.setSpacing(6)

        self.tab_signin = QPushButton("SIGN IN", tab_surface)
        self.tab_signin.setFixedHeight(38)
        self.tab_signin.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tab_signin.setStyleSheet("""
            QPushButton {
                background-color: #4f46e5;
                color: #ffffff;
                font-weight: 800;
                font-size: 13px;
                border-radius: 10px;
                border: none;
            }
        """)
        self.tab_signin.clicked.connect(self.switch_to_signin_mode)
        tab_layout.addWidget(self.tab_signin)

        self.tab_signup_web = QPushButton("SIGN UP (WEB) ↗", tab_surface)
        self.tab_signup_web.setFixedHeight(38)
        self.tab_signup_web.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tab_signup_web.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #818cf8;
                font-weight: 700;
                font-size: 12px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1e293b;
                color: #ffffff;
            }
        """)
        self.tab_signup_web.clicked.connect(self.open_web_signup)
        tab_layout.addWidget(self.tab_signup_web)

        card_layout.addWidget(tab_surface)

        # In-App Registration Sub-link
        self.mode_toggle_btn = QPushButton("Need in-app registration? Switch to in-app form", self.card_shell)
        self.mode_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mode_toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #64748b;
                font-size: 11px;
                padding: 2px;
            }
            QPushButton:hover {
                color: #94a3b8;
                text-decoration: underline;
            }
        """)
        self.mode_toggle_btn.clicked.connect(self.toggle_signup_in_app)
        card_layout.addWidget(self.mode_toggle_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # ----------------------------------------------------------------------
        # 3. ALERT BANNERS (Error & Success Alerts)
        # ----------------------------------------------------------------------
        self.error_banner = QFrame(self.card_shell)
        self.error_banner.setStyleSheet("""
            QFrame {
                background-color: rgba(239, 68, 68, 0.15);
                border: 1px solid rgba(239, 68, 68, 0.4);
                border-radius: 12px;
                padding: 10px;
            }
        """)
        error_layout = QHBoxLayout(self.error_banner)
        error_layout.setContentsMargins(10, 8, 10, 8)
        error_icon = QLabel("⚠️", self.error_banner)
        error_icon.setStyleSheet("font-size: 14px; background: transparent; border: none;")
        error_layout.addWidget(error_icon)
        self.error_label = QLabel("", self.error_banner)
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet("color: #fca5a5; font-size: 12px; font-weight: 600; background: transparent; border: none;")
        error_layout.addWidget(self.error_label, 1)
        self.error_banner.setVisible(False)
        card_layout.addWidget(self.error_banner)

        self.success_banner = QFrame(self.card_shell)
        self.success_banner.setStyleSheet("""
            QFrame {
                background-color: rgba(16, 185, 129, 0.15);
                border: 1px solid rgba(16, 185, 129, 0.4);
                border-radius: 12px;
                padding: 10px;
            }
        """)
        success_layout = QHBoxLayout(self.success_banner)
        success_layout.setContentsMargins(10, 8, 10, 8)
        success_icon = QLabel("✅", self.success_banner)
        success_icon.setStyleSheet("font-size: 14px; background: transparent; border: none;")
        success_layout.addWidget(success_icon)
        self.success_label = QLabel("", self.success_banner)
        self.success_label.setWordWrap(True)
        self.success_label.setStyleSheet("color: #6ee7b7; font-size: 12px; font-weight: 700; background: transparent; border: none;")
        success_layout.addWidget(self.success_label, 1)
        self.success_banner.setVisible(False)
        card_layout.addWidget(self.success_banner)

        # ----------------------------------------------------------------------
        # 4. FORM CARD CONTAINER
        # ----------------------------------------------------------------------
        self.form_card = QFrame(self.card_shell)
        self.form_card.setStyleSheet("""
            QFrame#formCard {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 20px;
            }
        """)
        self.form_card.setObjectName("formCard")
        self.form_layout = QVBoxLayout(self.form_card)
        self.form_layout.setContentsMargins(24, 24, 24, 24)
        self.form_layout.setSpacing(14)

        # --- SIGN IN WIDGETS ---
        self.signin_container = QWidget(self.form_card)
        signin_layout = QVBoxLayout(self.signin_container)
        signin_layout.setContentsMargins(0, 0, 0, 0)
        signin_layout.setSpacing(14)

        # Field: Email / Username
        lbl_email = QLabel("Email Address or Username", self.signin_container)
        lbl_email.setStyleSheet("font-size: 12px; font-weight: bold; color: #cbd5e1;")
        signin_layout.addWidget(lbl_email)

        self.input_email = QLineEdit(self.signin_container)
        self.input_email.setPlaceholderText("candidate@trace.edu or username")
        self.input_email.setFixedHeight(46)
        self.input_email.setStyleSheet("""
            QLineEdit {
                background-color: #0b0f19;
                border: 1.5px solid #334155;
                border-radius: 12px;
                color: #ffffff;
                font-size: 13px;
                padding: 10px 14px;
            }
            QLineEdit:focus { border: 1.5px solid #6366f1; background-color: #0b0f19; }
        """)
        signin_layout.addWidget(self.input_email)

        # Field: Password
        lbl_pass = QLabel("Password", self.signin_container)
        lbl_pass.setStyleSheet("font-size: 12px; font-weight: bold; color: #cbd5e1;")
        signin_layout.addWidget(lbl_pass)

        pass_row = QHBoxLayout()
        pass_row.setSpacing(8)
        self.input_pass = QLineEdit(self.signin_container)
        self.input_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_pass.setPlaceholderText("••••••••")
        self.input_pass.setFixedHeight(46)
        self.input_pass.setStyleSheet("""
            QLineEdit {
                background-color: #0b0f19;
                border: 1.5px solid #334155;
                border-radius: 12px;
                color: #ffffff;
                font-size: 13px;
                padding: 10px 14px;
            }
            QLineEdit:focus { border: 1.5px solid #6366f1; background-color: #0b0f19; }
        """)
        self.input_pass.returnPressed.connect(self.handle_signin)
        pass_row.addWidget(self.input_pass, 1)

        self.btn_toggle_pass = QPushButton("👁️", self.signin_container)
        self.btn_toggle_pass.setFixedSize(46, 46)
        self.btn_toggle_pass.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_pass.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 1.5px solid #334155;
                border-radius: 12px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #334155; }
        """)
        self.btn_toggle_pass.clicked.connect(self.toggle_password_visibility)
        pass_row.addWidget(self.btn_toggle_pass)
        signin_layout.addLayout(pass_row)

        # Forgot Password Link (aligned right)
        forgot_row = QHBoxLayout()
        forgot_row.addStretch()
        btn_forgot = QPushButton("Forgot password?", self.signin_container)
        btn_forgot.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_forgot.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #818cf8;
                font-weight: bold;
                font-size: 12px;
                padding: 2px 4px;
            }
            QPushButton:hover { color: #a5b4fc; text-decoration: underline; }
        """)
        btn_forgot.clicked.connect(self.open_forgot_password_modal)
        forgot_row.addWidget(btn_forgot)
        signin_layout.addLayout(forgot_row)

        # Submit Sign In Button
        self.btn_signin_submit = QPushButton("SIGN IN", self.signin_container)
        self.btn_signin_submit.setFixedHeight(48)
        self.btn_signin_submit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_signin_submit.setStyleSheet("""
            QPushButton {
                background-color: #4f46e5;
                color: #ffffff;
                font-weight: 800;
                font-size: 14px;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover { background-color: #4338ca; }
            QPushButton:disabled { background-color: #312e81; color: #64748b; }
        """)
        self.btn_signin_submit.clicked.connect(self.handle_signin)
        signin_layout.addWidget(self.btn_signin_submit)

        # Open Web Portal Sign Up Button
        btn_web_portal = QPushButton("New Student? Register on Web Portal ↗", self.signin_container)
        btn_web_portal.setFixedHeight(42)
        btn_web_portal.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_web_portal.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #334155;
                border-radius: 12px;
                color: #cbd5e1;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #1e293b; color: #ffffff; border-color: #475569; }
        """)
        btn_web_portal.clicked.connect(self.open_web_signup)
        signin_layout.addWidget(btn_web_portal)

        # Continue Offline Button
        btn_offline = QPushButton("⚡ Continue in Offline Mode (Local SQLite)", self.signin_container)
        btn_offline.setFixedHeight(42)
        btn_offline.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_offline.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 12px;
                color: #94a3b8;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #334155; color: #ffffff; }
        """)
        btn_offline.clicked.connect(self.handle_offline_login)
        signin_layout.addWidget(btn_offline)

        self.form_layout.addWidget(self.signin_container)

        # --- SIGN UP IN-APP WIDGETS ---
        self.signup_container = QWidget(self.form_card)
        signup_layout = QVBoxLayout(self.signup_container)
        signup_layout.setContentsMargins(0, 0, 0, 0)
        signup_layout.setSpacing(12)

        lbl_reg_title = QLabel("New Student Enrollment", self.signup_container)
        lbl_reg_title.setStyleSheet("font-size: 15px; font-weight: 900; color: #6366f1;")
        signup_layout.addWidget(lbl_reg_title)

        # 1. Full Name
        lbl_s_name = QLabel("1. Full Name", self.signup_container)
        lbl_s_name.setStyleSheet("font-size: 11px; font-weight: bold; color: #94a3b8;")
        signup_layout.addWidget(lbl_s_name)
        self.input_s_name = QLineEdit(self.signup_container)
        self.input_s_name.setPlaceholderText("e.g. Dr. Julius Kiptoo")
        self.input_s_name.setFixedHeight(42)
        signup_layout.addWidget(self.input_s_name)

        # 2. Email Address with Send OTP
        lbl_s_email = QLabel("2. Email Address", self.signup_container)
        lbl_s_email.setStyleSheet("font-size: 11px; font-weight: bold; color: #94a3b8;")
        signup_layout.addWidget(lbl_s_email)

        s_email_row = QHBoxLayout()
        self.input_s_email = QLineEdit(self.signup_container)
        self.input_s_email.setPlaceholderText("student@university.edu")
        self.input_s_email.setFixedHeight(42)
        s_email_row.addWidget(self.input_s_email, 1)

        self.btn_send_otp = QPushButton("Send OTP", self.signup_container)
        self.btn_send_otp.setFixedHeight(42)
        self.btn_send_otp.setStyleSheet("""
            QPushButton {
                background-color: #4f46e5;
                color: white;
                font-size: 11px;
                font-weight: bold;
                padding: 6px 14px;
                border-radius: 10px;
            }
            QPushButton:hover { background-color: #4338ca; }
        """)
        self.btn_send_otp.clicked.connect(self.handle_send_signup_otp)
        s_email_row.addWidget(self.btn_send_otp)
        signup_layout.addLayout(s_email_row)

        # 3. 6-Digit OTP
        lbl_s_otp = QLabel("3. 6-Digit Verification Code", self.signup_container)
        lbl_s_otp.setStyleSheet("font-size: 11px; font-weight: bold; color: #94a3b8;")
        signup_layout.addWidget(lbl_s_otp)
        self.input_s_otp = QLineEdit(self.signup_container)
        self.input_s_otp.setPlaceholderText("e.g. 123456")
        self.input_s_otp.setFixedHeight(42)
        signup_layout.addWidget(self.input_s_otp)

        # 4. Password
        lbl_s_pass = QLabel("4. Security Password", self.signup_container)
        lbl_s_pass.setStyleSheet("font-size: 11px; font-weight: bold; color: #94a3b8;")
        signup_layout.addWidget(lbl_s_pass)
        self.input_s_pass = QLineEdit(self.signup_container)
        self.input_s_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_s_pass.setPlaceholderText("At least 6 characters")
        self.input_s_pass.setFixedHeight(42)
        signup_layout.addWidget(self.input_s_pass)

        # 5. Level of Study
        lbl_s_level = QLabel("5. Level of Study", self.signup_container)
        lbl_s_level.setStyleSheet("font-size: 11px; font-weight: bold; color: #94a3b8;")
        signup_layout.addWidget(lbl_s_level)

        self.combo_s_level = QComboBox(self.signup_container)
        self.combo_s_level.setFixedHeight(42)
        self.combo_s_level.setStyleSheet("""
            QComboBox {
                background-color: #0b0f19;
                border: 1.5px solid #334155;
                border-radius: 10px;
                color: #ffffff;
                padding: 6px 12px;
                font-size: 12px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #0f172a;
                color: #ffffff;
                selection-background-color: #4f46e5;
            }
        """)
        self.combo_s_level.addItems([
            "Year 1 - Foundational Studies",
            "Year 2 - Core Disciplines",
            "Year 3 - Advanced Theory & Practicum",
            "Year 4 - Advanced Candidate / Capstone",
            "Year 5 - Final Year Candidate",
            "Postgraduate / Research & Fellowship"
        ])
        self.combo_s_level.setCurrentIndex(3)
        signup_layout.addWidget(self.combo_s_level)

        # 6. Course Pursued
        lbl_s_course = QLabel("6. Course / Discipline Pursued", self.signup_container)
        lbl_s_course.setStyleSheet("font-size: 11px; font-weight: bold; color: #94a3b8;")
        signup_layout.addWidget(lbl_s_course)
        self.input_s_course = QLineEdit(self.signup_container)
        self.input_s_course.setText("Computer Science & Engineering")
        self.input_s_course.setFixedHeight(42)
        signup_layout.addWidget(self.input_s_course)

        # Submit Create Account
        self.btn_signup_submit = QPushButton("CREATE ACCOUNT & SYNC", self.signup_container)
        self.btn_signup_submit.setFixedHeight(48)
        self.btn_signup_submit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_signup_submit.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: #ffffff;
                font-weight: 800;
                font-size: 14px;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover { background-color: #047857; }
        """)
        self.btn_signup_submit.clicked.connect(self.handle_signup_submit)
        signup_layout.addWidget(self.btn_signup_submit)

        self.signup_container.setVisible(False)
        self.form_layout.addWidget(self.signup_container)

        card_layout.addWidget(self.form_card)

        # ----------------------------------------------------------------------
        # 5. BACKEND GATEWAY SELECTOR (Matching Android Bottom Row)
        # ----------------------------------------------------------------------
        gateway_box = QFrame(self.card_shell)
        gateway_box.setStyleSheet("background: transparent; border: none;")
        gateway_layout = QVBoxLayout(gateway_box)
        gateway_layout.setContentsMargins(0, 8, 0, 0)
        gateway_layout.setSpacing(6)

        lbl_gw = QLabel("Backend Gateway Target", gateway_box)
        lbl_gw.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_gw.setStyleSheet("font-size: 11px; font-weight: bold; color: #64748b;")
        gateway_layout.addWidget(lbl_gw)

        gw_btn_row = QHBoxLayout()
        gw_btn_row.setSpacing(6)

        self.btn_gw_local = QPushButton("Local (7860)", gateway_box)
        self.btn_gw_local.setFixedHeight(34)
        self.btn_gw_local.setCheckable(True)
        self.btn_gw_local.setChecked(True)
        self.btn_gw_local.setStyleSheet(self._gw_btn_style(True))
        self.btn_gw_local.clicked.connect(lambda: self.select_gateway("local"))
        gw_btn_row.addWidget(self.btn_gw_local)

        self.btn_gw_cloud = QPushButton("Cloud Vault", gateway_box)
        self.btn_gw_cloud.setFixedHeight(34)
        self.btn_gw_cloud.setCheckable(True)
        self.btn_gw_cloud.setStyleSheet(self._gw_btn_style(False))
        self.btn_gw_cloud.clicked.connect(lambda: self.select_gateway("cloud"))
        gw_btn_row.addWidget(self.btn_gw_cloud)

        self.btn_gw_custom = QPushButton("Custom URL", gateway_box)
        self.btn_gw_custom.setFixedHeight(34)
        self.btn_gw_custom.setCheckable(True)
        self.btn_gw_custom.setStyleSheet(self._gw_btn_style(False))
        self.btn_gw_custom.clicked.connect(lambda: self.select_gateway("custom"))
        gw_btn_row.addWidget(self.btn_gw_custom)

        gateway_layout.addLayout(gw_btn_row)

        self.input_custom_url = QLineEdit(DEFAULT_BACKEND_URL, gateway_box)
        self.input_custom_url.setFixedHeight(36)
        self.input_custom_url.setStyleSheet("""
            QLineEdit {
                background-color: #0b0f19;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #38bdf8;
                font-family: monospace;
                font-size: 11px;
                padding: 6px 10px;
            }
        """)
        self.input_custom_url.setVisible(False)
        self.input_custom_url.textChanged.connect(lambda t: setattr(self, "backend_url", t.strip()))
        gateway_layout.addWidget(self.input_custom_url)

        card_layout.addWidget(gateway_box)

        # Footer security note
        footer = QLabel("🔒 TRACE local vault stores cached data in ~/.local/share/trace/ for zero-latency offline study.", self.card_shell)
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setWordWrap(True)
        footer.setStyleSheet("font-size: 10px; color: #475569; margin-top: 10px;")
        card_layout.addWidget(footer)

        container_layout.addWidget(self.card_shell)
        scroll.setWidget(container)
        root_layout.addWidget(scroll)

    def _gw_btn_style(self, selected: bool) -> str:
        if selected:
            return """
                QPushButton {
                    background-color: rgba(99, 102, 241, 0.25);
                    border: 1.5px solid #6366f1;
                    color: #a5b4fc;
                    font-size: 11px;
                    font-weight: bold;
                    border-radius: 8px;
                }
            """
        return """
            QPushButton {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                color: #64748b;
                font-size: 11px;
                font-weight: 600;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #1e293b;
                color: #94a3b8;
            }
        """

    def select_gateway(self, mode: str):
        self.btn_gw_local.setChecked(mode == "local")
        self.btn_gw_cloud.setChecked(mode == "cloud")
        self.btn_gw_custom.setChecked(mode == "custom")

        self.btn_gw_local.setStyleSheet(self._gw_btn_style(mode == "local"))
        self.btn_gw_cloud.setStyleSheet(self._gw_btn_style(mode == "cloud"))
        self.btn_gw_custom.setStyleSheet(self._gw_btn_style(mode == "custom"))

        if mode == "local":
            self.backend_url = DEFAULT_BACKEND_URL
            self.input_custom_url.setVisible(False)
        elif mode == "cloud":
            self.backend_url = CLOUD_BACKEND_URL
            self.input_custom_url.setVisible(False)
        else:
            self.backend_url = self.input_custom_url.text().strip() or DEFAULT_BACKEND_URL
            self.input_custom_url.setVisible(True)

    def switch_to_signin_mode(self):
        self.is_signup_mode = False
        self.tab_signin.setStyleSheet("""
            QPushButton {
                background-color: #4f46e5;
                color: #ffffff;
                font-weight: 800;
                font-size: 13px;
                border-radius: 10px;
                border: none;
            }
        """)
        self.tab_signup_web.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #818cf8;
                font-weight: 700;
                font-size: 12px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover { background-color: #1e293b; color: #ffffff; }
        """)
        self.signin_container.setVisible(True)
        self.signup_container.setVisible(False)
        self.subtitle_label.setText("Sign in to access your workspace")
        self.mode_toggle_btn.setText("Need in-app registration? Switch to in-app form")
        self.clear_alerts()

    def toggle_signup_in_app(self):
        if not self.is_signup_mode:
            self.is_signup_mode = True
            self.signin_container.setVisible(False)
            self.signup_container.setVisible(True)
            self.subtitle_label.setText("Enroll in Adaptive Academic Vault")
            self.mode_toggle_btn.setText("← Back to standard Sign In")
        else:
            self.switch_to_signin_mode()
        self.clear_alerts()

    def open_web_signup(self):
        url = f"{self.backend_url.rstrip('/')}/signup"
        try:
            webbrowser.open(url)
            self.show_success(f"Opened web registration portal in browser: {url}")
        except Exception as e:
            self.show_error(f"Could not open browser: {e}")

    def toggle_password_visibility(self):
        self.is_password_visible = not self.is_password_visible
        if self.is_password_visible:
            self.input_pass.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle_pass.setText("🙈")
        else:
            self.input_pass.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle_pass.setText("👁️")

    def show_error(self, message: str):
        self.error_label.setText(message)
        self.error_banner.setVisible(True)
        self.success_banner.setVisible(False)

    def show_success(self, message: str):
        self.success_label.setText(message)
        self.success_banner.setVisible(True)
        self.error_banner.setVisible(False)

    def clear_alerts(self):
        self.error_banner.setVisible(False)
        self.success_banner.setVisible(False)

    def handle_signin(self):
        email = self.input_email.text().strip()
        pwd = self.input_pass.text()

        if not email or not pwd:
            self.show_error("Please enter both email/username and password.")
            return

        self.clear_alerts()
        self.btn_signin_submit.setEnabled(False)
        self.btn_signin_submit.setText("Signing in...")
        QApplication.processEvents()

        success, msg, session = TraceRepository.login(email, pwd, self.backend_url)
        self.btn_signin_submit.setEnabled(True)
        self.btn_signin_submit.setText("SIGN IN")

        if success and session:
            self.show_success(f"Authenticated successfully as {session.get('username')}.")
            self.loginSuccessful.emit(session)
        else:
            self.show_error(msg)

    def handle_offline_login(self):
        email = self.input_email.text().strip() or "student"
        pwd = self.input_pass.text() or "offline"

        success, msg, session = TraceRepository.login(email, pwd, self.backend_url)
        if success and session:
            self.show_success("Loaded local offline workstation session.")
            self.loginSuccessful.emit(session)
        else:
            # Force guest offline profile
            success, msg, session = TraceRepository.login("student", "offline", self.backend_url)
            if session:
                self.show_success("Started session as local Candidate.")
                self.loginSuccessful.emit(session)
            else:
                self.show_error("Could not initialize local offline session.")

    def handle_send_signup_otp(self):
        email = self.input_s_email.text().strip()
        if not email or "@" not in email:
            self.show_error("Please enter a valid email address to receive verification OTP.")
            return

        self.btn_send_otp.setEnabled(False)
        self.btn_send_otp.setText("Sending...")
        QApplication.processEvents()

        try:
            url = f"{self.backend_url.rstrip('/')}{ENDPOINT_REQUEST_OTP}"
            resp = http_post(url, json_data={"email": email, "action": "signup"}, timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                preview = data.get("otp_preview")
                if preview:
                    self.input_s_otp.setText(str(preview))
                    self.show_success(f"OTP dispatched! [Preview: {preview}]")
                else:
                    self.show_success(f"6-digit OTP code sent to {email}.")
            else:
                self.show_error(f"Failed to dispatch OTP: {resp.text}")
        except Exception as e:
            self.show_error(f"Network error requesting OTP: {e}")
        finally:
            self.btn_send_otp.setEnabled(True)
            self.btn_send_otp.setText("Send OTP")

    def handle_signup_submit(self):
        name = self.input_s_name.text().strip()
        email = self.input_s_email.text().strip()
        otp = self.input_s_otp.text().strip()
        pwd = self.input_s_pass.text().strip()
        level = self.combo_s_level.currentText()
        course = self.input_s_course.text().strip()

        if not name:
            self.show_error("Please enter your Full Name.")
            return
        if not email or "@" not in email:
            self.show_error("Please enter a valid email address.")
            return
        if not otp:
            self.show_error("Please enter the 6-digit verification code.")
            return
        if len(pwd) < 6:
            self.show_error("Security password must be at least 6 characters.")
            return

        self.btn_signup_submit.setEnabled(False)
        self.btn_signup_submit.setText("Registering...")
        QApplication.processEvents()

        payload = {
            "fullName": name,
            "email": email,
            "password": pwd,
            "otp": otp,
            "levelOfStudy": level,
            "coursePursued": course,
            "role": "Student"
        }

        try:
            url = f"{self.backend_url.rstrip('/')}{ENDPOINT_SIGNUP}"
            resp = http_post(url, json_data=payload, timeout=6.0)
            if resp.status_code == 200:
                self.show_success("Account created successfully! Signing in...")
                # Automatic login
                ok, msg, session = TraceRepository.login(email, pwd, self.backend_url)
                if ok and session:
                    self.loginSuccessful.emit(session)
            else:
                self.show_error(f"Registration failed: {resp.text}")
        except Exception as e:
            self.show_error(f"Network error during registration: {e}")
        finally:
            self.btn_signup_submit.setEnabled(True)
            self.btn_signup_submit.setText("CREATE ACCOUNT & SYNC")

    def open_forgot_password_modal(self):
        modal = ForgotPasswordModal(self.backend_url, self)
        modal.exec()


class ForgotPasswordModal(QDialog):
    """Reset password modal dialog replicating Android's showForgotPasswordDialog."""
    def __init__(self, backend_url: str, parent=None):
        super().__init__(parent)
        self.backend_url = backend_url
        self.setWindowTitle("Reset Password - TRACE")
        self.setFixedSize(420, 480)
        self.setStyleSheet("background-color: #0f172a; color: #f8fafc;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # Header
        title = QLabel("🔒 Reset Password", self)
        title.setStyleSheet("font-size: 18px; font-weight: 900; color: #ffffff;")
        layout.addWidget(title)

        desc = QLabel("Enter your registered email address to receive a secure one-time verification code (OTP) and set a new password.", self)
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 11px; color: #94a3b8; line-height: 1.4;")
        layout.addWidget(desc)

        # Feedback label
        self.lbl_status = QLabel("", self)
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setStyleSheet("font-size: 11px; color: #f59e0b;")
        layout.addWidget(self.lbl_status)

        # Email + Send OTP
        lbl_em = QLabel("Account Email", self)
        lbl_em.setStyleSheet("font-size: 11px; font-weight: bold; color: #cbd5e1;")
        layout.addWidget(lbl_em)

        em_row = QHBoxLayout()
        self.txt_email = QLineEdit(self)
        self.txt_email.setPlaceholderText("candidate@trace.edu")
        self.txt_email.setFixedHeight(40)
        em_row.addWidget(self.txt_email, 1)

        self.btn_otp = QPushButton("Send OTP", self)
        self.btn_otp.setFixedHeight(40)
        self.btn_otp.setStyleSheet("""
            QPushButton {
                background-color: #4f46e5;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #4338ca; }
        """)
        self.btn_otp.clicked.connect(self.request_otp)
        em_row.addWidget(self.btn_otp)
        layout.addLayout(em_row)

        # OTP Code
        lbl_code = QLabel("6-Digit Verification Code", self)
        lbl_code.setStyleSheet("font-size: 11px; font-weight: bold; color: #cbd5e1;")
        layout.addWidget(lbl_code)
        self.txt_otp = QLineEdit(self)
        self.txt_otp.setPlaceholderText("e.g. 123456")
        self.txt_otp.setFixedHeight(40)
        layout.addWidget(self.txt_otp)

        # New Password
        lbl_pwd = QLabel("New Password", self)
        lbl_pwd.setStyleSheet("font-size: 11px; font-weight: bold; color: #cbd5e1;")
        layout.addWidget(lbl_pwd)
        self.txt_pwd = QLineEdit(self)
        self.txt_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_pwd.setPlaceholderText("At least 6 characters")
        self.txt_pwd.setFixedHeight(40)
        layout.addWidget(self.txt_pwd)

        layout.addStretch()

        # Action buttons
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel", self)
        btn_cancel.setFixedHeight(40)
        btn_cancel.setStyleSheet("background-color: #334155; color: white; border-radius: 8px;")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_submit = QPushButton("Reset Password", self)
        btn_submit.setFixedHeight(40)
        btn_submit.setStyleSheet("background-color: #059669; color: white; font-weight: bold; border-radius: 8px;")
        btn_submit.clicked.connect(self.submit_reset)
        btn_row.addWidget(btn_submit)

        layout.addLayout(btn_row)

    def request_otp(self):
        em = self.txt_email.text().strip()
        if not em or "@" not in em:
            self.lbl_status.setText("Please enter a valid email.")
            return

        self.btn_otp.setEnabled(False)
        self.lbl_status.setText("Sending reset code...")
        QApplication.processEvents()

        try:
            url = f"{self.backend_url.rstrip('/')}{ENDPOINT_REQUEST_OTP}"
            resp = http_post(url, json_data={"email": em, "action": "forgot_password"}, timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                preview = data.get("otp_preview")
                if preview:
                    self.txt_otp.setText(str(preview))
                    self.lbl_status.setText(f"Code sent! [Preview: {preview}]")
                else:
                    self.lbl_status.setText(f"Reset code sent to {em}.")
            else:
                self.lbl_status.setText("Failed to dispatch code.")
        except Exception as e:
            self.lbl_status.setText(f"Network error: {e}")
        finally:
            self.btn_otp.setEnabled(True)

    def submit_reset(self):
        em = self.txt_email.text().strip()
        code = self.txt_otp.text().strip()
        pwd = self.txt_pwd.text().strip()

        if not em or not code or len(pwd) < 6:
            self.lbl_status.setText("Fill all fields (password >= 6 chars).")
            return

        try:
            url = f"{self.backend_url.rstrip('/')}/api/auth/forgot-password/reset"
            resp = http_post(url, json_data={"email": em, "otp": code, "newPassword": pwd}, timeout=5.0)
            if resp.status_code == 200:
                QMessageBox.information(self, "Success", "Password reset successfully! Please sign in with your new password.")
                self.accept()
            else:
                self.lbl_status.setText(f"Reset failed: {resp.text}")
        except Exception as e:
            self.lbl_status.setText(f"Error: {e}")
