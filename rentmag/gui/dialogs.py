"""Application dialogs."""

from __future__ import annotations

from typing import Dict

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QGroupBox, QFrame,
    QFileDialog, QMessageBox, QDialogButtonBox,
)

from PyQt5.QtCore import Qt

from rentmag.settings import SettingsManager
from rentmag.gui.styles import QSS, SUCCESS, WARN, ERROR, MUTED
from rentmag.gui.widgets import btn

try:
    from rentmag.sheets import PropertyMasterClient, SheetsError
    _SHEETS = True
except ImportError:
    _SHEETS = False


class FileSettingsDialog(QDialog):
    """
    Configure file paths (input folder, logo, output folder) and optionally
    auto-fill property info from a Google Sheets property master.

    prop_fields is a reference to the main window's QLineEdit dict so the
    Sheets auto-fill can write into those fields directly.
    """

    def __init__(self, settings: SettingsManager,
                 prop_fields: Dict[str, QLineEdit], parent=None):
        super().__init__(parent)
        self.settings    = settings
        self.prop_fields = prop_fields
        self._client: PropertyMasterClient | None = None

        self.setWindowTitle("ファイル・スプレッドシート設定")
        self.setMinimumWidth(520)
        self.setModal(True)
        self.setStyleSheet(QSS)

        self._build()
        self._load()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(18, 18, 18, 18)

        root.addWidget(self._build_paths_group())
        root.addWidget(self._build_sheets_group())

        ok_cancel = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_cancel.button(QDialogButtonBox.Ok).setText("保存")
        ok_cancel.button(QDialogButtonBox.Cancel).setText("キャンセル")
        ok_cancel.accepted.connect(self._accept)
        ok_cancel.rejected.connect(self.reject)
        root.addWidget(ok_cancel)

    def _build_paths_group(self) -> QGroupBox:
        grp = QGroupBox("ファイルパス設定")
        lay = QFormLayout(grp)
        lay.setSpacing(7)

        def _row(placeholder: str, pick_slot):
            row = QHBoxLayout()
            edit = QLineEdit()
            edit.setReadOnly(True)
            edit.setPlaceholderText(placeholder)
            row.addWidget(edit)
            b = btn("参照...", "btn-secondary")
            b.setFixedWidth(58)
            b.clicked.connect(pick_slot)
            row.addWidget(b)
            return row, edit

        r1, self.input_edit  = _row("画像フォルダのパス", self._pick_input)
        r2, self.logo_edit   = _row("logo.png のパス",    self._pick_logo)
        r3, self.output_edit = _row("出力フォルダのパス", self._pick_output)
        lay.addRow("投入フォルダ:", r1)
        lay.addRow("ロゴファイル:", r2)
        lay.addRow("出力フォルダ:", r3)
        return grp

    def _build_sheets_group(self) -> QGroupBox:
        grp = QGroupBox("Google スプレッドシート連携（物件情報の自動入力）")
        lay = QVBoxLayout(grp)
        lay.setSpacing(8)

        # ── Credentials / sheet name (FormLayout) ──────────────────────────
        form = QFormLayout()
        form.setSpacing(6)
        form.setLabelAlignment(Qt.AlignRight)

        r_creds = QHBoxLayout()
        self.creds_edit = QLineEdit()
        self.creds_edit.setPlaceholderText("service-account.json")
        r_creds.addWidget(self.creds_edit)
        b_creds = btn("参照...", "btn-secondary")
        b_creds.setFixedWidth(58)
        b_creds.clicked.connect(self._pick_creds)
        r_creds.addWidget(b_creds)
        form.addRow("認証ファイル:", r_creds)

        r_sheet = QHBoxLayout()
        self.sheet_edit = QLineEdit()
        self.sheet_edit.setPlaceholderText("物件管理番号マスター")
        r_sheet.addWidget(self.sheet_edit)
        b_conn = btn("接続", "btn-secondary")
        b_conn.setFixedWidth(58)
        b_conn.clicked.connect(self._connect)
        r_sheet.addWidget(b_conn)
        form.addRow("シート名:", r_sheet)

        lay.addLayout(form)

        # Status label
        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet(f"color: {MUTED}; font-size: 10px;")
        lay.addWidget(self._status_lbl)

        # ── Separator ──────────────────────────────────────────────────────
        sep = QFrame()
        sep.setStyleSheet(f"background: #D6DAE1; border: none; max-height: 1px;")
        lay.addWidget(sep)

        # ── Property / room selection ──────────────────────────────────────
        sel_grid = QGridLayout()
        sel_grid.setSpacing(6)
        sel_grid.setColumnMinimumWidth(0, 40)
        sel_grid.setColumnStretch(1, 1)
        sel_grid.setColumnMinimumWidth(2, 40)
        sel_grid.setColumnStretch(3, 1)

        sel_grid.addWidget(QLabel("物件:"), 0, 0)
        self.prop_combo = QComboBox()
        self.prop_combo.currentTextChanged.connect(self._on_property_changed)
        sel_grid.addWidget(self.prop_combo, 0, 1)

        sel_grid.addWidget(QLabel("号室:"), 0, 2)
        self.room_combo = QComboBox()
        sel_grid.addWidget(self.room_combo, 0, 3)

        lay.addLayout(sel_grid)

        b_fill = btn("物件情報を自動入力", "btn-secondary")
        b_fill.clicked.connect(self._auto_fill)
        lay.addWidget(b_fill)

        return grp

    # ── File pickers ───────────────────────────────────────────────────────────

    def _pick_input(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "投入フォルダ", self.settings.get("last_input_dir"))
        if d: self.input_edit.setText(d)

    def _pick_logo(self) -> None:
        f, _ = QFileDialog.getOpenFileName(self, "ロゴファイル", self.settings.get("last_logo_path"), "PNG (*.png)")
        if f: self.logo_edit.setText(f)

    def _pick_output(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "出力フォルダ", self.settings.get("last_output_dir"))
        if d: self.output_edit.setText(d)

    def _pick_creds(self) -> None:
        f, _ = QFileDialog.getOpenFileName(self, "認証ファイル", "", "JSON (*.json)")
        if f: self.creds_edit.setText(f)

    # ── Sheets ─────────────────────────────────────────────────────────────────

    def _connect(self) -> None:
        creds = self.creds_edit.text().strip()
        sheet = self.sheet_edit.text().strip()
        if not creds:
            self._set_status("❌ 認証ファイルを指定してください", ERROR)
            return
        try:
            client = PropertyMasterClient()
            client.connect(creds, sheet)
            self._client = client
            props = self._client.property_names()
            self.prop_combo.clear()
            self.prop_combo.addItems(props)
            self._set_status(f"✅ 接続成功（{len(props)}件）", SUCCESS)
        except Exception as e:
            self._set_status(f"❌ {e}", ERROR)

    def _on_property_changed(self, prop: str) -> None:
        if self._client and prop:
            try:
                self.room_combo.clear()
                self.room_combo.addItems(self._client.rooms_for(prop))
            except Exception:
                pass

    def _auto_fill(self) -> None:
        if not self._client:
            self._set_status("先にスプレッドシートに接続してください", WARN)
            return
        prop = self.prop_combo.currentText()
        room = self.room_combo.currentText()
        if not prop:
            return
        try:
            pf = self.prop_fields
            pf["prop_mgmt"].setText(self._client.management_number(prop, room))
            pf["prop_name"].setText(prop)
            pf["prop_room"].setText(room)
            _try_set(pf, "prop_build", lambda: self._client.building(prop, room))
            _try_set(pf, "prop_addr",  lambda: self._client.city(prop, room))
            _try_set(pf, "prop_type",  lambda: self._client.prop_type(prop, room))
            _try_set(pf, "prop_sta_s", lambda: self._client.status(prop, room))
            _try_set(pf, "prop_hira",  lambda: self._client.hiragana(prop, room))
            _try_set(pf, "prop_sta",   lambda: self._client.station(prop, room))
            _try_set(pf, "prop_notes", lambda: self._client.notes(prop, room))
            self._set_status(f"✅ {prop} / {room} を入力しました", SUCCESS)
        except Exception as e:
            self._set_status(f"❌ {e}", ERROR)

    def _set_status(self, msg: str, color: str) -> None:
        self._status_lbl.setText(msg)
        self._status_lbl.setStyleSheet(f"color: {color}; font-size: 10px;")

    # ── Load / save ────────────────────────────────────────────────────────────

    def _load(self) -> None:
        s = self.settings
        self.input_edit.setText(s.get("last_input_dir"))
        self.logo_edit.setText(s.get("last_logo_path"))
        self.output_edit.setText(s.get("last_output_dir"))
        self.creds_edit.setText(s.get("credentials_path"))
        self.sheet_edit.setText(s.get("sheet_name"))

    def _accept(self) -> None:
        errs = []
        if not self.input_edit.text().strip():
            errs.append("投入フォルダを指定してください")
        if not self.logo_edit.text().strip():
            errs.append("ロゴファイルを指定してください")
        if not self.output_edit.text().strip():
            errs.append("出力フォルダを指定してください")
        if errs:
            QMessageBox.warning(self, "入力エラー", "\n".join(errs))
            return

        s = self.settings
        s.set("last_input_dir",   self.input_edit.text().strip())
        s.set("last_logo_path",   self.logo_edit.text().strip())
        s.set("last_output_dir",  self.output_edit.text().strip())
        s.set("credentials_path", self.creds_edit.text().strip())
        s.set("sheet_name",       self.sheet_edit.text().strip())
        s.save()
        self.accept()


# ── Private helpers ────────────────────────────────────────────────────────────

def _try_set(fields: dict, key: str, getter) -> None:
    """Call getter() and set the field; silently ignore exceptions."""
    try:
        value = getter()
        if value and key in fields:
            fields[key].setText(value)
    except Exception:
        pass
