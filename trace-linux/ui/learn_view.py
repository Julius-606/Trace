"""
TRACE Desktop (Linux Client) - Learning Reader & Socratic Study View
FILE: trace-linux/ui/learn_view.py
VERSION: 1.0.0
ROLE: Full-featured learning reader matching Android's LearnScreen.kt.
      Provides hierarchical topic navigation, formatted academic text,
      multi-color highlighting, clip bookmarking, inline Socratic Q&A,
      and subtopic completion toggling.
"""

import sys
try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QScrollArea, QFrame, QTextEdit, QLineEdit, QSplitter,
        QTreeWidget, QTreeWidgetItem, QMessageBox, QComboBox,
        QDialog, QButtonGroup, QRadioButton
    )
    from PyQt6.QtCore import Qt, pyqtSignal as Signal
    from PyQt6.QtGui import QFont, QColor, QTextCursor, QTextCharFormat
except ImportError:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QScrollArea, QFrame, QTextEdit, QLineEdit, QSplitter,
        QTreeWidget, QTreeWidgetItem, QMessageBox, QComboBox,
        QDialog, QButtonGroup, QRadioButton
    )
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QFont, QColor, QTextCursor, QTextCharFormat

from repository import TraceRepository


SAMPLE_LEARN_CURRICULUM = [
    {
        "unit_id": "CS101",
        "unit_title": "Computer Science: Distributed Systems",
        "modules": [
            {
                "module_title": "Module 1: High-Concurrency Ingestion Pipelines",
                "topics": [
                    {
                        "topic_title": "Topic 1.1: Event Streaming and Asynchronous Queues",
                        "subtopics": [
                            {
                                "id": "cs101_sub_1",
                                "title": "Decoupling Producers with Celery and Redis",
                                "content": (
                                    "# Decoupling Event Producers with Distributed Task Queues\n\n"
                                    "In high-throughput systems, HTTP request threads should never block while waiting for expensive I/O operations, database write locks, or AI inference models. Decoupling producers from consumer workers via distributed task queues (e.g. Redis, RabbitMQ, Celery) forms the backbone of resilient architectures.\n\n"
                                    "### Core Principles of Producer-Consumer Decoupling:\n"
                                    "1. **Backpressure Absorption:** Task queues act as shock absorbers when user traffic spikes exponentially, preventing database connection exhaustion.\n"
                                    "2. **Idempotency Guarantees:** Message processing must be idempotent. If a consumer crashes midway through a task, automated retry mechanisms can safely replay the event without duplicating side effects.\n"
                                    "3. **Fault Isolation:** Even if background analytics workers or machine learning inference nodes experience outages, user-facing API gateways remain operational with sub-50ms response times.\n\n"
                                    "### Clinical / Engineering Pearl:\n"
                                    "> Always pair queue-based architectures with Dead Letter Queues (DLQs) to capture poisoned or malformed payloads for post-mortem debugging rather than dropping them silently."
                                )
                            },
                            {
                                "id": "cs101_sub_2",
                                "title": "Write-Ahead Logging (WAL) and Multi-Reader Concurrency",
                                "content": (
                                    "# SQLite Concurrency: Write-Ahead Logging (WAL) Mode\n\n"
                                    "By default, traditional disk-based databases use rollback journals where writers block readers and readers block writers. On modern Linux desktop environments, enabling Write-Ahead Logging (WAL) revolutionizes performance.\n\n"
                                    "### How WAL Enhances Linux Desktop Workstations:\n"
                                    "- **Non-Blocking Concurrent Reads:** Readers read from the original database pages while new write transactions append exclusively to the `-wal` file.\n"
                                    "- **Atomic Checkpointing:** Data is sequentially synchronized to the main `.db` file during idle cycles or upon reaching preset page thresholds (e.g. 1000 pages).\n"
                                    "- **Reduced Disk Head Thrashing:** Sequential writes to the WAL file are order of magnitude faster than random-access page overwrites on NVMe and SSD drives.\n\n"
                                    "### Verification Command:\n"
                                    "```sql\nPRAGMA journal_mode = WAL;\nPRAGMA synchronous = NORMAL;\n```"
                                )
                            }
                        ]
                    }
                ]
            }
        ]
    },
    {
        "unit_id": "CS102",
        "unit_title": "Software Engineering: Cryptographic Security",
        "modules": [
            {
                "module_title": "Module 1: Zero-Trust Authentication and Cryptography",
                "topics": [
                    {
                        "topic_title": "Topic 1.1: Cryptographic Randomness and One-Time Passwords",
                        "subtopics": [
                            {
                                "id": "cs102_sub_1",
                                "title": "Cryptographically Secure Pseudorandom Number Generators (CSPRNG)",
                                "content": (
                                    "# Cryptographic Randomness in OTP Verification Systems\n\n"
                                    "Basic random generators (such as `Math.random()` or Python's default `random` module) rely on deterministic algorithms like the Mersenne Twister. If an attacker observes consecutive outputs, the internal state can be mathematically deduced.\n\n"
                                    "### CSPRNG Requirements for Academic and Financial Portals:\n"
                                    "1. **OS Hardware Entropy:** Must draw entropy directly from system kernel entropy pools (`/dev/urandom` on Linux, `CryptGenRandom` on Windows, or `crypto.randomInt` in Node.js).\n"
                                    "2. **Strict Time-to-Live (TTL):** One-time passwords (OTPs) must automatically expire after a maximum window of 10 minutes.\n"
                                    "3. **Hash at Rest:** Permanent databases must never store raw plaintext OTPs; always store bcrypt, Argon2, or SHA-256 salted hashes."
                                )
                            }
                        ]
                    }
                ]
            }
        ]
    }
]


class QuickHighlightDialog(QDialog):
    """Modal dialog allowing students to attach notes to highlighted text."""
    def __init__(self, snippet: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save Text Highlight")
        self.setFixedSize(420, 280)
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 14px;
            }
            QLabel { color: #f8fafc; font-size: 13px; font-weight: bold; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        lbl = QLabel("Selected Quote / Clip:", self)
        layout.addWidget(lbl)

        preview = QLabel(f'"{snippet[:120]}..."' if len(snippet) > 120 else f'"{snippet}"', self)
        preview.setWordWrap(True)
        preview.setStyleSheet("color: #94a3b8; font-style: italic; font-size: 12px; background: #0b0f19; padding: 10px; border-radius: 8px;")
        layout.addWidget(preview)

        lbl_note = QLabel("Annotation Note (Optional):", self)
        layout.addWidget(lbl_note)

        self.input_note = QLineEdit(self)
        self.input_note.setPlaceholderText("e.g. Essential exam objective / mnemonic...")
        self.input_note.setStyleSheet("background: #0b0f19; border: 1px solid #334155; border-radius: 8px; color: white; padding: 8px 12px;")
        layout.addWidget(self.input_note)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel", self)
        btn_cancel.setStyleSheet("background: #1e293b; color: #94a3b8; border-radius: 8px; padding: 8px 16px;")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_save = QPushButton("Save Highlight", self)
        btn_save.setStyleSheet("background: #4f46e5; color: white; font-weight: bold; border-radius: 8px; padding: 8px 16px;")
        btn_save.clicked.connect(self.accept)
        btn_row.addWidget(btn_save)

        layout.addLayout(btn_row)

    def get_note(self) -> str:
        return self.input_note.text().strip()


class LearnView(QWidget):
    """
    Interactive lesson and study reader screen replicating Android's LearnScreen.kt.
    """
    requestAssessment = Signal(str, str) # unit_id, topic_name
    progressUpdated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_unit_id = "CS101"
        self.current_subtopic = None
        self.selected_color = "#fbbf24" # Default Yellow
        self.init_ui()
        self.load_curriculum_tree()
        self.select_default_subtopic()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # ----------------------------------------------------------------------
        # 1. TOP BREADCRUMB & TOOLBAR (Matching Android LearnScreen AppBar)
        # ----------------------------------------------------------------------
        top_bar = QFrame(self)
        top_bar.setStyleSheet("background-color: #0b0f19; border: 1px solid #1e293b; border-radius: 12px; padding: 8px 14px;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)

        self.lbl_breadcrumb = QLabel("📚 Syllabus > Decoupling Event Producers", top_bar)
        self.lbl_breadcrumb.setStyleSheet("font-size: 14px; font-weight: 800; color: #6366f1;")
        top_layout.addWidget(self.lbl_breadcrumb, 1)

        # Highlighter Color Palette Buttons
        lbl_hl = QLabel("Highlighter:", top_bar)
        lbl_hl.setStyleSheet("font-size: 11px; font-weight: bold; color: #64748b;")
        top_layout.addWidget(lbl_hl)

        self.color_buttons = {}
        colors = [
            ("Yellow", "#fbbf24"),
            ("Green", "#34d399"),
            ("Blue", "#38bdf8"),
            ("Pink", "#f43f5e"),
            ("Violet", "#a855f7")
        ]
        for name, hex_code in colors:
            c_btn = QPushButton("", top_bar)
            c_btn.setFixedSize(22, 22)
            c_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            c_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {hex_code};
                    border-radius: 11px;
                    border: 2px solid #0b0f19;
                }}
                QPushButton:hover {{
                    border: 2px solid #ffffff;
                }}
            """)
            c_btn.clicked.connect(lambda checked, col=hex_code: self.set_highlighter_color(col))
            top_layout.addWidget(c_btn)
            self.color_buttons[hex_code] = c_btn

        # Bookmark Clip Button
        btn_bookmark = QPushButton("🔖 Bookmark Clip", top_bar)
        btn_bookmark.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_bookmark.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #334155;
                color: #e2e8f0;
                font-size: 12px;
                font-weight: 600;
                padding: 6px 12px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #334155; color: white; }
        """)
        btn_bookmark.clicked.connect(self.save_selected_as_bookmark)
        top_layout.addWidget(btn_bookmark)

        # Mark Completed Checkbox
        self.btn_complete = QPushButton("⬜ Mark Completed", top_bar)
        self.btn_complete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_complete.setStyleSheet("""
            QPushButton {
                background-color: #0f172a;
                border: 1px solid #10b981;
                color: #34d399;
                font-size: 12px;
                font-weight: bold;
                padding: 6px 14px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #064e3b; color: white; }
        """)
        self.btn_complete.clicked.connect(self.toggle_completed)
        top_layout.addWidget(self.btn_complete)

        # Launch Active Recall Drill Button
        btn_drill = QPushButton("🎯 Take Quiz on Topic", top_bar)
        btn_drill.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_drill.setStyleSheet("""
            QPushButton {
                background-color: #4f46e5;
                color: white;
                font-size: 12px;
                font-weight: bold;
                padding: 6px 14px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover { background-color: #4338ca; }
        """)
        btn_drill.clicked.connect(self.launch_topic_drill)
        top_layout.addWidget(btn_drill)

        main_layout.addWidget(top_bar)

        # ----------------------------------------------------------------------
        # 2. MAIN SPLITTER: LEFT TOPICS TREE | RIGHT READER & SOCRATIC MENTOR
        # ----------------------------------------------------------------------
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet("QSplitter::handle { background-color: #334155; }")

        # --- LEFT PANEL: CURRICULUM TREE ---
        left_panel = QFrame(splitter)
        left_panel.setFixedWidth(260)
        left_panel.setStyleSheet("background-color: #0b0f19; border: 1px solid #1e293b; border-radius: 12px;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)

        lbl_tree = QLabel("SYLLABUS TOPICS", left_panel)
        lbl_tree.setStyleSheet("font-size: 11px; font-weight: bold; color: #64748b; letter-spacing: 1px;")
        left_layout.addWidget(lbl_tree)

        self.curriculum_tree = QTreeWidget(left_panel)
        self.curriculum_tree.setHeaderHidden(True)
        self.curriculum_tree.setStyleSheet("""
            QTreeWidget {
                background-color: transparent;
                border: none;
                color: #e2e8f0;
                font-size: 12px;
            }
            QTreeWidget::item {
                padding: 6px 4px;
                border-radius: 6px;
            }
            QTreeWidget::item:hover {
                background-color: #1e293b;
            }
            QTreeWidget::item:selected {
                background-color: #312e81;
                color: #ffffff;
                font-weight: bold;
            }
        """)
        self.curriculum_tree.itemClicked.connect(self.on_tree_item_clicked)
        left_layout.addWidget(self.curriculum_tree)

        splitter.addWidget(left_panel)

        # --- RIGHT PANEL: READER CONTENT & SOCRATIC TUTOR ---
        right_panel = QWidget(splitter)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        # Reader Text Surface
        reader_frame = QFrame(right_panel)
        reader_frame.setStyleSheet("background-color: #0b0f19; border: 1px solid #1e293b; border-radius: 12px;")
        reader_box = QVBoxLayout(reader_frame)
        reader_box.setContentsMargins(16, 16, 16, 16)
        reader_box.setSpacing(10)

        self.reader_text = QTextEdit(reader_frame)
        self.reader_text.setReadOnly(True)
        self.reader_text.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: none;
                color: #f1f5f9;
                font-family: 'Inter', 'DejaVu Sans', sans-serif;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        reader_box.addWidget(self.reader_text)
        right_layout.addWidget(reader_frame, 3)

        # Inline Socratic Assistant Input Bar
        socratic_frame = QFrame(right_panel)
        socratic_frame.setStyleSheet("background-color: #0f172a; border: 1px solid #1e293b; border-radius: 12px; padding: 12px;")
        socratic_layout = QVBoxLayout(socratic_frame)
        socratic_layout.setContentsMargins(0, 0, 0, 0)
        socratic_layout.setSpacing(8)

        soc_head = QHBoxLayout()
        soc_icon = QLabel("🧠", socratic_frame)
        soc_head.addWidget(soc_icon)
        soc_title = QLabel("Ask Socratic Mentor regarding this subtopic", socratic_frame)
        soc_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #818cf8;")
        soc_head.addWidget(soc_title)
        soc_head.addStretch()
        socratic_layout.addLayout(soc_head)

        soc_input_row = QHBoxLayout()
        self.input_socratic = QLineEdit(socratic_frame)
        self.input_socratic.setPlaceholderText("Ask for clinical explanation, mnemonic, or mathematical proof...")
        self.input_socratic.setStyleSheet("background-color: #0b0f19; border: 1px solid #334155; border-radius: 8px; color: white; padding: 8px 12px;")
        self.input_socratic.returnPressed.connect(self.ask_socratic_mentor)
        soc_input_row.addWidget(self.input_socratic, 1)

        self.btn_ask = QPushButton("Consult Orbit", socratic_frame)
        self.btn_ask.setStyleSheet("background-color: #6366f1; color: white; font-weight: bold; border-radius: 8px; padding: 8px 16px;")
        self.btn_ask.clicked.connect(self.ask_socratic_mentor)
        soc_input_row.addWidget(self.btn_ask)
        socratic_layout.addLayout(soc_input_row)

        self.socratic_response_box = QLabel("", socratic_frame)
        self.socratic_response_box.setWordWrap(True)
        self.socratic_response_box.setStyleSheet("color: #cbd5e1; font-size: 12px; background: #0b0f19; padding: 10px; border-radius: 8px; border: 1px solid #1e293b;")
        self.socratic_response_box.setVisible(False)
        socratic_layout.addWidget(self.socratic_response_box)

        right_layout.addWidget(socratic_frame, 1)

        splitter.addWidget(right_panel)
        main_layout.addWidget(splitter)

    def set_highlighter_color(self, hex_code: str):
        self.selected_color = hex_code
        cursor = self.reader_text.textCursor()
        if cursor.hasSelection():
            fmt = QTextCharFormat()
            fmt.setBackground(QColor(hex_code))
            fmt.setForeground(QColor("#000000"))
            cursor.mergeCharFormat(fmt)

            selected_text = cursor.selectedText()
            if self.current_subtopic:
                TraceRepository.save_highlight(self.current_subtopic["id"], selected_text, hex_code)

    def save_selected_as_bookmark(self):
        cursor = self.reader_text.textCursor()
        snippet = cursor.selectedText().strip()
        if not snippet:
            if self.current_subtopic:
                snippet = self.current_subtopic.get("title", "")
            else:
                snippet = "Core Curriculum Reference"

        dlg = QuickHighlightDialog(snippet, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            note = dlg.get_note()
            sub_title = self.current_subtopic.get("title", "Curriculum Note") if self.current_subtopic else "Lesson Note"
            TraceRepository.add_bookmark(
                title=sub_title,
                target="Reader",
                category="Syllabus",
                notes=note,
                snippet=snippet,
                b_type="learn",
                unit_id=self.current_unit_id,
                subtopic_id=self.current_subtopic.get("id") if self.current_subtopic else ""
            )
            QMessageBox.information(self, "Saved", "✅ Clip successfully added to your Saved Bookmarks!")

    def toggle_completed(self):
        if not self.current_subtopic:
            return
        sub_id = self.current_subtopic["id"]
        is_done = TraceRepository.toggle_subtopic_completed(sub_id, self.current_unit_id)
        if is_done:
            self.btn_complete.setText("✅ Completed")
            self.btn_complete.setStyleSheet("background-color: #064e3b; border: 1px solid #10b981; color: #a7f3d0; font-size: 12px; font-weight: bold; padding: 6px 14px; border-radius: 8px;")
        else:
            self.btn_complete.setText("⬜ Mark Completed")
            self.btn_complete.setStyleSheet("background-color: #0f172a; border: 1px solid #10b981; color: #34d399; font-size: 12px; font-weight: bold; padding: 6px 14px; border-radius: 8px;")
        self.progressUpdated.emit()

    def launch_topic_drill(self):
        if self.current_subtopic:
            self.requestAssessment.emit(self.current_unit_id, self.current_subtopic.get("title", ""))

    def ask_socratic_mentor(self):
        query = self.input_socratic.text().strip()
        if not query:
            return
        self.btn_ask.setEnabled(False)
        self.btn_ask.setText("Thinking...")
        self.socratic_response_box.setVisible(True)
        self.socratic_response_box.setText("⏳ Orbit Socratic Mentor is formulating pedagogical inquiry...")

        try:
            sub_title = self.current_subtopic.get("title", "this topic") if self.current_subtopic else "the lesson"
            prompt = f"In the academic context of '{sub_title}', answer: {query}. Keep it concise, high-yield, and socratic."
            ans = TraceRepository.send_ai_chat(prompt)
            self.socratic_response_box.setText(f"💡 **Orbit Socratic Response:**\n{ans}")
        except Exception as e:
            self.socratic_response_box.setText(f"💡 **Orbit Socratic Guidance:**\nConsider the underlying principles of {query}. What inputs are required, and what failure modes could arise under high concurrency?")
        finally:
            self.btn_ask.setEnabled(True)
            self.btn_ask.setText("Consult Orbit")
            self.input_socratic.clear()

    def load_curriculum_tree(self):
        self.curriculum_tree.clear()
        for u in SAMPLE_LEARN_CURRICULUM:
            u_item = QTreeWidgetItem([f"📦 {u['unit_title']}"])
            u_item.setData(0, Qt.ItemDataRole.UserRole, ("unit", u["unit_id"]))
            for m in u["modules"]:
                m_item = QTreeWidgetItem([f"📁 {m['module_title']}"])
                u_item.addChild(m_item)
                for t in m["topics"]:
                    t_item = QTreeWidgetItem([f"📑 {t['topic_title']}"])
                    m_item.addChild(t_item)
                    for s in t["subtopics"]:
                        s_item = QTreeWidgetItem([f"📄 {s['title']}"])
                        s_item.setData(0, Qt.ItemDataRole.UserRole, ("subtopic", s))
                        t_item.addChild(s_item)
            self.curriculum_tree.addTopLevelItem(u_item)
        self.curriculum_tree.expandAll()

    def select_default_subtopic(self):
        first_sub = SAMPLE_LEARN_CURRICULUM[0]["modules"][0]["topics"][0]["subtopics"][0]
        self.open_subtopic(first_sub, "CS101")

    def on_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and data[0] == "subtopic":
            self.open_subtopic(data[1], self.current_unit_id)

    def open_subtopic(self, subtopic: dict, unit_id: str):
        self.current_subtopic = subtopic
        self.current_unit_id = unit_id
        self.lbl_breadcrumb.setText(f"📚 {unit_id} > {subtopic['title']}")

        # Render content
        content = subtopic.get("content", "")
        # Render markdown-like simple formatting to HTML
        html = self.format_markdown_to_html(content)
        self.reader_text.setHtml(html)

        # Check completion state
        is_done = TraceRepository.is_subtopic_completed(subtopic["id"])
        if is_done:
            self.btn_complete.setText("✅ Completed")
            self.btn_complete.setStyleSheet("background-color: #064e3b; border: 1px solid #10b981; color: #a7f3d0; font-size: 12px; font-weight: bold; padding: 6px 14px; border-radius: 8px;")
        else:
            self.btn_complete.setText("⬜ Mark Completed")
            self.btn_complete.setStyleSheet("background-color: #0f172a; border: 1px solid #10b981; color: #34d399; font-size: 12px; font-weight: bold; padding: 6px 14px; border-radius: 8px;")

        self.socratic_response_box.setVisible(False)

    def format_markdown_to_html(self, text: str) -> str:
        lines = text.split("\n")
        html_lines = []
        for line in lines:
            if line.startswith("# "):
                html_lines.append(f"<h1 style='color: #6366f1; font-size: 20px; font-weight: 900; margin-bottom: 8px;'>{line[2:]}</h1>")
            elif line.startswith("### "):
                html_lines.append(f"<h3 style='color: #38bdf8; font-size: 15px; font-weight: bold; margin-top: 14px; margin-bottom: 6px;'>{line[4:]}</h3>")
            elif line.startswith("> "):
                html_lines.append(f"<div style='background-color: #1e1b4b; border-left: 4px solid #6366f1; padding: 10px 14px; color: #c7d2fe; margin: 10px 0; border-radius: 6px;'><b>Insight:</b> {line[2:]}</div>")
            elif line.startswith("- ") or line.startswith("1. ") or line.startswith("2. ") or line.startswith("3. "):
                html_lines.append(f"<p style='margin: 4px 0 4px 16px; color: #e2e8f0;'>• {line[2:]}</p>")
            elif line.strip():
                html_lines.append(f"<p style='margin: 8px 0; color: #cbd5e1; line-height: 1.6;'>{line}</p>")
            else:
                html_lines.append("<br/>")
        return "".join(html_lines)
