from enum import Enum


class EnumGesture(str, Enum):
	POINTING_UP_LEFT = "pointing_up_left"
	POINTING_UP_RIGHT = "pointing_up_right"
	CLOSED_FIST_LEFT = "closed_fist_left"
	CLOSED_FIST_RIGHT = "closed_fist_right"
	VICTORY_LEFT = "victory_left"
	VICTORY_RIGHT = "victory_right"
	ILOVEYOU_LEFT = "i_love_you_left"
	ILOVEYOU_RIGHT = "i_love_you_right"
	THUMB_UP_LEFT = "thumb_up_left"
	THUMB_UP_RIGHT = "thumb_up_right"
	THUMB_DOWN_LEFT = "thumb_down_left"
	THUMB_DOWN_RIGHT = "thumb_down_right"
	OPEN_PALM = "open_palm"
	INVALID = "invalid"

	@staticmethod
	def from_gesture(gesture_category: str, handedness: str) -> "EnumGesture":
		hand = (handedness or "").strip().title()

		if gesture_category == "Open_Palm":
			return EnumGesture.OPEN_PALM

		if hand not in {"Left", "Right"}:
			return EnumGesture.INVALID

		pair_map = {
			"Pointing_Up": (EnumGesture.POINTING_UP_LEFT, EnumGesture.POINTING_UP_RIGHT),
			"Closed_Fist": (EnumGesture.CLOSED_FIST_LEFT, EnumGesture.CLOSED_FIST_RIGHT),
			"Victory": (EnumGesture.VICTORY_LEFT, EnumGesture.VICTORY_RIGHT),
			"ILoveYou": (EnumGesture.ILOVEYOU_LEFT, EnumGesture.ILOVEYOU_RIGHT),
			"Thumb_Up": (EnumGesture.THUMB_UP_LEFT, EnumGesture.THUMB_UP_RIGHT),
			"Thumb_Down": (EnumGesture.THUMB_DOWN_LEFT, EnumGesture.THUMB_DOWN_RIGHT),
		}

		pair = pair_map.get(gesture_category)
		if pair is None:
			return EnumGesture.INVALID

		return pair[0] if hand == "Left" else pair[1]


SUPPORTED_GESTURES = [
	EnumGesture.POINTING_UP_LEFT.value,
	EnumGesture.POINTING_UP_RIGHT.value,
	EnumGesture.CLOSED_FIST_LEFT.value,
	EnumGesture.CLOSED_FIST_RIGHT.value,
	EnumGesture.VICTORY_LEFT.value,
	EnumGesture.VICTORY_RIGHT.value,
	EnumGesture.ILOVEYOU_LEFT.value,
	EnumGesture.ILOVEYOU_RIGHT.value,
	EnumGesture.THUMB_UP_LEFT.value,
	EnumGesture.THUMB_UP_RIGHT.value,
	EnumGesture.THUMB_DOWN_LEFT.value,
	EnumGesture.THUMB_DOWN_RIGHT.value,
]


_DISPLAY_LABELS = {
	EnumGesture.POINTING_UP_LEFT.value: "Pointing Up Left",
	EnumGesture.POINTING_UP_RIGHT.value: "Pointing Up Right",
	EnumGesture.CLOSED_FIST_LEFT.value: "Closed Fist Left",
	EnumGesture.CLOSED_FIST_RIGHT.value: "Closed Fist Right",
	EnumGesture.VICTORY_LEFT.value: "Victory Left",
	EnumGesture.VICTORY_RIGHT.value: "Victory Right",
	EnumGesture.ILOVEYOU_LEFT.value: "I Love You Left",
	EnumGesture.ILOVEYOU_RIGHT.value: "I Love You Right",
	EnumGesture.THUMB_UP_LEFT.value: "Thumb Up Left",
	EnumGesture.THUMB_UP_RIGHT.value: "Thumb Up Right",
	EnumGesture.THUMB_DOWN_LEFT.value: "Thumb Down Left",
	EnumGesture.THUMB_DOWN_RIGHT.value: "Thumb Down Right",
	EnumGesture.OPEN_PALM.value: "Open Palm",
}


def to_display_text(gesture_id: str) -> str:
	"""Convert canonical gesture id to user-facing text."""
	key = (gesture_id or "").strip()
	return _DISPLAY_LABELS.get(key, key.replace("_", " ").title())


def normalize_gesture_id(value: str) -> str:
	"""Normalize gesture id from combo/userData into canonical id where possible."""
	raw = (value or "").strip()
	if not raw:
		return ""

	if raw in SUPPORTED_GESTURES or raw == EnumGesture.OPEN_PALM.value:
		return raw

	lowered = raw.lower()
	if lowered == "open_palm" or lowered == "open palm":
		return EnumGesture.OPEN_PALM.value
	return ""
