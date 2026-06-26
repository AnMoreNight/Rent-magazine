#!/usr/bin/env python3
"""
Rent Magazine — Phase 1 Image Processing Automation
====================================================
Processes property listing photos:
  - Camera Raw adjustments (Exposure +0.60, Contrast -16, Highlights -50,
    Shadows -4, Whites +50, Blacks +100) matching the Photoshop action PDF
  - Logo overlay at 45% opacity with orientation-aware positioning (regular only)
  - THETA 360° panoramic images auto-detected via EXIF or 2:1 aspect ratio
  - Output files renamed: ManagementID_PropertyName_Room_ImageType_Sequence.jpg
  - SUUMO folder structure created automatically
  - Processing log (JSON) saved alongside output

CLI usage:
  python3 rent_magazine_processor.py \\
    --input ./photos --logo ./logo.png --output ./output \\
    --city Chiryu --property "OO Mansion" --room 101 \\
    --image-type リビング --management-number RM-R000001

  For Nagoya (requires --hiragana and --station):
  python3 rent_magazine_processor.py \\
    --input ./photos --logo ./logo.png --output ./output \\
    --city Nagoya --property "OO Mansion" --room 301 \\
    --image-type リビング --management-number RM-R000001 \\
    --hiragana sa --station Sakae
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Windows consoles default to cp1252, which cannot encode box-drawing characters
# and emoji used in status output. Force UTF-8 so prints never crash mid-batch.
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("❌ Missing dependencies. Please run:")
    print("   pip install Pillow numpy")
    sys.exit(1)


SUPPORTED = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


def is_image(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED


# ─────────────────────────────────────────────────────────────
# THETA Auto-Detection
# ─────────────────────────────────────────────────────────────

def is_theta_image(img: Image.Image, path: Path) -> bool:
    """
    Detect THETA 360° panoramic images.
    Checks (in order):
      1. EXIF Make/Model containing RICOH or THETA
      2. Aspect ratio close to 2:1 (equirectangular convention)
    """
    try:
        exif = img._getexif()
        if exif:
            make  = str(exif.get(271, "")).upper()  # EXIF tag 271 = Make
            model = str(exif.get(272, "")).upper()  # EXIF tag 272 = Model
            if any(k in make  for k in ("RICOH", "THETA")):
                return True
            if "THETA" in model:
                return True
    except Exception:
        pass
    # Fallback: aspect ratio 2:1 within 3% tolerance
    w, h = img.size
    return w > h and abs(w / h - 2.0) < 0.03


# ─────────────────────────────────────────────────────────────
# Camera Raw Adjustments
# Matches Photoshop Camera Raw filter settings from action PDF:
#   Exposure +0.60 | Contrast -16 | Highlights -50
#   Shadows -4     | Whites +50   | Blacks +100
# ─────────────────────────────────────────────────────────────

def apply_camera_raw(img_pil: Image.Image) -> Image.Image:
    img_rgb = img_pil.convert("RGB")
    arr = np.array(img_rgb, dtype=np.float32)

    arr = arr * (2 ** 0.60)                                          # Exposure +0.60
    arr = np.where(arr > 200, arr + (arr - 200) * 0.25, arr)        # Whites  +50
    arr = np.where(arr < 50,  arr + 30,                  arr)        # Blacks  +100
    arr = np.where(arr > 200, arr - (arr - 200) * 0.30,  arr)       # Highlights -50
    arr = np.where(arr < 100, arr * 0.98,                arr)        # Shadows -4
    midpoint = 128.0
    arr = midpoint + (arr - midpoint) * (1 - 0.16 * 0.5)            # Contrast -16

    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


# ─────────────────────────────────────────────────────────────
# Logo Overlay
# Placement specs from Photoshop action PDF:
#   Portrait  → scale 221.6%, offset (-716.3px, -1726.3px) from center
#   Landscape → scale 257.7%, offset (-1112.4px, -1253.1px) from center
#   Opacity: 45%
# ─────────────────────────────────────────────────────────────

def apply_logo(img_pil: Image.Image, logo_pil: Image.Image) -> Image.Image:
    img  = img_pil.convert("RGBA")
    logo = logo_pil.convert("RGBA")

    iw, ih = img.size
    lw, lh = logo.size

    if ih > iw:  # portrait
        scale, offset_x, offset_y = 2.216, -716.3, -1726.3
    else:        # landscape
        scale, offset_x, offset_y = 2.577, -1112.4, -1253.1

    new_lw = int(lw * scale)
    new_lh = int(lh * scale)
    logo_scaled = logo.resize((new_lw, new_lh), Image.LANCZOS)

    cx, cy  = iw // 2, ih // 2
    paste_x = int(cx + offset_x - new_lw // 2)
    paste_y = int(cy + offset_y - new_lh // 2)

    r, g, b, a = logo_scaled.split()
    a = a.point(lambda px: int(px * 0.45))
    logo_final = Image.merge("RGBA", (r, g, b, a))

    img.paste(logo_final, (paste_x, paste_y), logo_final)
    return img.convert("RGB")


# ─────────────────────────────────────────────────────────────
# Folder Structure
# ─────────────────────────────────────────────────────────────

def build_output_path(base_output: Path, city: str, property_name: str,
                       room: str, is_theta: bool,
                       hiragana: str = "", station: str = "") -> Path:
    """
    Non-Nagoya: suumo/{city}/{property}/{room}/image/04_web/{02_web|01_theta}/
    Nagoya:     suumo/名古屋/{hiragana}/{station}/{property}/{room}/image/04_web/{02_web|01_theta}/
    """
    suumo     = base_output / "suumo"
    subfolder = "01_theta" if is_theta else "02_web"

    if city.lower() in ("nagoya", "名古屋"):
        path = suumo / "名古屋" / hiragana / station / property_name / room / "image" / "04_web" / subfolder
    else:
        path = suumo / city / property_name / room / "image" / "04_web" / subfolder

    path.mkdir(parents=True, exist_ok=True)
    return path


# ─────────────────────────────────────────────────────────────
# File Naming
# ─────────────────────────────────────────────────────────────

def next_sequence(out_path: Path, management_number: str,
                  property_name: str, room: str, image_type: str) -> int:
    """
    Return the next sequence number for this type in out_path by counting
    existing matching files. Safely continues across re-runs and retries.
    """
    parts  = [p for p in (management_number, property_name, room, image_type) if p]
    prefix = "_".join(parts) + "_" if parts else ""
    return len(list(out_path.glob(f"{prefix}*.jpg"))) + 1


def build_output_filename(management_number: str, property_name: str,
                           room: str, image_type: str, sequence: int) -> str:
    """
    Naming convention (empty segments are skipped):
      RM-R000001_八ツ田ハイツ北棟_101_リビング_01.jpg
      RM-R000001_八ツ田ハイツ北棟_101_THETA_01.jpg
      RM-T000001_FukuoBuilding_1F-A_Interior_01.jpg
    """
    parts = [management_number, property_name, room, image_type, f"{sequence:02d}"]
    return "_".join(p for p in parts if p) + ".jpg"


# ─────────────────────────────────────────────────────────────
# Main Processing Pipeline
# ─────────────────────────────────────────────────────────────

def process_images(
    input_dir: Path,
    logo_path: Path,
    output_dir: Path,
    city: str,
    property_name: str,
    room: str,
    image_type: str,              # Room label for regular-photo filenames (e.g. リビング).
                                  # THETA images are auto-detected and labelled "THETA".
    management_number: str = "",  # From Google Sheets (e.g. RM-R000001). Optional.
    hiragana: str = "",           # Nagoya folder: hiragana group (e.g. sa)
    station: str = "",            # Nagoya folder: nearest station (e.g. Sakae)
    verbose: bool = True,
    progress_callback=None,       # fn(current, total, source_name, output_name, status)
    retry_files: list = None,     # List of Path/str to reprocess; None = all in input_dir
) -> dict:
    """
    Process a batch of images and return a results dict:
      {
        "processed": [{"source": ..., "output": ..., "type": ...}, ...],
        "failed":    [{"file": ..., "error": ...}, ...],
        "skipped":   [],
        "start_time": ISO str,
        "end_time":   ISO str,
        "log_file":   str path or None,
      }
    """
    start_time = datetime.now()
    results = {
        "processed": [],
        "failed":    [],
        "skipped":   [],
        "start_time": start_time.isoformat(),
        "end_time":   None,
        "log_file":   None,
    }

    if not logo_path.exists():
        raise FileNotFoundError(f"Logo not found: {logo_path}")

    logo = Image.open(logo_path).convert("RGBA")

    if retry_files is not None:
        images = sorted(Path(f) for f in retry_files if is_image(Path(f)))
    else:
        images = sorted(f for f in input_dir.iterdir() if is_image(f))

    if not images:
        if verbose:
            print(f"⚠️  No images found in: {input_dir}")
        return results

    if verbose:
        mode = "RETRY" if retry_files is not None else "BATCH"
        print(f"\n{'─'*60}")
        print(f"  Rent Magazine — Image Processor  [{mode}]")
        print(f"{'─'*60}")
        print(f"  Input      : {input_dir}")
        print(f"  Output     : {output_dir}")
        print(f"  Property   : {property_name} / Room {room}")
        print(f"  Mgmt #     : {management_number or '(not set)'}")
        print(f"  Image Type : {image_type}")
        print(f"  Images     : {len(images)}")
        print(f"{'─'*60}\n")

    for i, img_path in enumerate(images, 1):
        try:
            if verbose:
                print(f"  [{i:02d}/{len(images):02d}] {img_path.name} ...", end=" ", flush=True)

            img   = Image.open(img_path)
            theta = is_theta_image(img, img_path)

            # Camera Raw adjustments (all image types)
            processed = apply_camera_raw(img)

            # Logo overlay (regular photos only)
            if not theta:
                processed = apply_logo(processed, logo)

            # Output folder and filename
            out_path       = build_output_path(output_dir, city, property_name, room,
                                               theta, hiragana, station)
            file_type      = "THETA" if theta else image_type
            seq            = next_sequence(out_path, management_number, property_name, room, file_type)
            out_filename   = build_output_filename(management_number, property_name, room, file_type, seq)
            out_file       = out_path / out_filename

            processed.save(str(out_file), "JPEG", quality=30, optimize=True)

            results["processed"].append({
                "source": str(img_path),
                "output": str(out_file),
                "type":   "theta" if theta else "regular",
            })

            if verbose:
                print(f"✅  →  {out_filename}")
            if progress_callback:
                progress_callback(i, len(images), img_path.name, out_filename, "✅")

        except Exception as e:
            results["failed"].append({"file": str(img_path), "error": str(e)})
            if verbose:
                print(f"❌  {e}")
            if progress_callback:
                progress_callback(i, len(images), img_path.name, "", f"❌ {e}")

    end_time            = datetime.now()
    results["end_time"] = end_time.isoformat()
    duration            = round((end_time - start_time).total_seconds(), 1)

    # ── Save processing log alongside output ──
    log_data = {
        "session": {
            "start_time":       results["start_time"],
            "end_time":         results["end_time"],
            "duration_seconds": duration,
            "mode":             "retry" if retry_files is not None else "batch",
        },
        "property": {
            "management_number": management_number,
            "property_name":     property_name,
            "room":              room,
            "city":              city,
            "image_type":        image_type,
        },
        "summary": {
            "total":     len(images),
            "processed": len(results["processed"]),
            "failed":    len(results["failed"]),
        },
        "processed": results["processed"],
        "failed":    results["failed"],
    }
    try:
        ts       = start_time.strftime("%Y%m%d_%H%M%S")
        log_file = output_dir / f"processing_log_{ts}.json"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        results["log_file"] = str(log_file)
    except Exception as e:
        if verbose:
            print(f"⚠️  Could not write log: {e}")

    if verbose:
        print(f"\n{'─'*60}")
        print(f"  ✅ Processed : {len(results['processed'])} images")
        print(f"  ❌ Failed    : {len(results['failed'])} images")
        print(f"  ⏱  Duration  : {duration}s")
        if results.get("log_file"):
            print(f"  📋 Log       : {results['log_file']}")
        print(f"{'─'*60}\n")

    return results


# ─────────────────────────────────────────────────────────────
# CLI Entry Point
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Rent Magazine Phase 1 — Image Processing Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Non-Nagoya property
  python3 rent_magazine_processor.py \\
    --input ./photos --logo ./logo.png --output ./output \\
    --city Chiryu --property "OO Mansion" --room 101 \\
    --image-type リビング --management-number RM-R000001

  # Nagoya property (requires --hiragana and --station)
  python3 rent_magazine_processor.py \\
    --input ./photos --logo ./logo.png --output ./output \\
    --city Nagoya --property "OO Mansion" --room 301 \\
    --image-type リビング --management-number RM-R000001 \\
    --hiragana sa --station Sakae

Note: THETA 360° images are detected automatically (no --type flag needed).
        """,
    )

    parser.add_argument("--input",             required=True,  help="Folder of raw input images")
    parser.add_argument("--logo",              required=True,  help="Path to logo PNG")
    parser.add_argument("--output",            required=True,  help="Base output folder")
    parser.add_argument("--city",              required=True,  help="City name (e.g. Nagoya, Chiryu)")
    parser.add_argument("--property",          required=True,  dest="property_name",
                                                               help="Property name")
    parser.add_argument("--room",              required=True,  help="Room/unit number")
    parser.add_argument("--image-type",        required=True,  dest="image_type",
                                                               help="Room label for filename (e.g. リビング). THETA is auto-detected.")
    parser.add_argument("--management-number", default="",     dest="management_number",
                                                               help="Management number (e.g. RM-R000001)")
    parser.add_argument("--hiragana",          default="",     help="Hiragana group for Nagoya (e.g. sa)")
    parser.add_argument("--station",           default="",     help="Nearest station for Nagoya (e.g. Sakae)")
    parser.add_argument("--quiet",             action="store_true", help="Suppress per-file output")

    args = parser.parse_args()

    input_dir  = Path(args.input)
    logo_path  = Path(args.logo)
    output_dir = Path(args.output)

    if not input_dir.exists():
        print(f"❌ Input folder not found: {input_dir}")
        sys.exit(1)

    if args.city.lower() in ("nagoya", "名古屋") and (not args.hiragana or not args.station):
        print("❌ --hiragana and --station are required for Nagoya")
        sys.exit(1)

    process_images(
        input_dir=input_dir,
        logo_path=logo_path,
        output_dir=output_dir,
        city=args.city,
        property_name=args.property_name,
        room=args.room,
        image_type=args.image_type,
        management_number=args.management_number,
        hiragana=args.hiragana,
        station=args.station,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    main()
