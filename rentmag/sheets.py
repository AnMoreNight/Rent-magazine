"""
Google Sheets integration — read-only access to the Property Master sheet.

Management number format:
  Residential → RM-R000001
  Tenant      → RM-T000001
  Building    → RM-B000001

Sheet must have these column headers (exact match):
  Management Number, Type, Property Name, Building, Room/Unit,
  City/Ward, Hiragana Group, Nearest Station,
  WordPress Post ID, WordPress URL, Status, Notes
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

try:
    import gspread
    from google.oauth2.service_account import Credentials
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

# Column header constants
COL_MGMT     = "Management Number"
COL_TYPE     = "Type"
COL_PROPERTY = "Property Name"
COL_BUILDING = "Building"
COL_ROOM     = "Room/Unit"
COL_CITY     = "City/Ward"
COL_HIRAGANA = "Hiragana Group"
COL_STATION  = "Nearest Station"
COL_WP_ID    = "WordPress Post ID"
COL_WP_URL   = "WordPress URL"
COL_STATUS   = "Status"
COL_NOTES    = "Notes"

REQUIRED_COLS = [COL_MGMT, COL_PROPERTY, COL_ROOM, COL_CITY]


class SheetsError(Exception):
    """Raised on connection or data validation failures."""


class PropertyMasterClient:
    """
    Read-only client for the Rent Magazine Property Master Google Sheet.

    Usage:
        client = PropertyMasterClient()
        client.connect("path/to/creds.json", "物件管理番号マスター")
        names = client.property_names()
        rooms = client.rooms_for("八ツ田ハイツ北棟")
        mgmt  = client.management_number("八ツ田ハイツ北棟", "101")
    """

    def __init__(self):
        self._records:    List[Dict] = []
        self._creds_path: str = ""
        self._sheet_name: str = ""
        self._connected:  bool = False

    # ── Connection ─────────────────────────────────────────────────────────────

    def connect(self, credentials_path: str, sheet_name: str) -> None:
        """Load all records from the sheet. Raises SheetsError on any failure."""
        if not _AVAILABLE:
            raise SheetsError(
                "Required packages missing.\n"
                "Run: pip install gspread google-auth"
            )
        creds_file = Path(credentials_path)
        if not creds_file.exists():
            raise SheetsError(f"Credentials file not found: {credentials_path}")
        try:
            creds          = Credentials.from_service_account_file(str(creds_file), scopes=_SCOPES)
            gc             = gspread.authorize(creds)
            sheet          = gc.open(sheet_name).sheet1
            self._records  = sheet.get_all_records()
        except gspread.exceptions.SpreadsheetNotFound:
            raise SheetsError(
                f'Sheet "{sheet_name}" not found.\n'
                "Check the name and that the sheet is shared with the service account email."
            )
        except Exception as e:
            raise SheetsError(f"Connection failed: {e}")

        if self._records:
            missing = [c for c in REQUIRED_COLS if c not in self._records[0]]
            if missing:
                self._records = []
                raise SheetsError(
                    "Sheet is missing required column(s):\n  " + "\n  ".join(missing)
                )

        self._creds_path = credentials_path
        self._sheet_name = sheet_name
        self._connected  = True

    def disconnect(self) -> None:
        self._records    = []
        self._connected  = False
        self._creds_path = ""
        self._sheet_name = ""

    def refresh(self) -> None:
        """Reload records using the current credentials."""
        creds, name = self._creds_path, self._sheet_name
        self.disconnect()
        self.connect(creds, name)

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def record_count(self) -> int:
        return len(self._records)

    # ── Queries ────────────────────────────────────────────────────────────────

    def property_names(self) -> List[str]:
        """Unique sorted property names for the UI dropdown."""
        seen: set = set()
        names: List[str] = []
        for r in self._records:
            name = str(r.get(COL_PROPERTY, "")).strip()
            if name and name not in seen:
                seen.add(name)
                names.append(name)
        return sorted(names)

    def rooms_for(self, property_name: str) -> List[str]:
        """Sorted room list for a given property."""
        return sorted({
            str(r.get(COL_ROOM, "")).strip()
            for r in self._records
            if str(r.get(COL_PROPERTY, "")).strip() == property_name
            and r.get(COL_ROOM, "")
        })

    def get_record(self, property_name: str, room: str) -> Optional[Dict]:
        """First row matching property + room, or None."""
        for r in self._records:
            if (str(r.get(COL_PROPERTY, "")).strip() == property_name and
                    str(r.get(COL_ROOM, "")).strip() == room):
                return r
        return None

    # ── Field accessors ────────────────────────────────────────────────────────

    def _field(self, prop: str, room: str, col: str) -> str:
        rec = self.get_record(prop, room)
        return str(rec.get(col, "")).strip() if rec else ""

    def management_number(self, p: str, r: str) -> str: return self._field(p, r, COL_MGMT)
    def prop_type(self,        p: str, r: str) -> str:  return self._field(p, r, COL_TYPE)
    def city(self,             p: str, r: str) -> str:  return self._field(p, r, COL_CITY)
    def hiragana(self,         p: str, r: str) -> str:  return self._field(p, r, COL_HIRAGANA)
    def station(self,          p: str, r: str) -> str:  return self._field(p, r, COL_STATION)
    def building(self,         p: str, r: str) -> str:  return self._field(p, r, COL_BUILDING)
    def status(self,           p: str, r: str) -> str:  return self._field(p, r, COL_STATUS)
    def notes(self,            p: str, r: str) -> str:  return self._field(p, r, COL_NOTES)
    def wp_id(self,            p: str, r: str) -> str:  return self._field(p, r, COL_WP_ID)
    def wp_url(self,           p: str, r: str) -> str:  return self._field(p, r, COL_WP_URL)
