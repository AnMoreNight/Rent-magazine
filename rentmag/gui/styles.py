"""Design tokens and application stylesheet."""

# ── Palette ────────────────────────────────────────────────────────────────────
BG         = "#EEF0F3"       # main background
PANEL_BG   = "#E6E9EE"       # left panel
PANEL_BDR  = "#CDD1D9"       # left panel right edge
CARD       = "#FFFFFF"
BORDER     = "#D6DAE1"
ACCENT     = "#1A56A0"
ACCENT2    = "#2261B8"
SUCCESS    = "#2E7D32"
WARN       = "#B45309"
ERROR      = "#B91C1C"
ERROR_BG   = "#FEF2F2"
WARN_BG    = "#FFFBEB"
CARD_BG    = "#FFFFFF"
TEXT1      = "#1C1F26"
TEXT2      = "#55606E"
MUTED      = "#8E96A2"

STEPS = ["検出", "リネーム", "振り分け", "レタッチ", "ロゴ挿入", "JPG保存"]

# ── Stylesheet ─────────────────────────────────────────────────────────────────
QSS = f"""
* {{
    font-family: "Segoe UI", "Yu Gothic UI", "Meiryo UI", sans-serif;
    font-size: 11px;
    color: {TEXT1};
}}
QMainWindow, QWidget   {{ background: {BG}; }}
QDialog                {{ background: {BG}; }}

/* ── Left panel ────────────────────────────────────────────────────── */
QWidget#left-panel {{
    background: {PANEL_BG};
    border-right: 1px solid {PANEL_BDR};
}}
QFrame#panel-sep {{
    background: {PANEL_BDR};
    border: none;
    max-height: 1px;
    min-height: 1px;
}}
QLabel#panel-heading {{
    color: {MUTED};
    font-size: 9px;
    font-weight: 700;
    background: transparent;
}}

/* ── Top bar ────────────────────────────────────────────────────────── */
QFrame#topbar {{
    background: {ACCENT};
    border: none;
}}
QLabel#topbar-title {{
    color: white;
    font-size: 13px;
    font-weight: 700;
    background: transparent;
}}
QLabel#conn-label {{ font-size: 10px; background: transparent; }}

/* ── Generic labels ─────────────────────────────────────────────────── */
QLabel {{ background: transparent; }}
QLabel#section-title {{ color: {ACCENT}; font-size: 11px; font-weight: 700; }}
QLabel#field-label   {{ color: {TEXT2}; font-size: 10px; }}
QLabel#stat-lbl      {{ color: {TEXT2}; font-size: 10px; }}
QLabel#stat-num      {{ font-size: 13px; font-weight: 700; }}
QLabel#pct-label     {{ color: {TEXT1}; font-size: 26px; font-weight: 800; }}

/* ── Right panel separators ─────────────────────────────────────────── */
QFrame#right-sep-h {{
    background: {BORDER};
    border: none;
    max-height: 1px;
    min-height: 1px;
}}
QFrame#right-sep-v {{
    background: {BORDER};
    border: none;
    max-width: 1px;
    min-width: 1px;
}}

/* ── Buttons ────────────────────────────────────────────────────────── */
QPushButton {{ outline: none; }}

QPushButton#btn-primary {{
    background: {ACCENT2};
    color: white;
    border: none;
    border-radius: 3px;
    padding: 6px 16px;
    font-size: 12px;
    font-weight: 600;
}}
QPushButton#btn-primary:hover    {{ background: {ACCENT}; }}
QPushButton#btn-primary:disabled {{ background: #BDBDBD; color: white; }}

QPushButton#btn-pause {{
    background: #6B7280;
    color: white;
    border: none;
    border-radius: 3px;
    padding: 6px 10px;
    font-size: 11px;
}}
QPushButton#btn-pause:hover    {{ background: #4B5563; }}
QPushButton#btn-pause:disabled {{ background: #D1D5DB; color: #9CA3AF; }}

QPushButton#btn-stop {{
    background: {ERROR};
    color: white;
    border: none;
    border-radius: 3px;
    padding: 6px 10px;
    font-size: 11px;
}}
QPushButton#btn-stop:hover    {{ background: #991B1B; }}
QPushButton#btn-stop:disabled {{ background: #D1D5DB; color: #9CA3AF; }}

QPushButton#btn-secondary {{
    background: transparent;
    color: {TEXT1};
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 5px 10px;
    font-size: 11px;
}}
QPushButton#btn-secondary:hover    {{ background: {CARD}; }}
QPushButton#btn-secondary:disabled {{ color: {MUTED}; border-color: {BORDER}; }}

QPushButton#btn-link {{
    background: transparent;
    color: {ACCENT2};
    border: none;
    padding: 3px 0;
    font-size: 10px;
    text-align: left;
}}
QPushButton#btn-link:hover {{ color: {ACCENT}; }}

QPushButton#btn-topbar {{
    background: rgba(255,255,255,0.12);
    color: white;
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 3px;
    padding: 5px 12px;
    font-size: 11px;
}}
QPushButton#btn-topbar:hover {{ background: rgba(255,255,255,0.22); }}

/* ── Progress bar ───────────────────────────────────────────────────── */
QProgressBar {{
    border: none;
    border-radius: 3px;
    background: #D1D5DB;
    height: 8px;
    color: transparent;
}}
QProgressBar::chunk {{
    border-radius: 3px;
    background: {ACCENT2};
}}

/* ── Table ──────────────────────────────────────────────────────────── */
QTableWidget {{
    border: none;
    background: {CARD};
    outline: none;
    gridline-color: transparent;
    font-size: 10px;
    selection-background-color: #DBEAFE;
    selection-color: {TEXT1};
}}
QTableWidget::item          {{ padding: 3px 8px; border-bottom: 1px solid #F3F4F6; }}
QTableWidget::item:selected {{ background: #DBEAFE; color: {TEXT1}; }}
QHeaderView::section {{
    background: #F9FAFB;
    color: {TEXT2};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 4px 8px;
    font-size: 10px;
    font-weight: 600;
}}

/* ── Inputs ─────────────────────────────────────────────────────────── */
QComboBox {{
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 3px 6px;
    background: {CARD};
    font-size: 11px;
    min-height: 20px;
}}
QComboBox:focus             {{ border-color: {ACCENT2}; }}
QComboBox::drop-down        {{ border: none; width: 16px; }}
QComboBox QAbstractItemView {{ background: {CARD}; border: 1px solid {BORDER}; }}

QLineEdit {{
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 3px 6px;
    background: {CARD};
    font-size: 11px;
    min-height: 20px;
}}
QLineEdit:focus     {{ border-color: {ACCENT2}; }}
QLineEdit:read-only {{ background: #F9FAFB; color: {TEXT2}; }}
QLineEdit#prop-field         {{ border: 1px solid {BORDER}; border-radius: 3px;
                                padding: 3px 6px; background: {CARD}; font-size: 11px; }}
QLineEdit#prop-field:focus   {{ border-color: {ACCENT2}; background: #FAFCFF; }}

/* ── Scrollbars ─────────────────────────────────────────────────────── */
QScrollBar:vertical, QScrollBar:horizontal {{
    background: transparent;
}}
QScrollBar:vertical   {{ width: 5px; }}
QScrollBar:horizontal {{ height: 5px; }}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background: #BEC3CB;
    border-radius: 3px;
    min-height: 16px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    height: 0; width: 0;
}}

/* ── Dialogs ────────────────────────────────────────────────────────── */
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 4px;
    margin-top: 14px;
    font-size: 11px;
    font-weight: 600;
    color: {ACCENT};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 8px;
    padding: 1px 5px;
    background: {BG};
}}
QRadioButton {{ spacing: 6px; background: transparent; color: {TEXT1}; font-size: 11px; }}
"""
