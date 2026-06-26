# Rent Magazine — Phase 1 Image Processing System (Developer Reference)

**Version:** 1.1 (Phase 1 complete)  
**Last updated:** 2026-06-24  
**Stack:** Python 3.11, PyQt5, Pillow, NumPy, gspread

---

## What This Is

Automates real estate property photo processing for Rent Magazine (Japanese real estate company).  
Replaces a manual Photoshop workflow. Staff picks a property + room from a dropdown, selects photos, clicks process — done.

**What it does automatically:**
- Camera Raw adjustments (Exposure +0.60, Contrast −16, Highlights −50, Shadows −4, Whites +50, Blacks +100)
- Logo overlay at 45% opacity, orientation-aware (portrait 221.6% / landscape 257.7%)
- THETA 360° image auto-detection via EXIF or 2:1 aspect ratio — no logo on these
- SUUMO folder structure creation (with special Nagoya path)
- File renaming: `ManagementNumber_PropertyName_Room_ImageType_Sequence.jpg`
- Processing log (JSON) saved to output folder
- Retry failed files without rerunning the whole batch
- Settings persist across sessions via `config.json`

**What stays manual (client decision):**
- Image selection and ordering
- Thumbnail/eyecatch selection
- THETA placement verification
- Final review and SUUMO publishing

---

## File Structure

```
photo automation/
├── rent_magazine_gui.py          PyQt5 desktop app (entry point)
├── rent_magazine_processor.py    Core image processing engine + CLI
├── rent_magazine_sheets.py       Google Sheets read-only client
├── test_setup.py                 Dependency + file checker
├── requirements.txt              pip dependencies
├── config.json                   Settings file (auto-written by app)
├── README.md                     Staff manual (Japanese)
├── README_DEV.md                 This file
└── samples/
    ├── input/                    4 sample raw photos (2 regular, 2 THETA)
    ├── output/                   Reference processed outputs
    └── logo/                     Rent Magazine white logo PNG
```

---

## Setup

```bash
pip install -r requirements.txt

# Verify everything
python test_setup.py

# Launch GUI
python rent_magazine_gui.py

# Or use the CLI directly
python rent_magazine_processor.py \
  --input ./photos \
  --logo ./logo.png \
  --output ./output \
  --city Chiryu \
  --property "○○マンション" \
  --room 101 \
  --image-type リビング \
  --management-number RM-R000001
```

**Nagoya requires two extra flags:**
```bash
python rent_magazine_processor.py ... \
  --city Nagoya \
  --hiragana sa \
  --station Sakae
```

---

## Architecture

```
rent_magazine_gui.py
    ├── SettingsManager          reads/writes config.json (same dir as script)
    ├── ProcessingWorker         QThread — runs process_images() in background
    │       signals: progress_signal, finished_signal, error_signal
    └── RentMagazineApp          QMainWindow
            ├── _build_sheets_section     Sheets connect/disconnect/refresh UI
            ├── _build_property_section   Property+Room combos, ImageType entry
            │       QStackedWidget[0] = auto-info labels (Sheets mode)
            │       QStackedWidget[1] = manual entry fields
            ├── _build_files_section      Input/Logo/Output file pickers
            ├── _build_controls_section   Start/Retry/Clear buttons + progress bar
            └── _build_logs_section       QSplitter → success log | error log

rent_magazine_processor.py
    ├── is_theta_image()         EXIF Make/Model → 2:1 ratio fallback
    ├── apply_camera_raw()       NumPy array operations matching Photoshop PDF
    ├── apply_logo()             RGBA paste at 45% opacity, portrait/landscape offsets
    ├── build_output_path()      Creates SUUMO folder structure
    ├── next_sequence()          Glob-counts existing files to continue numbering
    ├── build_output_filename()  Assembles the final filename
    └── process_images()         Main pipeline — returns results dict + saves JSON log

rent_magazine_sheets.py
    └── PropertyMasterClient
            ├── connect(creds, sheet)     loads all rows via gspread Service Account
            ├── property_names()          sorted unique list for dropdown
            ├── rooms_for(property)       sorted rooms for selected property
            ├── get_record(prop, room)    first matching row dict
            ├── management_number()       field accessors via _f()
            ├── city(), hiragana(), station()
            └── refresh()                disconnect + reconnect
```

---

## Google Sheets

### Sheet name
`物件管理番号マスター` (default, configurable in GUI)

### Required column headers (row 1, exact match)

| Column | Notes |
|--------|-------|
| `Management Number` | RM-R000001 / RM-T000001 / RM-B000001 |
| `Type` | Residential / Tenant / Building |
| `Property Name` | Used in dropdown and filename |
| `Building` | Optional |
| `Room/Unit` | Used in dropdown and filename |
| `City/Ward` | Drives folder path; `Nagoya` or `名古屋` triggers extra levels |
| `Hiragana Group` | Nagoya only — hiragana reading group (e.g. `さ`) |
| `Nearest Station` | Nagoya only — station name (e.g. `栄`) |
| `WordPress Post ID` | Stored, not used in Phase 1 |
| `WordPress URL` | Stored, not used in Phase 1 |
| `Status` | Stored, not used in Phase 1 |
| `Notes` | Stored, not used in Phase 1 |

### Auth
Service Account JSON — no browser OAuth. IT drops the `.json` file in the app folder, staff browses to it once, path saved to `config.json`.

Scopes used:
- `https://www.googleapis.com/auth/spreadsheets.readonly`
- `https://www.googleapis.com/auth/drive.readonly`

### What happens if gspread isn't installed
The GUI still works in manual-entry mode. `rent_magazine_sheets.py` sets `_AVAILABLE = False` and raises `SheetsError("Required packages not installed")` on `connect()`, which the GUI shows as a messagebox.

---

## Folder Structure

```
Non-Nagoya:
{output}/suumo/{city}/{property}/{room}/image/04_web/02_web/   ← regular
{output}/suumo/{city}/{property}/{room}/image/04_web/01_theta/ ← THETA

Nagoya:
{output}/suumo/名古屋/{hiragana}/{station}/{property}/{room}/image/04_web/02_web/
{output}/suumo/名古屋/{hiragana}/{station}/{property}/{room}/image/04_web/01_theta/
```

---

## File Naming

```
{ManagementNumber}_{PropertyName}_{Room}_{ImageType}_{Sequence:02d}.jpg
```

- Empty segments are omitted (if no management number, it just starts with PropertyName)
- `Sequence` is determined by `next_sequence()` which globs existing files in the output folder — safe across re-runs and retries, never overwrites
- THETA images always use `"THETA"` as the ImageType regardless of what's in the field

---

## Processing Log

Saved to `{output_dir}/processing_log_{YYYYMMDD_HHMMSS}.json`:

```json
{
  "session": { "start_time", "end_time", "duration_seconds", "mode" },
  "property": { "management_number", "property_name", "room", "city", "image_type" },
  "summary": { "total", "processed", "failed" },
  "processed": [ { "source": "...", "output": "...", "type": "regular|theta" } ],
  "failed":    [ { "file": "...", "error": "..." } ]
}
```

`mode` is `"batch"` or `"retry"`.

---

## Image Processing Pipeline (per image)

1. `Image.open(path)` — Pillow opens the file
2. `is_theta_image(img, path)` — checks EXIF 271/272 (Make/Model) for RICOH/THETA keywords, falls back to width/height ratio within 3% of 2.0
3. `apply_camera_raw(img)` — converts to RGB, runs NumPy array ops
4. `apply_logo(img, logo)` — skipped if THETA; applies logo at 45% opacity
5. `build_output_path(...)` — creates folders, returns destination path
6. `next_sequence(...)` — glob-counts existing matching files
7. `build_output_filename(...)` — assembles name
8. `img.save(..., "JPEG", quality=30, optimize=True)` — always exports as `.jpg`

---

## Camera Raw Values (from Photoshop action PDF)

| Setting | Value | NumPy implementation |
|---------|-------|----------------------|
| Exposure | +0.60 | `arr * (2 ** 0.60)` |
| Whites | +50 | `arr > 200 → arr + (arr−200) * 0.25` |
| Blacks | +100 | `arr < 50 → arr + 30` |
| Highlights | −50 | `arr > 200 → arr − (arr−200) * 0.30` |
| Shadows | −4 | `arr < 100 → arr * 0.98` |
| Contrast | −16 | `midpoint + (arr − midpoint) * (1 − 0.16 * 0.5)` |

Applied in that order, clipped to 0–255 at the end.

---

## Logo Placement (from Photoshop action PDF)

| Orientation | Scale | Offset from center (x, y) |
|-------------|-------|---------------------------|
| Portrait (h > w) | 221.6% | (−716.3 px, −1726.3 px) |
| Landscape (w ≥ h) | 257.7% | (−1112.4 px, −1253.1 px) |

Alpha channel of logo is multiplied by 0.45 before paste.

---

## Settings (`config.json`)

Lives in the **same directory as the scripts** (not in `~/.rent_magazine/`). Written on every change.

```json
{
  "credentials_path": "/path/to/service-account.json",
  "sheet_name": "物件管理番号マスター",
  "last_input_dir": "",
  "last_output_dir": "",
  "last_logo_path": "",
  "last_property": "",
  "last_room": "",
  "last_image_type": "リビング",
  "last_management_number": "",
  "last_city": "",
  "last_hiragana": "",
  "last_station": ""
}
```

---

## Threading Model

- Main thread: PyQt5 event loop
- `ProcessingWorker(QThread)` runs `process_images()` on a background thread
- `progress_callback` emits `pyqtSignal` — PyQt5 queues these to the main thread automatically (cross-thread signal/slot)
- All UI updates happen in connected slots on the main thread — no manual `root.after()` needed (unlike the old tkinter version)

---

## Known Limitations / Phase 2 Candidates

- **Image selection is manual** — staff chooses which photos to put in the input folder
- **No WordPress upload** — manual step after processing
- **No thumbnail selection** — manual
- **No Reapro integration** — planned Phase 3
- **JPEG quality is fixed at 30** — matches the original Photoshop action; not configurable in GUI
- **Camera Raw is approximated** — NumPy ops match the visual output but are not identical to Adobe's proprietary algorithm

---

## Dependency Versions (tested)

| Package | Version |
|---------|---------|
| Python | 3.11.9 |
| PyQt5 | 5.15.2 |
| Pillow | 12.0.0 |
| NumPy | 1.26.4 |
| gspread | 5.12.0 |
| google-auth | 2.23.4 |

---

## Phase Roadmap

### Phase 1 — Complete
- Camera Raw adjustments + logo overlay
- THETA auto-detection
- File renaming convention
- SUUMO folder structure (Nagoya + non-Nagoya)
- Google Sheets Property Master integration
- PyQt5 GUI with Japanese UI
- Success/error dual log panels
- Retry failed files
- Processing log (JSON)
- Settings persistence

### Phase 2 — Planned
- WordPress auto-upload
- YouTube URL integration
- Reapro property management system connection

### Phase 3 — Planned
- Web dashboard
- Batch scheduling
- Multi-user access control
