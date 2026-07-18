# Road Damage Detector

Road Damage Detector is an object detection project for inspecting road-surface photos and marking visible damage areas. It is built for a practical end-user workflow: upload a road image, run detection, and review the annotated result with the detected damage types.

The project detects four road damage categories:

- Longitudinal crack
- Transverse crack
- Alligator crack
- Pothole

## Project Goal

The goal is to support faster road inspection by automatically locating damaged areas in an image and identifying the damage type. This is an object detection task, not only an image classification task, because the model predicts both:

- the class of each damage instance
- the bounding box location of each damage instance

## Dataset And Training

The training workflow uses the RDD2022 road damage dataset. The original dataset annotations are converted from Pascal VOC XML format into YOLO format using `converter.py`.

The notebook `Road_detection.ipynb` covers the main experiment pipeline:

- Convert the dataset to YOLO format.
- Split the data into training, validation, and test sets.
- Train YOLO road-damage models.
- Evaluate the trained models on the test split.
- Select the best model for deployment.

The full dataset is not included in this repository because it is a large local artifact.

## Model Comparison

The project compares YOLO11 and YOLOv8 using detection metrics on the road-damage test split.

| Model | Precision | Recall | mAP50 | mAP50-95 | Mean IoU | FPS | Size |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| YOLO11 | 0.6668 | 0.5506 | 0.6153 | 0.3183 | 0.6434 | 99.92 | 54.34 MB |
| YOLOv8 | 0.6358 | 0.5505 | 0.5939 | 0.3075 | 0.6391 | 119.62 | 21.49 MB |

YOLO11 was selected for the deployed app because it achieved the best detection quality in the comparison, with the highest precision, mAP50, mAP50-95, and mean IoU. YOLOv8 is smaller and faster, but YOLO11 produced stronger detection performance for this project goal.

The raw comparison files are included in `comparison/`:

- `comparison/yolo_model_comparison.csv`
- `comparison/yolo_model_comparison.json`
- `comparison/yolo_model_comparison.md`

## Gradio App

The deployed interface is an end-user Gradio app. It keeps the training and hardware details out of the page and focuses on the inspection workflow:

- Upload a road photo.
- Run damage detection.
- View the annotated image.
- Read the detected damage report.

## Project Files

- `Road_detection.ipynb` - training and experiment notebook.
- `converter.py` - dataset conversion script for YOLO format.
- `gradio.py` - end-user Gradio app.
- `gradio_deploy/detector.py` - YOLO inference logic used by the app.
- `gradio_deploy/models/best.pt` - selected YOLO11 model weights used by the app.
- `comparison/` - saved model comparison results.
- `test images/` - held-out sample images for quick testing.

