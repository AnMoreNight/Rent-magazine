"""Reusable GUI widgets and factory helpers."""

from __future__ import annotations

from PyQt5.QtWidgets import QFrame, QLabel, QPushButton, QLineEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap, QColor, QPainter, QPen, QBrush

from rentmag.gui.styles import (
    CARD, BORDER, ACCENT2, SUCCESS, MUTED, TEXT1, TEXT2,
)


# ── Factory helpers ────────────────────────────────────────────────────────────

def card(parent=None) -> QFrame:
    f = QFrame(parent)
    f.setObjectName("card")
    return f


def label(text: str, obj: str = "", parent=None) -> QLabel:
    l = QLabel(text, parent)
    if obj:
        l.setObjectName(obj)
    return l


def hline(parent=None) -> QFrame:
    f = QFrame(parent)
    f.setObjectName("hline")
    return f


def btn(text: str, obj: str = "btn-secondary") -> QPushButton:
    b = QPushButton(text)
    b.setObjectName(obj)
    return b


def prop_field(placeholder: str = "") -> QLineEdit:
    """Styled inline input field for the property info grid."""
    e = QLineEdit()
    e.setObjectName("prop-field")
    if placeholder:
        e.setPlaceholderText(placeholder)
    return e


# ── Step badge ─────────────────────────────────────────────────────────────────

class StepBadge(QLabel):
    """
    Circular processing-step indicator.
    States: 'pending' (grey) | 'active' (blue) | 'done' (green)
    """

    def __init__(self, step_label: str, parent=None):
        super().__init__(parent)
        self._label = step_label
        self._state = "pending"
        self.setFixedSize(58, 46)

    def setState(self, state: str) -> None:
        if self._state != state:
            self._state = state
            self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        cx, cy, r = self.width() // 2, 16, 12

        if self._state == "done":
            bg_c, sym, lbl_c = QColor(SUCCESS), "✓", QColor(SUCCESS)
            fg_c = QColor("white")
        elif self._state == "active":
            bg_c, sym, lbl_c = QColor(ACCENT2), "●", QColor(ACCENT2)
            fg_c = QColor("white")
        else:
            bg_c, sym, lbl_c = QColor("#DCDFE4"), "○", QColor(MUTED)
            fg_c = lbl_c

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(bg_c))
        p.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        p.setPen(QPen(fg_c))
        p.setFont(QFont("Segoe UI", 8, QFont.Bold))
        p.drawText(cx - r, cy - r, r * 2, r * 2, Qt.AlignCenter, sym)

        p.setPen(QPen(lbl_c))
        p.setFont(QFont("Segoe UI", 7))
        p.drawText(0, cy + r + 2, self.width(), 14, Qt.AlignCenter, self._label)
        p.end()


# ── Preview image slot ─────────────────────────────────────────────────────────

class PreviewImage(QLabel):
    """Fixed-size image preview that shows a placeholder until an image is loaded."""

    W, H = 175, 118

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._title = title
        self.setFixedSize(self.W, self.H)
        self.setAlignment(Qt.AlignCenter)
        self._apply_empty_style()
        self.setText(f"({title})")

    def _apply_empty_style(self) -> None:
        self.setStyleSheet(f"""
            QLabel {{
                border: 1px solid {BORDER}; border-radius: 3px;
                background: #EAECF0; color: {MUTED}; font-size: 10px;
            }}
        """)

    def setImage(self, pixmap: QPixmap) -> None:
        self.setPixmap(
            pixmap.scaled(self.W, self.H, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        self.setStyleSheet(f"QLabel {{ border: 1px solid {BORDER}; border-radius: 3px; }}")

    def clearImage(self) -> None:
        self.clear()
        self.setText(f"({self._title})")
        self._apply_empty_style()
