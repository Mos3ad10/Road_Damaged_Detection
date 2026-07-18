# Road Damage Detector Gradio App

Dark Gradio app for the trained YOLO11 road-damage model.

## Run locally

```powershell
cd "D:\CV_INSTANT\Project 2"
python -m pip install -r .\gradio_deploy\requirements.txt
python gradio.py
```

The app expects the trained weights at:

```text
gradio_deploy/models/best.pt
```

## Deploy

For Hugging Face Spaces, create a Gradio Space and upload `gradio.py` with
`requirements.txt`, `models/best.pt`, and the optional `examples` folder.
