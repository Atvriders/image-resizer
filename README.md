# Editor

A self-hosted video-to-GIF and image editing web app. Drop in a video and convert it to a GIF, then resize, crop, rotate, apply effects, optimize, and convert — all in the browser, all on your own server.

![Python](https://img.shields.io/badge/Python-3.12-blue) ![Flask](https://img.shields.io/badge/Flask-3.1-green) ![Docker](https://img.shields.io/badge/Docker-ready-blue)

## Features

### Video → GIF
- Supports MP4, MOV, AVI, MKV, WEBM, FLV, WMV, M4V and more
- Keeps original resolution by default — or pick from presets (4K, 1440p, 1080p, 720p, 480p, 360p, 240p) or set a custom width
- Control start time, duration (up to 60s), frame rate, and loop count
- High-quality output using ffmpeg's two-pass palette (palettegen + paletteuse)
- Auto-detects video dimensions and length on upload

### Image Editing (unlocked after a GIF is created or an image is uploaded)
- **Resize** — pixel dimensions or percentage (1%–500%), aspect ratio lock, 5 resampling methods
- **Crop** — interactive canvas with drag-to-select, corner/edge handles, rule-of-thirds grid, 7 aspect ratio presets
- **Rotate & Flip** — 90°/180° quick presets, flip H/V, custom angle
- **Effects** — live preview: brightness, contrast, saturation, sharpness + grayscale, sepia, invert, blur, sharpen, emboss, edge detect, smooth
- **Optimize** — quality slider, optional max dimensions, format selection
- **Convert** — JPEG, PNG, WEBP, GIF, BMP, TIFF
- Operations chain — each result becomes the input for the next tool
- Animated GIF support — all operations preserve animation across every frame
- No file size limit

## Quick Start (Docker)

**1. Create a `docker-compose.yml`:**

```yaml
services:
  editor:
    image: ghcr.io/atvriders/image-resizer:latest
    ports:
      - "5000:5000"
    restart: unless-stopped
```

**2. Run it:**

```bash
docker compose up -d
```

**3. Open your browser:**

```
http://localhost:5000
```

## Running from Source (Docker)

```bash
git clone https://github.com/Atvriders/image-resizer.git
cd image-resizer
docker compose up -d --build
```

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 + Flask 3.1 |
| Video processing | ffmpeg |
| Image processing | Pillow 11 |
| Server | Gunicorn |
| Frontend | Vanilla JS + Bootstrap Icons |
| Container | Docker |

## Running without Docker

**Requirements:** Python 3.12+, ffmpeg

**1. Install ffmpeg:**

```bash
# Ubuntu / Debian
sudo apt install ffmpeg

# macOS (Homebrew)
brew install ffmpeg

# Windows — download from https://ffmpeg.org/download.html and add to PATH
```

**2. Clone the repo and install Python dependencies:**

```bash
git clone https://github.com/Atvriders/image-resizer.git
cd image-resizer
pip install -r app/requirements.txt
```

**3. Run the app:**

```bash
# Development server
python app/app.py

# Production (recommended)
gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 600 --chdir app app:app
```

**4. Open your browser:**

```
http://localhost:5000
```
