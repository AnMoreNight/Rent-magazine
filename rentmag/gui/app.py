"""Main application window."""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QScrollArea, QFrame, QProgressBar, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QFileDialog, QMessageBox, QDialog, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap, QColor, QBrush

from rentmag.settings import SettingsManager
from rentmag.worker import ProcessingWorker
from rentmag.gui.styles import (
    QSS, STEPS,
    BG, CARD, BORDER, ACCENT, ACCENT2,
    SUCCESS, WARN, ERROR, ERROR_BG, WARN_BG,
    TEXT1, TEXT2, MUTED, PANEL_BG,
)
from rentmag.gui.widgets import (
    StepBadge, PreviewImage,
    card, label, hline, btn, prop_field,
)
from rentmag.gui.dialogs import FileSettingsDialog


# ── Window ─────────────────────────────────────────────────────────────────────

class RentMagApp(QMainWindow):
    """
    Two-panel single-page layout:
      Left panel  (fixed 260 px) — property inputs, controls, summary
      Right area  (flexible)     — progress, log, preview
    """

    def __init__(self):
        super().__init__()
        self.settings:      SettingsManager           = SettingsManager()
        self._worker:       Optional[ProcessingWorker] = None
        self._paused:       bool                      = False
        self._failed_files: list                      = []
        self._log_rows:     list                      = []

        self.setWindowTitle("RentMag")
        self.setMinimumSize(1080, 720)
        self.resize(1280, 840)
        self.setStyleSheet(QSS)

        root = QWidget()
        self.setCentralWidget(root)
        vl = QVBoxLayout(root)
        vl.setSpacing(0)
        vl.setContentsMargins(0, 0, 0, 0)

        vl.addWidget(self._build_topbar())

        body = QHBoxLayout()
        body.setSpacing(0)
        body.setContentsMargins(0, 0, 0, 0)
        body.addWidget(self._build_left_panel())
        body.addWidget(self._build_right_panel(), 1)
        vl.addLayout(body, 1)

        self._load_property_fields()

    # ── Top bar ───────────────────────────────────────────────────────────────

    def _build_topbar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("topbar")
        bar.setFixedHeight(42)

        lay = QHBoxLayout(bar)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.setSpacing(10)

        t = label("RentMag", "topbar-title")
        t.setFont(QFont("Segoe UI", 13, QFont.Bold))
        lay.addWidget(t)
        lay.addStretch()

        self._conn_label = label("", "conn-label")
        self._conn_label.setStyleSheet("color: rgba(255,255,255,0.55); font-size: 10px;")
        lay.addWidget(self._conn_label)

        cfg = btn("設定", "btn-topbar")
        cfg.clicked.connect(self._open_file_settings)
        lay.addWidget(cfg)
        return bar

    # ── Left panel ─────────────────────────────────────────────────────────────

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("left-panel")
        panel.setFixedWidth(258)

        # Inner scroll so narrow panel never clips
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        inner = QWidget()
        inner.setObjectName("left-panel")
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(0)

        lay.addWidget(self._panel_section("物件情報"))
        lay.addWidget(self._build_property_form())
        lay.addWidget(self._panel_sep())

        lay.addWidget(self._panel_section("コントロール"))
        lay.addWidget(self._build_controls_section())
        lay.addWidget(self._panel_sep())

        lay.addWidget(self._panel_section("処理サマリー"))
        lay.addWidget(self._build_summary_section())
        lay.addStretch()

        scroll.setWidget(inner)
        pl = QVBoxLayout(panel)
        pl.setSpacing(0)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.addWidget(scroll)
        return panel

    def _panel_section(self, text: str) -> QLabel:
        l = QLabel(text.upper())
        l.setObjectName("panel-heading")
        l.setContentsMargins(0, 10, 0, 4)
        return l

    def _panel_sep(self) -> QFrame:
        f = QFrame()
        f.setObjectName("panel-sep")
        f.setContentsMargins(0, 8, 0, 8)
        return f

    def _build_property_form(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        lay = QGridLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setHorizontalSpacing(6)
        lay.setVerticalSpacing(4)
        lay.setColumnMinimumWidth(0, 78)
        lay.setColumnStretch(1, 1)

        self._pf: dict = {}

        def row(r, lbl_text, key, placeholder=""):
            lay.addWidget(label(lbl_text, "field-label"), r, 0)
            f = prop_field(placeholder)
            lay.addWidget(f, r, 1)
            self._pf[key] = f

        row(0,  "管理番号",         "prop_mgmt",  "RM-R000001")
        row(1,  "物件名",           "prop_name",  "物件名")
        row(2,  "棟",               "prop_build", "北棟")
        row(3,  "号室 / 区画",      "prop_room",  "101")
        row(4,  "表示名",           "prop_disp",  "")
        row(5,  "種別",             "prop_type",  "住居")
        row(6,  "所在地",           "prop_addr",  "市区町村")
        row(7,  "ステータス",       "prop_sta_s", "募集中")
        row(8,  "ひらがな(名古屋)", "prop_hira",  "さ")
        row(9,  "最寄駅(名古屋)",   "prop_sta",   "栄")
        row(10, "画像種別",         "prop_itype", "リビング")
        row(11, "備考",             "prop_notes", "")

        # Save button below form
        save_row = QHBoxLayout()
        save_row.setContentsMargins(0, 6, 0, 0)
        sb = btn("保存", "btn-secondary")
        sb.clicked.connect(self._save_property_fields)
        save_row.addWidget(sb)
        save_row.addStretch()
        lay.addLayout(save_row, 12, 0, 1, 2)

        return w

    def _build_controls_section(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        # Start / Pause / Stop
        row1 = QHBoxLayout()
        row1.setSpacing(4)
        self._start_btn = btn("▶  処理開始", "btn-primary")
        self._start_btn.clicked.connect(self._start_processing)
        row1.addWidget(self._start_btn, 2)
        self._pause_btn = btn("⏸", "btn-pause")
        self._pause_btn.setFixedWidth(34)
        self._pause_btn.setEnabled(False)
        self._pause_btn.clicked.connect(self._toggle_pause)
        row1.addWidget(self._pause_btn)
        self._stop_btn = btn("■", "btn-stop")
        self._stop_btn.setFixedWidth(34)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop_processing)
        row1.addWidget(self._stop_btn)
        lay.addLayout(row1)

        self._retry_btn = btn("失敗を再実行", "btn-secondary")
        self._retry_btn.setEnabled(False)
        self._retry_btn.clicked.connect(self._retry_failed)
        lay.addWidget(self._retry_btn)

        # Output path
        out_lbl = label("出力先", "field-label")
        out_lbl.setContentsMargins(0, 6, 0, 2)
        lay.addWidget(out_lbl)

        self._output_path_lbl = QLabel("-")
        self._output_path_lbl.setWordWrap(True)
        self._output_path_lbl.setStyleSheet(f"""
            background: #DADDE3; border-radius: 3px;
            padding: 4px 6px; color: {TEXT2}; font-size: 10px;
        """)
        lay.addWidget(self._output_path_lbl)

        open_btn = btn("フォルダを開く", "btn-link")
        open_btn.clicked.connect(self._open_output_folder)
        lay.addWidget(open_btn)

        return w

    def _build_summary_section(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        lay = QGridLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setHorizontalSpacing(12)
        lay.setVerticalSpacing(3)
        lay.setColumnStretch(1, 1)

        self._stat_labels: dict = {}
        STATS = [
            ("投入",   "total",   ""),
            ("通常",   "regular", ""),
            ("THETA",  "theta",   ""),
            ("処理済", "done",    ""),
            ("処理中", "active",  ACCENT2),
            ("成功",   "success", SUCCESS),
            ("失敗",   "failed",  ERROR),
            ("スキップ","skipped", ""),
        ]
        for r, (lbl_t, key, color) in enumerate(STATS):
            lay.addWidget(label(lbl_t, "stat-lbl"), r, 0)
            v = label("0", "stat-num")
            if color:
                v.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 700;")
            else:
                v.setStyleSheet("font-size: 12px; font-weight: 600;")
            lay.addWidget(v, r, 1, Qt.AlignRight)
            self._stat_labels[key] = v

        return w

    # ── Right panel ────────────────────────────────────────────────────────────

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(f"background: {BG};")
        lay = QVBoxLayout(panel)
        lay.setSpacing(6)
        lay.setContentsMargins(8, 8, 8, 8)

        lay.addWidget(self._card_wrap(self._build_progress_section()))
        lay.addWidget(self._card_wrap(self._build_log_section()), 1)
        lay.addWidget(self._card_wrap(self._build_preview_section()))

        return panel

    def _card_wrap(self, widget: QWidget) -> QFrame:
        """Wrap a section widget in a bordered card frame."""
        frame = QFrame()
        frame.setObjectName("right-card")
        inner = QVBoxLayout(frame)
        inner.setSpacing(0)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.addWidget(widget)
        return frame

    def _build_progress_section(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        w.setFixedHeight(170)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 14, 20, 14)
        lay.setSpacing(6)

        # Row: big % + bar + times
        top = QHBoxLayout()
        top.setSpacing(14)
        self._pct_label = label("0%", "pct-label")
        self._pct_label.setFont(QFont("Segoe UI", 26, QFont.Bold))
        self._pct_label.setFixedWidth(72)
        top.addWidget(self._pct_label)

        bar_col = QVBoxLayout()
        bar_col.setSpacing(3)
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setFixedHeight(8)
        bar_col.addWidget(self._progress_bar)

        times_row = QHBoxLayout()
        el = label("経過", "field-label")
        times_row.addWidget(el)
        self._elapsed_label = QLabel("00:00:00")
        self._elapsed_label.setStyleSheet(f"color: {TEXT1}; font-size: 11px; font-weight: 600;")
        times_row.addWidget(self._elapsed_label)
        times_row.addStretch()
        eta_l = label("残り", "field-label")
        times_row.addWidget(eta_l)
        self._eta_label = QLabel("-")
        self._eta_label.setStyleSheet(f"color: {TEXT2}; font-size: 11px;")
        times_row.addWidget(self._eta_label)
        bar_col.addLayout(times_row)
        top.addLayout(bar_col, 1)
        lay.addLayout(top)

        # Current file + step
        info = QHBoxLayout()
        self._file_label = QLabel("-")
        self._file_label.setStyleSheet(f"color: {TEXT2}; font-size: 10px;")
        self._file_label.setWordWrap(False)
        info.addWidget(self._file_label, 1)
        self._step_label = QLabel("-")
        self._step_label.setStyleSheet(f"color: {ACCENT2}; font-size: 10px; font-weight: 600;")
        self._step_label.setAlignment(Qt.AlignRight)
        info.addWidget(self._step_label)
        lay.addLayout(info)

        # Step badges
        sep = QFrame()
        sep.setObjectName("right-sep-h")
        lay.addWidget(sep)

        badges = QHBoxLayout()
        badges.setSpacing(0)
        self._step_badges: list = []
        for i, name in enumerate(STEPS):
            badge = StepBadge(name)
            self._step_badges.append(badge)
            badges.addWidget(badge, 1)
            if i < len(STEPS) - 1:
                conn = label("─")
                conn.setStyleSheet(f"color: {MUTED}; margin-bottom: 12px;")
                conn.setAlignment(Qt.AlignCenter)
                conn.setFixedWidth(12)
                badges.addWidget(conn)
        lay.addLayout(badges)

        return w

    def _build_log_section(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)

        # Header: title + filter
        hdr = QHBoxLayout()
        hdr.addWidget(label("ログ", "section-title"))
        hdr.addStretch()
        self._log_filter = QComboBox()
        self._log_filter.addItems(["すべて", "INFO", "WARN", "ERROR"])
        self._log_filter.setFixedWidth(90)
        self._log_filter.currentTextChanged.connect(self._rebuild_log_table)
        hdr.addWidget(self._log_filter)
        lay.addLayout(hdr)

        # Log table inside a bordered frame
        log_frame = QFrame()
        log_frame.setObjectName("log-frame")
        lf_lay = QVBoxLayout(log_frame)
        lf_lay.setContentsMargins(0, 0, 0, 0)
        lf_lay.setSpacing(0)

        self._log_table = QTableWidget(0, 3)
        self._log_table.setHorizontalHeaderLabels(["日時", "Lv", "メッセージ"])
        self._log_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._log_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._log_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self._log_table.verticalHeader().setVisible(False)
        self._log_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._log_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._log_table.setShowGrid(True)
        lf_lay.addWidget(self._log_table)
        lay.addWidget(log_frame, 1)

        # Footer buttons with visible borders
        foot = QHBoxLayout()
        foot.setSpacing(6)
        b1 = btn("ログを保存", "btn-secondary"); b1.clicked.connect(self._save_log)
        b2 = btn("クリア",     "btn-secondary"); b2.clicked.connect(self._clear_log)
        foot.addWidget(b1)
        foot.addWidget(b2)
        foot.addStretch()
        lay.addLayout(foot)
        return w

    def _build_preview_section(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        w.setFixedHeight(252)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(6)

        lay.addWidget(label("プレビュー", "section-title"))

        img_row = QHBoxLayout()
        img_row.setSpacing(6)

        def _col(title: str, attr: str):
            col = QVBoxLayout()
            col.setSpacing(3)
            lbl = label(title, "field-label")
            lbl.setAlignment(Qt.AlignCenter)
            col.addWidget(lbl)
            img = PreviewImage(title)
            col.addWidget(img, alignment=Qt.AlignCenter)
            setattr(self, attr, img)
            return col

        img_row.addLayout(_col("元画像",    "_prev_orig"))
        img_row.addLayout(_col("レタッチ後", "_prev_ret"))
        img_row.addLayout(_col("ロゴ挿入後", "_prev_final"))
        lay.addLayout(img_row)

        # File info
        sep = QFrame()
        sep.setObjectName("right-sep-h")
        lay.addWidget(sep)

        info_grid = QGridLayout()
        info_grid.setSpacing(3)
        info_grid.setColumnMinimumWidth(0, 58)
        self._file_info: dict = {}
        for r, (lt, key) in enumerate([
            ("ファイル名", "filename"), ("種別",  "type"),
            ("解像度",    "resolution"), ("向き", "orientation"), ("サイズ", "size"),
        ]):
            info_grid.addWidget(label(lt, "field-label"), r, 0)
            v = label("-")
            info_grid.addWidget(v, r, 1)
            self._file_info[key] = v
        lay.addLayout(info_grid)
        lay.addStretch()
        return w

    # ── Property persistence ──────────────────────────────────────────────────

    def _load_property_fields(self) -> None:
        s  = self.settings
        pf = self._pf
        pf["prop_mgmt"].setText(s.get("last_management_number"))
        pf["prop_name"].setText(s.get("last_property"))
        pf["prop_build"].setText(s.get("last_building"))
        pf["prop_room"].setText(s.get("last_room"))
        pf["prop_disp"].setText(s.get("last_display_name"))
        pf["prop_addr"].setText(s.get("last_city"))
        pf["prop_type"].setText(s.get("last_type"))
        pf["prop_sta_s"].setText(s.get("last_status"))
        pf["prop_hira"].setText(s.get("last_hiragana"))
        pf["prop_sta"].setText(s.get("last_station"))
        pf["prop_itype"].setText(s.get("last_image_type", "リビング"))
        pf["prop_notes"].setText(s.get("last_notes"))
        self._output_path_lbl.setText(s.get("last_output_dir") or "-")
        self._refresh_conn_label()

    def _save_property_fields(self) -> None:
        s  = self.settings
        pf = self._pf
        s.set("last_management_number", pf["prop_mgmt"].text().strip())
        s.set("last_property",          pf["prop_name"].text().strip())
        s.set("last_building",          pf["prop_build"].text().strip())
        s.set("last_room",              pf["prop_room"].text().strip())
        s.set("last_display_name",      pf["prop_disp"].text().strip())
        s.set("last_city",              pf["prop_addr"].text().strip())
        s.set("last_type",              pf["prop_type"].text().strip())
        s.set("last_status",            pf["prop_sta_s"].text().strip())
        s.set("last_hiragana",          pf["prop_hira"].text().strip())
        s.set("last_station",           pf["prop_sta"].text().strip())
        s.set("last_image_type",        pf["prop_itype"].text().strip() or "リビング")
        s.set("last_notes",             pf["prop_notes"].text().strip())
        s.save()

    def _refresh_conn_label(self) -> None:
        if self.settings.get("last_input_dir") and self.settings.get("last_logo_path"):
            self._conn_label.setText("設定済み")
            self._conn_label.setStyleSheet("color: rgba(180,255,180,0.75); font-size: 10px;")
        else:
            self._conn_label.setText("ファイル未設定")
            self._conn_label.setStyleSheet("color: rgba(255,200,100,0.85); font-size: 10px;")

    # ── Dialogs ───────────────────────────────────────────────────────────────

    def _open_file_settings(self) -> None:
        dlg = FileSettingsDialog(self.settings, self._pf, self)
        if dlg.exec_() == QDialog.Accepted:
            self._output_path_lbl.setText(self.settings.get("last_output_dir") or "-")
            self._refresh_conn_label()

    def _open_output_folder(self) -> None:
        out = self.settings.get("last_output_dir")
        if out and Path(out).exists():
            subprocess.Popen(f'explorer "{out}"')
        else:
            QMessageBox.information(self, "情報", "出力フォルダが設定されていません。")

    # ── Processing ────────────────────────────────────────────────────────────

    def _validate(self) -> list:
        s  = self.settings
        pf = self._pf
        errs = []
        inp = s.get("last_input_dir")
        lgp = s.get("last_logo_path")
        out = s.get("last_output_dir")
        if not inp:
            errs.append("投入フォルダが未設定です（設定ボタンから設定してください）")
        elif not Path(inp).exists():
            errs.append(f"投入フォルダが存在しません: {inp}")
        if not lgp:
            errs.append("ロゴファイルが未設定です")
        elif not Path(lgp).exists():
            errs.append(f"ロゴファイルが存在しません: {lgp}")
        if not out:
            errs.append("出力フォルダが未設定です")
        if not pf["prop_name"].text().strip():
            errs.append("物件名を入力してください")
        if not pf["prop_room"].text().strip():
            errs.append("号室を入力してください")
        return errs

    def _build_params(self) -> dict:
        s  = self.settings
        pf = self._pf
        return {
            "input_dir":         s.get("last_input_dir"),
            "logo_path":         s.get("last_logo_path"),
            "output_dir":        s.get("last_output_dir"),
            "city":              pf["prop_addr"].text().strip(),
            "property_name":     pf["prop_name"].text().strip(),
            "room":              pf["prop_room"].text().strip(),
            "image_type":        pf["prop_itype"].text().strip() or "リビング",
            "management_number": pf["prop_mgmt"].text().strip(),
            "hiragana":          pf["prop_hira"].text().strip(),
            "station":           pf["prop_sta"].text().strip(),
        }

    def _set_running(self, running: bool) -> None:
        self._start_btn.setEnabled(not running)
        self._pause_btn.setEnabled(running)
        self._stop_btn.setEnabled(running)
        self._retry_btn.setEnabled(not running and bool(self._failed_files))

    def _reset_ui(self) -> None:
        self._clear_log()
        self._pct_label.setText("0%")
        self._progress_bar.setValue(0)
        self._file_label.setText("-")
        self._step_label.setText("-")
        self._elapsed_label.setText("00:00:00")
        self._eta_label.setText("-")
        for b in self._step_badges:
            b.setState("pending")
        for v in self._stat_labels.values():
            v.setText("0")
        self._prev_orig.clearImage()
        self._prev_ret.clearImage()
        self._prev_final.clearImage()
        for v in self._file_info.values():
            v.setText("-")

    def _start_processing(self, retry_files=None) -> None:
        errs = self._validate()
        if errs:
            QMessageBox.warning(self, "設定エラー", "\n".join(errs))
            return
        self._save_property_fields()
        self._reset_ui()
        self._failed_files = []
        self._paused = False
        self._pause_btn.setText("⏸")
        self._set_running(True)

        self._worker = ProcessingWorker(self._build_params(), retry_files=retry_files)
        self._worker.log_signal.connect(self._append_log)
        self._worker.stats_signal.connect(self._on_stats)
        self._worker.step_signal.connect(self._on_step)
        self._worker.progress_signal.connect(self._on_progress)
        self._worker.elapsed_signal.connect(lambda t: self._elapsed_label.setText(t))
        self._worker.finished_signal.connect(self._on_finished)
        self._worker.error_signal.connect(self._on_error)
        self._worker.start()

    def _toggle_pause(self) -> None:
        if not self._worker:
            return
        ts = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        if self._paused:
            self._worker.resume()
            self._paused = False
            self._pause_btn.setText("⏸")
            self._append_log(ts, "INFO", "処理を再開しました。")
        else:
            self._worker.pause()
            self._paused = True
            self._pause_btn.setText("▶")
            self._append_log(ts, "INFO", "処理を一時停止しました。")

    def _stop_processing(self) -> None:
        if not self._worker:
            return
        if QMessageBox.question(self, "停止確認", "処理を停止しますか？",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            if self._paused:
                self._worker.resume()
            self._worker.stop()

    def _retry_failed(self) -> None:
        if self._failed_files:
            self._start_processing(retry_files=self._failed_files)

    # ── Log ───────────────────────────────────────────────────────────────────

    def _append_log(self, ts: str, level: str, msg: str) -> None:
        self._log_rows.append((ts, level, msg))
        self._add_log_row(ts, level, msg)

    def _add_log_row(self, ts: str, level: str, msg: str) -> None:
        flt = self._log_filter.currentText()
        if flt not in ("すべて", level):
            return
        row = self._log_table.rowCount()
        self._log_table.insertRow(row)
        if level == "ERROR":
            bg, fg_lv, fg_m = QColor(ERROR_BG), QColor(ERROR),   QColor(ERROR)
        elif level == "WARN":
            bg, fg_lv, fg_m = QColor(WARN_BG),  QColor(WARN),    QColor(TEXT1)
        else:
            bg, fg_lv, fg_m = QColor(CARD),      QColor(TEXT2),   QColor(TEXT1)
        for col, (text, fg) in enumerate([(ts, QColor(MUTED)), (level, fg_lv), (msg, fg_m)]):
            item = QTableWidgetItem(text)
            item.setBackground(QBrush(bg))
            item.setForeground(QBrush(fg))
            self._log_table.setItem(row, col, item)
        self._log_table.scrollToBottom()

    def _rebuild_log_table(self, _=None) -> None:
        self._log_table.setRowCount(0)
        for ts, lv, msg in self._log_rows:
            self._add_log_row(ts, lv, msg)

    def _clear_log(self) -> None:
        self._log_rows.clear()
        self._log_table.setRowCount(0)

    def _save_log(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "ログを保存", "", "テキスト (*.txt);;CSV (*.csv)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("日時\tレベル\tメッセージ\n")
                for ts, lv, msg in self._log_rows:
                    f.write(f"{ts}\t{lv}\t{msg}\n")
            QMessageBox.information(self, "完了", f"保存しました:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "エラー", str(e))

    # ── Worker slots ──────────────────────────────────────────────────────────

    def _on_step(self, name: str, idx: int) -> None:
        _map = {
            "検出":    "ファイル検出中",
            "リネーム": "リネーム処理中",
            "振り分け": "振り分け処理中",
            "レタッチ": "Camera Raw 処理中",
            "ロゴ挿入": "ロゴ挿入処理中",
            "JPG保存": "JPG 書き出し中",
        }
        self._step_label.setText(_map.get(name, name))
        for i, b in enumerate(self._step_badges):
            b.setState("done" if i < idx else ("active" if i == idx else "pending"))

    def _on_progress(self, current: int, total: int, src: str, out: str) -> None:
        pct = int(current / total * 100) if total > 0 else 0
        self._pct_label.setText(f"{pct}%")
        self._progress_bar.setValue(pct)
        self._file_label.setText(Path(src).name if src else "-")
        try:
            if self._worker and self._worker._t0 and current > 0:
                elapsed   = (datetime.now() - self._worker._t0).total_seconds()
                remaining = elapsed / current * (total - current)
                h, rem    = divmod(int(remaining), 3600)
                m, s      = divmod(rem, 60)
                self._eta_label.setText(f"{h:02d}:{m:02d}:{s:02d}")
        except Exception:
            pass
        if src and Path(src).exists():
            self._load_preview(src, self._prev_orig, update_info=True)
        if out and Path(out).exists():
            self._load_preview(out, self._prev_final)
            self._load_preview(out, self._prev_ret)

    def _load_preview(self, path: str, target: PreviewImage,
                      update_info: bool = False) -> None:
        try:
            pmap = QPixmap(path)
            if pmap.isNull():
                return
            target.setImage(pmap)
            if update_info:
                p = Path(path)
                w, h = pmap.width(), pmap.height()
                self._file_info["filename"].setText(p.name)
                self._file_info["resolution"].setText(f"{w} × {h}")
                self._file_info["orientation"].setText("縦" if h > w else "横")
                self._file_info["type"].setText("通常画像")
                try:
                    self._file_info["size"].setText(f"{p.stat().st_size/1024/1024:.1f} MB")
                except Exception:
                    pass
        except Exception:
            pass

    def _on_stats(self, stats: dict) -> None:
        for k, lbl in self._stat_labels.items():
            lbl.setText(str(stats.get(k, 0)))

    def _on_finished(self, results: dict) -> None:
        self._set_running(False)
        self._failed_files = [r["file"] for r in results.get("failed", [])]
        self._retry_btn.setEnabled(bool(self._failed_files))
        self._pct_label.setText("100%")
        self._progress_bar.setValue(100)
        for b in self._step_badges:
            b.setState("done")
        n_ok  = len(results.get("processed", []))
        n_err = len(results.get("failed",    []))
        self._file_label.setText(f"完了 — 成功 {n_ok}件 / 失敗 {n_err}件")
        self._eta_label.setText("00:00:00")

    def _on_error(self, message: str) -> None:
        ts = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        self._append_log(ts, "ERROR", message)
        self._set_running(False)
        QMessageBox.critical(self, "エラー", message)
