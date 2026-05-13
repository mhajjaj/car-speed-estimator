import cv2, numpy as np

img = cv2.imread("outputs/frame_4s.jpg")
h, w = img.shape[:2]
annotated = img.copy()

# Draw crop region (yellow line)
annotated = cv2.line(annotated, (0, int(h*0.5)), (w, int(h*0.5)), (0, 255, 255), 2)

# Draw scan line (magenta)
scan_y = int(h * 0.72)
annotated = cv2.line(annotated, (0, scan_y), (w, scan_y), (255, 0, 255), 2)

# Analyze brightness along scan strip
strip = img[scan_y-15:scan_y+15, :, :]
gray_strip = cv2.cvtColor(strip, cv2.COLOR_BGR2GRAY)
mean_row = np.mean(gray_strip, axis=0)

print(f"Brightness stats: min={mean_row.min():.1f}, max={mean_row.max():.1f}, mean={mean_row.mean():.1f}")
print(f"Pixels > 200: {np.sum(mean_row > 200)}")
print(f"Pixels > 180: {np.sum(mean_row > 180)}")
print(f"Pixels > 150: {np.sum(mean_row > 150)}")

# Mark bright regions on annotated image
for x in range(0, w, 5):
    brightness = mean_row[x]
    if brightness > 200:
        cv2.circle(annotated, (x, scan_y), 4, (0, 0, 255), -1)    # red
    elif brightness > 180:
        cv2.circle(annotated, (x, scan_y), 3, (0, 165, 255), -1)   # orange
    elif brightness > 150:
        cv2.circle(annotated, (x, scan_y), 2, (0, 255, 255), -1)   # yellow

# ROI stats
roi = img[int(h*0.5):h, :]
roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
print(f"ROI stats: min={roi_gray.min()}, max={roi_gray.max()}, mean={roi_gray.mean():.1f}")

cv2.imwrite("outputs/frame_4s_annotated.jpg", annotated)
print("Saved outputs/frame_4s_annotated.jpg")
