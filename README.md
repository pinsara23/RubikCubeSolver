# Rubik Cube Solver Backend

Flask backend for detecting Rubik's Cube colors and generating solve moves.

This project includes two variants:

- `Color_Extraction.py`: detects cube colors from a static image file.
- `Color_Extraction_With_Video.py`: detects cube colors from a live webcam stream.

## Features

- Color classification using OpenCV + HSV thresholds.
- Block detection and spatial sorting (top-to-bottom, left-to-right).
- REST API to return scanned cube stickers.
- Solve endpoint using a two-phase Rubik's Cube solver.
- Live MJPEG webcam stream (video version).

## Project Structure

- `Color_Extraction.py`
- `Color_Extraction_With_Video.py`
- `tables.json`
- Sample image files (`rub.jpeg`, `rubbt3.jpeg`, etc.)

## Requirements

- Python 3.9+
- Webcam (only for `Color_Extraction_With_Video.py`)

Install dependencies:

```bash
pip install flask flask-cors opencv-python numpy twophase
```

## Run

### Option 1: Static Image Backend

```bash
python Color_Extraction.py
```

Runs Flask server at:

- `http://127.0.0.1:5000`

This script currently reads image file:

- `rubbt3.jpeg`

You can change that filename inside `Color_Extraction.py` if needed.

### Option 2: Live Webcam Backend

```bash
python Color_Extraction_With_Video.py
```

Runs Flask server at:

- `http://127.0.0.1:5000`

Video stream endpoint:

- `GET /video_feed`

## API Endpoints

### `GET /api/cube-colors`

Returns detected cube blocks with:

- `id`
- `color`
- `center_coordinates` (`x`, `y`)

Notes:

- In webcam mode, endpoint expects a clear frame and returns an error if fewer than 9 blocks are detected.
- In static-image mode, it returns all detected blocks.

### `POST /api/solve`

Request body:

```json
{
  "cube_string": "<54-character cube string>"
}
```

Response:

```json
{
  "moves": ["U", "R2", "F", "B'"]
}
```

## Typical Workflow

1. Scan each face and map colors to cube notation expected by your frontend.
2. Build a valid 54-character cube string.
3. Send it to `POST /api/solve`.
4. Execute returned moves.

## Notes

- HSV thresholds are hardcoded in `classify_color`; tune them for your camera and lighting.
- Keep cube centered and well lit for best detection quality.
- `tables.json` is present in the repository for solver-related data usage.
