"""
TRACE Desktop (Linux Client) - Assessment Center & Active Recall Runner
FILE: trace-linux/ui/assessment_view.py
VERSION: 1.0.0
ROLE: Interactive quiz engine providing high-yield active recall testing,
      instant pedagogical explanations, and Neurons reward payouts.
"""

import json
try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QRadioButton, QButtonGroup, QProgressBar, QFrame, QMessageBox,
        QScrollArea
    )
    from PyQt6.QtCore import Qt, pyqtSignal as Signal, QTimer
    from PyQt6.QtGui import QFont
except ImportError:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QRadioButton, QButtonGroup, QProgressBar, QFrame, QMessageBox,
        QScrollArea
    )
    from PySide6.QtCore import Qt, Signal, QTimer
    from PySide6.QtGui import QFont

from repository import TraceRepository


# Pre-loaded high-yield question pools for offline active recall drills
OFFLINE_QUESTION_POOLS = {
    "CS101": [
        {
            "question": "In an asynchronous processing pipeline, what is the primary benefit of decoupling event producers from worker pools using task queues?",
            "options": [
                "Guarantees that database reads bypass write locks completely",
                "Prevents user-facing request threads from blocking during heavy ingestion jobs",
                "Enforces synchronous execution across all CPU cores",
                "Automatically compiles Python bytecode into machine binaries"
            ],
            "correct_idx": 1,
            "explanation": "Decoupling with queues (like Celery/Redis) prevents long-running I/O or LLM tasks from stalling HTTP request handlers, isolating failures and handling spikes."
        },
        {
            "question": "Which SQLite journal mode is best suited for concurrent multi-process reads and writes on Linux desktops?",
            "options": [
                "DELETE mode",
                "MEMORY mode",
                "Write-Ahead Logging (WAL)",
                "TRUNCATE mode"
            ],
            "correct_idx": 2,
            "explanation": "WAL mode allows concurrent readers to continue without blocking writers and vice versa, offering significantly higher throughput on Linux filesystems."
        }
    ],
    "CS102": [
        {
            "question": "Why must cryptographic one-time passwords (OTPs) use CSPRNGs like Python's 'secrets' rather than 'random'?",
            "options": [
                "CSPRNGs utilize hardware entropy sources, making seed prediction computationally unfeasible",
                "The random module only generates floating-point numbers",
                "Secrets module runs faster on x86 processors",
                "Random module is deprecated in Python 3.11"
            ],
            "correct_idx": 0,
            "explanation": "The 'random' module uses the Mersenne Twister algorithm, which can be reverse-engineered after observing 624 outputs. The 'secrets' module accesses system cryptographic entropy (/dev/urandom)."
        }
    ],
    "DEFAULT": [
        {
            "question": "What is the primary cognitive mechanism behind active recall and spaced repetition?",
            "options": [
                "Passive re-reading of highlighted text",
                "Testing-effect retrieval that strengthens neural synaptic connectivity",
                "Subconscious osmosis while resting",
                "Cramming within 2 hours of examination"
            ],
            "correct_idx": 1,
            "explanation": "Active retrieval forces the brain to reconstruct memory traces, significantly increasing retention compared to passive re-reading."
        },
        {
            "question": "When balancing complex academic study with project execution, what is the optimal chronotype scheduling approach?",
            "options": [
                "Perform creative low-stakes tasks during peak morning hours",
                "Reserve peak cognitive focus hours for the heaviest conceptual material",
                "Multi-task across 5 windows simultaneously",
                "Skip sleep to gain extra working hours"
            ],
            "correct_idx": 1,
            "explanation": "Deep work theory demonstrates that cognitive stamina is highest earlier in circadian cycles; heavy conceptual learning must occupy peak focus windows."
        }
    ]
}


class AssessmentView(QWidget):
    """
    Interactive test engine running active recall quizzes.
    """
    quizFinished = Signal(dict) # Emits result dict

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_unit_id = "CS101"
        self.active_unit_title = "Distributed Systems & Cloud Ingestion"
        self.questions = []
        self.current_q_index = 0
        self.score = 0
        self.user_answers = {}

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Header bar
        header_row = QHBoxLayout()
        self.title_label = QLabel("🎯 Assessment Center: Active Recall Drill", self)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 800; color: #ffffff;")
        header_row.addWidget(self.title_label)

        header_row.addStretch()

        self.badge_neurons = QLabel("🎁 75%+ Score = +10 to +15 Neurons", self)
        self.badge_neurons.setStyleSheet("background-color: rgba(245, 158, 11, 0.15); border: 1px solid #f59e0b; color: #fbbf24; border-radius: 8px; padding: 4px 10px; font-size: 11px; font-weight: bold;")
        header_row.addWidget(self.badge_neurons)

        layout.addLayout(header_row)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                height: 8px;
                text-align: center;
                color: transparent;
            }
            QProgressBar::chunk {
                background-color: #6366f1;
                border-radius: 6px;
            }
        """)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Question Container Card
        self.card = QFrame(self)
        self.card.setStyleSheet("""
            QFrame {
                background-color: #0b0f19;
                border: 1px solid #1e293b;
                border-radius: 14px;
                padding: 20px;
            }
        """)
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setSpacing(14)

        self.q_number_label = QLabel("QUESTION 1 OF 5", self.card)
        self.q_number_label.setStyleSheet("font-size: 11px; font-weight: 900; color: #818cf8; letter-spacing: 1px;")
        self.card_layout.addWidget(self.q_number_label)

        self.q_text_label = QLabel("Question text will load here...", self.card)
        self.q_text_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #ffffff; line-height: 1.4;")
        self.q_text_label.setWordWrap(True)
        self.card_layout.addWidget(self.q_text_label)

        # Options group
        self.button_group = QButtonGroup(self)
        self.option_buttons = []
        for i in range(4):
            rb = QRadioButton(f"Option {i + 1}", self.card)
            rb.setStyleSheet("""
                QRadioButton {
                    color: #cbd5e1;
                    font-size: 13px;
                    padding: 8px;
                    border-radius: 8px;
                }
                QRadioButton:hover {
                    background-color: #1e293b;
                }
                QRadioButton::indicator {
                    width: 16px;
                    height: 16px;
                }
            """)
            self.button_group.addButton(rb, i)
            self.option_buttons.append(rb)
            self.card_layout.addWidget(rb)

        # Explanation box (hidden until submitted or answered)
        self.explanation_box = QLabel("", self.card)
        self.explanation_box.setWordWrap(True)
        self.explanation_box.setStyleSheet("background-color: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; border-radius: 8px; padding: 10px; color: #6ee7b7; font-size: 12px;")
        self.explanation_box.setVisible(False)
        self.card_layout.addWidget(self.explanation_box)

        layout.addWidget(self.card)

        # Bottom buttons
        btn_layout = QHBoxLayout()

        self.btn_submit_ans = QPushButton("Check Answer", self)
        self.btn_submit_ans.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #2563eb; }
        """)
        self.btn_submit_ans.clicked.connect(self.check_current_answer)
        btn_layout.addWidget(self.btn_submit_ans)

        self.btn_next = QPushButton("Next Question →", self)
        self.btn_next.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #4f46e5; }
        """)
        self.btn_next.clicked.connect(self.advance_question)
        self.btn_next.setEnabled(False)
        btn_layout.addWidget(self.btn_next)

        btn_layout.addStretch()

        layout.addLayout(btn_layout)

    def load_quiz_for_unit(self, unit_id: str, unit_title: str):
        self.active_unit_id = unit_id
        self.active_unit_title = unit_title
        self.title_label.setText(f"🎯 Assessment: {unit_title}")

        pool = OFFLINE_QUESTION_POOLS.get(unit_id, OFFLINE_QUESTION_POOLS["DEFAULT"])
        self.questions = list(pool)
        self.current_q_index = 0
        self.score = 0
        self.user_answers = {}

        self.render_question()

    def render_question(self):
        if not self.questions or self.current_q_index >= len(self.questions):
            return

        q = self.questions[self.current_q_index]
        self.q_number_label.setText(f"QUESTION {self.current_q_index + 1} OF {len(self.questions)}")
        self.q_text_label.setText(q["question"])
        self.explanation_box.setVisible(False)

        # Clear selection
        self.button_group.setExclusive(False)
        for rb in self.option_buttons:
            rb.setChecked(False)
        self.button_group.setExclusive(True)

        for i, opt in enumerate(q["options"]):
            if i < len(self.option_buttons):
                self.option_buttons[i].setText(opt)
                self.option_buttons[i].setVisible(True)

        for j in range(len(q["options"]), len(self.option_buttons)):
            self.option_buttons[j].setVisible(False)

        pct = int(((self.current_q_index) / len(self.questions)) * 100)
        self.progress_bar.setValue(pct)
        self.btn_submit_ans.setEnabled(True)
        self.btn_next.setEnabled(False)

    def check_current_answer(self):
        selected_id = self.button_group.checkedId()
        if selected_id == -1:
            QMessageBox.warning(self, "Select an Option", "Please choose an answer before verifying.")
            return

        q = self.questions[self.current_q_index]
        correct_idx = q["correct_idx"]
        is_correct = (selected_id == correct_idx)

        if is_correct:
            self.score += 1
            self.explanation_box.setText(f"✅ Correct!\n{q['explanation']}")
            self.explanation_box.setStyleSheet("background-color: rgba(16, 185, 129, 0.12); border: 1px solid #10b981; border-radius: 8px; padding: 10px; color: #6ee7b7;")
        else:
            self.explanation_box.setText(f"❌ Incorrect. Correct answer was Option {correct_idx + 1}.\n{q['explanation']}")
            self.explanation_box.setStyleSheet("background-color: rgba(239, 68, 68, 0.12); border: 1px solid #ef4444; border-radius: 8px; padding: 10px; color: #fca5a5;")

        self.explanation_box.setVisible(True)
        self.btn_submit_ans.setEnabled(False)
        self.btn_next.setEnabled(True)

    def advance_question(self):
        self.current_q_index += 1
        if self.current_q_index < len(self.questions):
            self.render_question()
        else:
            self.finish_quiz()

    def finish_quiz(self):
        total = len(self.questions)
        pct = (self.score / total) * 100 if total > 0 else 0
        self.progress_bar.setValue(100)

        # Record to local SQLite database via repository
        result = TraceRepository.record_quiz_result(
            unit_id=self.active_unit_id,
            unit_name=self.active_unit_title,
            score=self.score,
            total=total
        )

        neurons_msg = f"\n\n🪙 Bonus: Awarded +{result['neurons_awarded']} Neurons to your wallet!" if result['neurons_awarded'] > 0 else ""

        QMessageBox.information(
            self,
            "Assessment Completed",
            f"Active Recall Drill Finished!\n\nScore: {self.score} / {total} ({pct:.1f}%){neurons_msg}\n\nOutcome recorded in local SQLite database."
        )

        self.quizFinished.emit(result)
