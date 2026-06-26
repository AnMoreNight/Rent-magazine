#!/usr/bin/env python3
"""
Rent Magazine — Google Sheets Integration
==========================================
Read-only client for the 物件管理番号マスター sheet via a Service Account credential file.

Required sheet columns (header row must match exactly):
  Management Number | Type | Property Name | Building | Room/Unit |
  City/Ward | Hiragana Group | Nearest Station |
  WordPress Post ID | WordPress URL | Status | Notes

Management number format:
  Residential → RM-R000001
  Tenant      → RM-T000001
  Building    → RM-B000001
"""

from pathlib import Path
from typing import Dict, List, Optional

try:
    import gspread
    from google.oauth2.service_account import Credentials
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

# Column header names — must match the sheet's first row exactly
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

REQUIRED_COLUMNS = [COL_MGMT, COL_PROPERTY, COL_ROOM, COL_CITY]


class SheetsError(Exception):
    """Raised on connection or data errors."""


class PropertyMasterClient:
    """
    Read-only access to the Rent Magazine Property Master Google Sheet.

    Usage:
        client = PropertyMasterClient()
        client.connect("path/to/creds.json", "Property Master")

        names = client.property_names()
        rooms = client.rooms_for("八ツ田ハイツ北棟")
        mgmt  = client.management_number("八ツ田ハイツ北棟", "101")
        city  = client.city("八ツ田ハイツ北棟", "101")
    """

    def __init__(self):
        self._records: List[Dict] = []
        self._connected = False
        self._credentials_path = ""
        self._sheet_name = ""

    # ─────────────────────────────────────────────
    # Connection
    # ─────────────────────────────────────────────

    def connect(self, credentials_path: str, sheet_name: str) -> None:
        """Connect to the sheet and load all records. Raises SheetsError on failure."""
        if not _AVAILABLE:
            raise SheetsError(
                "Required packages not installed.\n"
                "Run:  pip install gspread google-auth"
            )
        creds_file = Path(credentials_path)
        if not creds_file.exists():
            raise SheetsError(f"Credentials file not found:\n{credentials_path}")
        try:
            creds          = Credentials.from_service_account_file(str(creds_file), scopes=SCOPES)
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
            missing = [c for c in REQUIRED_COLUMNS if c not in self._records[0]]
            if missing:
                self._records = []
                raise SheetsError(
                    "Sheet is missing required column(s):\n  " + "\n  ".join(missing) +
                    "\n\nCheck that the header row matches exactly."
                )

        self._credentials_path = credentials_path
        self._sheet_name       = sheet_name
        self._connected        = True

    def disconnect(self) -> None:
        self._records          = []
        self._connected        = False
        self._credentials_path = ""
        self._sheet_name       = ""

    def refresh(self) -> None:
        """Reload all records from the sheet (keeps current credentials)."""
        creds = self._credentials_path
        name  = self._sheet_name
        self.disconnect()
        self.connect(creds, name)

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def record_count(self) -> int:
        return len(self._records)

    # ─────────────────────────────────────────────
    # Queries
    # ─────────────────────────────────────────────

    def property_names(self) -> List[str]:
        """Unique, sorted list of property names for the UI dropdown."""
        seen: set = set()
        result: List[str] = []
        for r in self._records:
            name = str(r.get(COL_PROPERTY, "")).strip()
            if name and name not in seen:
                seen.add(name)
                result.append(name)
        return sorted(result)

    def rooms_for(self, property_name: str) -> List[str]:
        """Sorted list of rooms for a given property name."""
        return sorted({
            str(r.get(COL_ROOM, "")).strip()
            for r in self._records
            if str(r.get(COL_PROPERTY, "")).strip() == property_name
            and r.get(COL_ROOM, "")
        })

    def get_record(self, property_name: str, room: str) -> Optional[Dict]:
        """Return the first sheet row matching property + room, or None."""
        for r in self._records:
            if (str(r.get(COL_PROPERTY, "")).strip() == property_name and
                    str(r.get(COL_ROOM, "")).strip() == room):
                return r
        return None

    # ─────────────────────────────────────────────
    # Field accessors
    # ─────────────────────────────────────────────

    def _f(self, property_name: str, room: str, col: str) -> str:
        rec = self.get_record(property_name, room)
        return str(rec.get(col, "")).strip() if rec else ""

    def management_number(self, p: str, r: str) -> str: return self._f(p, r, COL_MGMT)
    def prop_type(self,        p: str, r: str) -> str:  return self._f(p, r, COL_TYPE)
    def city(self,             p: str, r: str) -> str:  return self._f(p, r, COL_CITY)
    def hiragana(self,         p: str, r: str) -> str:  return self._f(p, r, COL_HIRAGANA)
    def station(self,          p: str, r: str) -> str:  return self._f(p, r, COL_STATION)
    def building(self,         p: str, r: str) -> str:  return self._f(p, r, COL_BUILDING)
    def address(self,          p: str, r: str) -> str:  return self._f(p, r, COL_ADDRESS)
    def status(self,           p: str, r: str) -> str:  return self._f(p, r, COL_STATUS)
