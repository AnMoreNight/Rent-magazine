#!/usr/bin/env python3
"""
Rent Magazine — Phase 1 Desktop GUI (PyQt5)
物件写真処理システム

All user-facing text is in Japanese.
Code identifiers and comments stay in English.
"""

import sys
import json
import html as html_mod
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
        QGridLayout, QGroupBox, QLabel, QLineEdit, QPushButton, QComboBox,
        QProgressBar, QTextEdit, QSplitter, QFileDialog, QMessageBox,
        QFrame, QStackedWidget, QSizePolicy, QStatusBar,
    )
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
    from PyQt5.QtGui import QFont
except ImportError:
    print("PyQt5が見つかりません。次のコマンドを実行してください: pip install PyQt5")
    sys.exit(1)

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("必須ライブラリが不足しています。次のコマンドを実行してください: pip install Pillow numpy")
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

# ─────────────────────────────────────────────────────────────
# Application Stylesheet
# ─────────────────────────────────────────────────────────────

STYLESHEET = """
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #d1d1d6;
    border-radius: 10px;
    margin-top: 18px;
    padding: 6px 2px 2px 2px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    top: 0px;
    padding: 1px 8px;
    color: #3a3a3c;
    font-weight: bold;
    font-size: 10pt;
}
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #c7c7cc;
    border-radius: 6px;
    padding: 5px 9px;
    color: #1c1c1e;
    selection-background-color: #0071e3;
    min-height: 22px;
}
QLineEdit:focus {
    border: 1.5px solid #0071e3;
    background-color: #fafafe;
}
QLineEdit:read-only {
    background-color: #f5f5f7;
    color: #636366;
    border-color: #d1d1d6;
}
QLineEdit:disabled {
    background-color: #f2f2f7;
    color: #aeaeb2;
    border-color: #d1d1d6;
}
QComboBox {
    background-color: #ffffff;
    border: 1px solid #c7c7cc;
    border-radius: 6px;
    padding: 5px 9px;
    color: #1c1c1e;
    min-height: 22px;
}
QComboBox:focus {
    border: 1.5px solid #0071e3;
    background-color: #fafafe;
}
QComboBox::drop-down {
    border: none;
    width: 22px;
}
QComboBox:disabled {
    background-color: #f2f2f7;
    color: #aeaeb2;
    border-color: #d1d1d6;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #c7c7cc;
    border-radius: 6px;
    selection-background-color: #e5f0fb;
    selection-color: #1c1c1e;
    outline: none;
    padding: 2px;
}
QPushButton {
    background-color: #e5e5ea;
    color: #1c1c1e;
    border: 1px solid #c7c7cc;
    border-radius: 6px;
    padding: 5px 14px;
    min-height: 26px;
    font-size: 10pt;
}
QPushButton:hover {
    background-color: #d8d8dd;
    border-color: #aeaeb2;
}
QPushButton:pressed {
    background-color: #c7c7cc;
}
QPushButton:disabled {
    color: #aeaeb2;
    background-color: #eeeeef;
    border-color: #d8d8dd;
}
QProgressBar {
    background-color: #e5e5ea;
    border: none;
    border-radius: 4px;
    max-height: 7px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background-color: #0071e3;
    border-radius: 4px;
}
QTextEdit {
    background-color: #ffffff;
    border: 1px solid #d1d1d6;
    border-radius: 8px;
    padding: 4px;
    color: #1c1c1e;
}
QTextEdit#logSuccess {
    background-color: #f6fff8;
    border-color: #c3e6cb;
}
QTextEdit#logError {
    background-color: #fff8f8;
    border-color: #f5c6cb;
}
QSplitter::handle {
    background-color: #e5e5ea;
    width: 6px;
    margin: 0 2px;
}
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    border-radius: 4px;
    margin: 2px 0;
}
QScrollBar::handle:vertical {
    background: #c7c7cc;
    border-radius: 4px;
    min-height: 24px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QStatusBar {
    border-top: 1px solid #d1d1d6;
    color: #636366;
    font-size: 9pt;
    padding: 2px 8px;
}
"""

_BTN_PRIMARY = (
    "QPushButton {"
    " background-color: #0071e3;"
    " color: #ffffff;"
    " border: none;"
    " border-radius: 8px;"
    " padding: 7px 28px;"
    " font-weight: bold;"
    " font-size: 11pt;"
    "}"
    "QPushButton:hover { background-color: #0077ed; }"
    "QPushButton:pressed { background-color: #005dc0; }"
    "QPushButton:disabled {"
    " background-color: #b8d4ef;"
    " color: #e5effa;"
    " border: none;"
    "}"
)


# ─────────────────────────────────────────────────────────────
# Settings Manager
# ─────────────────────────────────────────────────────────────

class SettingsManager:
    """Read/write config.json in the same directory as this script."""

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
    progress_signal  = pyqtSignal(int, int, str, str, str)
    finished_signal  = pyqtSignal(dict)
    error_signal     = pyqtSignal(str)

    def __init__(self, process_kwargs: dict):
        super().__init__()
        self._kwargs = process_kwargs

    def run(self):
        try:
            results = process_images(**self._kwargs, progress_callback=self._on_progress)
            self.finished_signal.emit(results)
        except Exception as e:
            self.error_signal.emit(str(e))

    def _on_progress(self, current: int, total: int,
                     source: str, output: str, status: str):
        self.progress_signal.emit(current, total, source, output, status)


# ─────────────────────────────────────────────────────────────
# Main Application Window
# ─────────────────────────────────────────────────────────────

class RentMagazineApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.settings     = SettingsManager()
        self.sheets       = PropertyMasterClient()
        self.last_failed: list = []
        self._worker: ProcessingWorker = None

        self.setWindowTitle("Rent Magazine — 物件写真処理システム")
        self.resize(1060, 960)
        self.setMinimumSize(860, 720)

        central = QWidget()
        self.setCentralWidget(central)
        self._layout = QVBoxLayout(central)
        self._layout.setSpacing(10)
        self._layout.setContentsMargins(16, 14, 16, 14)

        self._build_header()
        self._build_sheets_section()
        self._build_property_section()
        self._build_files_section()
        self._build_controls_section()
        self._build_logs_section()

        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.showMessage("準備完了  —  Rent Magazine Phase 1")

        # Auto-connect to Sheets if saved credentials exist
        creds = self.settings.get("credentials_path")
        sheet = self.settings.get("sheet_name")
        if creds and Path(creds).exists() and sheet:
            QTimer.singleShot(250, self._connect_sheets)

    # ─────────────────────────────────────────────────────────
    # UI Construction
    # ─────────────────────────────────────────────────────────

    def _build_header(self):
        header = QFrame()
        header.setStyleSheet("background-color: transparent;")
        h = QHBoxLayout(header)
        h.setContentsMargins(4, 0, 4, 2)
        h.setSpacing(0)

        title = QLabel("Rent Magazine")
        title.setFont(QFont("Yu Gothic UI", 17, QFont.Bold))
        title.setStyleSheet("color: #1c1c1e; letter-spacing: 0px;")
        h.addWidget(title)

        sep = QLabel("  |  ")
        sep.setStyleSheet("color: #aeaeb2; font-size: 14pt;")
        h.addWidget(sep)

        sub = QLabel("物件写真処理システム")
        sub.setFont(QFont("Yu Gothic UI", 12))
        sub.setStyleSheet("color: #3a3a3c;")
        h.addWidget(sub)

        h.addStretch()

        badge = QLabel("Phase 1")
        badge.setFont(QFont("Yu Gothic UI", 9))
        badge.setStyleSheet(
            "color: #0071e3;"
            "background-color: #e5f0fb;"
            "border: 1px solid #b8d4ef;"
            "border-radius: 10px;"
            "padding: 2px 12px;"
        )
        h.addWidget(badge)

        self._layout.addWidget(header)

        # Accent line under header
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #d1d1d6; border: none;")
        self._layout.addWidget(line)

    def _build_sheets_section(self):
        group = QGroupBox("Google Sheets  —  物件管理番号マスター")
        outer = QVBoxLayout(group)
        outer.setContentsMargins(14, 10, 14, 12)
        outer.setSpacing(6)

        # Config row (shown when disconnected)
        self._sheets_config = QFrame()
        self._sheets_config.setStyleSheet("background: transparent;")
        cfg = QGridLayout(self._sheets_config)
        cfg.setContentsMargins(0, 0, 0, 0)
        cfg.setSpacing(8)

        lbl_creds = QLabel("認証情報ファイル:")
        lbl_creds.setStyleSheet("color: #636366;")
        cfg.addWidget(lbl_creds, 0, 0)
        self._creds_edit = QLineEdit(self.settings.get("credentials_path"))
        self._creds_edit.setReadOnly(True)
        self._creds_edit.setPlaceholderText("サービスアカウントJSONファイルを選択してください")
        cfg.addWidget(self._creds_edit, 0, 1)

        browse_btn = QPushButton("参照")
        browse_btn.setFixedWidth(62)
        browse_btn.clicked.connect(self._pick_credentials)
        cfg.addWidget(browse_btn, 0, 2)

        lbl_sheet = QLabel("シート名:")
        lbl_sheet.setStyleSheet("color: #636366;")
        cfg.addWidget(lbl_sheet, 0, 3)
        self._sheet_name_edit = QLineEdit(self.settings.get("sheet_name"))
        self._sheet_name_edit.setMinimumWidth(190)
        cfg.addWidget(self._sheet_name_edit, 0, 4)

        connect_btn = QPushButton("接続")
        connect_btn.setFixedWidth(68)
        connect_btn.clicked.connect(self._connect_sheets)
        cfg.addWidget(connect_btn, 0, 5)

        cfg.setColumnStretch(1, 1)
        cfg.setColumnStretch(4, 1)
        outer.addWidget(self._sheets_config)

        # Connected banner (hidden until connected)
        self._sheets_banner = QFrame()
        self._sheets_banner.setStyleSheet("background: transparent;")
        self._sheets_banner.hide()
        ban = QHBoxLayout(self._sheets_banner)
        ban.setContentsMargins(0, 0, 0, 0)
        ban.setSpacing(10)

        self._sheets_status_lbl = QLabel("● 接続済み")
        self._sheets_status_lbl.setStyleSheet(
            "color: #1a8a3a; font-weight: bold; font-size: 10pt;")
        ban.addWidget(self._sheets_status_lbl)
        ban.addStretch()

        refresh_btn = QPushButton("↺  更新")
        refresh_btn.setFixedWidth(80)
        refresh_btn.setStyleSheet(
            "QPushButton { color: #0071e3; background: transparent;"
            " border: 1px solid #0071e3; border-radius: 6px; padding: 4px 10px; }"
            "QPushButton:hover { background: #e5f0fb; }")
        refresh_btn.clicked.connect(self._refresh_sheets)
        ban.addWidget(refresh_btn)

        disconnect_btn = QPushButton("切断")
        disconnect_btn.setFixedWidth(68)
        disconnect_btn.setStyleSheet(
            "QPushButton { color: #d33; background: transparent;"
            " border: 1px solid #d33; border-radius: 6px; padding: 4px 10px; }"
            "QPushButton:hover { background: #fff0f0; }")
        disconnect_btn.clicked.connect(self._disconnect_sheets)
        ban.addWidget(disconnect_btn)

        outer.addWidget(self._sheets_banner)
        self._layout.addWidget(group)

    def _build_property_section(self):
        group = QGroupBox("物件情報")
        v = QVBoxLayout(group)
        v.setContentsMargins(14, 10, 14, 12)
        v.setSpacing(8)

        # ── Selector row ──────────────────────────────────────────────────────
        row0 = QHBoxLayout()
        row0.setSpacing(0)

        self._selector_stack = QStackedWidget()
        self._selector_stack.setStyleSheet("background: transparent;")

        # Page 0 — Sheets mode: readonly dropdowns
        sheets_sel = QFrame()
        sheets_sel.setStyleSheet("background: transparent;")
        h0 = QHBoxLayout(sheets_sel)
        h0.setContentsMargins(0, 0, 0, 0)
        h0.setSpacing(8)

        lbl0a = QLabel("物件名:")
        lbl0a.setFont(QFont("Yu Gothic UI", 10, QFont.Bold))
        h0.addWidget(lbl0a)
        self._property_combo = QComboBox()
        self._property_combo.setMinimumWidth(220)
        self._property_combo.currentIndexChanged.connect(
            lambda _: self._on_property_changed())
        h0.addWidget(self._property_combo, 2)

        h0.addSpacing(16)
        lbl0b = QLabel("部屋番号:")
        lbl0b.setFont(QFont("Yu Gothic UI", 10, QFont.Bold))
        h0.addWidget(lbl0b)
        self._room_combo = QComboBox()
        self._room_combo.setMinimumWidth(90)
        self._room_combo.currentIndexChanged.connect(
            lambda _: self._on_room_changed())
        h0.addWidget(self._room_combo, 1)
        self._selector_stack.addWidget(sheets_sel)   # index 0

        # Page 1 — Manual mode: plain text fields
        manual_sel = QFrame()
        manual_sel.setStyleSheet("background: transparent;")
        h1 = QHBoxLayout(manual_sel)
        h1.setContentsMargins(0, 0, 0, 0)
        h1.setSpacing(8)

        mode_badge = QLabel("手動入力")
        mode_badge.setStyleSheet(
            "color: #b25000;"
            "background-color: #fff4e5;"
            "font-weight: bold;"
            "border: 1px solid #f5c080;"
            "border-radius: 5px;"
            "padding: 2px 10px;")
        h1.addWidget(mode_badge)

        h1.addSpacing(8)
        lbl1a = QLabel("物件名:")
        lbl1a.setFont(QFont("Yu Gothic UI", 10, QFont.Bold))
        h1.addWidget(lbl1a)
        self._property_edit = QLineEdit(self.settings.get("last_property"))
        self._property_edit.setMinimumWidth(200)
        self._property_edit.setPlaceholderText("物件名を入力してください")
        h1.addWidget(self._property_edit, 2)

        h1.addSpacing(16)
        lbl1b = QLabel("部屋番号:")
        lbl1b.setFont(QFont("Yu Gothic UI", 10, QFont.Bold))
        h1.addWidget(lbl1b)
        self._room_edit = QLineEdit(self.settings.get("last_room"))
        self._room_edit.setMinimumWidth(80)
        self._room_edit.setPlaceholderText("101")
        h1.addWidget(self._room_edit, 1)
        self._selector_stack.addWidget(manual_sel)   # index 1

        self._selector_stack.setCurrentIndex(1)      # default: manual mode
        row0.addWidget(self._selector_stack, 3)

        # Image type — always visible on the right
        row0.addSpacing(20)
        lbl_type = QLabel("画像種別:")
        lbl_type.setFont(QFont("Yu Gothic UI", 10, QFont.Bold))
        row0.addWidget(lbl_type)
        self._image_type_edit = QLineEdit(self.settings.get("last_image_type"))
        self._image_type_edit.setMinimumWidth(120)
        self._image_type_edit.setPlaceholderText("例: リビング")
        row0.addWidget(self._image_type_edit, 1)

        v.addLayout(row0)

        # ── Info row ──────────────────────────────────────────────────────────
        self._info_stack = QStackedWidget()
        self._info_stack.setStyleSheet("background: transparent;")

        # Page 0 — Sheets auto-info labels
        sheets_page = QFrame()
        sheets_page.setStyleSheet(
            "background: #f8f8fa;"
            "border: 1px solid #e5e5ea;"
            "border-radius: 6px;")
        sp = QHBoxLayout(sheets_page)
        sp.setContentsMargins(12, 6, 12, 6)
        sp.setSpacing(24)
        self._lbl_mgmt    = QLabel("管理番号: —")
        self._lbl_mgmt.setStyleSheet("color: #636366; background: transparent;")
        sp.addWidget(self._lbl_mgmt)
        self._lbl_city    = QLabel("市区: —")
        self._lbl_city.setStyleSheet("color: #636366; background: transparent;")
        sp.addWidget(self._lbl_city)
        self._lbl_station = QLabel("最寄駅: —")
        self._lbl_station.setStyleSheet("color: #636366; background: transparent;")
        sp.addWidget(self._lbl_station)
        sp.addStretch()
        self._info_stack.addWidget(sheets_page)   # index 0

        # Page 1 — Manual entry fields
        manual_page = QFrame()
        manual_page.setStyleSheet("background: transparent;")
        mp = QHBoxLayout(manual_page)
        mp.setContentsMargins(0, 0, 0, 0)
        mp.setSpacing(8)

        mp.addWidget(QLabel("管理番号:"))
        self._mgmt_edit = QLineEdit(self.settings.get("last_management_number"))
        self._mgmt_edit.setFixedWidth(134)
        self._mgmt_edit.setPlaceholderText("RM-R000001")
        mp.addWidget(self._mgmt_edit)

        mp.addSpacing(8)
        mp.addWidget(QLabel("市区:"))
        self._city_combo = QComboBox()
        self._city_combo.setEditable(True)
        self._city_combo.addItems(["名古屋", "知立", "刈谷", "岡崎"])
        self._city_combo.setCurrentText(self.settings.get("last_city"))
        self._city_combo.setFixedWidth(110)
        self._city_combo.currentTextChanged.connect(
            lambda _: self._toggle_nagoya_fields())
        mp.addWidget(self._city_combo)

        mp.addSpacing(8)
        self._lbl_hiragana = QLabel("よみがな:")
        mp.addWidget(self._lbl_hiragana)
        self._hiragana_edit = QLineEdit(self.settings.get("last_hiragana"))
        self._hiragana_edit.setFixedWidth(68)
        self._hiragana_edit.setPlaceholderText("さ")
        mp.addWidget(self._hiragana_edit)

        mp.addSpacing(8)
        self._lbl_station_manual = QLabel("最寄駅:")
        mp.addWidget(self._lbl_station_manual)
        self._station_edit = QLineEdit(self.settings.get("last_station"))
        self._station_edit.setFixedWidth(124)
        self._station_edit.setPlaceholderText("栄")
        mp.addWidget(self._station_edit)
        mp.addStretch()

        self._info_stack.addWidget(manual_page)   # index 1
        self._info_stack.setCurrentIndex(1)
        v.addWidget(self._info_stack)

        self._toggle_nagoya_fields()
        self._layout.addWidget(group)

    def _build_files_section(self):
        group = QGroupBox("ファイル")
        grid = QGridLayout(group)
        grid.setContentsMargins(14, 10, 14, 12)
        grid.setSpacing(8)

        def _row(r, label, attr, slot):
            lbl = QLabel(label)
            lbl.setFont(QFont("Yu Gothic UI", 10, QFont.Bold))
            lbl.setStyleSheet("color: #3a3a3c;")
            grid.addWidget(lbl, r, 0)
            edit = QLineEdit()
            edit.setReadOnly(True)
            grid.addWidget(edit, r, 1)
            setattr(self, attr, edit)
            btn = QPushButton("参照")
            btn.setFixedWidth(62)
            btn.clicked.connect(slot)
            grid.addWidget(btn, r, 2)

        _row(0, "入力フォルダ:", "_input_edit",  self._pick_input)
        _row(1, "ロゴファイル:", "_logo_edit",   self._pick_logo)
        _row(2, "出力フォルダ:", "_output_edit", self._pick_output)

        self._input_edit.setText(self.settings.get("last_input_dir"))
        self._logo_edit.setText(self.settings.get("last_logo_path"))
        self._output_edit.setText(self.settings.get("last_output_dir"))

        grid.setColumnStretch(1, 1)
        self._layout.addWidget(group)

    def _build_controls_section(self):
        frame = QFrame()
        frame.setStyleSheet("background: transparent;")
        v = QVBoxLayout(frame)
        v.setContentsMargins(0, 4, 0, 4)
        v.setSpacing(10)

        # Button row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self._run_btn = QPushButton("▶  処理開始")
        self._run_btn.setMinimumHeight(42)
        self._run_btn.setFont(QFont("Yu Gothic UI", 11, QFont.Bold))
        self._run_btn.setStyleSheet(_BTN_PRIMARY)
        self._run_btn.clicked.connect(self._run_processing)
        btn_row.addWidget(self._run_btn)

        self._retry_btn = QPushButton("↺  失敗ファイルを再処理")
        self._retry_btn.setMinimumHeight(42)
        self._retry_btn.setEnabled(False)
        self._retry_btn.clicked.connect(self._retry_failed)
        btn_row.addWidget(self._retry_btn)

        clear_btn = QPushButton("ログをクリア")
        clear_btn.setMinimumHeight(42)
        clear_btn.clicked.connect(self._clear_logs)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        v.addLayout(btn_row)

        # Progress row
        prog_row = QHBoxLayout()
        prog_row.setSpacing(12)

        self._progress_lbl = QLabel("準備完了")
        self._progress_lbl.setStyleSheet("color: #636366; font-size: 9pt;")
        self._progress_lbl.setMinimumWidth(200)
        prog_row.addWidget(self._progress_lbl)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setFixedHeight(7)
        prog_row.addWidget(self._progress_bar, 1)

        v.addLayout(prog_row)
        self._layout.addWidget(frame)

    def _build_logs_section(self):
        mono = "Consolas" if sys.platform == "win32" else "Menlo"
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        ok_group = QGroupBox("成功ログ")
        ok_v = QVBoxLayout(ok_group)
        ok_v.setContentsMargins(10, 10, 10, 10)
        self._log_ok = QTextEdit()
        self._log_ok.setObjectName("logSuccess")
        self._log_ok.setReadOnly(True)
        self._log_ok.setFont(QFont(mono, 9))
        self._log_ok.setLineWrapMode(QTextEdit.WidgetWidth)
        ok_v.addWidget(self._log_ok)
        splitter.addWidget(ok_group)

        err_group = QGroupBox("エラーログ")
        err_v = QVBoxLayout(err_group)
        err_v.setContentsMargins(10, 10, 10, 10)
        self._log_err = QTextEdit()
        self._log_err.setObjectName("logError")
        self._log_err.setReadOnly(True)
        self._log_err.setFont(QFont(mono, 9))
        self._log_err.setLineWrapMode(QTextEdit.WidgetWidth)
        err_v.addWidget(self._log_err)
        splitter.addWidget(err_group)

        splitter.setSizes([530, 530])
        self._layout.addWidget(splitter, 1)   # stretch → fills remaining height

    # ─────────────────────────────────────────────────────────
    # Google Sheets Handlers
    # ─────────────────────────────────────────────────────────

    def _pick_credentials(self):
        init = str(Path(self._creds_edit.text()).parent) if self._creds_edit.text() else str(Path.home())
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

        self._sheets_config.hide()
        self._sheets_status_lbl.setText(
            f"●  接続済み  —  {sheet}　（{count}件　/　{len(names)}物件）")
        self._sheets_banner.show()

        self._selector_stack.setCurrentIndex(0)
        self._info_stack.setCurrentIndex(0)

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
        self.statusBar().showMessage(f"Sheets 接続済み  —  {sheet}  （{count}件）")

    def _disconnect_sheets(self):
        self.sheets.disconnect()
        self._sheets_banner.hide()
        self._sheets_config.show()

        self._property_combo.blockSignals(True)
        self._property_combo.clear()
        self._property_combo.blockSignals(False)

        self._room_combo.blockSignals(True)
        self._room_combo.clear()
        self._room_combo.blockSignals(False)

        self._property_edit.setText(self.settings.get("last_property"))
        self._room_edit.setText(self.settings.get("last_room"))

        self._selector_stack.setCurrentIndex(1)
        self._info_stack.setCurrentIndex(1)
        self._toggle_nagoya_fields()
        self.statusBar().showMessage("切断済み  —  手動入力モード")

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
            f"●  接続済み  —  {sheet}　（{count}件　/　{len(names)}物件）")

        self._property_combo.blockSignals(True)
        self._property_combo.clear()
        self._property_combo.addItems(names)
        cur = self._property_combo.currentText()
        if cur in names:
            self._property_combo.setCurrentText(cur)
        self._property_combo.blockSignals(False)

        self._on_property_changed()
        self.statusBar().showMessage(f"シート更新完了  —  {count}件")

    # ─────────────────────────────────────────────────────────
    # Property / Room Handlers
    # ─────────────────────────────────────────────────────────

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
            self._lbl_city.setStyleSheet("color: #b25000; background: transparent;")
            self._lbl_city.setText(f"市区: {city}  ⚠ よみがな・最寄駅がシートに未登録です")
        else:
            self._lbl_city.setStyleSheet("color: #636366; background: transparent;")
            self._lbl_city.setText(f"市区: {city or '—'}")

        parts = [s for s in (sta, f"（{hira}）" if hira else "") if s]
        self._lbl_station.setText(f"最寄駅: {'　'.join(parts)}" if parts else "最寄駅: —")

    def _toggle_nagoya_fields(self):
        is_nagoya = self._city_combo.currentText().strip().lower() in ("nagoya", "名古屋")
        for w in (self._lbl_hiragana, self._hiragana_edit,
                  self._lbl_station_manual, self._station_edit):
            w.setEnabled(is_nagoya)

    # ─────────────────────────────────────────────────────────
    # File Pickers
    # ─────────────────────────────────────────────────────────

    def _pick_input(self):
        d = QFileDialog.getExistingDirectory(
            self, "入力フォルダを選択",
            self._input_edit.text() or str(Path.home()))
        if d:
            self._input_edit.setText(d)
            self.settings.save("last_input_dir", d)

    def _pick_logo(self):
        init = str(Path(self._logo_edit.text()).parent) if self._logo_edit.text() else str(Path.home())
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

    # ─────────────────────────────────────────────────────────
    # Input Validation
    # ─────────────────────────────────────────────────────────

    def _resolve_fields(self):
        """Validate all inputs and return (prop, room, mgmt, city, hira, sta, image_type)."""
        if self.sheets.is_connected:
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

        if self.sheets.is_connected:
            mgmt = self.sheets.management_number(prop, room)
            city = self.sheets.city(prop, room)
            hira = self.sheets.hiragana(prop, room)
            sta  = self.sheets.station(prop, room)
            if not city:
                raise ValueError(
                    f"シートに市区が登録されていません。\n"
                    f"  物件: {prop}\n  部屋: {room}\n\n"
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

    # ─────────────────────────────────────────────────────────
    # Processing
    # ─────────────────────────────────────────────────────────

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
        self._progress_lbl.setText(
            f"{n}件を再処理中..." if retry_files else "処理を開始しています...")
        self._progress_bar.setValue(0)
        self._run_btn.setEnabled(False)
        self._retry_btn.setEnabled(False)

        kwargs = dict(
            input_dir=Path(self._input_edit.text()),
            logo_path=Path(self._logo_edit.text()),
            output_dir=Path(self._output_edit.text()),
            city=city,
            property_name=prop,
            room=room,
            image_type=image_type,
            management_number=mgmt,
            hiragana=hira,
            station=sta,
            verbose=True,
            retry_files=retry_files,
        )
        self._worker = ProcessingWorker(kwargs)
        self._worker.progress_signal.connect(self._on_progress)
        self._worker.finished_signal.connect(self._on_finished)
        self._worker.error_signal.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, current: int, total: int,
                     source: str, output: str, status: str):
        pct = int(current / total * 100) if total else 0
        self._progress_bar.setValue(pct)
        self._progress_lbl.setText(f"{current} / {total}  —  {source}")
        self.statusBar().showMessage(f"処理中  {current}/{total}  —  {source}")
        if "✅" in status:
            self._append_success(f"{source}  →  {output}")
        else:
            self._append_error(f"{source}: {status.replace('❌ ', '')}")

    def _on_finished(self, results: dict):
        self.last_failed = [r["file"] for r in results.get("failed", [])]
        n_ok   = len(results.get("processed", []))
        n_fail = len(self.last_failed)

        self._run_btn.setEnabled(True)
        self._progress_bar.setValue(0)
        self._progress_lbl.setText("準備完了")
        self.statusBar().showMessage(
            f"完了  —  成功: {n_ok}件  /  失敗: {n_fail}件")

        if self.last_failed:
            self._retry_btn.setText(f"↺  失敗ファイルを再処理（{n_fail}件）")
            self._retry_btn.setEnabled(True)
        else:
            self._retry_btn.setText("↺  失敗ファイルを再処理")
            self._retry_btn.setEnabled(False)

        msg = f"処理が完了しました\n\n✅ 成功: {n_ok}件\n❌ 失敗: {n_fail}件"
        if results.get("log_file"):
            msg += f"\n\n📋 ログファイル:\n{results['log_file']}"
        QMessageBox.information(self, "完了", msg)

    def _on_error(self, error_msg: str):
        self._run_btn.setEnabled(True)
        self._progress_bar.setValue(0)
        self._progress_lbl.setText("エラーが発生しました")
        self.statusBar().showMessage("エラーが発生しました")
        self._append_error(f"致命的なエラー: {error_msg}")
        QMessageBox.critical(self, "処理エラー", error_msg)

    # ─────────────────────────────────────────────────────────
    # Log Helpers
    # ─────────────────────────────────────────────────────────

    def _append_success(self, msg: str):
        escaped = html_mod.escape(msg)
        self._log_ok.append(f'<span style="color:#1a6b1a;">{escaped}</span>')
        self._log_ok.ensureCursorVisible()

    def _append_error(self, msg: str):
        escaped = html_mod.escape(msg)
        self._log_err.append(f'<span style="color:#b22222;">{escaped}</span>')
        self._log_err.ensureCursorVisible()

    def _clear_logs(self):
        self._log_ok.clear()
        self._log_err.clear()


# ─────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Rent Magazine")
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
