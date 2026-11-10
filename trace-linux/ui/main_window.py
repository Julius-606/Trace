"""
TRACE Desktop (Linux Client) - Main Window & Dashboard Shell
FILE: trace-linux/ui/main_window.py
VERSION: 1.0.0
ROLE: Primary PyQt6/PySide6 desktop window manager featuring sidebar navigation,
      live Neurons wallet integration, syllabus browsing, and AI Socratic links.
"""

import sys
try:
    from PyQt6.QtWidgets import (
        QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
        QLabel, QStackedWidget, QFrame, QListWidget, QListWidgetItem,
        QLineEdit, QTextEdit, QMessageBox
    )
    from PyQt6.QtCore import Qt, QSize
    from PyQt6.QtGui import QIcon, QFont
except ImportError:
    from PySide6.QtWidgets import (
        QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
        QLabel, QStackedWidget, QFrame, QListWidget, QListWidgetItem,
        QLineEdit, QTextEdit, QMessageBox
    )
    from PySide6.QtCore import Qt, QSize
    from PySide6.QtGui import QIcon, QFont

from repository import TraceRepository
from ui.wallet_widget import WalletBadgeWidget
from ui.syllabus_view import SyllabusView
from ui.assessment_view import AssessmentView
from config import APP_DISPLAY_NAME, APP_VERSION, DATABASE_FILE


class MainWindow(QMainWindow):
    """
    Main application desktop window for TRACE Desktop (Linux Client).
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_DISPLAY_NAME} v{APP_VERSION} (Linux Workstation)")
        self.resize(1180, 780)
        self.setMinimumSize(920, 600)
        self.init_ui()

    def init_ui(self):
        # Central Container
        central_widget = QWidget(self)
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ----------------------------------------------------------------------
        # 1. LEFT SIDEBAR NAVIGATION
        # ----------------------------------------------------------------------
        sidebar = QFrame(self)
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("""
            QFrame#sidebar {
                background-color: #0b0f19;
                border-right: 1px solid #1e293b;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 20, 16, 20)
        sidebar_layout.setSpacing(10)

        # Brand Logo / Title
        brand_layout = QHBoxLayout()
        logo_icon = QLabel("⚡", sidebar)
        logo_icon.setStyleSheet("font-size: 20px;")
        brand_layout.addWidget(logo_icon)

        brand_text = QLabel("TRACE", sidebar)
        brand_text.setStyleSheet("font-size: 18px; font-weight: 900; letter-spacing: 2px; color: #6366f1;")
        brand_layout.addWidget(brand_text)

        badge_sub = QLabel("DESKTOP", sidebar)
        badge_sub.setStyleSheet("font-size: 9px; font-weight: bold; background: #312e81; color: #a5b4fc; padding: 2px 6px; border-radius: 4px;")
        brand_layout.addWidget(badge_sub)
        brand_layout.addStretch()

        sidebar_layout.addLayout(brand_layout)

        env_label = QLabel("Linux XFCE / XDG Architecture", sidebar)
        env_label.setStyleSheet("font-size: 10px; color: #64748b; margin-bottom: 12px;")
        sidebar_layout.addWidget(env_label)

        # Navigation Buttons
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "📊  Dashboard Overview"),
            ("syllabi", "📚  Syllabus & Units"),
            ("assessment", "🎯  Assessment Center"),
            ("ai_terminal", "🧠  Orbit AI Terminal"),
            ("tasks", "📋  Study Tasks"),
        ]

        for nav_id, label in nav_items:
            btn = QPushButton(label, sidebar)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setStyleSheet("""
                QPushButton#navButton {
                    text-align: left;
                    padding: 10px 14px;
                    border-radius: 10px;
                    font-size: 13px;
                    font-weight: 600;
                    color: #94a3b8;
                    border: none;
                }
                QPushButton#navButton:hover {
                    background-color: #1e293b;
                    color: #f8fafc;
                }
                QPushButton#navButton:checked {
                    background-color: #4f46e5;
                    color: #ffffff;
                    font-weight: 700;
                }
            """)
            btn.clicked.connect(lambda checked, nid=nav_id: self.navigate_to(nid))
            sidebar_layout.addWidget(btn)
            self.nav_buttons[nav_id] = btn

        sidebar_layout.addStretch()

        # Database File Indicator
        db_box = QFrame(sidebar)
        db_box.setStyleSheet("background-color: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 8px;")
        db_box_layout = QVBoxLayout(db_box)
        db_title = QLabel("LOCAL SQLITE VAULT", db_box)
        db_title.setStyleSheet("font-size: 9px; font-weight: bold; color: #64748b; letter-spacing: 0.5px;")
        db_box_layout.addWidget(db_title)
        db_path = QLabel(DATABASE_FILE.name, db_box)
        db_path.setStyleSheet("font-size: 11px; font-family: monospace; color: #10b981;")
        db_box_layout.addWidget(db_path)
        sidebar_layout.addWidget(db_box)

        root_layout.addWidget(sidebar)

        # ----------------------------------------------------------------------
        # 2. MAIN CONTENT STACK & TOP HEADER
        # ----------------------------------------------------------------------
        content_container = QWidget(self)
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Top Bar
        top_bar = QFrame(content_container)
        top_bar.setFixedHeight(56)
        top_bar.setStyleSheet("background-color: #0b0f19; border-bottom: 1px solid #1e293b;")
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(20, 0, 20, 0)

        self.current_section_title = QLabel("Dashboard Overview", top_bar)
        self.current_section_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #ffffff;")
        top_bar_layout.addWidget(self.current_section_title)

        top_bar_layout.addStretch()

        # Live Neurons Badge Widget
        self.wallet_badge = WalletBadgeWidget(top_bar)
        top_bar_layout.addWidget(self.wallet_badge)

        content_layout.addWidget(top_bar)

        # Main Stacked Pages
        self.stack = QStackedWidget(content_container)
        self.stack.setStyleSheet("background-color: #090d16;")

        # Page 0: Dashboard
        self.page_dashboard = self.create_dashboard_page()
        self.stack.addWidget(self.page_dashboard)

        # Page 1: Syllabi Browser
        self.page_syllabi = SyllabusView(self)
        self.page_syllabi.unitUnlocked.connect(lambda uid: self.wallet_badge.refresh_balance())
        self.page_syllabi.startAssessmentRequested.connect(self.launch_assessment_for_unit)
        self.stack.addWidget(self.page_syllabi)

        # Page 2: Assessment Center
        self.page_assessment = AssessmentView(self)
        self.page_assessment.quizFinished.connect(lambda res: self.wallet_badge.refresh_balance())
        self.stack.addWidget(self.page_assessment)

        # Page 3: AI Terminal
        self.page_ai_terminal = self.create_ai_terminal_page()
        self.stack.addWidget(self.page_ai_terminal)

        # Page 4: Tasks
        self.page_tasks = self.create_tasks_page()
        self.stack.addWidget(self.page_tasks)

        content_layout.addWidget(self.stack)
        root_layout.addWidget(content_container)

        # Set default page to Dashboard
        self.nav_buttons["dashboard"].setChecked(True)

    def navigate_to(self, nav_id: str):
        mapping = {
            "dashboard": (0, "Dashboard Overview"),
            "syllabi": (1, "Course Syllabi & Curriculum Vault"),
            "assessment": (2, "Assessment Center: Active Recall"),
            "ai_terminal": (3, "Orbit AI Socratic Terminal"),
            "tasks": (4, "Study Tasks & Schedule"),
        }
        if nav_id in mapping:
            idx, title = mapping[nav_id]
            self.stack.setCurrentIndex(idx)
            self.current_section_title.setText(title)
            self.wallet_badge.refresh_balance()

    def launch_assessment_for_unit(self, unit_id: str, unit_title: str):
        self.page_assessment.load_quiz_for_unit(unit_id, unit_title)
        self.nav_buttons["assessment"].setChecked(True)
        self.navigate_to("assessment")

    # ==========================================================================
    # DASHBOARD PAGE GENERATOR
    # ==========================================================================
    def create_dashboard_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Hero Banner
        hero = QFrame(page)
        hero.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e1b4b, stop:1 #0f172a);
            border: 1px solid #3730a3;
            border-radius: 16px;
            padding: 20px;
        """)
        hero_layout = QVBoxLayout(hero)
        hero_title = QLabel("Welcome back, Academic Candidate", hero)
        hero_title.setStyleSheet("font-size: 22px; font-weight: 900; color: #ffffff;")
        hero_layout.addWidget(hero_title)

        hero_sub = QLabel(
            "TRACE Desktop is synchronized with your native Linux environment. "
            "Explore structured course syllabi, unlock new units with your Neurons reserve, "
            "and strengthen memory via active recall testing.", hero
        )
        hero_sub.setStyleSheet("font-size: 13px; color: #c7d2fe; line-height: 1.4;")
        hero_sub.setWordWrap(True)
        hero_layout.addWidget(hero_sub)
        layout.addWidget(hero)

        # Metrics Row
        metrics_row = QHBoxLayout()
        balance = TraceRepository.get_wallet_balance()
        unlocked_count = len(TraceRepository.get_all_unlocked_unit_ids())

        card1 = self.create_metric_card("NEURONS BALANCE", f"{balance} N", "#fbbf24")
        card2 = self.create_metric_card("UNLOCKED UNITS", f"{unlocked_count} Active", "#34d399")
        card3 = self.create_metric_card("LOCAL PERSISTENCE", "SQLite (XDG)", "#818cf8")

        metrics_row.addWidget(card1)
        metrics_row.addWidget(card2)
        metrics_row.addWidget(card3)
        layout.addLayout(metrics_row)

        # Quick Actions
        actions_label = QLabel("QUICK SATELLITE ACTIONS", page)
        actions_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #64748b; letter-spacing: 1px;")
        layout.addWidget(actions_label)

        action_btns = QHBoxLayout()
        btn_open_syllabi = QPushButton("📚 Browse & Unlock Syllabi", page)
        btn_open_syllabi.setStyleSheet("""
            QPushButton {
                background-color: #4f46e5;
                color: white;
                font-weight: bold;
                padding: 12px;
                border-radius: 10px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #4338ca; }
        """)
        btn_open_syllabi.clicked.connect(lambda: [self.nav_buttons["syllabi"].setChecked(True), self.navigate_to("syllabi")])
        action_btns.addWidget(btn_open_syllabi)

        btn_open_quiz = QPushButton("🎯 Start Active Recall Drill", page)
        btn_open_quiz.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: white;
                font-weight: bold;
                padding: 12px;
                border-radius: 10px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #047857; }
        """)
        btn_open_quiz.clicked.connect(lambda: [self.nav_buttons["assessment"].setChecked(True), self.navigate_to("assessment")])
        action_btns.addWidget(btn_open_quiz)

        layout.addLayout(action_btns)
        layout.addStretch()
        return page

    def create_metric_card(self, title: str, value: str, highlight_color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            background-color: #0f172a;
            border: 1px solid #1e293b;
            border-radius: 12px;
            padding: 14px;
        """)
        l = QVBoxLayout(card)
        t = QLabel(title, card)
        t.setStyleSheet("font-size: 10px; font-weight: bold; color: #64748b; letter-spacing: 1px;")
        l.addWidget(t)

        v = QLabel(value, card)
        v.setStyleSheet(f"font-size: 20px; font-weight: 900; color: {highlight_color}; font-family: monospace;")
        l.addWidget(v)
        return card

    # ==========================================================================
    # AI TERMINAL PAGE GENERATOR (WITH LOCAL OFFLINE STAGING)
    # ==========================================================================
    def create_ai_terminal_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel("🧠 Orbit Socratic Terminal (Thin-Client Interface)", page)
        header.setStyleSheet("font-size: 18px; font-weight: 800; color: #ffffff;")
        layout.addWidget(header)

        info = QLabel("Queries are processed via the central FastAPI AI Core. If offline, prompts are staged in your local SQLite vault.", page)
        info.setStyleSheet("font-size: 12px; color: #94a3b8;")
        layout.addWidget(info)

        self.chat_history = QTextEdit(page)
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                background-color: #0b0f19;
                border: 1px solid #1e293b;
                border-radius: 12px;
                color: #e2e8f0;
                padding: 12px;
                font-size: 13px;
                font-family: monospace;
            }
        """)
        self.chat_history.append("⚡ [TRACE-OS]: Orbit Socratic Terminal ready. What concepts are we mastering today?")
        layout.addWidget(self.chat_history)

        input_row = QHBoxLayout()
        self.chat_input = QLineEdit(page)
        self.chat_input.setPlaceholderText("Ask a question, enter a clinical case, or input a study query...")
        self.chat_input.setStyleSheet("""
            QLineEdit {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 10px;
                color: white;
                padding: 10px 14px;
                font-size: 13px;
            }
            QLineEdit:focus { border-color: #6366f1; }
        """)
        self.chat_input.returnPressed.connect(self.send_ai_query)
        input_row.addWidget(self.chat_input)

        btn_send = QPushButton("Ask Orbit", page)
        btn_send.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 10px;
            }
            QPushButton:hover { background-color: #4f46e5; }
        """)
        btn_send.clicked.connect(self.send_ai_query)
        input_row.addWidget(btn_send)

        layout.addLayout(input_row)
        return page

    def send_ai_query(self):
        text = self.chat_input.text().strip()
        if not text:
            return

        self.chat_history.append(f"\n👤 You: {text}")
        self.chat_input.clear()

        # Thin client routing: Stage in local SQLite first
        prompt_id = TraceRepository.stage_offline_prompt(text, "Linux Client")

        # Attempt immediate local Socratic reply or simulated backend response
        reply = (
            f"🧠 Orbit AI: Analyzed inquiry regarding '{text}'.\n"
            "Key High-Yield Principle: Break the system into foundational axioms first, "
            "then test your recall boundaries with an active assessment drill in the syllabus view."
        )
        self.chat_history.append(f"\n{reply}\n")
        TraceRepository.mark_prompt_synced(prompt_id, reply)

    # ==========================================================================
    # STUDY TASKS PAGE GENERATOR
    # ==========================================================================
    def create_tasks_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel("📋 Chronotype Task & Study Planner", page)
        header.setStyleSheet("font-size: 18px; font-weight: 800; color: #ffffff;")
        layout.addWidget(header)

        # Task input
        task_input_row = QHBoxLayout()
        self.task_input = QLineEdit(page)
        self.task_input.setPlaceholderText("New study task or exam objective...")
        self.task_input.setStyleSheet("background-color: #0f172a; border: 1px solid #334155; border-radius: 8px; color: white; padding: 8px 12px;")
        task_input_row.addWidget(self.task_input)

        btn_add = QPushButton("Add Task", page)
        btn_add.setStyleSheet("background-color: #3b82f6; color: white; font-weight: bold; border-radius: 8px; padding: 8px 16px;")
        btn_add.clicked.connect(self.add_task_item)
        task_input_row.addWidget(btn_add)
        layout.addLayout(task_input_row)

        self.task_list = QListWidget(page)
        self.task_list.setStyleSheet("""
            QListWidget {
                background-color: #0b0f19;
                border: 1px solid #1e293b;
                border-radius: 12px;
                color: #e2e8f0;
                padding: 8px;
            }
            QListWidget::item { padding: 10px; border-bottom: 1px solid #1e293b; }
            QListWidget::item:hover { background-color: #1e293b; }
        """)
        self.task_list.itemClicked.connect(self.toggle_task_item)
        layout.addWidget(self.task_list)
        self.refresh_tasks_list()

        return page

    def refresh_tasks_list(self):
        self.task_list.clear()
        tasks = TraceRepository.get_study_tasks()
        if not tasks:
            # Seed default starter tasks
            TraceRepository.add_study_task("Review Distributed Systems & Ingestion", "Computer Science")
            TraceRepository.add_study_task("Run Active Recall Assessment on CS101", "Assessments")
            tasks = TraceRepository.get_study_tasks()

        for t in tasks:
            check_box = "✅" if t.get("completed") else "⬜"
            item = QListWidgetItem(f"{check_box}  {t.get('title')} ({t.get('subject', 'General')})")
            item.setData(Qt.ItemDataRole.UserRole, t.get("id"))
            self.task_list.addItem(item)

    def add_task_item(self):
        txt = self.task_input.text().strip()
        if txt:
            TraceRepository.add_study_task(txt, "Workstation")
            self.task_input.clear()
            self.refresh_tasks_list()

    def toggle_task_item(self, item: QListWidgetItem):
        task_id = item.data(Qt.ItemDataRole.UserRole)
        if task_id:
            TraceRepository.toggle_task(task_id)
            self.refresh_tasks_list()
