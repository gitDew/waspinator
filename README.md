# Waspinator: Invasive Wasp Detection and Capture

A Python tool for **detecting and catching the invasive _Vespa velutina_**, while recognizing and **not triggering on native _Vespa crabro_**. Powered by the latest YOLO26 object detection model from Ultralytics.

Developed by **Lab42 at ERNI** ([betterask.erni](https://betterask.erni))

<img src="assets/capturing_paper_velutina.gif" alt="Capturing an image of a vespa velutina" width="1200"/>
<img src="assets/velutina_tracking.gif" alt="Tracking a vespa velutina" width="1200"/>
<img src="assets/crabro_tracking.gif" alt="Tracking a vespa crabro" width="1200"/>

---

## Features

- Accurate distinction between *Vespa velutina* and *Vespa crabro*
- Automated or dry-run trap triggering
- Real-time detection from camera, image, video, or CSV files

---

## Getting Started

### Installation

Clone the repository and install in editable mode:
```bash
git clone <your-url-here>
cd <your-project-folder>
pip install -e .
```

### Requirements

- Python 3.8+
- [Ultralytics YOLO](https://docs.ultralytics.com/)
- Other dependencies as per `requirements.txt`

---

## Usage

Run the main detection-and-capture script via command line:

### Start Waspinator Trap

Detect and catch invasive *Vespa velutina* from picamera2 (**default**):

```bash
python -m waspinator start
```

From a video file:
```bash
python -m waspinator start --source path/to/video.mp4
```

Image file:
```bash
python -m waspinator start --source path/to/image.jpg
```

CSV file (for batch inference):
```bash
python -m waspinator start --source path/to/inputs.csv
```

#### Useful Options

- `--dry-run`: Do not trigger trap hardware (simulation mode)
    ```bash
    python -m waspinator start --dry-run
    ```
- `--show`: Display real-time frames/results
    ```bash
    python -m waspinator start --show
    ```
- `--step`: Manual stepping through frames (press SPACE to advance)

For all options:
```bash
python -m waspinator start --help
```

## Hardware & 3D Printing

Prototype 3D models for the waspinator trap are available in the `hardware/` directory as `.stl` files. You can freely download and print these files to build your own trap housing.

- **Location:** [`hardware/`](hardware/)
- **Formats:** `.stl` (compatible with most 3D printers)

