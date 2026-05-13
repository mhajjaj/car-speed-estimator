#!/usr/bin/env python3
"""
Per-frame speed logger + accuracy analyzer.

Usage:
    python src/analyze_speed.py --video videos/truck_video.mp4 --profile config/truck.yaml

Outputs a CSV of every frame's raw speed, smoothed speed, and point count.
Then prints accuracy statistics.
"""

import argparse
import csv
import math
import sys
from pathlib import Path
from collections import deque
import numpy as np

# Use functions from estimate_speed.py
sys.path.insert(0, str(Path(__file__).parent))
from estimate_speed import load_profile, init_features, compute_speed, create_roi_mask

import cv2


def main():
    parser = argparse.ArgumentParser(description="Log per-frame speed for analysis")
    parser.add_argument("--video", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--csv", default="outputs/speed_log.csv")
    parser.add_argument("--max-frames", type=int, default=0, help="Limit frames for quick test")
    args = parser.parse_args()

    profile = load_profile(Path(args.profile))
    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open {args.video}")
        sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    roi = profile["roi"]
    lk_params = {
        "winSize": tuple(profile["lk_params"]["winSize"]),
        "maxLevel": profile["lk_params"]["maxLevel"],
        "criteria": tuple(profile["lk_params"]["criteria"]),
    }
    feature_params = {
        "maxCorners": profile["feature_params"]["maxCorners"],
        "qualityLevel": profile["feature_params"]["qualityLevel"],
        "minDistance": profile["feature_params"]["minDistance"],
        "blockSize": profile["feature_params"]["blockSize"],
    }
    min_motion = profile.get("min_motion_pixels", 1.0)
    smooth_win = profile.get("smoothing_window", 10)
    mpp = profile["ipm"].get("meters_per_pixel", 0.04)

    homography = None
    if "homography" in profile["ipm"]:
        homography = np.array(profile["ipm"]["homography"], dtype=np.float32)
        print("[INFO] Using calibrated homography.")
    else:
        print("[WARN] No homography — using constant meters_per_pixel (approximate).")

    speed_history = deque(maxlen=smooth_win)

    prev_gray = None
    prev_pts = None
    frame_idx = 0
    logs = []

    print(f"[INFO] Processing up to {total} frames @ {fps:.2f} fps ...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        if args.max_frames and frame_idx > args.max_frames:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if prev_gray is None or prev_pts is None or len(prev_pts) < 10:
            roi_mask = create_roi_mask(frame.shape, roi)
            prev_pts = init_features(gray, feature_params, roi_mask)
            prev_gray = gray.copy()
            logs.append({
                "frame": frame_idx,
                "raw_speed": None,
                "smoothed_speed": None,
                "points": 0 if prev_pts is None else len(prev_pts),
                "median_px": None,
                "state": "init"
            })
            continue

        curr_pts, status, err = cv2.calcOpticalFlowPyrLK(
            prev_gray, gray, prev_pts, None, **lk_params
        )

        raw_speed = None
        smoothed_speed = None
        median_px = None
        points = 0
        state = "track"

        if curr_pts is not None:
            good_new = curr_pts[status == 1]
            good_old = prev_pts[status == 1]
            points = len(good_new)

            if homography is not None and len(good_new) > 0:
                new_ipm = cv2.perspectiveTransform(good_new.reshape(-1, 1, 2), homography)
                old_ipm = cv2.perspectiveTransform(good_old.reshape(-1, 1, 2), homography)
                speed_kmh, _, _ = compute_speed(
                    old_ipm, new_ipm, [1] * len(old_ipm),
                    mpp=1.0, dt=1.0 / fps, fps=fps,
                    min_motion_pixels=min_motion
                )
            else:
                speed_kmh, _, _ = compute_speed(
                    good_old.reshape(-1, 1, 2),
                    good_new.reshape(-1, 1, 2),
                    [1] * len(good_new),
                    mpp=mpp, dt=1.0 / fps, fps=fps,
                    min_motion_pixels=min_motion
                )

            if speed_kmh is not None:
                raw_speed = round(speed_kmh, 2)
                speed_history.append(speed_kmh)
                smoothed_speed = round(float(np.median(speed_history)), 2)
                displacements = []
                for p0, p1 in zip(good_old, good_new):
                    x0, y0 = p0.ravel()
                    x1, y1 = p1.ravel()
                    displacements.append(math.hypot(x1 - x0, y1 - y0))
                if displacements:
                    median_px = round(float(np.median(displacements)), 2)

            if len(good_new) < 30:
                roi_mask = create_roi_mask(frame.shape, roi)
                new_pts = init_features(gray, feature_params, roi_mask)
                if new_pts is not None:
                    prev_pts = new_pts
                    state = "reinit"
                else:
                    prev_pts = good_new.reshape(-1, 1, 2)
            else:
                prev_pts = good_new.reshape(-1, 1, 2)

            prev_gray = gray.copy()

        logs.append({
            "frame": frame_idx,
            "raw_speed": raw_speed,
            "smoothed_speed": smoothed_speed,
            "points": points,
            "median_px": median_px,
            "state": state
        })

    cap.release()

    csv_path = Path(args.csv)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["frame", "raw_speed", "smoothed_speed", "points", "median_px", "state"])
        writer.writeheader()
        writer.writerows(logs)
    print(f"[INFO] Wrote {len(logs)} rows to {csv_path}")

    speeds = [r["smoothed_speed"] for r in logs if r["smoothed_speed"] is not None]
    raw_speeds = [r["raw_speed"] for r in logs if r["raw_speed"] is not None]
    pxs = [r["median_px"] for r in logs if r["median_px"] is not None]
    init_count = sum(1 for r in logs if r["state"] == "init")
    reinit_count = sum(1 for r in logs if r["state"] == "reinit")

    print("\n========== SPEED ACCURACY REPORT ==========")
    print(f"Total frames processed:  {len(logs)}")
    print(f"Frames with valid speed: {len(speeds)} ({len(speeds)/len(logs)*100:.1f}%)")
    print(f"Init events (skipped):   {init_count}")
    print(f"Re-init events:          {reinit_count}")
    print(f"\n--- SMOOTHED SPEED (displayed on video) ---")
    if speeds:
        print(f"  Min:    {min(speeds):.1f} km/h")
        print(f"  Max:    {max(speeds):.1f} km/h")
        print(f"  Mean:   {sum(speeds)/len(speeds):.1f} km/h")
        print(f"  Median: {sorted(speeds)[len(speeds)//2]:.1f} km/h")
        std = math.sqrt(sum((x-sum(speeds)/len(speeds))**2 for x in speeds)/len(speeds))
        print(f"  StdDev: {std:.1f} km/h")
        print(f"  Jitter (max-min): {max(speeds)-min(speeds):.1f} km/h")
    print(f"\n--- RAW SPEED (before smoothing) ---")
    if raw_speeds:
        print(f"  Min:    {min(raw_speeds):.1f} km/h")
        print(f"  Max:    {max(raw_speeds):.1f} km/h")
        std_raw = math.sqrt(sum((x-sum(raw_speeds)/len(raw_speeds))**2 for x in raw_speeds)/len(raw_speeds))
        print(f"  StdDev: {std_raw:.1f} km/h")
        print(f"  Jitter (max-min): {max(raw_speeds)-min(raw_speeds):.1f} km/h")
    print(f"\n--- MEDIAN PIXEL DISPLACEMENT ---")
    if pxs:
        print(f"  Min:    {min(pxs):.2f} px")
        print(f"  Max:    {max(pxs):.2f} px")
        print(f"  Mean:   {sum(pxs)/len(pxs):.2f} px")

    if speeds:
        print("\n--- SPEED HISTOGRAM ---")
        bins = [(0,20), (20,40), (40,60), (60,80), (80,100), (100,120), (120,999)]
        for lo, hi in bins:
            c = sum(1 for s in speeds if lo <= s < hi)
            bar = "#" * (c * 50 // len(speeds))
            label = f"{lo:>3}-{hi:>3} km/h" if hi < 999 else "  120+ km/h"
            print(f"  {label}: {c:>4} frames {bar}")

    print("\n--- SANITY CHECKS ---")
    if speeds and max(speeds) > 120:
        print("  [!] Max speed exceeds 120 km/h — possible calibration error.")
    if speeds and (max(speeds) - min(speeds)) > 80:
        print("  [!] Speed swing > 80 km/h — high jitter.")
    if not homography:
        print("  [!] No homography matrix. Constant m/px causes ±20-40% systematic error.")
    if len(speeds) / len(logs) < 0.8:
        print("  [!] < 80% frames with valid speed. Too many init/reinit events.")

    print("==========================================\n")


if __name__ == "__main__":
    main()
