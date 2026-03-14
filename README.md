# Image Resizer

A self-hosted web app for resizing images — similar to ezgif.com/resize. Runs entirely in Docker with no external dependencies.

![Python](https://img.shields.io/badge/Python-3.12-blue) ![Flask](https://img.shields.io/badge/Flask-3.1-green) ![Docker](https://img.shields.io/badge/Docker-ready-blue)

## Features

- Upload images via click or drag & drop
- Resize by **pixel dimensions** or **percentage** (1%–500%)
- **Aspect ratio lock** — changing width auto-calculates height and vice versa
- 4 resampling methods: Lanczos, Bicubic, Bilinear, Nearest Neighbor
- Side-by-side preview of original and resized image
- Shows file size and dimensions before and after
- One-click download of the resized image
- Supports PNG, JPG, GIF, WEBP, BMP, TIFF (up to 50 MB)
- Stateless — nothing written to disk

## Quick Start (Docker)

**1. Create a `docker-compose.yml`:**

```yaml
services:
  image-resizer:
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

Or replace `localhost` with your server's IP address.

## Usage

1. **Upload** — click the upload area or drag an image onto it
2. **Choose resize mode** — switch between Pixels and Percentage
3. **Set dimensions** — enter width/height (use the link icon to lock aspect ratio) or drag the percentage slider
4. **Pick a resampling method** — Lanczos gives the best quality
5. **Click Resize Image**
6. **Download** — click the download button to save the result

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
| Frontend | Bootstrap 5 + vanilla JS |
| Container | Docker |
