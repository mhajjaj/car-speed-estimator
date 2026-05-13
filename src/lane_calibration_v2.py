import cv2, numpy as np, json, os

def analyze_frame_v2(img_path, t):
    img = cv2.imread(img_path)
    h, w = img.shape[:2]
    print(f"\n=== Frame at {t}s ({w}x{h}) ===")
    
    # Use full bottom 60% as ROI
    crop_y = int(h * 0.4)
    roi = img[crop_y:h, :]
    roi_h = roi.shape[0]
    
    # Convert to LAB and use L channel for better contrast separation
    lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)
    l = lab[:, :, 0]
    
    # Use CLAHE to enhance local contrast
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    l_enhanced = clahe.apply(l)
    
    # The road may have bright lane markings. Try Otsu's threshold
    # Blur slightly to reduce noise
    blur = cv2.GaussianBlur(l_enhanced, (7, 7), 0)
    
    # Adaptive threshold: lane markings are bright against darker asphalt
    # Try a low threshold around 150-180
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY, 51, -10)
    
    cv2.imwrite(f"outputs/lane_threshold_{t}s.jpg", thresh)
    
    # Find contours in threshold image
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter contours: lane dashes are elongated rectangles
    dash_candidates = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 100 or area > 20000:
            continue
        
        rect = cv2.minAreaRect(cnt)
        width, height = rect[1]
        if width < 1 or height < 1:
            continue
        
        aspect = max(width, height) / min(width, height)
        if aspect > 0.2 and aspect < 5.0:  # not too elongated
            # Get center
            M = cv2.moments(cnt)
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"]) + crop_y
                dash_candidates.append((cx, cy, area, aspect, rect))
    
    print(f"  Dash candidates: {len(dash_candidates)}")
    
    # Cluster by y-position to find dashes at similar road depth
    # Sort by y (image rows, larger = closer to camera)
    dash_candidates.sort(key=lambda d: d[1], reverse=True)
    
    # Group dashes that are in the same "row" (within 20 px vertically)
    rows = []
    current_row = []
    current_y = None
    for dash in dash_candidates:
        if current_y is None or abs(dash[1] - current_y) < 30:
            current_row.append(dash)
            current_y = dash[1] if current_y is None else (current_y + dash[1]) / 2
        else:
            if len(current_row) >= 2:
                rows.append(current_row)
            current_row = [dash]
            current_y = dash[1]
    if len(current_row) >= 2:
        rows.append(current_row)
    
    print(f"  Rows with >=2 dashes: {len(rows)}")
    
    # For each row, sort by x and find gaps between consecutive dashes
    all_gaps = []
    all_scales = []
    
    for row_idx, row in enumerate(rows):
        row.sort(key=lambda d: d[0])
        if len(row) < 2:
            continue
        
        # Compute gaps between consecutive dashes
        gaps = [row[i+1][0] - row[i][0] for i in range(len(row)-1)]
        gaps = [g for g in gaps if g > 20]  # filter noise
        
        if len(gaps) == 0:
            continue
        
        avg_gap = np.mean(gaps)
        std_gap = np.std(gaps)
        
        # Distinguish lane dashes from road texture based on:
        # - Gap should be somewhat consistent
        # - Gap should be large enough to be a road marking cycle
        if avg_gap < 50:
            continue  # too small, probably texture
        
        all_gaps.extend(gaps)
        
        # Try standard cycles
        for name, cycle_m in [("JP/EU 9m", 9.0), ("US 12m", 12.0)]:
            scale = cycle_m / avg_gap
            all_scales.append(scale)
        
        print(f"  Row {row_idx} (y~{int(current_y)}): {len(row)} dashes, "
              f"avg_gap={avg_gap:.1f}px (std={std_gap:.1f}, n_gaps={len(gaps)})")
    
    if len(all_gaps) == 0:
        print("  No valid dash gaps found.")
        return None
    
    overall_gap = np.mean(all_gaps)
    overall_std = np.std(all_gaps)
    
    scales_jp = [9.0 / g for g in all_gaps]
    scales_us = [12.0 / g for g in all_gaps]
    
    print(f"  Overall average gap: {overall_gap:.1f} px (std={overall_std:.1f})")
    print(f"  Inferred scales:")
    print(f"    JP/EU (9m): {np.mean(scales_jp):.4f} +/- {np.std(scales_jp):.4f} m/px")
    print(f"    US (12m):   {np.mean(scales_us):.4f} +/- {np.std(scales_us):.4f} m/px")
    
    # Return with default to JP/EU standard
    return {
        "frame_time": t,
        "avg_gap_px": float(overall_gap),
        "std_gap_px": float(overall_std),
        "num_gaps": len(all_gaps),
        "scales": {
            "JP_EU_9m": float(np.mean(scales_jp)),
            "US_12m": float(np.mean(scales_us))
        }
    }

def main():
    results = []
    for t in [4, 8, 12]:
        path = f"outputs/frame_{t}s.jpg"
        r = analyze_frame_v2(path, t)
        if r:
            results.append(r)
    
    with open("outputs/lane_calibration.json", "w") as f:
        json.dump(results, f, indent=2)
    
    if results:
        print("\n=== SUMMARY ===")
        jp_scales = [r["scales"]["JP_EU_9m"] for r in results]
        us_scales = [r["scales"]["US_12m"] for r in results]
        
        print(f"JP/EU (9m) scale: {np.mean(jp_scales):.4f} +/- {np.std(jp_scales):.4f} m/px")
        print(f"US (12m)   scale: {np.mean(us_scales):.4f} +/- {np.std(us_scales):.4f} m/px")
        
        orig = 0.0795
        print(f"Original assumed scale: {orig:.4f} m/px")
        
        for name, scales in [("JP/EU", jp_scales), ("US", us_scales)]:
            mean_s = np.mean(scales)
            speed = 75.8 * (mean_s / orig)
            print(f"  Corrected speed ({name}): {speed:.1f} km/h")
    else:
        print("No valid calibration data.")

if __name__ == "__main__":
    main()
