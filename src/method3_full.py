import cv2, numpy as np, json

def analyze_calibration_features():
    results = {
        "method": "Road Feature Calibration",
        "description": "Using known dimensions of standardized road markings to infer meters-per-pixel scale",
        "assumptions": "Japan road marking standards (JIS/Japan Road Association)",
        "features_analyzed": []
    }
    
    img = cv2.imread("outputs/frame_4s.jpg")
    h, w = img.shape[:2]
    
    # ============== Feature 1: "60" Speed Limit Marking ==============
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_yellow = np.array([15, 80, 140])
    upper_yellow = np.array([40, 255, 255])
    yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    
    kernel = np.ones((5, 5), np.uint8)
    yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_OPEN, kernel)
    yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_CLOSE, kernel)
    
    # Right lane ROI where "60" is located
    x1, x2 = int(w*0.45), int(w*0.85)
    y1, y2 = int(h*0.55), int(h*0.85)
    roi_mask = yellow_mask[y1:y2, x1:x2]
    
    contours, _ = cv2.findContours(roi_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    digit_components = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 200 or area > 15000:
            continue
        cx, cy, cw, ch = cv2.boundingRect(cnt)
        digit_components.append((cx, cy, cw, ch, area))
    
    # Group into digit clusters
    digit_components.sort(key=lambda c: c[0])
    clusters = []
    current = []
    for c in digit_components:
        if not current:
            current = [c]
        elif abs(c[0] - current[-1][0] - current[-1][2]) < 80:
            current.append(c)
        else:
            clusters.append(current)
            current = [c]
    if current:
        clusters.append(current)
    
    # Find cluster matching "60" (should span ~200+ px, height ~100+ px)
    best_cluster = None
    for cluster in clusters:
        min_x = min(c[0] for c in cluster)
        max_x = max(c[0] + c[2] for c in cluster)
        min_y = min(c[1] for c in cluster)
        max_y = max(c[1] + c[3] for c in cluster)
        cluster_w = max_x - min_x
        cluster_h = max_y - min_y
        if cluster_w > 150 and cluster_h > 80:
            if best_cluster is None or cluster_w > best_cluster[4]:
                best_cluster = (min_x+x1, min_y+y1, max_x+x1, max_y+y1, cluster_w, cluster_h)
    
    if best_cluster:
        bx1, by1, bx2, by2, c_w, c_h = best_cluster
        print(f"\n'60' marking detected: {c_w}px x {c_h}px")
        
        # Japan standard: road surface numeral height = 2.5m (standard road) or 3.0m (expressway)
        # Width of "60" combined: approximately 3.0-4.0m
        for std_name, digit_h_m, total_w_m in [
            ("Standard road (2.5m height, ~3.5m width)", 2.5, 3.5),
            ("Expressway (3.0m height, ~4.0m width)", 3.0, 4.0)
        ]:
            scale_from_height = digit_h_m / c_h
            scale_from_width = total_w_m / c_w
            print(f"  {std_name}: scale_h={scale_from_height:.5f}, scale_w={scale_from_width:.5f}")
            results["features_analyzed"].append({
                "feature": f"60_marking_{std_name.split('(')[0].strip()}",
                "pixel_height": int(c_h),
                "pixel_width": int(c_w),
                "real_height_m": digit_h_m,
                "real_width_m": total_w_m,
                "scale_from_height": float(scale_from_height),
                "scale_from_width": float(scale_from_width)
            })
    
    # ============== Feature 2: Lane Width ==============
    # Measure lane width from lane boundary lines
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    
    # Focus on bottom 30% where lanes are widest in image
    y_start = int(h * 0.7)
    bottom_edges = edges[y_start:h, :]
    
    # Hough for horizontal-ish lines (lane boundaries appear as converging lines)
    lines = cv2.HoughLinesP(bottom_edges, 1, np.pi/180, threshold=100,
                            minLineLength=100, maxLineGap=20)
    
    lane_boundaries = []
    if lines is not None:
        for line in lines:
            lx1, ly1, lx2, ly2 = line[0]
            ly1 += y_start
            ly2 += y_start
            dx = abs(lx2 - lx1)
            dy = abs(ly2 - ly1)
            if dx > 30 and dy < 50:  # nearly horizontal
                mid_x = (lx1 + lx2) / 2
                lane_boundaries.append(mid_x)
    
    lane_boundaries.sort()
    if len(lane_boundaries) >= 2:
        # Take outermost plausible boundaries
        lane_width_px = lane_boundaries[-1] - lane_boundaries[0]
        # But this may capture both lanes + shoulder
        # Standard Japan lane width: 3.0-3.5m (single lane)
        # If we measured 2 lanes: ~7m
        for lane_name, real_width in [
            ("Single lane (3.0m)", 3.0),
            ("Single lane (3.25m)", 3.25),
            ("Single lane (3.5m)", 3.5),
            ("Two lanes (7.0m)", 7.0)
        ]:
            scale = real_width / lane_width_px
            results["features_analyzed"].append({
                "feature": f"lane_width_{lane_name}",
                "pixel_width": float(lane_width_px),
                "real_width_m": real_width,
                "scale": float(scale)
            })
        print(f"\nLane span measured: {lane_width_px:.0f} px")
    
    # ============== Method 3 Scale Summary ==============
    all_scales = []
    for f in results["features_analyzed"]:
        if "scale" in f:
            all_scales.append(f["scale"])
        if "scale_from_height" in f:
            all_scales.append(f["scale_from_height"])
        if "scale_from_width" in f:
            all_scales.append(f["scale_from_width"])
    
    if all_scales:
        results["scale_summary"] = {
            "all_scales": [float(s) for s in all_scales],
            "mean_scale": float(np.mean(all_scales)),
            "median_scale": float(np.median(all_scales)),
            "min_scale": float(min(all_scales)),
            "max_scale": float(max(all_scales)),
            "std_scale": float(np.std(all_scales))
        }
        
        orig = 0.0795
        for stat, val in [("mean", results["scale_summary"]["mean_scale"]),
                          ("median", results["scale_summary"]["median_scale"]),
                          ("min", results["scale_summary"]["min_scale"]),
                          ("max", results["scale_summary"]["max_scale"])]:
            speed = 75.8 * (val / orig)
            results["scale_summary"][f"speed_from_{stat}"] = float(speed)
            print(f"\nScale {stat}: {val:.5f} m/px -> speed: {speed:.1f} km/h")
    
    with open("outputs/method3_calibration.json", "w") as f:
        json.dump(results, f, indent=2)
    
    return results

analyze_calibration_features()
