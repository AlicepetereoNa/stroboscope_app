import os
from pathlib import Path
import time
import shutil
import json
from stroboscope import render_engine, scene_manager, file_manager, progress_monitor

# Experiments definition
# A: rotation 0.5 Hz (= 30 RPM), r in [0, 0.5, 0.4, 0.6, 0.05, 1.0], quality=2 (30 FPS)
# B: rotation 0.5 Hz (= 30 RPM), r = 0.4, quality in [1,2,3]
A_ITEMS = [
    ("A-1", 30.0, 0.0, 2),
    ("A-2", 30.0, 0.5, 2),
    ("A-3", 30.0, 0.4, 2),
    ("A-4", 30.0, 0.6, 2),
    ("A-5", 30.0, 0.05, 2),
    ("A-6", 30.0, 1.0, 2),
]
B_ITEMS = [
    ("B-1", 30.0, 0.4, 1),
    ("B-2", 30.0, 0.4, 2),
    ("B-3", 30.0, 0.4, 3),
]

# Make target dir relative to this script file location (project-root agnostic)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR
# If script placed at project root, this is the root; if moved, still local
TARGET_DIR = str(PROJECT_ROOT / "experiment_videos")
os.makedirs(TARGET_DIR, exist_ok=True)


def wait_until_done(timeout_sec: int = 1800) -> dict:
    start = time.time()
    while time.time() - start < timeout_sec:
        status = progress_monitor.get_status()
        if not status.get("is_rendering"):
            return status
        time.sleep(0.5)
    return {"is_rendering": False, "error": "timeout"}


def render_one(label: str, rpm: float, r_hz: float, quality: int) -> dict:
    # If target already exists, skip re-render to save time
    dst_name = f"{label.replace('-', '_')}.mp4"
    dst = os.path.join(TARGET_DIR, dst_name)
    if os.path.exists(dst):
        return {"label": label, "success": True, "path": dst, "skipped": True}

    unique_suffix = str(int(time.time() * 1000))[-6:]
    unique_id = f"{label.lower()}_{unique_suffix}"

    # retry submit if engine busy
    max_submit_retries = 3
    backoff = 2.0
    for attempt in range(1, max_submit_retries + 1):
        ok = render_engine.render_animation(rpm, r_hz, quality, unique_id)
        if ok:
            break
        if attempt == max_submit_retries:
            return {"label": label, "success": False, "error": "engine busy"}
        time.sleep(backoff)
        backoff *= 1.5

    status = wait_until_done()
    if status.get("error"):
        return {"label": label, "success": False, "error": status["error"]}

    # Locate the file by expected name pattern
    src = file_manager.get_video_path(unique_id)
    if not src or not os.path.exists(src):
        # fallback: try scan video dir
        expected = f"stroboscope_{unique_id}.mp4"
        for root, _, files in os.walk(file_manager.video_dir):
            for f in files:
                if f == expected:
                    src = os.path.join(root, f)
                    break
        if not src or not os.path.exists(src):
            return {"label": label, "success": False, "error": "video not found"}

    # Copy to target with requested name (safe: we already checked existence)
    shutil.copy2(src, dst)
    return {"label": label, "success": True, "path": dst}


def main():
    results = []
    items = A_ITEMS + B_ITEMS
    for idx, (label, rpm, r_hz, q) in enumerate(items):
        res = render_one(label, rpm, r_hz, q)
        results.append(res)
        # small spacing between tasks to avoid overlap
        time.sleep(1.0)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
