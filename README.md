# Image Studio

A self-hosted image editing web app — crop, resize, rotate, apply effects, optimize, and convert images. Runs entirely in Docker with no external dependencies and no file size limit.

![Python](https://img.shields.io/badge/Python-3.12-blue) ![Flask](https://img.shields.io/badge/Flask-3.1-green) ![Docker](https://img.shields.io/badge/Docker-ready-blue)

## Features

- **Resize** — by pixel dimensions or percentage (1%–500%), aspect ratio lock, 5 resampling methods
- **Crop** — interactive canvas with drag-to-select, corner/edge handles, rule-of-thirds grid, 7 aspect ratio presets
- **Rotate & Flip** — 90°/180° presets, flip horizontal/vertical, custom angle with canvas expand option
- **Effects** — live preview while adjusting: brightness, contrast, saturation, sharpness + filters (grayscale, sepia, invert, blur, sharpen, emboss, edge detect, smooth)
- **Optimize** — compress with quality control, optional max dimensions, format selection
- **Convert** — convert between JPEG, PNG, WEBP, GIF, BMP, TIFF
- **Chainable** — each operation's output becomes the input for the next
- Upload via click or drag & drop — **no file size limit**
- Stateless — nothing written to disk, images never leave your server

## Quick Start (Docker)

**1. Create a `docker-compose.yml`:**

```yaml
services:
  image-studio:
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

## Running from Source

```bash
git clone https://github.com/Atvriders/image-resizer.git
cd image-resizer
docker compose up -d --build
```

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 + Flask 3.1 |
| Image processing | Pillow 11 |
| Server | Gunicorn |
| Frontend | Vanilla JS + Bootstrap Icons |
| Container | Docker |
