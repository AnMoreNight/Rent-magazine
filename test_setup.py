#!/usr/bin/env python3
"""
Rent Magazine — Setup Test & Diagnostics
==========================================
Verifies that all required (and optional) dependencies are installed
and the project files are present.

Run with:
  python3 test_setup.py
"""

import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def check_python_version():
    print("Checking Python version...", end=" ")
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 7):
        print(f"❌ {v.major}.{v.minor} (need 3.7+)")
        return False
    print(f"✅ {v.major}.{v.minor}.{v.micro}")
    return True


def check_pyqt5():
    print("Checking PyQt5...", end=" ")
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QThread
        import PyQt5
        print(f"✅ {PyQt5.QtCore.QT_VERSION_STR}")
        return True
    except ImportError:
        print("❌ Not installed")
        print("   Run:  pip install PyQt5")
        return False


def check_pillow():
    print("Checking Pillow (PIL)...", end=" ")
    try:
        from PIL import Image
        print(f"✅ {Image.__version__}")
        return True
    except ImportError:
        print("❌ Not installed")
        print("   Run:  pip install Pillow")
        return False


def check_numpy():
    print("Checking numpy...", end=" ")
    try:
        import numpy as np
        print(f"✅ {np.__version__}")
        return True
    except ImportError:
        print("❌ Not installed")
        print("   Run:  pip install numpy")
        return False


def check_gspread():
    print("Checking gspread (optional — for Google Sheets)...", end=" ")
    try:
        import gspread
        print(f"✅ {gspread.__version__}")
        return True
    except ImportError:
        print("⚠  Not installed (Google Sheets integration disabled)")
        print("   Run:  pip install gspread google-auth")
        return None  # None = optional, not a failure


def check_google_auth():
    print("Checking google-auth (optional — for Google Sheets)...", end=" ")
    try:
        from google.oauth2.service_account import Credentials
        import google.auth
        print(f"✅ {google.auth.__version__}")
        return True
    except ImportError:
        print("⚠  Not installed (Google Sheets integration disabled)")
        return None


def check_file(name: str, required: bool = True) -> bool:
    label = "required" if required else "optional"
    print(f"Checking {name} ({label})...", end=" ")
    p = Path(__file__).parent / name
    if p.exists():
        print("✅")
        return True
    if required:
        print(f"❌ Not found")
        return False
    print("⚠  Not found")
    return None


def create_sample_config():
    """Create a default config file if one doesn't exist."""
    import json
    config_dir  = Path.home() / ".rent_magazine"
    config_file = config_dir / "config.json"
    config_dir.mkdir(exist_ok=True)
    print("\nChecking config file...", end=" ")
    if config_file.exists():
        print(f"✅ {config_file}")
    else:
        default = {
            "credentials_path":       "",
            "sheet_name":             "物件管理番号マスター",
            "last_input_dir":         "",
            "last_output_dir":        "",
            "last_logo_path":         "",
            "last_property":          "",
            "last_room":              "",
            "last_image_type":        "リビング",
            "last_management_number": "",
            "last_city":              "Nagoya",
            "last_hiragana":          "",
            "last_station":           "",
        }
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        print(f"✅ Created at {config_file}")


def main():
    print("\n" + "─" * 60)
    print("  Rent Magazine — Setup Test")
    print("─" * 60 + "\n")

    required_checks = [
        ("Python 3.7+",       check_python_version),
        ("PyQt5",             check_pyqt5),
        ("Pillow",            check_pillow),
        ("numpy",             check_numpy),
        ("rent_magazine_processor.py", lambda: check_file("rent_magazine_processor.py")),
        ("rent_magazine_gui.py",       lambda: check_file("rent_magazine_gui.py")),
        ("rent_magazine_sheets.py",    lambda: check_file("rent_magazine_sheets.py")),
    ]

    optional_checks = [
        ("gspread",       check_gspread),
        ("google-auth",   check_google_auth),
    ]

    results = {}
    for name, fn in required_checks:
        results[name] = fn()

    print()
    for name, fn in optional_checks:
        results[name] = fn()

    try:
        create_sample_config()
    except Exception as e:
        print(f"⚠  Could not create config: {e}")

    # Tally — only required checks count toward pass/fail
    required_names = [n for n, _ in required_checks]
    passed   = sum(1 for n in required_names if results.get(n) is True)
    total    = len(required_names)
    optional_missing = [n for n, _ in optional_checks if results.get(n) is None]

    print("\n" + "─" * 60)
    print(f"  {passed}/{total} required checks passed")
    if optional_missing:
        print(f"  Optional not installed: {', '.join(optional_missing)}")
        print("  (Google Sheets integration will run in manual-entry mode)")
    print("─" * 60)

    if passed == total:
        print("\n✅ All systems ready! Run the GUI with:")
        print("   python3 rent_magazine_gui.py\n")
        return 0
    else:
        print("\n❌ Some required checks failed. Fix the issues above and re-run.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
