"""
Image processing pipeline.

Camera Raw adjustments mirror the Photoshop action PDF:
  Exposure +0.60 | Contrast -16 | Highlights -50
  Shadows -4     | Whites +50   | Blacks +100

Logo overlay specs:
  Portrait  → scale 221.6 %, offset (−716.3 px, −1726.3 px), opacity 45 %
  Landscape → scale 257.7 %, offset (−1112.4 px, −1253.1 px), opacity 45 %

Output folder layout:
  Non-Nagoya : suumo/{city}/{property}/{room}/image/04_web/{02_web|01_theta}/
  Nagoya     : suumo/名古屋/{hiragana}/{station}/{property}/{room}/image/04_web/{…}/

CLI:
  python -m rentmag.processor --input ./photos --logo ./logo.png --output ./out \\
      --city Chiryu --property "OO Mansion" --room 101 --image-type リビング
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

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
    print("Missing dependencies — run: pip install Pillow numpy")
    sys.exit(1)


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


def is_image(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


# ── THETA detection ────────────────────────────────────────────────────────────

def is_theta_image(img: Image.Image, path: Path) -> bool:
    """
    Return True when the image is a THETA 360° panoramic.
    Checks EXIF Make/Model first, then falls back to 2:1 aspect ratio.
    """
    try:
        exif = img._getexif() or {}
        make  = str(exif.get(271, "")).upper()
        model = str(exif.get(272, "")).upper()
        if any(k in make  for k in ("RICOH", "THETA")): return True
        if "THETA" in model: return True
    except Exception:
        pass
    w, h = img.size
    return w > h and abs(w / h - 2.0) < 0.03


# ── Camera Raw ─────────────────────────────────────────────────────────────────

def apply_camera_raw(img: Image.Image) -> Image.Image:
    """Apply Camera Raw adjustments (Exposure / Contrast / Highlights / …)."""
    arr = np.array(img.convert("RGB"), dtype=np.float32)

    arr = arr * (2 ** 0.60)                                    # Exposure  +0.60
    arr = np.where(arr > 200, arr + (arr - 200) * 0.25, arr)  # Whites    +50
    arr = np.where(arr < 50,  arr + 30,                  arr)  # Blacks    +100
    arr = np.where(arr > 200, arr - (arr - 200) * 0.30,  arr)  # Highlights -50
    arr = np.where(arr < 100, arr * 0.98,                arr)  # Shadows   -4
    arr = 128.0 + (arr - 128.0) * (1 - 0.16 * 0.5)            # Contrast  -16

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


# ── Logo overlay ───────────────────────────────────────────────────────────────

def apply_logo(img: Image.Image, logo: Image.Image) -> Image.Image:
    """Paste a semi-transparent logo onto the image at the spec position."""
    base = img.convert("RGBA")
    lg   = logo.convert("RGBA")

    iw, ih = base.size
    lw, lh = lg.size

    if ih > iw:   # portrait
        scale, ox, oy = 2.216, -716.3, -1726.3
    else:          # landscape
        scale, ox, oy = 2.577, -1112.4, -1253.1

    nw, nh  = int(lw * scale), int(lh * scale)
    lg      = lg.resize((nw, nh), Image.LANCZOS)

    r, g, b, a = lg.split()
    a = a.point(lambda v: int(v * 0.45))
    lg = Image.merge("RGBA", (r, g, b, a))

    cx, cy   = iw // 2, ih // 2
    paste_x  = int(cx + ox - nw // 2)
    paste_y  = int(cy + oy - nh // 2)

    base.paste(lg, (paste_x, paste_y), lg)
    return base.convert("RGB")


# ── Folder / filename helpers ──────────────────────────────────────────────────

def build_output_path(
    base: Path, city: str, property_name: str, room: str,
    is_theta: bool, hiragana: str = "", station: str = "",
) -> Path:
    sub = "01_theta" if is_theta else "02_web"
    if city.lower() in ("nagoya", "名古屋"):
        path = base / "suumo" / "名古屋" / hiragana / station / property_name / room / "image" / "04_web" / sub
    else:
        path = base / "suumo" / city / property_name / room / "image" / "04_web" / sub
    path.mkdir(parents=True, exist_ok=True)
    return path


def _next_sequence(out_path: Path, mgmt: str, prop: str, room: str, img_type: str) -> int:
    parts  = [p for p in (mgmt, prop, room, img_type) if p]
    prefix = "_".join(parts) + "_" if parts else ""
    return len(list(out_path.glob(f"{prefix}*.jpg"))) + 1


def build_output_filename(mgmt: str, prop: str, room: str, img_type: str, seq: int) -> str:
    parts = [mgmt, prop, room, img_type, f"{seq:02d}"]
    return "_".join(p for p in parts if p) + ".jpg"


# ── Main pipeline ──────────────────────────────────────────────────────────────

ProgressCallback = Callable[[int, int, str, str, str], None]


def process_images(
    input_dir:         Path,
    logo_path:         Path,
    output_dir:        Path,
    city:              str,
    property_name:     str,
    room:              str,
    image_type:        str,
    management_number: str = "",
    hiragana:          str = "",
    station:           str = "",
    verbose:           bool = True,
    progress_callback: Optional[ProgressCallback] = None,
    retry_files:       Optional[List] = None,
) -> dict:
    """
    Process a batch of images and return:
      { "processed": [...], "failed": [...], "skipped": [],
        "start_time": ISO, "end_time": ISO, "log_file": path|None }
    """
    start = datetime.now()
    results: dict = {"processed": [], "failed": [], "skipped": [],
                     "start_time": start.isoformat(), "end_time": None, "log_file": None}

    if not logo_path.exists():
        raise FileNotFoundError(f"Logo not found: {logo_path}")

    logo   = Image.open(logo_path).convert("RGBA")
    images = (sorted(Path(f) for f in retry_files if is_image(Path(f)))
              if retry_files is not None
              else sorted(f for f in input_dir.iterdir() if is_image(f)))

    if not images:
        if verbose:
            print(f"⚠  No images in: {input_dir}")
        return results

    if verbose:
        mode = "RETRY" if retry_files is not None else "BATCH"
        print(f"\n{'─'*56}\n  RentMag Processor  [{mode}]")
        print(f"  Property : {property_name} / {room}")
        print(f"  Mgmt #   : {management_number or '(not set)'}")
        print(f"  Images   : {len(images)}\n{'─'*56}\n")

    for i, img_path in enumerate(images, 1):
        try:
            if verbose:
                print(f"  [{i:02d}/{len(images):02d}] {img_path.name} ...", end=" ", flush=True)

            img   = Image.open(img_path)
            theta = is_theta_image(img, img_path)
            proc  = apply_camera_raw(img)
            if not theta:
                proc = apply_logo(proc, logo)

            out_dir  = build_output_path(output_dir, city, property_name, room,
                                         theta, hiragana, station)
            ftype    = "THETA" if theta else image_type
            seq      = _next_sequence(out_dir, management_number, property_name, room, ftype)
            out_name = build_output_filename(management_number, property_name, room, ftype, seq)
            out_file = out_dir / out_name

            proc.save(str(out_file), "JPEG", quality=30, optimize=True)
            results["processed"].append({"source": str(img_path), "output": str(out_file),
                                          "type": "theta" if theta else "regular"})

            if verbose:           print(f"✅  →  {out_name}")
            if progress_callback: progress_callback(i, len(images), str(img_path), str(out_file), "✅")

        except Exception as e:
            results["failed"].append({"file": str(img_path), "error": str(e)})
            if verbose:           print(f"❌  {e}")
            if progress_callback: progress_callback(i, len(images), str(img_path), "", f"❌ {e}")

    end = datetime.now()
    results["end_time"] = end.isoformat()
    duration = round((end - start).total_seconds(), 1)

    # Save JSON log
    log_data = {
        "session":  {"start": results["start_time"], "end": results["end_time"],
                     "duration_s": duration,
                     "mode": "retry" if retry_files is not None else "batch"},
        "property": {"management_number": management_number, "property_name": property_name,
                     "room": room, "city": city, "image_type": image_type},
        "summary":  {"total": len(images), "processed": len(results["processed"]),
                     "failed": len(results["failed"])},
        "processed": results["processed"],
        "failed":    results["failed"],
    }
    try:
        log_file = output_dir / f"log_{start.strftime('%Y%m%d_%H%M%S')}.json"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        results["log_file"] = str(log_file)
    except Exception:
        pass

    if verbose:
        print(f"\n{'─'*56}")
        print(f"  ✅ Processed : {len(results['processed'])}")
        print(f"  ❌ Failed    : {len(results['failed'])}")
        print(f"  ⏱  Duration  : {duration}s")
        print(f"{'─'*56}\n")

    return results


# ── CLI entry point ────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="RentMag Phase 1 — Image Processor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--input",    required=True,  help="Input folder of raw photos")
    ap.add_argument("--logo",     required=True,  help="Logo PNG path")
    ap.add_argument("--output",   required=True,  help="Base output folder")
    ap.add_argument("--city",     required=True)
    ap.add_argument("--property", required=True,  dest="property_name")
    ap.add_argument("--room",     required=True)
    ap.add_argument("--image-type", required=True, dest="image_type",
                    help="Room label for filenames, e.g. リビング (THETA auto-detected)")
    ap.add_argument("--management-number", default="", dest="management_number")
    ap.add_argument("--hiragana",  default="", help="Nagoya hiragana group (e.g. さ)")
    ap.add_argument("--station",   default="", help="Nagoya nearest station (e.g. 栄)")
    ap.add_argument("--quiet",     action="store_true")
    args = ap.parse_args()

    input_dir = Path(args.input)
    if not input_dir.exists():
        print(f"❌ Input folder not found: {input_dir}")
        sys.exit(1)
    if args.city.lower() in ("nagoya", "名古屋") and not (args.hiragana and args.station):
        print("❌ --hiragana and --station are required for Nagoya")
        sys.exit(1)

    process_images(
        input_dir=input_dir, logo_path=Path(args.logo),
        output_dir=Path(args.output), city=args.city,
        property_name=args.property_name, room=args.room,
        image_type=args.image_type, management_number=args.management_number,
        hiragana=args.hiragana, station=args.station,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    main()
