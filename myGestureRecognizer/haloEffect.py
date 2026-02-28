import cv2

def draw_halo_effect(frame, box: tuple[int, int, int, int]) -> None:
    """
    Draw a rounded-rectangle halo on top of the detected person box.
    """
    top, left, bottom, right = box

    h, w = frame.shape[:2]
    left = max(0, min(left, w - 1))
    right = max(0, min(right, w - 1))
    top = max(0, min(top, h - 1))
    bottom = max(0, min(bottom, h - 1))

    if right <= left or bottom <= top:
        return

    radius = int(max(1, min(18, (right - left) // 2, (bottom - top) // 2)))
    color = (80, 230, 255)  # BGR

    overlay = frame.copy()

    glow_thickness = 6
    cv2.line(overlay, (left + radius, top), (right - radius, top), color, glow_thickness, cv2.LINE_AA)
    cv2.line(overlay, (left + radius, bottom), (right - radius, bottom), color, glow_thickness, cv2.LINE_AA)
    cv2.line(overlay, (left, top + radius), (left, bottom - radius), color, glow_thickness, cv2.LINE_AA)
    cv2.line(overlay, (right, top + radius), (right, bottom - radius), color, glow_thickness, cv2.LINE_AA)
    cv2.ellipse(overlay, (left + radius, top + radius), (radius, radius), 0, 180, 270, color, glow_thickness, cv2.LINE_AA)
    cv2.ellipse(overlay, (right - radius, top + radius), (radius, radius), 0, 270, 360, color, glow_thickness, cv2.LINE_AA)
    cv2.ellipse(overlay, (right - radius, bottom - radius), (radius, radius), 0, 0, 90, color, glow_thickness, cv2.LINE_AA)
    cv2.ellipse(overlay, (left + radius, bottom - radius), (radius, radius), 0, 90, 180, color, glow_thickness, cv2.LINE_AA)

    cv2.addWeighted(overlay, 0.25, frame, 0.75, 0, frame)
