"""
TRACE Desktop (Linux Client) - Syllabus Browser & Unit Unlock Cards
FILE: trace-linux/ui/syllabus_view.py
VERSION: 1.0.0
ROLE: Renders hierarchical course trees from local JSON files and backend APIs.
      Provides atomic unit unlocking via Neurons currency transactions.
"""

import json
from pathlib import Path
try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QScrollArea, QFrame, QTreeWidget, QTreeWidgetItem, QMessageBox,
        QSplitter, QHeaderView
    )
    from PyQt6.QtCore import Qt, pyqtSignal as Signal
    from PyQt6.QtGui import QFont, QColor
except ImportError:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QScrollArea, QFrame, QTreeWidget, QTreeWidgetItem, QMessageBox,
        QSplitter, QHeaderView
    )
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QFont, QColor

from repository import TraceRepository
from config import SYLLABI_DIR, DEFAULT_UNIT_PRICE_NEURONS


class SyllabusView(QWidget):
    """
    Syllabus & Curriculum browser with interactive unlock cards and tree drilldowns.
    """
    unitUnlocked = Signal(str) # Emits unit_id upon unlock
    startAssessmentRequested = Signal(str, str) # Emits (unit_id, unit_title)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_syllabi_data = []
        self.init_ui()
        self.load_syllabi_from_disk()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header bar
        header_layout = QHBoxLayout()
        header_title = QLabel("📚 Course Syllabi & Curriculum Vault", self)
        header_title.setStyleSheet("font-size: 20px; font-weight: 800; color: #ffffff;")
        header_layout.addWidget(header_title)

        header_layout.addStretch()

        refresh_btn = QPushButton("🔄 Reload Syllabi", self)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #334155;
                color: #94a3b8;
                padding: 6px 14px;
                border-radius: 8px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #334155; color: white; }
        """)
        refresh_btn.clicked.connect(self.load_syllabi_from_disk)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Splitter: Left side Units list / cards; Right side Module & Topic tree
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet("QSplitter::handle { background-color: #334155; }")

        # Left Panel: Units Scroll Area
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 10, 0)

        left_label = QLabel("DISCIPLINES & UNITS", left_widget)
        left_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #64748b; letter-spacing: 1px;")
        left_layout.addWidget(left_label)

        self.cards_scroll = QScrollArea(left_widget)
        self.cards_scroll.setWidgetResizable(True)
        self.cards_scroll.setStyleSheet("background: transparent; border: none;")

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(12)
        self.cards_layout.addStretch()

        self.cards_scroll.setWidget(self.cards_container)
        left_layout.addWidget(self.cards_scroll)

        splitter.addWidget(left_widget)

        # Right Panel: Module / Topic Explorer Tree
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 0, 0, 0)

        self.detail_title = QLabel("Select a unit to inspect curriculum objectives", right_widget)
        self.detail_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #cbd5e1;")
        right_layout.addWidget(self.detail_title)

        self.tree_widget = QTreeWidget(right_widget)
        self.tree_widget.setHeaderLabels(["Curriculum Hierarchy & Objectives"])
        self.tree_widget.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tree_widget.setStyleSheet("""
            QTreeWidget {
                background-color: #0b0f19;
                border: 1px solid #1e293b;
                border-radius: 12px;
                color: #e2e8f0;
                padding: 10px;
                font-size: 13px;
            }
            QTreeWidget::item { padding: 6px; }
            QTreeWidget::item:hover { background-color: #1e293b; border-radius: 6px; }
            QTreeWidget::item:selected { background-color: #312e81; color: #c7d2fe; }
        """)
        right_layout.addWidget(self.tree_widget)

        # Action bar under tree
        self.action_panel = QFrame(right_widget)
        self.action_panel.setStyleSheet("background-color: #1e293b; border-radius: 10px; padding: 10px;")
        action_layout = QHBoxLayout(self.action_panel)
        action_layout.setContentsMargins(12, 8, 12, 8)

        self.action_info = QLabel("Ready to drill?", self.action_panel)
        self.action_info.setStyleSheet("color: #94a3b8; font-size: 12px;")
        action_layout.addWidget(self.action_info)

        action_layout.addStretch()

        self.btn_take_quiz = QPushButton("🎯 Launch Active Recall Assessment", self.action_panel)
        self.btn_take_quiz.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #4f46e5; }
        """)
        self.btn_take_quiz.clicked.connect(self.on_launch_assessment_clicked)
        self.btn_take_quiz.setEnabled(False)
        action_layout.addWidget(self.btn_take_quiz)

        right_layout.addWidget(self.action_panel)

        splitter.addWidget(right_widget)
        splitter.setSizes([380, 520])

        layout.addWidget(splitter)
        self.selected_unit_data = None

    def load_syllabi_from_disk(self):
        """Scans ~/.local/share/trace/syllabi/ for JSON syllabi and renders cards."""
        self.current_syllabi_data = []

        # Clear existing card widgets
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        syllabi_files = list(SYLLABI_DIR.glob("*.json"))
        # Fallback to local package folder if XDG directory was fresh
        if not syllabi_files:
            fallback_dir = Path(__file__).resolve().parent.parent / "syllabi"
            syllabi_files = list(fallback_dir.glob("*.json"))

        for file_path in syllabi_files:
            try:
                content = json.loads(file_path.read_text(encoding="utf-8"))
                self.current_syllabi_data.append(content)
            except Exception as e:
                print(f"[TRACE] Error parsing {file_path.name}: {e}")

        unlocked_ids = set(TraceRepository.get_all_unlocked_unit_ids())

        for course in self.current_syllabi_data:
            course_title = course.get("course_title", "General Course")
            discipline = course.get("discipline", "Core Discipline")

            for unit in course.get("units", []):
                unit_id = unit.get("unit_id")
                unit_title = unit.get("unit_title")
                cost = unit.get("cost_neurons", DEFAULT_UNIT_PRICE_NEURONS)
                desc = unit.get("description", "")
                is_unlocked = unit_id in unlocked_ids

                card = self.create_unit_card(course, unit, is_unlocked)
                self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def create_unit_card(self, course: dict, unit: dict, is_unlocked: bool) -> QFrame:
        card = QFrame()
        card.setObjectName("unitCard")
        border_color = "#3b82f6" if is_unlocked else "#334155"
        bg_color = "#1e293b" if is_unlocked else "#0f172a"

        card.setStyleSheet(f"""
            QFrame#unitCard {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
                padding: 12px;
            }}
            QFrame#unitCard:hover {{
                border-color: #6366f1;
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(8)

        # Header line with Title + Lock Status Badge
        top_row = QHBoxLayout()
        code_label = QLabel(unit.get("unit_id", "UNIT"), card)
        code_label.setStyleSheet("font-size: 11px; font-weight: 800; color: #818cf8; font-family: monospace;")
        top_row.addWidget(code_label)

        top_row.addStretch()

        status_text = "🔓 UNLOCKED" if is_unlocked else f"🔒 {unit.get('cost_neurons', 20)} N"
        status_color = "#10b981" if is_unlocked else "#f59e0b"
        status_label = QLabel(status_text, card)
        status_label.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {status_color};")
        top_row.addWidget(status_label)

        card_layout.addLayout(top_row)

        # Unit Title
        title_label = QLabel(unit.get("unit_title", "Untitled Unit"), card)
        title_label.setStyleSheet("font-size: 14px; font-weight: 800; color: #ffffff;")
        title_label.setWordWrap(True)
        card_layout.addWidget(title_label)

        # Description
        desc_label = QLabel(unit.get("description", ""), card)
        desc_label.setStyleSheet("font-size: 11px; color: #94a3b8;")
        desc_label.setWordWrap(True)
        card_layout.addWidget(desc_label)

        # Buttons
        btn_row = QHBoxLayout()

        view_btn = QPushButton("Inspect Hierarchy", card)
        view_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #e2e8f0;
                font-size: 11px;
                padding: 6px 12px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        view_btn.clicked.connect(lambda: self.select_unit(unit, is_unlocked))
        btn_row.addWidget(view_btn)

        if not is_unlocked:
            unlock_btn = QPushButton(f"Unlock ({unit.get('cost_neurons', 20)} N)", card)
            unlock_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f59e0b;
                    color: #000000;
                    font-weight: 900;
                    font-size: 11px;
                    padding: 6px 12px;
                    border-radius: 6px;
                }
                QPushButton:hover { background-color: #fbbf24; }
            """)
            unlock_btn.clicked.connect(lambda: self.handle_unlock_request(course.get("course_id", "course"), unit))
            btn_row.addWidget(unlock_btn)

        card_layout.addLayout(btn_row)
        return card

    def select_unit(self, unit: dict, is_unlocked: bool):
        self.selected_unit_data = unit
        unit_title = unit.get("unit_title", "Unit")
        self.detail_title.setText(f"Curriculum Tree: {unit_title}")
        self.tree_widget.clear()

        for mod in unit.get("modules", []):
            mod_item = QTreeWidgetItem(self.tree_widget, [f"📦 Module: {mod.get('module_title')}"])
            mod_item.setExpanded(True)

            for topic in mod.get("topics", []):
                topic_item = QTreeWidgetItem(mod_item, [f"📑 Topic: {topic.get('topic_title')}"])
                topic_item.setExpanded(True)

                for sub in topic.get("subtopics", []):
                    sub_item = QTreeWidgetItem(topic_item, [f"🔹 {sub.get('subtopic_title')}"])
                    for obj in sub.get("objectives", []):
                        QTreeWidgetItem(sub_item, [f"   • {obj}"])

        self.btn_take_quiz.setEnabled(is_unlocked)
        self.action_info.setText("Unit unlocked! Launch active recall quiz." if is_unlocked else "Unit is locked. Spend Neurons to take quizzes.")

    def handle_unlock_request(self, course_id: str, unit: dict):
        unit_id = unit.get("unit_id")
        unit_title = unit.get("unit_title")
        cost = unit.get("cost_neurons", DEFAULT_UNIT_PRICE_NEURONS)

        confirm = QMessageBox.question(
            self,
            "Confirm Unit Unlock",
            f"Unlock '{unit_title}' for {cost} Neurons?\n\nYour wallet balance will be atomically deducted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            success, msg = TraceRepository.unlock_unit(unit_id, course_id, cost, unit_title)
            if success:
                QMessageBox.information(self, "Unit Unlocked", msg)
                self.unitUnlocked.emit(unit_id)
                self.load_syllabi_from_disk()
                if self.selected_unit_data and self.selected_unit_data.get("unit_id") == unit_id:
                    self.select_unit(self.selected_unit_data, True)
            else:
                QMessageBox.warning(self, "Unlock Failed", msg)

    def on_launch_assessment_clicked(self):
        if self.selected_unit_data:
            unit_id = self.selected_unit_data.get("unit_id")
            unit_title = self.selected_unit_data.get("unit_title")
            self.startAssessmentRequested.emit(unit_id, unit_title)
