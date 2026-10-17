"""
Decodes base64 image data (as sent by React Webcam / the browser's
canvas.toDataURL()) into an OpenCV BGR numpy array. Kept separate from
detector/embedder so it can be unit-tested without loading any ML model.
"""

import base64
import re

import cv2
import numpy as np

_DATA_URL_PREFIX_RE = re.compile(r"^data:image/\w+;base64,")


def decode_base64_image(data: str) -> np.ndarray:
    """
    Accepts either a raw base64 string or a full data URL
    (e.g. "data:image/jpeg;base64,/9j/4AAQ..."). Returns a BGR image
    array (OpenCV's native format) or raises ValueError if it can't be
    decoded — callers should turn that into a clean 4xx response.
    """
    if not data or not isinstance(data, str):
        raise ValueError("No image data provided.")

    cleaned = _DATA_URL_PREFIX_RE.sub("", data)

    try:
        raw_bytes = base64.b64decode(cleaned, validate=False)
    except Exception as exc:
        raise ValueError("Image data is not valid base64.") from exc

    if len(raw_bytes) == 0:
        raise ValueError("Decoded image is empty.")

    array = np.frombuffer(raw_bytes, dtype=np.uint8)
    frame = cv2.imdecode(array, cv2.IMREAD_COLOR)

    if frame is None:
        raise ValueError("Could not decode image — unsupported or corrupt format.")

    return frame
