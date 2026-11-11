"""
TRACE Desktop (Linux Client) - Saved Highlights & Bookmarks View
FILE: trace-linux/ui/bookmarks_view.py
VERSION: 1.0.0
ROLE: Manages saved highlights, academic excerpts, and notes matching
      Android's BookmarksScreen.kt. Supports categorization, full-text
      search filtering, and jumping directly back into the learning reader.
"""

import sys
try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QScrollArea, QFrame, QLineEdit, QComboBox, QMessageBox,
        QDialog, QTextEdit
    )
    from PyQt6.QtCore import Qt, pyqtSignal as Signal
    from PyQt6.QtGui import QFont, QCursor
except ImportError:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QScrollArea, QFrame, QLineEdit, QComboBox, QMessageBox,
        QDialog, QTextEdit
    )
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QFont, QCursor

from repository import TraceRepository


class AddBookmarkDialog(QDialog):
    """Dialog allowing users to manually create an academic note or clip."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save New Clip / Bookmark")
        self.setFixedSize(480, 380)
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 14px;
            }
            QLabel { color: #f8fafc; font-size: 13px; font-weight: bold; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Clip Title / Concept:", self))
        self.input_title = QLineEdit(self)
        self.input_title.setPlaceholderText("e.g. Asynchronous Task Queue Decoupling")
        self.input_title.setStyleSheet("background: #0b0f19; border: 1px solid #334155; border-radius: 8px; color: white; padding: 8px 12px;")
        layout.addWidget(self.input_title)

        layout.addWidget(QLabel("Category Tag:", self))
        self.combo_cat = QComboBox(self)
        self.combo_cat.addItems(["Syllabus", "Clinical Pearl", "Engineering Note", "Exam Objective"])
        self.combo_cat.setStyleSheet("background: #0b0f19; border: 1px solid #334155; border-radius: 8px; color: white; padding: 6px 12px;")
        layout.addWidget(self.combo_cat)

        layout.addWidget(QLabel("Key Quote / Snippet:", self))
        self.input_snippet = QTextEdit(self)
        self.input_snippet.setPlaceholderText("Paste text excerpt or core takeaway here...")
        self.input_snippet.setStyleSheet("background: #0b0f19; border: 1px solid #334155; border-radius: 8px; color: white; padding: 8px;")
        self.input_snippet.setFixedHeight(90)
        layout.addWidget(self.input_snippet)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel", self)
        btn_cancel.setStyleSheet("background: #1e293b; color: #94a3b8; border-radius: 8px; padding: 8px 16px;")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_save = QPushButton("Save Bookmark", self)
        btn_save.setStyleSheet("background: #4f46e5; color: white; font-weight: bold; border-radius: 8px; padding: 8px 16px;")
        btn_save.clicked.connect(self.accept)
        btn_row.addWidget(btn_save)

        layout.addLayout(btn_row)

    def get_data(self) -> dict:
        return {
            "title": self.input_title.text().strip() or "Untitled Bookmark",
            "category": self.combo_cat.currentText(),
            "snippet": self.input_snippet.toPlainText().strip()
        }


class BookmarkCard(QFrame):
    """Visual card representing a saved academic clip or highlight."""
    def __init__(self, bookmark: dict, on_open, on_delete, parent=None):
        super().__init__(parent)
        self.bookmark = bookmark
        self.on_open = on_open
        self.on_delete = on_delete

        self.setStyleSheet("""
            QFrame#bookmarkCard {
                background-color: #0b0f19;
                border: 1px solid #1e293b;
                border-radius: 14px;
                padding: 16px;
            }
            QFrame#bookmarkCard:hover {
                border-color: #3b82f6;
                background-color: #0f172a;
            }
        """)
        self.setObjectName("bookmarkCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Top row: Title + Category pill
        top_row = QHBoxLayout()
        title_lbl = QLabel(f"🔖 {bookmark.get('title', 'Academic Clip')}", self)
        title_lbl.setStyleSheet("font-size: 15px; font-weight: 800; color: #f8fafc;")
        top_row.addWidget(title_lbl, 1)

        cat_lbl = QLabel(bookmark.get("category", "Syllabus").upper(), self)
        cat_lbl.setStyleSheet("font-size: 10px; font-weight: bold; background: #312e81; color: #c7d2fe; padding: 3px 8px; border-radius: 6px;")
        top_row.addWidget(cat_lbl)

        layout.addLayout(top_row)

        # Snippet body
        snippet = bookmark.get("snippet") or bookmark.get("notes") or "Saved reference for active review."
        snippet_lbl = QLabel(f'"{snippet}"', self)
        snippet_lbl.setWordWrap(True)
        snippet_lbl.setStyleSheet("color: #cbd5e1; font-size: 13px; font-style: italic; background: #020617; padding: 10px; border-left: 3px solid #6366f1; border-radius: 6px;")
        layout.addWidget(snippet_lbl)

        # Bottom row: Timestamp + Action Buttons
        bot_row = QHBoxLayout()
        time_lbl = QLabel(f"Saved: {str(bookmark.get('created_at', 'Recently'))[:16]}", self)
        time_lbl.setStyleSheet("font-size: 11px; color: #64748b;")
        bot_row.addWidget(time_lbl, 1)

        btn_open = QPushButton("📖 Open in Reader", self)
        btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #334155;
                color: #38bdf8;
                font-weight: bold;
                font-size: 12px;
                padding: 5px 12px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #0284c7; color: white; }
        """)
        btn_open.clicked.connect(lambda: self.on_open(bookmark))
        bot_row.addWidget(btn_open)

        btn_del = QPushButton("🗑️", self)
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setFixedSize(30, 30)
        btn_del.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #334155;
                color: #ef4444;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #7f1d1d; border-color: #ef4444; color: white; }
        """)
        btn_del.clicked.connect(lambda: self.on_delete(bookmark.get("id")))
        bot_row.addWidget(btn_del)

        layout.addLayout(bot_row)


class BookmarksView(QWidget):
    """
    Dedicated screen for viewing and managing saved academic bookmarks and highlights.
    Matches Android BookmarksScreen.kt.
    """
    openReaderRequested = Signal(str, str) # unit_id, subtopic_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_filter = "All Clips"
        self.search_query = ""
        self.init_ui()
        self.refresh_bookmarks()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header Bar
        header = QHBoxLayout()
        header_title = QLabel("Saved Bookmarks and Clips", self)
        header_title.setStyleSheet("font-size: 20px; font-weight: 800; color: #ffffff;")
        header.addWidget(header_title)
        header.addStretch()

        btn_add = QPushButton("➕ Save New Clip", self)
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton {
                background-color: #4f46e5;
                color: white;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 16px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover { background-color: #4338ca; }
        """)
        btn_add.clicked.connect(self.prompt_add_bookmark)
        header.addWidget(btn_add)
        layout.addLayout(header)

        # Filter Tabs Row
        filter_row = QHBoxLayout()
        self.filter_buttons = {}
        tab_names = ["All Clips", "Syllabus", "Clinical Pearl", "Quick Notes"]
        for tab_name in tab_names:
            t_btn = QPushButton(tab_name, self)
            t_btn.setCheckable(True)
            t_btn.setAutoExclusive(True)
            t_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0f172a;
                    border: 1px solid #1e293b;
                    color: #94a3b8;
                    font-size: 12px;
                    font-weight: 600;
                    padding: 8px 16px;
                    border-radius: 8px;
                }
                QPushButton:hover { background-color: #1e293b; color: white; }
                QPushButton:checked {
                    background-color: #312e81;
                    border-color: #6366f1;
                    color: #ffffff;
                    font-weight: bold;
                }
            """)
            t_btn.clicked.connect(lambda checked, name=tab_name: self.set_filter(name))
            filter_row.addWidget(t_btn)
            self.filter_buttons[tab_name] = t_btn
        self.filter_buttons["All Clips"].setChecked(True)
        filter_row.addStretch()

        # Search Bar
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("🔍 Search saved clips and concepts...")
        self.search_input.setFixedWidth(240)
        self.search_input.setStyleSheet("background-color: #0b0f19; border: 1px solid #334155; border-radius: 8px; color: white; padding: 6px 12px;")
        self.search_input.textChanged.connect(self.on_search_changed)
        filter_row.addWidget(self.search_input)

        layout.addLayout(filter_row)

        # Cards Scroll Area
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(12)
        self.cards_layout.addStretch()

        self.scroll_area.setWidget(self.cards_container)
        layout.addWidget(self.scroll_area)

    def set_filter(self, tab_name: str):
        self.current_filter = tab_name
        self.refresh_bookmarks()

    def on_search_changed(self, text: str):
        self.search_query = text.strip().lower()
        self.refresh_bookmarks()

    def refresh_bookmarks(self):
        # Clear existing cards
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        all_b = TraceRepository.get_bookmarks(self.current_filter)

        # Filter by search
        if self.search_query:
            all_b = [
                b for b in all_b
                if self.search_query in (b.get("title") or "").lower()
                or self.search_query in (b.get("snippet") or "").lower()
                or self.search_query in (b.get("notes") or "").lower()
            ]

        if not all_b:
            empty_frame = QFrame(self.cards_container)
            empty_layout = QVBoxLayout(empty_frame)
            empty_layout.setContentsMargins(40, 60, 40, 60)
            empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            icon = QLabel("🔖", empty_frame)
            icon.setStyleSheet("font-size: 40px; color: #475569;")
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(icon)

            msg = QLabel("No clips or bookmarks found in this section.", empty_frame)
            msg.setStyleSheet("color: #64748b; font-size: 14px; font-weight: bold;")
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(msg)

            submsg = QLabel("Save excerpts while reading in the Learning Reader to review them here.", empty_frame)
            submsg.setStyleSheet("color: #475569; font-size: 12px;")
            submsg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(submsg)

            self.cards_layout.insertWidget(0, empty_frame)
            return

        for b in all_b:
            card = BookmarkCard(b, self.on_open_bookmark, self.on_delete_bookmark, self.cards_container)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def on_open_bookmark(self, bookmark: dict):
        unit_id = bookmark.get("unit_id") or "CS101"
        subtopic_id = bookmark.get("subtopic_id") or ""
        self.openReaderRequested.emit(unit_id, subtopic_id)

    def on_delete_bookmark(self, bookmark_id: int):
        confirm = QMessageBox.question(
            self,
            "Delete Bookmark",
            "Are you sure you want to remove this clip?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            TraceRepository.delete_bookmark(bookmark_id)
            self.refresh_bookmarks()

    def prompt_add_bookmark(self):
        dlg = AddBookmarkDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            TraceRepository.add_bookmark(
                title=data["title"],
                target="Manual",
                category=data["category"],
                notes="",
                snippet=data["snippet"],
                b_type="quick_note"
            )
            self.refresh_bookmarks()
