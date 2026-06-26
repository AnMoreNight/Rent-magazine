#!/usr/bin/env python3
"""
Rent Magazine — Phase 1 Desktop GUI (PyQt5)
物件写真処理システム
"""

import sys
import json
import html as html_mod
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QGridLayout, QLabel, QLineEdit, QPushButton, QComboBox,
        QProgressBar, QTextEdit, QFileDialog, QMessageBox,
        QFrame, QStackedWidget, QSizePolicy,
    )
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
    from PyQt5.QtGui import QFont
except ImportError:
    print("PyQt5が見つかりません: pip install PyQt5")
    sys.exit(1)

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("pip install Pillow numpy")
    sys.exit(1)

from rent_magazine_processor import process_images
from rent_magazine_sheets import PropertyMasterClient, SheetsError

CONFIG_FILE = Path(__file__).parent / "config.json"

DEFAULTS = {
    "credentials_path":       "",
    "sheet_name":             "物件管理番号マスター",
    "last_input_dir":         "",
    "last_output_dir":        "",
    "last_logo_path":         "",
    "last_property":          "",
    "last_room":              "",
    "last_image_type":        "リビング",
    "last_management_number": "",
    "last_city":              "",
    "last_hiragana":          "",
    "last_station":           "",
}

# ── Design tokens ──────────────────────────────────────────────────────────────
PAGE_BG  = "#eaecef"
CARD_BG  = "#ffffff"
CARD_BDR = "#e8eaee"
INNER_BG = "#f6f7f9"
T_PRI    = "#1f2430"
T_SEC    = "#6b7280"
T_MUT    = "#9aa1ac"
INP_BDR  = "#d7dbe0"
ACCENT   = "#334155"
OG_TEXT  = "#b65a18"
OG_BG    = "#fdeedf"
OG_BDR   = "#f0c090"
OK_TEXT  = "#22a35a"
OK_BG    = "#eef7f0"
OK_BDR   = "#cfe9d6"
ER_TEXT  = "#dc2626"
ER_BG    = "#fef2f2"
ER_BDR   = "#fecaca"

STYLESHEET = f"""
QLabel {{
    background: transparent;
    color: {T_PRI};
}}
QLabel:disabled {{
    color: {T_MUT};
}}
QFrame#card {{
    background: {CARD_BG};
    border: 1px solid {CARD_BDR};
    border-radius: 13px;
    padding: 0px;
}}
QFrame#innerSection {{
    background: {INNER_BG};
    border: 1px solid {CARD_BDR};
    border-radius: 8px;
}}
QFrame#hdrBar {{
    background: {CARD_BG};
    border-bottom: 1px solid {CARD_BDR};
}}
QFrame#divider {{
    background: {CARD_BDR};
    border: none;
    max-height: 1px;
}}
QFrame#segTrack {{
    background: #f1f3f6;
    border: 1px solid {CARD_BDR};
    border-radius: 9px;
}}
QLineEdit {{
    background: {CARD_BG};
    border: 1px solid {INP_BDR};
    border-radius: 9px;
    padding: 0 12px;
    min-height: 38px;
    font-size: 13px;
    color: {T_PRI};
    selection-background-color: {ACCENT};
}}
QLineEdit:focus {{
    border-color: {ACCENT};
}}
QLineEdit:read-only {{
    background: {INNER_BG};
    color: {T_SEC};
    border-color: {CARD_BDR};
}}
QLineEdit:disabled {{
    background: {INNER_BG};
    color: {T_MUT};
    border-color: {CARD_BDR};
}}
QComboBox {{
    background: {CARD_BG};
    border: 1px solid {INP_BDR};
    border-radius: 9px;
    padding: 0 12px;
    min-height: 38px;
    font-size: 13px;
    color: {T_PRI};
}}
QComboBox:focus {{
    border-color: {ACCENT};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox:disabled {{
    background: {INNER_BG};
    color: {T_MUT};
    border-color: {CARD_BDR};
}}
QComboBox QAbstractItemView {{
    background: {CARD_BG};
    border: 1px solid {INP_BDR};
    selection-background-color: {INNER_BG};
    selection-color: {T_PRI};
    outline: none;
    border-radius: 8px;
    padding: 4px;
}}
QPushButton {{
    background: {INNER_BG};
    color: {T_SEC};
    border: 1px solid {INP_BDR};
    border-radius: 9px;
    padding: 0 16px;
    min-height: 36px;
    font-size: 13px;
}}
QPushButton:hover {{
    background: #e8ebee;
    border-color: #bfc3ca;
    color: {T_PRI};
}}
QPushButton:pressed {{
    background: #dde0e5;
}}
QPushButton:disabled {{
    color: {T_MUT};
    background: {INNER_BG};
    border-color: {CARD_BDR};
}}
QProgressBar {{
    background: {INNER_BG};
    border: none;
    border-radius: 3px;
    max-height: 6px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: {ACCENT};
    border-radius: 3px;
}}
QTextEdit {{
    background: transparent;
    border: none;
    color: {T_PRI};
    font-size: 12px;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {INP_BDR};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QStatusBar {{
    background: {CARD_BG};
    border-top: 1px solid {CARD_BDR};
    color: {T_SEC};
    font-size: 11px;
    padding: 0 4px;
}}
QStatusBar::item {{
    border: none;
}}
"""

_BTN_PRI = f"""
    QPushButton {{
        background: {ACCENT}; color: #fff; border: none; border-radius: 11px;
        font-size: 14px; font-weight: 700; min-height: 44px; padding: 0 24px;
    }}
    QPushButton:hover {{ background: #3d5166; }}
    QPushButton:pressed {{ background: #263545; }}
    QPushButton:disabled {{ background: #c0c8d0; color: #eef0f2; border: none; }}
"""
_BTN_GHOST = f"""
    QPushButton {{
        background: transparent; color: {T_SEC}; border: 1px solid {INP_BDR};
        border-radius: 9px; font-size: 13px; min-height: 44px; padding: 0 18px;
    }}
    QPushButton:hover {{ background: {INNER_BG}; color: {T_PRI}; }}
    QPushButton:pressed {{ background: #e0e3e8; }}
    QPushButton:disabled {{ color: {T_MUT}; }}
"""
_SEG_ON = f"""
    QPushButton {{
        background: {OG_BG}; color: {OG_TEXT}; border: 1px solid {OG_BDR};
        border-radius: 7px; font-size: 12px; font-weight: 600;
        min-height: 32px; padding: 0 16px;
    }}
"""
_SEG_OFF = f"""
    QPushButton {{
        background: transparent; color: {T_SEC}; border: none;
        border-radius: 7px; font-size: 12px; min-height: 32px; padding: 0 16px;
    }}
    QPushButton:hover {{ background: rgba(0,0,0,.04); color: {T_PRI}; }}
    QPushButton:disabled {{ color: {T_MUT}; background: transparent; border: none; }}
"""


# ─────────────────────────────────────────────────────────────
# Settings Manager
# ─────────────────────────────────────────────────────────────

class SettingsManager:
    def __init__(self):
        self._data = {**DEFAULTS}
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._data.update(json.load(f))
            except Exception:
                pass

    def get(self, key: str) -> str:
        return self._data.get(key, DEFAULTS.get(key, ""))

    def save(self, key: str, value) -> None:
        self._data[key] = value
        self._flush()

    def save_many(self, pairs: dict) -> None:
        self._data.update(pairs)
        self._flush()

    def _flush(self) -> None:
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"設定の保存に失敗しました: {e}")


# ─────────────────────────────────────────────────────────────
# Background Worker Thread
# ─────────────────────────────────────────────────────────────

class ProcessingWorker(QThread):
    progress_signal = pyqtSignal(int, int, str, str, str)
    finished_signal = pyqtSignal(dict)
    error_signal    = pyqtSignal(str)

    def __init__(self, process_kwargs: dict):
        super().__init__()
        self._kwargs = process_kwargs

    def run(self):
        try:
            results = process_images(**self._kwargs, progress_callback=self._on_progress)
            self.finished_signal.emit(results)
        except Exception as e:
            self.error_signal.emit(str(e))

    def _on_progress(self, current, total, source, output, status):
        self.progress_signal.emit(current, total, source, output, status)


# ─────────────────────────────────────────────────────────────
# Main Application Window
# ─────────────────────────────────────────────────────────────

class RentMagazineApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.settings        = SettingsManager()
        self.sheets          = PropertyMasterClient()
        self.last_failed: list = []
        self._worker: ProcessingWorker = None
        self._log_ok_count   = 0
        self._log_err_count  = 0

        self.setWindowTitle("Rent Magazine — 物件写真処理システム")
        self.resize(1180, 900)
        self.setMinimumSize(900, 680)

        # Central widget with page background
        central = QWidget()
        central.setStyleSheet(f"background: {PAGE_BG};")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # In-app header bar
        self._build_header(root)

        # Body: left pane + right log card
        body = QWidget()
        body.setStyleSheet("background: transparent;")
        body_h = QHBoxLayout(body)
        body_h.setContentsMargins(20, 16, 20, 20)
        body_h.setSpacing(22)

        left = QWidget()
        left.setStyleSheet("background: transparent;")
        left.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        left_v = QVBoxLayout(left)
        left_v.setContentsMargins(0, 0, 0, 0)
        left_v.setSpacing(16)

        self._build_sheets_card(left_v)
        self._build_property_card(left_v)
        self._build_files_card(left_v)
        left_v.addStretch(1)
        self._build_action_row(left_v)

        right = QFrame()
        right.setObjectName("card")
        right.setFrameShape(QFrame.NoFrame)
        right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._build_log_card(right)

        body_h.addWidget(left, 155)
        body_h.addWidget(right, 100)

        root.addWidget(body, 1)

        # Status bar
        sb = self.statusBar()
        self._status_dot = QLabel()
        self._status_dot.setFixedSize(8, 8)
        self._status_dot.setStyleSheet(f"background: {T_MUT}; border-radius: 4px; margin: 0 4px;")
        self._status_txt = QLabel("準備完了")
        self._status_txt.setStyleSheet(f"color: {T_SEC}; font-size: 11px;")
        sb.addWidget(self._status_dot)
        sb.addWidget(self._status_txt)

        # Auto-connect if credentials saved
        creds = self.settings.get("credentials_path")
        sheet = self.settings.get("sheet_name")
        if creds and Path(creds).exists() and sheet:
            QTimer.singleShot(250, self._connect_sheets)

    # ── Widget helpers ─────────────────────────────────────────────────────────

    def _flbl(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {T_SEC};")
        return lbl

    def _fw(self, label_text: str, widget=None) -> QFrame:
        """Stacked field label + input, for use inside grid layouts."""
        box = QFrame()
        box.setStyleSheet("background: transparent;")
        v = QVBoxLayout(box)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(5)
        v.addWidget(self._flbl(label_text))
        if widget is not None:
            v.addWidget(widget)
        return box

    def _card_hdr(self, layout, title: str, dot_color: str = ACCENT,
                  right_widget=None):
        """Add a colored-dot card header row + 1-px divider to a VBoxLayout."""
        row = QHBoxLayout()
        row.setSpacing(8)
        row.setContentsMargins(0, 0, 0, 0)

        dot = QLabel()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"background: {dot_color}; border-radius: 4px;")
        row.addWidget(dot)

        lbl = QLabel(title)
        lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {T_PRI};")
        row.addWidget(lbl)
        row.addStretch()
        if right_widget:
            row.addWidget(right_widget)
        layout.addLayout(row)

        div = QFrame()
        div.setObjectName("divider")
        div.setFrameShape(QFrame.NoFrame)
        div.setFixedHeight(1)
        layout.addWidget(div)

    def _pill(self, text: str, bg: str, fg: str, border: str = "") -> QLabel:
        border_rule = f"border: 1px solid {border};" if border else "border: none;"
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"background: {bg}; color: {fg}; {border_rule}"
            f"border-radius: 999px; font-size: 11px; font-weight: 600; padding: 2px 10px;"
        )
        return lbl

    def _set_status(self, state: str, msg: str):
        dot_colors = {
            "ready":   T_MUT,
            "running": OK_TEXT,
            "done":    "#0ea5e9",
            "error":   ER_TEXT,
        }
        pill_styles = {
            "ready":   (f"#e5e7eb", "#4b5563"),
            "running": (OK_BG,     OK_TEXT),
            "done":    ("#dbeafe", "#1e40af"),
            "error":   (ER_BG,     ER_TEXT),
        }
        dc = dot_colors.get(state, T_MUT)
        bg, fg = pill_styles.get(state, pill_styles["ready"])
        self._status_dot.setStyleSheet(
            f"background: {dc}; border-radius: 4px; margin: 0 4px;")
        self._status_txt.setText(msg)
        self._status_pill.setText(msg)
        self._status_pill.setStyleSheet(
            f"background: {bg}; color: {fg}; border-radius: 999px;"
            f"font-size: 11px; font-weight: 600; padding: 3px 12px;"
        )

    # ── Build: in-app header bar ───────────────────────────────────────────────

    def _build_header(self, root_layout):
        hdr = QFrame()
        hdr.setObjectName("hdrBar")
        hdr.setFrameShape(QFrame.NoFrame)
        hdr.setFixedHeight(52)
        h = QHBoxLayout(hdr)
        h.setContentsMargins(20, 0, 20, 0)
        h.setSpacing(10)

        # App icon (slate square)
        icon = QLabel()
        icon.setFixedSize(26, 26)
        icon.setStyleSheet(f"background: {ACCENT}; border-radius: 6px;")
        h.addWidget(icon)

        # Wordmark
        wm = QLabel("Rent Magazine")
        wm.setStyleSheet(
            f"font-size: 15px; font-weight: 800; color: {T_PRI};"
            f"font-family: 'Manrope', 'Segoe UI', 'Yu Gothic UI', sans-serif;"
        )
        h.addWidget(wm)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.NoFrame)
        sep.setFixedSize(1, 18)
        sep.setStyleSheet(f"background: {CARD_BDR};")
        h.addWidget(sep)

        # Subtitle
        sub = QLabel("物件写真処理システム")
        sub.setStyleSheet(f"font-size: 13px; color: {T_SEC};")
        h.addWidget(sub)

        h.addStretch()

        # Status pill (dynamic)
        self._status_pill = self._pill("準備完了", "#e5e7eb", "#4b5563")
        h.addWidget(self._status_pill)

        # Phase badge
        phase = self._pill("Phase 1", INNER_BG, T_SEC, CARD_BDR)
        h.addWidget(phase)

        root_layout.addWidget(hdr)

    # ── Build: Google Sheets card ──────────────────────────────────────────────

    def _build_sheets_card(self, parent_layout):
        card = QFrame()
        card.setObjectName("card")
        card.setFrameShape(QFrame.NoFrame)
        v = QVBoxLayout(card)
        v.setContentsMargins(18, 14, 18, 16)
        v.setSpacing(12)

        self._card_hdr(v, "Google スプレッドシート連携", "#22c55e")

        # QStackedWidget: disconnected (0) / connected (1)
        self._sheets_stack = QStackedWidget()
        self._sheets_stack.setStyleSheet("background: transparent;")

        # ── Page 0: disconnected ──────────────────────────────────────────────
        disconn = QWidget()
        disconn.setStyleSheet("background: transparent;")
        dc_v = QVBoxLayout(disconn)
        dc_v.setContentsMargins(0, 0, 0, 0)
        dc_v.setSpacing(10)

        # Row 1: creds file
        r1 = QHBoxLayout()
        r1.setSpacing(8)
        creds_box = QVBoxLayout()
        creds_box.setSpacing(5)
        creds_box.addWidget(self._flbl("サービスアカウント JSON"))
        self._creds_edit = QLineEdit(self.settings.get("credentials_path"))
        self._creds_edit.setReadOnly(True)
        self._creds_edit.setPlaceholderText("認証情報ファイルを選択してください")
        creds_box.addWidget(self._creds_edit)
        r1.addLayout(creds_box, 1)
        browse_btn = QPushButton("参照")
        browse_btn.setFixedWidth(66)
        browse_btn.setStyleSheet("min-height: 38px;")
        browse_btn.clicked.connect(self._pick_credentials)
        creds_box.addWidget(QWidget())   # spacer to align button
        r1.insertWidget(1, browse_btn)

        # Restructure: label above, then [edit + button] side by side
        r1 = QHBoxLayout()
        r1.setSpacing(8)
        r1.addWidget(self._creds_edit, 1)
        r1.addWidget(browse_btn)

        creds_outer = QVBoxLayout()
        creds_outer.setSpacing(5)
        creds_outer.addWidget(self._flbl("サービスアカウント JSON"))
        creds_outer.addLayout(r1)
        dc_v.addLayout(creds_outer)

        # Row 2: sheet name + connect
        r2 = QHBoxLayout()
        r2.setSpacing(8)
        sheet_outer = QVBoxLayout()
        sheet_outer.setSpacing(5)
        sheet_outer.addWidget(self._flbl("シート名"))
        self._sheet_name_edit = QLineEdit(self.settings.get("sheet_name"))
        self._sheet_name_edit.setPlaceholderText("物件管理番号マスター")
        sheet_outer.addWidget(self._sheet_name_edit)
        r2.addLayout(sheet_outer, 1)

        connect_btn = QPushButton("接続")
        connect_btn.setFixedWidth(80)
        connect_btn.setStyleSheet(
            f"QPushButton {{ background: {ACCENT}; color: #fff; border: none;"
            f"border-radius: 9px; min-height: 38px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: #3d5166; }}"
        )
        connect_btn.clicked.connect(self._connect_sheets)
        r2.addWidget(connect_btn)
        r2.setAlignment(connect_btn, Qt.AlignBottom)
        dc_v.addLayout(r2)

        self._sheets_stack.addWidget(disconn)   # index 0

        # ── Page 1: connected ─────────────────────────────────────────────────
        conn = QFrame()
        conn.setObjectName("innerSection")
        conn.setFrameShape(QFrame.NoFrame)
        conn.setStyleSheet(
            f"QFrame#innerSection {{ background: {OK_BG}; border: 1px solid {OK_BDR}; border-radius: 8px; }}")
        ban = QHBoxLayout(conn)
        ban.setContentsMargins(14, 10, 14, 10)
        ban.setSpacing(12)

        self._sheets_status_lbl = QLabel("接続済み")
        self._sheets_status_lbl.setStyleSheet(
            f"color: {OK_TEXT}; font-weight: 700; font-size: 13px; background: transparent;")
        ban.addWidget(self._sheets_status_lbl)
        ban.addStretch()

        refresh_btn = QPushButton("更新")
        refresh_btn.setFixedWidth(72)
        refresh_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {OK_TEXT}; border: 1px solid {OK_BDR};"
            f"border-radius: 7px; min-height: 32px; }}"
            f"QPushButton:hover {{ background: #d4f0de; }}")
        refresh_btn.clicked.connect(self._refresh_sheets)
        ban.addWidget(refresh_btn)

        disconnect_btn = QPushButton("切断")
        disconnect_btn.setFixedWidth(64)
        disconnect_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {ER_TEXT}; border: 1px solid {ER_BDR};"
            f"border-radius: 7px; min-height: 32px; }}"
            f"QPushButton:hover {{ background: {ER_BG}; }}")
        disconnect_btn.clicked.connect(self._disconnect_sheets)
        ban.addWidget(disconnect_btn)

        self._sheets_stack.addWidget(conn)   # index 1

        v.addWidget(self._sheets_stack)
        parent_layout.addWidget(card)

    # ── Build: property info card ──────────────────────────────────────────────

    def _build_property_card(self, parent_layout):
        card = QFrame()
        card.setObjectName("card")
        card.setFrameShape(QFrame.NoFrame)
        v = QVBoxLayout(card)
        v.setContentsMargins(18, 14, 18, 16)
        v.setSpacing(12)

        self._card_hdr(v, "物件情報", "#6366f1")

        # Top row: image type field + mode toggle
        top = QHBoxLayout()
        top.setSpacing(16)

        self._image_type_edit = QLineEdit(self.settings.get("last_image_type"))
        self._image_type_edit.setPlaceholderText("例: リビング")
        top.addWidget(self._fw("画像種別", self._image_type_edit), 1)

        # Segmented toggle track
        track = QFrame()
        track.setObjectName("segTrack")
        track.setFrameShape(QFrame.NoFrame)
        track_h = QHBoxLayout(track)
        track_h.setContentsMargins(3, 3, 3, 3)
        track_h.setSpacing(2)

        self._seg_auto = QPushButton("自動取得")
        self._seg_auto.setStyleSheet(_SEG_OFF)
        self._seg_auto.setEnabled(False)
        self._seg_auto.clicked.connect(self._on_seg_auto)
        track_h.addWidget(self._seg_auto)

        self._seg_manual = QPushButton("手動入力")
        self._seg_manual.setStyleSheet(_SEG_ON)
        self._seg_manual.clicked.connect(self._on_seg_manual)
        track_h.addWidget(self._seg_manual)

        top.addWidget(self._fw("入力モード", track))

        v.addLayout(top)

        # Fields stack
        self._prop_stack = QStackedWidget()
        self._prop_stack.setStyleSheet("background: transparent;")

        # ── Page 0: auto / Sheets mode ────────────────────────────────────────
        auto_page = QWidget()
        auto_page.setStyleSheet("background: transparent;")
        auto_v = QVBoxLayout(auto_page)
        auto_v.setContentsMargins(0, 0, 0, 0)
        auto_v.setSpacing(10)

        auto_grid = QGridLayout()
        auto_grid.setHorizontalSpacing(14)
        auto_grid.setVerticalSpacing(14)
        auto_grid.setColumnStretch(0, 1)
        auto_grid.setColumnStretch(1, 1)
        auto_grid.setColumnStretch(2, 1)

        self._property_combo = QComboBox()
        self._property_combo.currentIndexChanged.connect(
            lambda _: self._on_property_changed())
        auto_grid.addWidget(self._fw("物件名", self._property_combo), 0, 0, 1, 2)

        self._room_combo = QComboBox()
        self._room_combo.currentIndexChanged.connect(
            lambda _: self._on_room_changed())
        auto_grid.addWidget(self._fw("部屋番号", self._room_combo), 0, 2)
        auto_v.addLayout(auto_grid)

        # Info bar
        info_f = QFrame()
        info_f.setObjectName("innerSection")
        info_f.setFrameShape(QFrame.NoFrame)
        info_h = QHBoxLayout(info_f)
        info_h.setContentsMargins(14, 9, 14, 9)
        info_h.setSpacing(24)
        self._lbl_mgmt    = QLabel("管理番号: —")
        self._lbl_city    = QLabel("市区: —")
        self._lbl_station = QLabel("最寄駅: —")
        for lbl in (self._lbl_mgmt, self._lbl_city, self._lbl_station):
            lbl.setStyleSheet(f"color: {T_SEC}; font-size: 12px; background: transparent;")
            info_h.addWidget(lbl)
        info_h.addStretch()
        auto_v.addWidget(info_f)

        self._prop_stack.addWidget(auto_page)   # index 0

        # ── Page 1: manual mode ───────────────────────────────────────────────
        manual_page = QWidget()
        manual_page.setStyleSheet("background: transparent;")
        manual_v = QVBoxLayout(manual_page)
        manual_v.setContentsMargins(0, 0, 0, 0)
        manual_v.setSpacing(10)

        mgrid = QGridLayout()
        mgrid.setHorizontalSpacing(14)
        mgrid.setVerticalSpacing(14)
        mgrid.setColumnStretch(0, 1)
        mgrid.setColumnStretch(1, 1)
        mgrid.setColumnStretch(2, 1)

        self._property_edit = QLineEdit(self.settings.get("last_property"))
        self._property_edit.setPlaceholderText("物件名を入力してください")
        mgrid.addWidget(self._fw("物件名", self._property_edit), 0, 0, 1, 2)

        self._room_edit = QLineEdit(self.settings.get("last_room"))
        self._room_edit.setPlaceholderText("101")
        mgrid.addWidget(self._fw("部屋番号", self._room_edit), 0, 2)

        self._mgmt_edit = QLineEdit(self.settings.get("last_management_number"))
        self._mgmt_edit.setPlaceholderText("RM-R000001")
        mgrid.addWidget(self._fw("管理番号", self._mgmt_edit), 1, 0)

        self._city_combo = QComboBox()
        self._city_combo.setEditable(True)
        self._city_combo.addItems(["名古屋", "知立", "刈谷", "岡崎"])
        self._city_combo.setCurrentText(self.settings.get("last_city"))
        self._city_combo.currentTextChanged.connect(
            lambda _: self._toggle_nagoya_fields())
        mgrid.addWidget(self._fw("市区", self._city_combo), 1, 1)

        self._hiragana_edit = QLineEdit(self.settings.get("last_hiragana"))
        self._hiragana_edit.setPlaceholderText("さ")
        self._hiragana_fw = self._fw("よみがな (名古屋のみ)", self._hiragana_edit)
        mgrid.addWidget(self._hiragana_fw, 2, 0)

        self._station_edit = QLineEdit(self.settings.get("last_station"))
        self._station_edit.setPlaceholderText("栄")
        self._station_fw = self._fw("最寄駅 (名古屋のみ)", self._station_edit)
        mgrid.addWidget(self._station_fw, 2, 1)

        manual_v.addLayout(mgrid)
        self._prop_stack.addWidget(manual_page)  # index 1

        self._prop_stack.setCurrentIndex(1)      # default: manual mode
        v.addWidget(self._prop_stack)

        self._toggle_nagoya_fields()
        parent_layout.addWidget(card)

    # ── Build: files card ─────────────────────────────────────────────────────

    def _build_files_card(self, parent_layout):
        card = QFrame()
        card.setObjectName("card")
        card.setFrameShape(QFrame.NoFrame)
        v = QVBoxLayout(card)
        v.setContentsMargins(18, 14, 18, 16)
        v.setSpacing(12)

        self._card_hdr(v, "ファイル", "#f59e0b")

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(14)
        grid.setColumnStretch(0, 1)

        def _row(r, label_text, attr, slot):
            edit = QLineEdit()
            edit.setReadOnly(True)
            setattr(self, attr, edit)
            btn = QPushButton("参照")
            btn.setFixedWidth(66)
            btn.setMinimumHeight(38)
            btn.clicked.connect(slot)
            fw = self._fw(label_text, edit)
            grid.addWidget(fw, r, 0)
            grid.addWidget(btn, r, 1, Qt.AlignBottom)

        _row(0, "入力フォルダ",  "_input_edit",  self._pick_input)
        _row(1, "ロゴファイル",  "_logo_edit",   self._pick_logo)
        _row(2, "出力フォルダ",  "_output_edit", self._pick_output)

        self._input_edit.setText(self.settings.get("last_input_dir"))
        self._logo_edit.setText(self.settings.get("last_logo_path"))
        self._output_edit.setText(self.settings.get("last_output_dir"))

        v.addLayout(grid)
        parent_layout.addWidget(card)

    # ── Build: action row ─────────────────────────────────────────────────────

    def _build_action_row(self, parent_layout):
        row = QHBoxLayout()
        row.setSpacing(10)
        row.setContentsMargins(0, 0, 0, 0)

        self._run_btn = QPushButton("▶  処理開始")
        self._run_btn.setStyleSheet(_BTN_PRI)
        self._run_btn.clicked.connect(self._run_processing)
        row.addWidget(self._run_btn)

        self._retry_btn = QPushButton("↻  失敗ファイルを再処理")
        self._retry_btn.setEnabled(False)
        self._retry_btn.setStyleSheet(_BTN_GHOST)
        self._retry_btn.clicked.connect(self._retry_failed)
        row.addWidget(self._retry_btn)

        clear_btn = QPushButton("ログをクリア")
        clear_btn.setStyleSheet(_BTN_GHOST)
        clear_btn.clicked.connect(self._clear_logs)
        row.addWidget(clear_btn)

        row.addStretch()
        parent_layout.addLayout(row)

    # ── Build: log card (right pane) ──────────────────────────────────────────

    def _build_log_card(self, container: QFrame):
        v = QVBoxLayout(container)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        hdr_w = QWidget()
        hdr_w.setStyleSheet("background: transparent;")
        hdr_v = QVBoxLayout(hdr_w)
        hdr_v.setContentsMargins(18, 14, 18, 0)
        hdr_v.setSpacing(12)

        hdr_h = QHBoxLayout()
        hdr_h.setSpacing(8)

        dot = QLabel()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"background: {ACCENT}; border-radius: 4px;")
        hdr_h.addWidget(dot)

        title_lbl = QLabel("処理ログ")
        title_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {T_PRI};")
        hdr_h.addWidget(title_lbl)
        hdr_h.addStretch()

        self._chip_total = self._pill("0 件", INNER_BG, T_SEC, CARD_BDR)
        hdr_h.addWidget(self._chip_total)

        self._chip_ok = self._pill("成功 0", OK_BG, OK_TEXT, OK_BDR)
        hdr_h.addWidget(self._chip_ok)

        self._chip_err = self._pill("エラー 0", ER_BG, ER_TEXT, ER_BDR)
        hdr_h.addWidget(self._chip_err)

        hdr_v.addLayout(hdr_h)

        div = QFrame()
        div.setObjectName("divider")
        div.setFrameShape(QFrame.NoFrame)
        div.setFixedHeight(1)
        hdr_v.addWidget(div)

        v.addWidget(hdr_w)

        # ── Log area: empty state or log text ─────────────────────────────────
        self._log_stack = QStackedWidget()
        self._log_stack.setStyleSheet("background: transparent;")

        # Page 0: empty state
        empty = QLabel("ここに処理結果が表示されます")
        empty.setAlignment(Qt.AlignCenter)
        empty.setStyleSheet(f"color: {T_MUT}; font-size: 13px;")
        self._log_stack.addWidget(empty)

        # Page 1: log text area
        mono = "Consolas" if sys.platform == "win32" else "Menlo"
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setFont(QFont(mono, 11))
        self._log_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self._log_stack.addWidget(self._log_text)

        v.addWidget(self._log_stack, 1)

        # ── Footer: progress ──────────────────────────────────────────────────
        ftr_div = QFrame()
        ftr_div.setObjectName("divider")
        ftr_div.setFrameShape(QFrame.NoFrame)
        ftr_div.setFixedHeight(1)
        v.addWidget(ftr_div)

        ftr_w = QWidget()
        ftr_w.setStyleSheet("background: transparent;")
        ftr_v = QVBoxLayout(ftr_w)
        ftr_v.setContentsMargins(18, 10, 18, 14)
        ftr_v.setSpacing(6)

        lbl_row = QHBoxLayout()
        self._progress_lbl = QLabel("準備完了")
        self._progress_lbl.setStyleSheet(f"color: {T_SEC}; font-size: 11px;")
        lbl_row.addWidget(self._progress_lbl)
        lbl_row.addStretch()
        self._progress_pct = QLabel("0%")
        self._progress_pct.setStyleSheet(f"color: {T_SEC}; font-size: 11px;")
        lbl_row.addWidget(self._progress_pct)
        ftr_v.addLayout(lbl_row)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setFixedHeight(6)
        ftr_v.addWidget(self._progress_bar)

        v.addWidget(ftr_w)

    # ── Google Sheets handlers ─────────────────────────────────────────────────

    def _pick_credentials(self):
        init = str(Path(self._creds_edit.text()).parent) \
            if self._creds_edit.text() else str(Path.home())
        path, _ = QFileDialog.getOpenFileName(
            self, "サービスアカウントJSONを選択", init,
            "JSONファイル (*.json);;すべてのファイル (*.*)")
        if path:
            self._creds_edit.setText(path)
            self.settings.save("credentials_path", path)

    def _connect_sheets(self):
        creds = self._creds_edit.text().strip()
        sheet = self._sheet_name_edit.text().strip()
        if not creds:
            QMessageBox.warning(self, "接続エラー", "認証情報ファイルを選択してください。")
            return
        if not sheet:
            QMessageBox.warning(self, "接続エラー", "シート名を入力してください。")
            return
        self.settings.save_many({"credentials_path": creds, "sheet_name": sheet})
        try:
            self.sheets.connect(creds, sheet)
        except SheetsError as e:
            QMessageBox.critical(self, "シートエラー", str(e))
            return

        names = self.sheets.property_names()
        count = self.sheets.record_count

        self._sheets_status_lbl.setText(
            f"接続済み  —  {sheet}  （{count} 件 / {len(names)} 物件）")
        self._sheets_stack.setCurrentIndex(1)

        self._seg_auto.setEnabled(True)
        self._on_seg_auto()   # switch to auto mode

        self._property_combo.blockSignals(True)
        self._property_combo.clear()
        self._property_combo.addItems(names)
        last = self.settings.get("last_property")
        if last in names:
            self._property_combo.setCurrentText(last)
        elif names:
            self._property_combo.setCurrentIndex(0)
        self._property_combo.blockSignals(False)

        self._on_property_changed()
        self._set_status("ready", f"Sheets 接続済み  —  {count} 件")

    def _disconnect_sheets(self):
        self.sheets.disconnect()
        self._sheets_stack.setCurrentIndex(0)

        self._property_combo.blockSignals(True)
        self._property_combo.clear()
        self._property_combo.blockSignals(False)
        self._room_combo.blockSignals(True)
        self._room_combo.clear()
        self._room_combo.blockSignals(False)

        self._property_edit.setText(self.settings.get("last_property"))
        self._room_edit.setText(self.settings.get("last_room"))

        self._seg_auto.setEnabled(False)
        self._on_seg_manual()   # switch to manual mode
        self._set_status("ready", "切断済み  —  手動入力モード")

    def _refresh_sheets(self):
        try:
            self.sheets.refresh()
        except SheetsError as e:
            QMessageBox.critical(self, "シートエラー", str(e))
            return
        names = self.sheets.property_names()
        count = self.sheets.record_count
        sheet = self.settings.get("sheet_name")
        self._sheets_status_lbl.setText(
            f"接続済み  —  {sheet}  （{count} 件 / {len(names)} 物件）")

        self._property_combo.blockSignals(True)
        self._property_combo.clear()
        self._property_combo.addItems(names)
        cur = self._property_combo.currentText()
        if cur in names:
            self._property_combo.setCurrentText(cur)
        self._property_combo.blockSignals(False)

        self._on_property_changed()
        self._set_status("ready", f"シート更新完了  —  {count} 件")

    # ── Property / Room handlers ──────────────────────────────────────────────

    def _on_seg_auto(self):
        if not self.sheets.is_connected:
            QMessageBox.information(
                self, "Sheets未接続",
                "「Google スプレッドシート連携」で接続してから\n「自動取得」モードに切り替えてください。")
            self._seg_auto.setStyleSheet(_SEG_OFF)
            self._seg_manual.setStyleSheet(_SEG_ON)
            return
        self._seg_auto.setStyleSheet(_SEG_ON)
        self._seg_manual.setStyleSheet(_SEG_OFF)
        self._prop_stack.setCurrentIndex(0)

    def _on_seg_manual(self):
        self._seg_auto.setStyleSheet(_SEG_OFF)
        self._seg_manual.setStyleSheet(_SEG_ON)
        self._prop_stack.setCurrentIndex(1)

    def _on_property_changed(self):
        if not self.sheets.is_connected:
            return
        prop = self._property_combo.currentText().strip()
        if not prop:
            return
        rooms = self.sheets.rooms_for(prop)

        self._room_combo.blockSignals(True)
        self._room_combo.clear()
        self._room_combo.addItems(rooms)
        last = self.settings.get("last_room")
        if last in rooms:
            self._room_combo.setCurrentText(last)
        elif rooms:
            self._room_combo.setCurrentIndex(0)
        self._room_combo.blockSignals(False)

        self._refresh_property_info()

    def _on_room_changed(self):
        if self.sheets.is_connected:
            self._refresh_property_info()

    def _refresh_property_info(self):
        if not self.sheets.is_connected:
            return
        prop = self._property_combo.currentText().strip()
        room = self._room_combo.currentText().strip()
        if not prop or not room:
            return

        mgmt = self.sheets.management_number(prop, room)
        city = self.sheets.city(prop, room)
        hira = self.sheets.hiragana(prop, room)
        sta  = self.sheets.station(prop, room)

        self._lbl_mgmt.setText(f"管理番号: {mgmt or '—'}")

        is_nagoya = city.lower() in ("nagoya", "名古屋")
        if is_nagoya and (not hira or not sta):
            self._lbl_city.setStyleSheet(f"color: {OG_TEXT}; font-size: 12px; background: transparent;")
            self._lbl_city.setText(f"市区: {city}  ⚠ よみがな・最寄駅が未登録です")
        else:
            self._lbl_city.setStyleSheet(f"color: {T_SEC}; font-size: 12px; background: transparent;")
            self._lbl_city.setText(f"市区: {city or '—'}")

        parts = [s for s in (sta, f"（{hira}）" if hira else "") if s]
        self._lbl_station.setText(
            f"最寄駅: {'　'.join(parts)}" if parts else "最寄駅: —")

    def _toggle_nagoya_fields(self):
        is_nagoya = self._city_combo.currentText().strip().lower() in ("nagoya", "名古屋")
        self._hiragana_fw.setEnabled(is_nagoya)
        self._station_fw.setEnabled(is_nagoya)

    # ── File pickers ──────────────────────────────────────────────────────────

    def _pick_input(self):
        d = QFileDialog.getExistingDirectory(
            self, "入力フォルダを選択",
            self._input_edit.text() or str(Path.home()))
        if d:
            self._input_edit.setText(d)
            self.settings.save("last_input_dir", d)

    def _pick_logo(self):
        init = str(Path(self._logo_edit.text()).parent) \
            if self._logo_edit.text() else str(Path.home())
        f, _ = QFileDialog.getOpenFileName(
            self, "ロゴファイルを選択", init,
            "画像ファイル (*.png *.jpg *.jpeg);;すべてのファイル (*.*)")
        if f:
            self._logo_edit.setText(f)
            self.settings.save("last_logo_path", f)

    def _pick_output(self):
        d = QFileDialog.getExistingDirectory(
            self, "出力フォルダを選択",
            self._output_edit.text() or str(Path.home()))
        if d:
            self._output_edit.setText(d)
            self.settings.save("last_output_dir", d)

    # ── Input validation ──────────────────────────────────────────────────────

    def _resolve_fields(self):
        using_sheets = (self._prop_stack.currentIndex() == 0) and self.sheets.is_connected
        if using_sheets:
            prop = self._property_combo.currentText().strip()
            room = self._room_combo.currentText().strip()
        else:
            prop = self._property_edit.text().strip()
            room = self._room_edit.text().strip()

        image_type = self._image_type_edit.text().strip()
        if not prop:
            raise ValueError("物件名を入力してください。")
        if not room:
            raise ValueError("部屋番号を入力してください。")
        if not image_type:
            raise ValueError("画像種別を入力してください（例：リビング）。")

        if using_sheets:
            mgmt = self.sheets.management_number(prop, room)
            city = self.sheets.city(prop, room)
            hira = self.sheets.hiragana(prop, room)
            sta  = self.sheets.station(prop, room)
            if not city:
                raise ValueError(
                    f"シートに市区が登録されていません。\n物件: {prop}  部屋: {room}\n"
                    "シートに市区を入力して「更新」を押してください。")
            if city.lower() in ("nagoya", "名古屋") and (not hira or not sta):
                raise ValueError(
                    "この名古屋物件のよみがなまたは最寄駅がシートに未登録です。\n"
                    "両方を入力してから「更新」を押してください。")
        else:
            mgmt = self._mgmt_edit.text().strip()
            city = self._city_combo.currentText().strip()
            hira = self._hiragana_edit.text().strip()
            sta  = self._station_edit.text().strip()
            if not city:
                raise ValueError("市区を入力してください。")
            if city.lower() in ("nagoya", "名古屋") and (not hira or not sta):
                raise ValueError("名古屋の場合はよみがなと最寄駅を入力してください。")

        errs = []
        if not self._input_edit.text():
            errs.append("入力フォルダを選択してください。")
        elif not Path(self._input_edit.text()).exists():
            errs.append("入力フォルダが見つかりません。")
        if not self._logo_edit.text():
            errs.append("ロゴファイルを選択してください。")
        elif not Path(self._logo_edit.text()).exists():
            errs.append("ロゴファイルが見つかりません。")
        if not self._output_edit.text():
            errs.append("出力フォルダを選択してください。")
        if errs:
            raise ValueError("\n".join(f"・{e}" for e in errs))

        return prop, room, mgmt, city, hira, sta, image_type

    # ── Processing ────────────────────────────────────────────────────────────

    def _run_processing(self):
        if self._worker and self._worker.isRunning():
            return
        try:
            fields = self._resolve_fields()
        except ValueError as e:
            QMessageBox.warning(self, "入力エラー", str(e))
            return
        prop, room, mgmt, city, hira, sta, image_type = fields
        self.settings.save_many({
            "last_property": prop, "last_room": room,
            "last_image_type": image_type, "last_management_number": mgmt,
            "last_city": city, "last_hiragana": hira, "last_station": sta,
        })
        self._clear_logs()
        self._start_worker(prop, room, mgmt, city, hira, sta, image_type, retry_files=None)

    def _retry_failed(self):
        if (self._worker and self._worker.isRunning()) or not self.last_failed:
            return
        try:
            fields = self._resolve_fields()
        except ValueError as e:
            QMessageBox.warning(self, "入力エラー", str(e))
            return
        prop, room, mgmt, city, hira, sta, image_type = fields
        self._start_worker(prop, room, mgmt, city, hira, sta, image_type,
                           retry_files=list(self.last_failed))

    def _start_worker(self, prop, room, mgmt, city, hira, sta, image_type, retry_files):
        n = len(retry_files) if retry_files else None
        lbl = f"{n} 件を再処理中..." if retry_files else "処理を開始しています..."
        self._progress_lbl.setText(lbl)
        self._progress_pct.setText("0%")
        self._progress_bar.setValue(0)
        self._run_btn.setEnabled(False)
        self._retry_btn.setEnabled(False)
        self._set_status("running", lbl)

        kwargs = dict(
            input_dir=Path(self._input_edit.text()),
            logo_path=Path(self._logo_edit.text()),
            output_dir=Path(self._output_edit.text()),
            city=city, property_name=prop, room=room,
            image_type=image_type, management_number=mgmt,
            hiragana=hira, station=sta,
            verbose=True, retry_files=retry_files,
        )
        self._worker = ProcessingWorker(kwargs)
        self._worker.progress_signal.connect(self._on_progress)
        self._worker.finished_signal.connect(self._on_finished)
        self._worker.error_signal.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, current, total, source, output, status):
        pct = int(current / total * 100) if total else 0
        self._progress_bar.setValue(pct)
        self._progress_pct.setText(f"{pct}%")
        self._progress_lbl.setText(f"{current} / {total}  —  {source}")
        self._set_status("running", f"処理中  {current}/{total}")
        if "✅" in status:
            self._append_success(f"{source}  →  {output}")
        else:
            self._append_error(f"{source}: {status.replace('❌ ', '')}")

    def _on_finished(self, results: dict):
        self.last_failed = [r["file"] for r in results.get("failed", [])]
        n_ok   = len(results.get("processed", []))
        n_fail = len(self.last_failed)

        self._run_btn.setEnabled(True)
        self._progress_bar.setValue(100)
        self._progress_pct.setText("100%")
        self._progress_lbl.setText(f"完了  —  成功 {n_ok} 件  /  失敗 {n_fail} 件")
        self._set_status("done", f"完了  —  成功 {n_ok} 件  /  失敗 {n_fail} 件")

        if self.last_failed:
            self._retry_btn.setText(f"↻  失敗ファイルを再処理（{n_fail} 件）")
            self._retry_btn.setEnabled(True)
        else:
            self._retry_btn.setText("↻  失敗ファイルを再処理")
            self._retry_btn.setEnabled(False)

        msg = f"処理が完了しました\n\n成功: {n_ok} 件\n失敗: {n_fail} 件"
        if results.get("log_file"):
            msg += f"\n\nログファイル:\n{results['log_file']}"
        QMessageBox.information(self, "完了", msg)

    def _on_error(self, error_msg: str):
        self._run_btn.setEnabled(True)
        self._progress_bar.setValue(0)
        self._progress_pct.setText("—")
        self._progress_lbl.setText("エラーが発生しました")
        self._set_status("error", "エラーが発生しました")
        self._append_error(f"致命的なエラー: {error_msg}")
        QMessageBox.critical(self, "処理エラー", error_msg)

    # ── Log helpers ───────────────────────────────────────────────────────────

    def _append_success(self, msg: str):
        if self._log_stack.currentIndex() == 0:
            self._log_stack.setCurrentIndex(1)
        self._log_ok_count += 1
        self._update_log_chips()
        ts  = datetime.now().strftime("%H:%M:%S")
        esc = html_mod.escape(msg)
        self._log_text.append(
            f'<span style="color:{OK_TEXT};">&#10003;&nbsp;&nbsp;{esc}</span>'
            f'&nbsp;&nbsp;<span style="color:{T_MUT}; font-size:10px;">{ts}</span>')
        self._log_text.ensureCursorVisible()

    def _append_error(self, msg: str):
        if self._log_stack.currentIndex() == 0:
            self._log_stack.setCurrentIndex(1)
        self._log_err_count += 1
        self._update_log_chips()
        ts  = datetime.now().strftime("%H:%M:%S")
        esc = html_mod.escape(msg)
        self._log_text.append(
            f'<span style="color:{ER_TEXT};">&#10007;&nbsp;&nbsp;{esc}</span>'
            f'&nbsp;&nbsp;<span style="color:{T_MUT}; font-size:10px;">{ts}</span>')
        self._log_text.ensureCursorVisible()

    def _clear_logs(self):
        self._log_text.clear()
        self._log_ok_count  = 0
        self._log_err_count = 0
        self._update_log_chips()
        self._log_stack.setCurrentIndex(0)
        self._progress_bar.setValue(0)
        self._progress_pct.setText("0%")
        self._progress_lbl.setText("準備完了")

    def _update_log_chips(self):
        total = self._log_ok_count + self._log_err_count
        self._chip_total.setText(f"{total} 件")
        self._chip_ok.setText(f"成功 {self._log_ok_count}")
        self._chip_err.setText(f"エラー {self._log_err_count}")


# ─────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Rent Magazine")
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)

    if sys.platform == "win32":
        app.setFont(QFont("Yu Gothic UI", 10))
    elif sys.platform == "darwin":
        app.setFont(QFont("Hiragino Sans", 10))

    window = RentMagazineApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
