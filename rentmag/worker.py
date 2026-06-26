"""Background QThread worker that runs the image processing pipeline."""

from __future__ import annotations

import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import QThread, pyqtSignal

from rentmag.processor import process_images, is_image, is_theta_image

try:
    from PIL import Image
    _PIL = True
except ImportError:
    _PIL = False

STEPS = ["検出", "リネーム", "振り分け", "レタッチ", "ロゴ挿入", "JPG保存"]


class ProcessingWorker(QThread):
    """
    Runs process_images() on a background thread and emits Qt signals
    for the GUI to display progress, logs, previews, and statistics.
    """

    log_signal      = pyqtSignal(str, str, str)       # timestamp, level, message
    stats_signal    = pyqtSignal(dict)                 # running counts
    step_signal     = pyqtSignal(str, int)             # step name, step index
    progress_signal = pyqtSignal(int, int, str, str)  # current, total, src_path, out_path
    finished_signal = pyqtSignal(dict)                 # final results dict
    error_signal    = pyqtSignal(str)                  # critical error message
    elapsed_signal  = pyqtSignal(str)                  # HH:MM:SS elapsed

    def __init__(self, params: dict, retry_files: Optional[list] = None):
        super().__init__()
        self.params      = params
        self.retry_files = retry_files

        self._stop  = threading.Event()
        self._pause = threading.Event()
        self._t0: Optional[datetime] = None

        self._stats = dict(total=0, regular=0, theta=0,
                           done=0, active=0, success=0, failed=0, skipped=0)

    # ── Control ────────────────────────────────────────────────────────────────

    def stop(self)   -> None: self._stop.set()
    def pause(self)  -> None: self._pause.set()
    def resume(self) -> None: self._pause.clear()

    # ── Thread entry ───────────────────────────────────────────────────────────

    def run(self) -> None:
        self._t0 = datetime.now()
        threading.Thread(target=self._tick, daemon=True).start()
        try:
            self._run_pipeline()
        except Exception as e:
            self.error_signal.emit(str(e))
            self._log("ERROR", f"致命的エラー: {e}")
        finally:
            self._stop.set()

    def _tick(self) -> None:
        """Emit elapsed time every second until stopped."""
        while not self._stop.is_set() and self.isRunning():
            d = datetime.now() - self._t0
            h, rem = divmod(int(d.total_seconds()), 3600)
            m, s   = divmod(rem, 60)
            self.elapsed_signal.emit(f"{h:02d}:{m:02d}:{s:02d}")
            time.sleep(1)

    # ── Internal helpers ────────────────────────────────────────────────────────

    def _log(self, level: str, msg: str) -> None:
        ts = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        self.log_signal.emit(ts, level, msg)

    def _on_file(self, current: int, total: int,
                 src: str, out: str, status: str) -> None:
        """progress_callback passed to process_images."""
        while self._pause.is_set() and not self._stop.is_set():
            time.sleep(0.05)
        if self._stop.is_set():
            return

        ok  = "✅" in status
        err = "❌" in status

        self._stats["done"]   = current
        self._stats["active"] = 0 if current >= total else 1
        if ok:
            self._stats["success"] += 1
            self._log("INFO", f"{Path(src).name} の処理が完了しました。")
        elif err:
            self._stats["failed"] += 1
            detail = status.replace("❌", "").strip()
            self._log("WARN", f"{Path(src).name} の処理に失敗しました。[{detail}]")

        self.progress_signal.emit(current, total, src, out)
        self.stats_signal.emit(dict(self._stats))

    def _emit_step(self, name: str, idx: int) -> None:
        self.step_signal.emit(name, idx)

    # ── Pipeline ───────────────────────────────────────────────────────────────

    def _run_pipeline(self) -> None:
        p          = self.params
        input_dir  = Path(p["input_dir"])
        logo_path  = Path(p["logo_path"])
        output_dir = Path(p["output_dir"])

        # Build file list
        if self.retry_files:
            images = [Path(f) for f in self.retry_files if is_image(Path(f))]
        else:
            images = sorted(f for f in input_dir.iterdir() if is_image(f))

        self._log("INFO", f"処理を開始しました。[管理番号: {p.get('management_number', '-')}]")

        if not images:
            self._log("WARN", "処理対象のファイルが見つかりませんでした。")
            self.finished_signal.emit({"processed": [], "failed": [], "skipped": []})
            return

        # Count THETA vs regular
        regular = theta = 0
        if _PIL:
            for f in images:
                try:
                    if is_theta_image(Image.open(f), f):
                        theta += 1
                    else:
                        regular += 1
                except Exception:
                    regular += 1
        else:
            regular = len(images)

        self._stats.update(total=len(images), regular=regular, theta=theta,
                           done=0, active=1, success=0, failed=0, skipped=0)
        self.stats_signal.emit(dict(self._stats))
        self._log("INFO", f"ファイル検出: {len(images)}件（通常: {regular}, THETA: {theta}）")

        # Announce prep steps before processing starts
        for idx, name in enumerate(STEPS[:4]):
            self._emit_step(name, idx)
            if idx > 0:
                time.sleep(0.04)

        results = process_images(
            input_dir=input_dir, logo_path=logo_path, output_dir=output_dir,
            city=p.get("city", ""), property_name=p.get("property_name", ""),
            room=p.get("room", ""), image_type=p.get("image_type", ""),
            management_number=p.get("management_number", ""),
            hiragana=p.get("hiragana", ""), station=p.get("station", ""),
            verbose=False,
            progress_callback=self._on_file,
            retry_files=self.retry_files,
        )

        if not self._stop.is_set():
            self._emit_step("ロゴ挿入", 4)
            self._emit_step("JPG保存",  5)

        self._stats["active"] = 0
        self.stats_signal.emit(dict(self._stats))

        n_ok  = len(results["processed"])
        n_err = len(results["failed"])
        self._log("INFO", f"処理完了: 成功 {n_ok}件、失敗 {n_err}件")
        self.finished_signal.emit(results)
