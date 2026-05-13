import cv2, numpy as np, json

# Load frame at 4s where "60" marking is clearest
img = cv2.imread("outputs/frame_4s.jpg")
h, w = img.shape[:2]

# Convert to HSV to easily detect yellow
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Yellow in HSV: low saturation high value, hue around 20-40
# Road yellow paint under overcast: slightly desaturated
lower_yellow = np.array([15, 80, 140])
upper_yellow = np.array([40, 255, 255])
yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

# Morphological cleanup to remove small noise
kernel = np.ones((5, 5), np.uint8)
yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_OPEN, kernel)
yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_CLOSE, kernel)

# Find contours in yellow mask
contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

annotated = img.copy()

# Filter for large yellow objects that could be the "60"
candidates = []
for cnt in contours:
    area = cv2.contourArea(cnt)
    if area < 500 or area > 50000:
        continue
    
    x, y, cw, ch = cv2.boundingRect(cnt)
    aspect = cw / ch if ch > 0 else 0
    
    # "60" digits are roughly square to slightly wide
    # But they are composed of multiple components
    # So we look for clusters of yellow in the lower portion of the image
    if 0.3 < aspect < 3.0 and y > int(h * 0.4):
        candidates.append((x, y, cw, ch, area, aspect, cnt))
        cv2.rectangle(annotated, (x, y), (x+cw, y+ch), (0, 255, 0), 2)
        cv2.putText(annotated, f"{cw}x{ch}, a={aspect:.1f}", (x, y-5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)

print(f"Found {len(candidates)} yellow candidates in lower half")

# Save yellow mask and annotated
yellow_img = np.zeros_like(img)
yellow_img[yellow_mask > 0] = (0, 255, 255)
cv2.imwrite("outputs/yellow_mask_4s.jpg", yellow_img)
cv2.imwrite("outputs/yellow_candidates_4s.jpg", annotated)

# Try alternative: look at known y-range where "60" should be
# From dashcam perspective, "60" is typically painted in the lane ~10-30m ahead
# At truck height (3m), a 3m-tall marking at 20m distance
# subtends angle = arctan(3/20) = 8.5 degrees
# In frame, that's 8.5/tilt_FOV * frame_height = likely 100-200 pixels tall

# The marking should be in the right lane (from truck dashcam, ~center-right of frame)
# Let's analyze yellow pixels by region

# Crop right lane region
x_start = int(w * 0.45)
x_end = int(w * 0.85)
y_start = int(h * 0.5)
y_end = int(h * 0.9)

lane_roi = img[y_start:y_end, x_start:x_end]
lane_hsv = cv2.cvtColor(lane_roi, cv2.COLOR_BGR2HSV)
lane_yellow = cv2.inRange(lane_hsv, lower_yellow, upper_yellow)

# Find components in this ROI
contours2, _ = cv2.findContours(lane_yellow, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
print(f"\nIn right-lane ROI: {len(contours2)} yellow components")

roi_annotated = lane_roi.copy()
components = []
for cnt in contours2:
    area = cv2.contourArea(cnt)
    if area < 100:
        continue
    x, y, cw, ch = cv2.boundingRect(cnt)
    cv2.rectangle(roi_annotated, (x, y), (x+cw, y+ch), (0, 255, 0), 2)
    components.append({"x": x, "y": y, "w": cw, "h": ch, "area": area})
    print(f"  component: x={x}, y={y}, w={cw}, h={ch}, area={area}")

cv2.imwrite("outputs/right_lane_yellow_4s.jpg", roi_annotated)

# Group nearby components into digit clusters
components.sort(key=lambda c: c["x"])
clusters = []
current_cluster = []
for c in components:
    if not current_cluster:
        current_cluster = [c]
    elif abs(c["x"] - current_cluster[-1]["x"]) < 50:  # close in x
        current_cluster.append(c)
    else:
        if len(current_cluster) >= 1:
            clusters.append(current_cluster)
        current_cluster = [c]
if current_cluster:
    clusters.append(current_cluster)

print(f"\n{len(clusters)} clusters")
for i, cluster in enumerate(clusters):
    min_x = min(c["x"] for c in cluster)
    max_x = max(c["x"] + c["w"] for c in cluster)
    min_y = min(c["y"] for c in cluster)
    max_y = max(c["y"] + c["h"] for c in cluster)
    total_area = sum(c["area"] for c in cluster)
    print(f"  Cluster {i}: x=[{min_x}-{max_x}], y=[{min_y}-{max_y}], "
          f"w={max_x-min_x}, h={max_y-min_y}, area={total_area}")
    
    # If it looks like a '6' or '0' or part of '60'
    cluster_h = max_y - min_y
    cluster_w = max_x - min_x
    if 300 < cluster_h < 800:  # reasonable digit height in pixels
        # Save measurement
        pass
