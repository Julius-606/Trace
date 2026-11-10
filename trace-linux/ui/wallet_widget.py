"""
TRACE Desktop (Linux Client) - Wallet & Neurons Currency Widget
FILE: trace-linux/ui/wallet_widget.py
VERSION: 1.0.0
ROLE: Displays live virtual Neurons balance with glowing badges,
      real-time state signals, and simulated top-up/award dialogues.
"""

try:
    from PyQt6.QtWidgets import (
        QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
        QDialog, QFrame, QMessageBox
    )
    from PyQt6.QtCore import Qt, pyqtSignal as Signal
    from PyQt6.QtGui import QFont
except ImportError:
    from PySide6.QtWidgets import (
        QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
        QDialog, QFrame, QMessageBox
    )
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QFont

from repository import TraceRepository


class WalletBadgeWidget(QFrame):
    """
    Compact header widget showing current Neurons balance.
    Clicking it opens the Neurons Top-up & History Dialog.
    """
    balanceChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("walletBadge")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.init_ui()
        self.refresh_balance()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(6)

        # Coin Icon
        self.icon_label = QLabel("🪙", self)
        self.icon_label.setStyleSheet("font-size: 15px;")
        layout.addWidget(self.icon_label)

        # Balance text
        self.balance_label = QLabel("200", self)
        self.balance_label.setObjectName("walletBalanceText")
        self.balance_label.setStyleSheet("font-weight: 900; font-size: 13px; color: #fbbf24; font-family: monospace;")
        layout.addWidget(self.balance_label)

        # Currency symbol (N for Neurons)
        self.currency_label = QLabel("Neurons", self)
        self.currency_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #d97706;")
        layout.addWidget(self.currency_label)

        self.setStyleSheet("""
            QFrame#walletBadge {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(245, 158, 11, 0.15), stop:1 rgba(217, 119, 6, 0.25));
                border: 1px solid rgba(245, 158, 11, 0.45);
                border-radius: 12px;
            }
            QFrame#walletBadge:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(245, 158, 11, 0.25), stop:1 rgba(217, 119, 6, 0.40));
                border: 1px solid #fbbf24;
            }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            dialog = WalletModalDialog(self)
            dialog.walletUpdated.connect(self.refresh_balance)
            dialog.exec()

    def refresh_balance(self):
        balance = TraceRepository.get_wallet_balance()
        self.balance_label.setText(str(balance))
        self.balanceChanged.emit(balance)


class WalletModalDialog(QDialog):
    """
    Dialog for managing Neurons: reviewing balance, simulating top-ups,
    and learning how Neurons are earned through active recall.
    """
    walletUpdated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Neurons Currency Vault")
        self.setFixedSize(450, 420)
        self.setStyleSheet("background-color: #0f172a; color: #f8fafc;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header Title
        title_label = QLabel("🧠 Neurons Reserve & Wallet", self)
        title_label.setStyleSheet("font-size: 18px; font-weight: 800; color: #ffffff;")
        layout.addWidget(title_label)

        subtitle = QLabel("Neurons are used to unlock curriculum units and AI case drills.", self)
        subtitle.setStyleSheet("font-size: 12px; color: #94a3b8;")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # Balance Card
        card = QFrame(self)
        card.setStyleSheet("""
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 16px;
        """)
        card_layout = QVBoxLayout(card)

        card_title = QLabel("CURRENT AVAILABLE BALANCE", card)
        card_title.setStyleSheet("font-size: 10px; font-weight: bold; color: #fbbf24; letter-spacing: 1px;")
        card_layout.addWidget(card_title)

        self.big_balance_label = QLabel(f"{TraceRepository.get_wallet_balance()} Neurons", card)
        self.big_balance_label.setStyleSheet("font-size: 28px; font-weight: 900; color: #f59e0b; font-family: monospace;")
        card_layout.addWidget(self.big_balance_label)

        layout.addWidget(card)

        # Top-up options
        actions_label = QLabel("Top-up or Earn Neurons:", self)
        actions_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #cbd5e1;")
        layout.addWidget(actions_label)

        btn_layout = QHBoxLayout()

        btn_50 = QPushButton("+50 Neurons (Daily Grant)", self)
        btn_50.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #2563eb; }
        """)
        btn_50.clicked.connect(lambda: self.add_neurons_amount(50))
        btn_layout.addWidget(btn_50)

        btn_200 = QPushButton("+200 Neurons (Term Top-Up)", self)
        btn_200.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        btn_200.clicked.connect(lambda: self.add_neurons_amount(200))
        btn_layout.addWidget(btn_200)

        layout.addLayout(btn_layout)

        # Information note
        info_box = QLabel("💡 Academic Pro-Tip: Scoring 75%+ on Active Recall Quizzes automatically awards 10 to 15 bonus Neurons!", self)
        info_box.setWordWrap(True)
        info_box.setStyleSheet("background-color: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 8px; padding: 10px; font-size: 11px; color: #93c5fd;")
        layout.addWidget(info_box)

        layout.addStretch()

        close_btn = QPushButton("Done", self)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: white;
                padding: 8px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def add_neurons_amount(self, amount: int):
        new_balance = TraceRepository.add_neurons(amount)
        self.big_balance_label.setText(f"{new_balance} Neurons")
        self.walletUpdated.emit()
        QMessageBox.information(
            self,
            "Neurons Credited",
            f"Successfully credited {amount} Neurons to your vault.\nNew Balance: {new_balance} Neurons."
        )
