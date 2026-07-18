from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image
from ultralytics import YOLO


MODEL_PATH = Path(__file__).resolve().parent / "models" / "best.pt"

CLASS_LABELS = {
    "D00_longitudinal_crack": "Longitudinal crack",
    "D10_transverse_crack": "Transverse crack",
    "D20_alligator_crack": "Alligator crack",
    "D40_pothole": "Pothole",
}

DEVICE = 0 if torch.cuda.is_available() else "cpu"
MODEL: YOLO | None = None


@dataclass(frozen=True)
class Detection:
    damage_type: str
    confidence: float
    box: tuple[int, int, int, int]


def get_model() -> YOLO:
    global MODEL
    if MODEL is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model weights were not found at {MODEL_PATH}. "
                "Place best.pt inside gradio_deploy/models/."
            )
        MODEL = YOLO(str(MODEL_PATH))
    return MODEL


def friendly_class_name(raw_name: Any) -> str:
    raw_name = str(raw_name)
    return CLASS_LABELS.get(raw_name, raw_name.replace("_", " "))


def detect_road_damage(
    image: Image.Image,
    confidence: float = 0.25,
    iou: float = 0.45,
    image_size: int = 640,
) -> tuple[Image.Image, list[Detection]]:
    model = get_model()
    rgb_image = image.convert("RGB")
    result = model.predict(
        source=np.asarray(rgb_image),
        conf=confidence,
        iou=iou,
        imgsz=image_size,
        device=DEVICE,
        verbose=False,
    )[0]

    raw_names = result.names
    if isinstance(raw_names, dict):
        display_names = {
            class_id: friendly_class_name(raw_name)
            for class_id, raw_name in raw_names.items()
        }
    else:
        display_names = [friendly_class_name(raw_name) for raw_name in raw_names]
    result.names = display_names

    plotted = result.plot(line_width=2, font_size=12)
    annotated = Image.fromarray(plotted[..., ::-1])

    detections: list[Detection] = []
    if result.boxes is not None:
        for box in result.boxes:
            class_id = int(box.cls.item())
            display_name = (
                display_names[class_id]
                if isinstance(display_names, dict)
                else display_names[class_id]
            )
            coordinates = tuple(int(value) for value in box.xyxy[0].tolist())
            detections.append(
                Detection(
                    damage_type=display_name,
                    confidence=float(box.conf.item()),
                    box=coordinates,
                )
            )

    detections.sort(key=lambda detection: detection.confidence, reverse=True)
    return annotated, detections
