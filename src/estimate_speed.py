#!/usr/bin/env python3
"""
Dash cam speed estimator using optical flow + IPM.

Usage:
    python estimate_speed.py --video videos/drive.mp4 --profile config/family_car.yaml --output outputs/result.mp4

Press:
    q / ESC  = quit
    p        = pause
    r        = reset tracked points
    d        = toggle debug view (IPM warp)
"""

import argparse
import math
import sys
from collections import deque
from pathlib import Path

import cv2
import numpy as np
import yaml


def load_profile(path: Path) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def init_features(gray, feature_params, mask):
    """Detect good features to track inside the masked ROI."""
    pts = cv2.goodFeaturesToTrack(gray, mask=mask, **feature_params)
    return pts


def compute_speed(
    prev_pts, curr_pts, status, mpp, dt, fps,
    min_motion_pixels: float
):
    """
    Convert tracked pixel displacements to speed in km/h.

    Args:
        prev_pts, curr_pts: Nx1x2 arrays from LK
        status: 1D array from LK (1 = found)
        mpp: meters per pixel (float)
        dt: time delta in seconds
        fps: frames per second
        min_motion_pixels: ignore motion below this threshold

    Returns:
        speed_kmh: scalar or None
        valid_prev, valid_curr: filtered point arrays for visualization
    """
    if prev_pts is None or curr_pts is None or status is None:
        return None, None, None

    valid_prev = []
    valid_curr = []
    distances_m = []

    for p0, p1, s in zip(prev_pts, curr_pts, status):
        if not s:
            continue
        x0, y0 = p0.ravel()
        x1, y1 = p1.ravel()

        dx = x1 - x0
        dy = y1 - y0
        dist_px = math.hypot(dx, dy)

        if dist_px < min_motion_pixels:
            continue

        dist_m = dist_px * mpp
        distances_m.append(dist_m)
        valid_prev.append((x0, y0))
        valid_curr.append((x1, y1))

    if not distances_m:
        return None, None, None

    # Median displacement this frame (robust to outliers)
    median_disp_m = float(np.median(distances_m))

    # Speed: distance / time
    # dt should be ~1/fps, but we measure actual
    if dt <= 0:
        return None, None, None

    speed_ms = median_disp_m / dt
    speed_kmh = speed_ms * 3.6

    valid_prev = np.array(valid_prev, dtype=np.float32).reshape(-1, 1, 2)
    valid_curr = np.array(valid_curr, dtype=np.float32).reshape(-1, 1, 2)

    return speed_kmh, valid_prev, valid_curr


def create_roi_mask(frame_shape, roi):
    """Build a binary mask for the region of interest."""
    h, w = frame_shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    x1 = int(roi["x_start"] * w)
    y1 = int(roi["y_start"] * h)
    x2 = int(roi["x_end"] * w)
    y2 = int(roi["y_end"] * h)
    cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
    return mask


def draw_overlay(frame, speed_kmh, prev_pts, curr_pts, roi, fps, debug_info=None):
    h, w = frame.shape[:2]
    overlay = frame.copy()

    # Draw ROI rectangle
    x1 = int(roi["x_start"] * w)
    y1 = int(roi["y_start"] * h)
    x2 = int(roi["x_end"] * w)
    y2 = int(roi["y_end"] * h)
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 255), 2)

    # Draw tracks
    if prev_pts is not None and curr_pts is not None:
        for p0, p1 in zip(prev_pts, curr_pts):
            x0, y0 = p0.ravel()
            x1_, y1_ = p1.ravel()
            cv2.line(overlay, (int(x0), int(y0)), (int(x1_), int(y1_)), (0, 255, 0), 2)
            cv2.circle(overlay, (int(x1_), int(y1_)), 3, (0, 0, 255), -1)

    # Draw speed panel
    panel_w, panel_h = 320, 120
    cv2.rectangle(overlay, (10, 10), (10 + panel_w, 10 + panel_h), (0, 0, 0), -1)
    cv2.rectangle(overlay, (10, 10), (10 + panel_w, 10 + panel_h), (255, 255, 255), 2)

    if speed_kmh is not None:
        text = f"{speed_kmh:.1f} km/h"
        color = (0, 255, 0) if speed_kmh < 120 else (0, 0, 255)
    else:
        text = "-- km/h"
        color = (128, 128, 128)

    cv2.putText(overlay, text, (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 2.0, color, 3)

    # Sub-info
    info = f"FPS: {fps:.1f}"
    if debug_info:
        info += f" | {debug_info}"
    cv2.putText(overlay, info, (30, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

    return overlay


def main():
    parser = argparse.ArgumentParser(description="Estimate vehicle speed from dash cam video")
    parser.add_argument("--video", required=True, help="Path to input video")
    parser.add_argument("--profile", required=True, help="Path to vehicle YAML profile")
    parser.add_argument("--output", help="Path to save output video (optional)")
    parser.add_argument("--headless", action="store_true", help="Process without GUI (e.g., for batch jobs)")
    args = parser.parse_args()

    video_path = Path(args.video)
    profile = load_profile(Path(args.profile))

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"[ERROR] Cannot open video: {video_path}")
        sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

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
        print("[INFO] Using calibrated homography for IPM.")
    else:
        print("[WARN] No homography found. Using approximate meters_per_pixel only.")
        print("[WARN] Run src/calibrate.py with a reference image for accuracy.")

    # Video writer
    writer = None
    if args.output:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(args.output, fourcc, fps, (frame_w, frame_h))

    # State
    prev_gray = None
    prev_pts = None
    speed_history = deque(maxlen=smooth_win)
    frame_idx = 0
    paused = False
    show_debug = False
    last_time = 0.0

    print("[INFO] Starting speed estimation...")
    print("       q/ESC = quit | p = pause | r = reset points | d = debug view")

    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                print("[INFO] End of video.")
                break
            frame_idx += 1
        else:
            # When paused, keep showing current frame
            pass

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # --- Feature initialization on first frame or reset ---
        if prev_gray is None or prev_pts is None or len(prev_pts) < 10:
            roi_mask = create_roi_mask(frame.shape, roi)
            prev_pts = init_features(gray, feature_params, roi_mask)
            prev_gray = gray.copy()
            if prev_pts is not None:
                print(f"[INFO] Detected {len(prev_pts)} features.")
            continue

        # --- Optical Flow ---
        curr_pts, status, err = cv2.calcOpticalFlowPyrLK(
            prev_gray, gray, prev_pts, None, **lk_params
        )

        if curr_pts is not None:
            # Keep only successfully tracked points
            good_new = curr_pts[status == 1]
            good_old = prev_pts[status == 1]

            # If homography exists, warp points to IPM before measuring
            if homography is not None and len(good_new) > 0:
                # Warp points through H
                # pts shape: Nx1x2
                new_ipm = cv2.perspectiveTransform(good_new.reshape(-1, 1, 2), homography)
                old_ipm = cv2.perspectiveTransform(good_old.reshape(-1, 1, 2), homography)
                speed_kmh, vprev, vcurr = compute_speed(
                    old_ipm, new_ipm, [1] * len(old_ipm),
                    mpp=1.0, dt=1.0 / fps, fps=fps,
                    min_motion_pixels=min_motion
                )
                # Use vcurr for visualization on original frame (map back?)
                # For simplicity, visualize on original
                viz_prev = good_old.reshape(-1, 1, 2)
                viz_curr = good_new.reshape(-1, 1, 2)
            else:
                speed_kmh, viz_prev, viz_curr = compute_speed(
                    good_old.reshape(-1, 1, 2),
                    good_new.reshape(-1, 1, 2),
                    [1] * len(good_new),
                    mpp=mpp, dt=1.0 / fps, fps=fps,
                    min_motion_pixels=min_motion
                )

            if speed_kmh is not None:
                speed_history.append(speed_kmh)

            # Smooth output
            if speed_history:
                display_speed = float(np.median(speed_history))
            else:
                display_speed = None

            # --- Visualization ---
            debug_info = f"pts: {len(good_new)}"
            overlay = draw_overlay(frame, display_speed, viz_prev, viz_curr, roi, fps, debug_info)

            # Debug: show IPM warp
            if show_debug and homography is not None:
                ipm_w = profile["ipm"]["width"]
                ipm_h = profile["ipm"]["height"]
                ipm_view = cv2.warpPerspective(frame, homography, (ipm_w, ipm_h))
                cv2.imshow("IPM Debug", ipm_view)
            elif show_debug:
                cv2.imshow("IPM Debug", np.zeros((240, 320, 3), dtype=np.uint8))

            if not args.headless:
                cv2.imshow("Speed Estimator", overlay)

            if writer:
                writer.write(overlay)

            # --- Update state ---
            prev_gray = gray.copy()
            prev_pts = good_new.reshape(-1, 1, 2)

            # Re-detect if too few remain
            if len(prev_pts) < 30:
                roi_mask = create_roi_mask(frame.shape, roi)
                new_pts = init_features(gray, feature_params, roi_mask)
                if new_pts is not None:
                    prev_pts = new_pts

        # Keyboard
        if not args.headless:
            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), 27):
                break
            elif key == ord('p'):
                paused = not paused
                print("[INFO] Paused." if paused else "[INFO] Resumed.")
            elif key == ord('r'):
                prev_pts = None
                print("[INFO] Resetting features...")
            elif key == ord('d'):
                show_debug = not show_debug
                print(f"[INFO] Debug view {'ON' if show_debug else 'OFF'}.")

    cap.release()
    if writer:
        writer.release()
    cv2.destroyAllWindows()
    print("[INFO] Done.")


if __name__ == "__main__":
    main()
