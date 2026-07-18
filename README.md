# Road Damage Detector

Road Damage Detector is an object detection project for checking road photos and marking visible surface damage. The app detects four damage types: longitudinal cracks, transverse cracks, alligator cracks, and potholes.

## Project Files

- `Road_detection.ipynb` - training and experiment notebook.
- `converter.py` - dataset conversion script for YOLO format.
- `gradio.py` - end-user Gradio app.
- `gradio_deploy/detector.py` - YOLO inference logic used by the app.
- `gradio_deploy/models/best.pt` - trained road damage detector weights.
- `test images/` - held-out sample images for quick testing.

## Run The App

```powershell
conda activate subway_rl
pip install -r gradio_deploy/requirements.txt
python gradio.py
```

Then open the local URL printed by Gradio, usually `http://127.0.0.1:7861`.

## Notes

The full RDD2022 dataset and training output folders are intentionally not included in this repository because they are large local artifacts. The uploaded app includes the final model needed for inference.
