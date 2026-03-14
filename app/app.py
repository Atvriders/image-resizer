import io
import os
from flask import Flask, request, jsonify, render_template, Response
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename
import base64

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff', 'tif'}

RESAMPLE_MAP = {
    'LANCZOS': Image.Resampling.LANCZOS,
    'BICUBIC': Image.Resampling.BICUBIC,
    'BILINEAR': Image.Resampling.BILINEAR,
    'NEAREST': Image.Resampling.NEAREST,
}

FORMAT_MIME = {
    'JPEG': 'image/jpeg',
    'PNG': 'image/png',
    'GIF': 'image/gif',
    'WEBP': 'image/webp',
    'BMP': 'image/bmp',
    'TIFF': 'image/tiff',
}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def human_size(size_bytes):
    if size_bytes < 1024:
        return f'{size_bytes} B'
    elif size_bytes < 1024 * 1024:
        return f'{size_bytes / 1024:.1f} KB'
    else:
        return f'{size_bytes / (1024 * 1024):.2f} MB'


def compute_target_size(orig_w, orig_h, mode, width, height, percent, maintain_aspect):
    if mode == 'percent':
        scale = float(percent) / 100.0
        return max(1, round(orig_w * scale)), max(1, round(orig_h * scale))

    ratio = orig_w / orig_h

    if not maintain_aspect:
        w = int(width) if width else orig_w
        h = int(height) if height else orig_h
        return max(1, w), max(1, h)

    # Maintain aspect ratio
    w = int(width) if width else None
    h = int(height) if height else None

    if w and not h:
        return max(1, w), max(1, round(w / ratio))
    elif h and not w:
        return max(1, round(h * ratio)), max(1, h)
    elif w and h:
        # Fit within box
        if w / h > ratio:
            w = max(1, round(h * ratio))
        else:
            h = max(1, round(w / ratio))
        return w, h
    else:
        return orig_w, orig_h


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/health')
def health():
    return jsonify({'status': 'ok'})


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    try:
        data = file.read()
        img = Image.open(io.BytesIO(data))
        img.verify()  # Verify it's a valid image
        img = Image.open(io.BytesIO(data))  # Re-open after verify

        orig_format = img.format or 'PNG'
        width, height = img.size

        # Encode to base64 data URI for preview
        buf = io.BytesIO()
        save_format = orig_format if orig_format in ('JPEG', 'PNG', 'GIF', 'WEBP') else 'PNG'
        if save_format == 'JPEG' and img.mode in ('RGBA', 'P', 'LA'):
            save_format = 'PNG'
            img = img.convert('RGBA')

        img.save(buf, format=save_format)
        buf.seek(0)
        mime = FORMAT_MIME.get(save_format, 'image/png')
        data_uri = f'data:{mime};base64,{base64.b64encode(buf.getvalue()).decode()}'

        return jsonify({
            'width': width,
            'height': height,
            'size_bytes': len(data),
            'size_human': human_size(len(data)),
            'format': orig_format,
            'mode': img.mode,
            'filename': secure_filename(file.filename),
            'data_uri': data_uri,
        })

    except UnidentifiedImageError:
        return jsonify({'error': 'Cannot identify image file'}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to process image: {str(e)}'}), 500


@app.route('/resize', methods=['POST'])
def resize():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        data = file.read()
        img = Image.open(io.BytesIO(data))
        orig_format = img.format or 'PNG'
        orig_w, orig_h = img.size

        mode = request.form.get('mode', 'pixels')
        width = request.form.get('width', '').strip() or None
        height = request.form.get('height', '').strip() or None
        percent = request.form.get('percent', '100').strip()
        maintain_aspect = request.form.get('maintain_aspect', 'true').lower() == 'true'
        resample_key = request.form.get('resample', 'LANCZOS').upper()
        resample = RESAMPLE_MAP.get(resample_key, Image.Resampling.LANCZOS)

        new_w, new_h = compute_target_size(orig_w, orig_h, mode, width, height, percent, maintain_aspect)

        # Handle palette/transparency modes
        if orig_format == 'GIF':
            img = img.convert('RGBA')
        elif img.mode == 'P':
            img = img.convert('RGBA')

        resized = img.resize((new_w, new_h), resample)

        # Determine output format
        out_format = orig_format
        if out_format not in ('JPEG', 'PNG', 'GIF', 'WEBP', 'BMP', 'TIFF'):
            out_format = 'PNG'
        if out_format == 'JPEG' and resized.mode in ('RGBA', 'LA', 'P'):
            resized = resized.convert('RGB')
            out_format = 'PNG'  # Keep as PNG to preserve transparency

        buf = io.BytesIO()
        save_kwargs = {}
        if out_format == 'JPEG':
            save_kwargs['quality'] = 95
            save_kwargs['optimize'] = True
            # Preserve EXIF if present
            exif = img.info.get('exif')
            if exif:
                save_kwargs['exif'] = exif
        elif out_format == 'PNG':
            save_kwargs['optimize'] = True

        resized.save(buf, format=out_format, **save_kwargs)
        result_bytes = buf.getvalue()

        orig_filename = secure_filename(file.filename)
        base, ext = os.path.splitext(orig_filename)
        # Adjust extension if format changed
        ext_map = {'JPEG': '.jpg', 'PNG': '.png', 'GIF': '.gif', 'WEBP': '.webp', 'BMP': '.bmp', 'TIFF': '.tiff'}
        ext = ext_map.get(out_format, ext)
        out_filename = f'resized_{base}{ext}'

        mime = FORMAT_MIME.get(out_format, 'application/octet-stream')
        response = Response(result_bytes, mimetype=mime)
        response.headers['Content-Disposition'] = f'attachment; filename="{out_filename}"'
        response.headers['X-Resized-Width'] = str(new_w)
        response.headers['X-Resized-Height'] = str(new_h)
        response.headers['X-Resized-Size'] = str(len(result_bytes))
        response.headers['X-Resized-Size-Human'] = human_size(len(result_bytes))
        response.headers['Access-Control-Expose-Headers'] = (
            'X-Resized-Width, X-Resized-Height, X-Resized-Size, X-Resized-Size-Human, Content-Disposition'
        )
        return response

    except UnidentifiedImageError:
        return jsonify({'error': 'Cannot identify image file'}), 400
    except Exception as e:
        return jsonify({'error': f'Resize failed: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
