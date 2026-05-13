import cv2, numpy as np, os, json

def analyze_frame(img_path, t):
    img = cv2.imread(img_path)
    h, w = img.shape[:2]
    print(f"\n=== Frame at {t}s ({w}x{h}) ===")
    
    crop_y = int(h * 0.5)
    roi = img[crop_y:h, :]
    roi_h, roi_w = roi.shape[:2]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)
    
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50,
                            minLineLength=40, maxLineGap=30)
    
    lane_lines = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            dx = x2 - x1
            dy = y2 - y1
            if abs(dx) < 20:
                continue
            angle = np.degrees(np.arctan2(abs(dy), abs(dx)))
            if angle < 15 or angle > 75:
                continue
            y1f, y2f = y1 + crop_y, y2 + crop_y
            slope = float(dy) / dx if dx != 0 else 999
            lane_lines.append((x1, y1f, x2, y2f, slope))
    
    print(f"  Candidate lane lines: {len(lane_lines)}")
    if len(lane_lines) < 2:
        print("  Not enough lane lines.")
        return None
    
    bottom_data = []
    for x1, y1, x2, y2, slope in lane_lines:
        if abs(slope) > 0.01:
            x_bottom = x1 + (h - 1 - y1) / slope
            bottom_data.append((x_bottom, x1, y1, x2, y2, slope))
    bottom_data.sort(key=lambda item: item[0])
    
    left  = bottom_data[0]
    right = bottom_data[-1]
    lane_width_px = right[0] - left[0]
    print(f"  Lane width: {lane_width_px:.0f} px")
    
    scan_y = int(h * 0.72)
    strip_h = 30
    gray_full = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    strip = gray_full[scan_y - strip_h//2 : scan_y + strip_h//2, :]
    strip_mean = np.mean(strip, axis=0)
    
    white_thresh = 200
    white_mask = strip_mean > white_thresh
    transitions = np.diff(white_mask.astype(int))
    starts = np.where(transitions == 1)[0]
    ends   = np.where(transitions == -1)[0]
    
    if white_mask[0]:
        starts = np.concatenate(([0], starts))
    if white_mask[-1]:
        ends = np.concatenate((ends, [len(white_mask) - 1]))
    
    if len(starts) == 0 or len(ends) == 0:
        print("  No white segments found.")
        return None
    
    segments = []
    s_idx = 0
    for e in ends:
        while s_idx < len(starts) and starts[s_idx] <= e:
            segments.append((starts[s_idx], e))
            s_idx += 1
            break
    
    print(f"  Detected {len(segments)} white segments")
    
    left_x_scan = left[1] + (scan_y - left[2]) / left[5] if abs(left[5]) > 0.01 else left[1]
    nearby = [(s, e) for s, e in segments if abs((s + e) / 2 - left_x_scan) < 120]
    
    if len(nearby) < 2:
        right_x_scan = right[1] + (scan_y - right[2]) / right[5] if abs(right[5]) > 0.01 else right[1]
        nearby = [(s, e) for s, e in segments if abs((s + e) / 2 - right_x_scan) < 120]
        print(f"  Trying right boundary: {len(nearby)} dashes")
    
    if len(nearby) < 2:
        print("  Not enough dashes.")
        return None
    
    centers = [(s + e) / 2 for s, e in nearby]
    gaps = [centers[i+1] - centers[i] for i in range(len(centers) - 1)]
    gaps = [g for g in gaps if g > 10]
    if len(gaps) == 0:
        print("  No valid gaps.")
        return None
    
    avg_gap = np.mean(gaps)
    std_gap = np.std(gaps)
    print(f"  Dash-to-dash gap: {avg_gap:.1f} px (std={std_gap:.1f}, n={len(gaps)})")
    
    cycles = [
        ("Japan/EU (3m dash + 6m gap = 9m)", 9.0),
        ("US standard (3m dash + 9m gap = 12m)", 12.0),
    ]
    scales = []
    for name, cycle_m in cycles:
        scale = cycle_m / avg_gap
        scales.append((name, scale))
        print(f"    {name}: scale = {scale:.4f} m/px")
    
    return {
        "frame_time": t,
        "lane_width_px": float(lane_width_px),
        "avg_gap_px": float(avg_gap),
        "std_gap_px": float(std_gap),
        "num_gaps": len(gaps),
        "scales": dict(scales)
    }

def main():
    results = []
    for t in [4, 8, 12]:
        path = f"outputs/frame_{t}s.jpg"
        if os.path.exists(path):
            r = analyze_frame(path, t)
            if r:
                results.append(r)
    
    with open("outputs/lane_calibration.json", "w") as f:
        json.dump(results, f, indent=2)
    
    if results:
        print("\n=== Summary ===")
        all_scales = []
        for r in results:
            print(f"  t={r['frame_time']}s: gap={r['avg_gap_px']:.1f}px")
            all_scales.extend(r["scales"].values())
        mean_scale = np.mean(all_scales)
        std_scale = np.std(all_scales)
        print(f"  Avg inferred scale: {mean_scale:.4f} +/- {std_scale:.4f} m/px")
        
        orig = 0.0795
        speed = 75.8 * (mean_scale / orig)
        print(f"  Original scale: {orig:.4f} m/px")
        print(f"  Corrected speed: {speed:.1f} km/h")
    else:
        print("No valid lane calibration data.")

if __name__ == "__main__":
    main()
