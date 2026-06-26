#!/usr/bin/env python3
"""
RentMag Image Processing System — Phase 1
Launch: python main.py
"""

import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from PyQt5.QtWidgets import QApplication, QMessageBox

try:
    from rentmag.gui import RentMagApp
    _import_ok = True
    _import_err = ""
except ImportError as e:
    _import_ok = False
    _import_err = str(e)


def main() -> None:
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    if not _import_ok:
        QMessageBox.critical(
            None, "起動エラー",
            f"モジュールの読み込みに失敗しました:\n{_import_err}\n\n"
            "pip install PyQt5 Pillow numpy gspread google-auth",
        )
        sys.exit(1)

    win = RentMagApp()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
