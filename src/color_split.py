import cv2, numpy as np

img = cv2.imread("outputs/frame_8s.jpg")
h, w = img.shape[:2]

# Focus on bottom 25% where features are largest
y_start = int(h * 0.75)
roi = img[y_start:h, :]
roi_h = roi.shape[0]

# Save this crop for inspection
cv2.imwrite("outputs/bottom_crop_8s.jpg", roi)

# LAB color space to separate yellow markings (center line) from white (lane lines)
lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)
l = lab[:,:,0]
a = lab[:,:,1]
b = lab[:,:,2]

# Yellow in LAB: high b, moderate a
yellow_mask = (b > 140) & (a > 120) & (l > 80)
white_mask = (l > 180) & (a > 120) & (b > 120)

yellow_img = np.zeros_like(roi)
yellow_img[yellow_mask] = (0, 255, 255)

white_img = np.zeros_like(roi)
white_img[white_mask] = (255, 255, 255)

cv2.imwrite("outputs/yellow_mask_8s.jpg", yellow_img)
cv2.imwrite("outputs/white_mask_8s.jpg", white_img)

# Try to detect the "60" marking specifically
# It's large yellow text in the right portion of the image
print(f"ROI shape: {roi.shape}")
print(f"Yellow pixels: {np.sum(yellow_mask)}")
print(f"White pixels: {np.sum(white_mask)}")

# Save combined
combined = cv2.hconcat([roi, yellow_img, white_img])
cv2.imwrite("outputs/color_analysis_8s.jpg", combined)
print("Saved color_analysis_8s.jpg")
