import io
import os
from flask import Flask, request, jsonify, render_template, Response
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, UnidentifiedImageError
from werkzeug.utils import secure_filename
import base64

app = Flask(__name__)
# No file size limit
app.config['MAX_CONTENT_LENGTH'] = None

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff', 'tif'}

RESAMPLE_MAP = {
    'LANCZOS': Image.Resampling.LANCZOS,
    'BICUBIC': Image.Resampling.BICUBIC,
    'BILINEAR': Image.Resampling.BILINEAR,
    'NEAREST': Image.Resampling.NEAREST,
    'BOX': Image.Resampling.BOX,
    'HAMMING': Image.Resampling.HAMMING,
}

FORMAT_MIME = {
    'JPEG': 'image/jpeg', 'PNG': 'image/png', 'GIF': 'image/gif',
    'WEBP': 'image/webp', 'BMP': 'image/bmp', 'TIFF': 'image/tiff',
}
EXT_MAP = {
    'JPEG': 'jpg', 'PNG': 'png', 'GIF': 'gif',
    'WEBP': 'webp', 'BMP': 'bmp', 'TIFF': 'tiff',
}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def human_size(n):
    if n < 1024: return f'{n} B'
    if n < 1024 * 1024: return f'{n/1024:.1f} KB'
    return f'{n/(1024*1024):.2f} MB'


def norm_fmt(fmt):
    fmt = (fmt or 'PNG').upper().strip()
    if fmt == 'JPG': fmt = 'JPEG'
    if fmt == 'TIF': fmt = 'TIFF'
    return fmt if fmt in FORMAT_MIME else 'PNG'


def prepare(img):
    """Normalize image mode for processing."""
    if img.mode == 'P':
        img = img.convert('RGBA')
    elif img.mode == 'CMYK':
        img = img.convert('RGB')
    elif img.mode not in ('RGB', 'RGBA', 'L', 'LA'):
        img = img.convert('RGBA')
    return img


def finalize(img, fmt):
    """Convert image mode to be compatible with output format."""
    if fmt == 'JPEG':
        if img.mode in ('RGBA', 'LA'):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1])
            return bg
        if img.mode == 'P':
            return img.convert('RGB')
        if img.mode not in ('RGB', 'L'):
            return img.convert('RGB')
    elif fmt == 'BMP':
        if img.mode not in ('RGB', 'RGBA', 'L', '1'):
            return img.convert('RGB')
    elif fmt == 'GIF':
        return img.convert('RGB').quantize(256)
    return img


def sepia(img):
    gray = ImageOps.grayscale(img.convert('RGB'))
    r = gray.point([min(255, int(i * 1.08)) for i in range(256)])
    g = gray.point([min(255, int(i * 0.88)) for i in range(256)])
    b = gray.point([min(255, int(i * 0.72)) for i in range(256)])
    return Image.merge('RGB', (r, g, b))


def make_response(img, fmt, quality, base_name, op):
    img = finalize(img, fmt)
    buf = io.BytesIO()
    kw = {}
    if fmt == 'JPEG':
        kw = {'quality': quality, 'optimize': True}
    elif fmt == 'PNG':
        kw = {'optimize': True}
    elif fmt == 'WEBP':
        kw = {'quality': quality, 'method': 4}
    img.save(buf, format=fmt, **kw)
    data = buf.getvalue()
    ext = EXT_MAP.get(fmt, 'png')
    mime = FORMAT_MIME.get(fmt, 'image/png')
    fname = f'{op}_{base_name}.{ext}'
    resp = Response(data, mimetype=mime)
    resp.headers['Content-Disposition'] = f'attachment; filename="{fname}"'
    resp.headers['X-Image-Width'] = str(img.width)
    resp.headers['X-Image-Height'] = str(img.height)
    resp.headers['X-Image-Size'] = str(len(data))
    resp.headers['X-Image-Size-Human'] = human_size(len(data))
    resp.headers['X-Image-Format'] = fmt
    resp.headers['Access-Control-Expose-Headers'] = (
        'X-Image-Width,X-Image-Height,X-Image-Size,X-Image-Size-Human,X-Image-Format,Content-Disposition'
    )
    return resp


def load_file(file):
    """Open uploaded file, return (img, orig_format, base_name)."""
    data = file.read()
    img = Image.open(io.BytesIO(data))
    img.load()
    fmt = norm_fmt(img.format)
    base = os.path.splitext(secure_filename(file.filename or 'image'))[0] or 'image'
    return prepare(img), fmt, base


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
    if not file or not file.filename:
        return jsonify({'error': 'No file selected'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': 'Unsupported file type. Use PNG, JPG, GIF, WEBP, BMP, or TIFF.'}), 400
    try:
        data = file.read()
        img = Image.open(io.BytesIO(data))
        img.verify()
        img = Image.open(io.BytesIO(data))
        img.load()
        w, h = img.size
        fmt = img.format or 'PNG'

        # Thumbnail for preview (max 900px)
        prev = img.copy()
        if prev.mode == 'P': prev = prev.convert('RGBA')
        elif prev.mode not in ('RGB', 'RGBA', 'L'): prev = prev.convert('RGB')
        if prev.width > 900 or prev.height > 900:
            prev.thumbnail((900, 900), Image.Resampling.LANCZOS)

        buf = io.BytesIO()
        if prev.mode == 'RGBA':
            prev.save(buf, format='PNG', optimize=True)
            mime = 'image/png'
        else:
            if prev.mode != 'RGB': prev = prev.convert('RGB')
            prev.save(buf, format='JPEG', quality=85)
            mime = 'image/jpeg'

        uri = f'data:{mime};base64,{base64.b64encode(buf.getvalue()).decode()}'
        return jsonify({
            'width': w, 'height': h, 'format': fmt, 'mode': img.mode,
            'size_bytes': len(data), 'size_human': human_size(len(data)),
            'filename': secure_filename(file.filename),
            'data_uri': uri,
        })
    except UnidentifiedImageError:
        return jsonify({'error': 'Cannot identify image file'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/resize', methods=['POST'])
def resize():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    try:
        img, orig_fmt, base = load_file(request.files['file'])
        ow, oh = img.size
        mode = request.form.get('mode', 'pixels')
        resample = RESAMPLE_MAP.get(request.form.get('resample', 'LANCZOS').upper(), Image.Resampling.LANCZOS)
        fmt_sel = request.form.get('output_format', 'auto')
        fmt = orig_fmt if fmt_sel == 'auto' else norm_fmt(fmt_sel)
        quality = int(request.form.get('quality', 90))

        if mode == 'percent':
            scale = float(request.form.get('percent', 100)) / 100
            nw, nh = max(1, round(ow * scale)), max(1, round(oh * scale))
        else:
            maintain = request.form.get('maintain_aspect', 'true') == 'true'
            ws = request.form.get('width', '').strip()
            hs = request.form.get('height', '').strip()
            w = int(ws) if ws else None
            h = int(hs) if hs else None
            ratio = ow / oh
            if maintain:
                if w and not h: nw, nh = max(1, w), max(1, round(w / ratio))
                elif h and not w: nw, nh = max(1, round(h * ratio)), max(1, h)
                elif w and h:
                    if w / h > ratio: w = max(1, round(h * ratio))
                    else: h = max(1, round(w / ratio))
                    nw, nh = w, h
                else: nw, nh = ow, oh
            else:
                nw = max(1, w) if w else ow
                nh = max(1, h) if h else oh

        return make_response(img.resize((nw, nh), resample), fmt, quality, base, 'resized')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/crop', methods=['POST'])
def crop():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    try:
        img, orig_fmt, base = load_file(request.files['file'])
        ow, oh = img.size
        x = max(0, int(request.form.get('x', 0)))
        y = max(0, int(request.form.get('y', 0)))
        w = max(1, int(request.form.get('width', ow)))
        h = max(1, int(request.form.get('height', oh)))
        x = min(x, ow - 1); y = min(y, oh - 1)
        right = min(x + w, ow); bottom = min(y + h, oh)
        fmt_sel = request.form.get('output_format', 'auto')
        fmt = orig_fmt if fmt_sel == 'auto' else norm_fmt(fmt_sel)
        quality = int(request.form.get('quality', 90))
        return make_response(img.crop((x, y, right, bottom)), fmt, quality, base, 'cropped')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/rotate', methods=['POST'])
def rotate():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    try:
        img, orig_fmt, base = load_file(request.files['file'])
        action = request.form.get('action', 'rotate')
        fmt_sel = request.form.get('output_format', 'auto')
        fmt = orig_fmt if fmt_sel == 'auto' else norm_fmt(fmt_sel)
        quality = int(request.form.get('quality', 90))
        if action == 'flip_h': result = ImageOps.mirror(img)
        elif action == 'flip_v': result = ImageOps.flip(img)
        else:
            angle = float(request.form.get('angle', 90))
            expand = request.form.get('expand', 'true') == 'true'
            result = img.rotate(-angle, expand=expand, resample=Image.Resampling.BICUBIC)
        return make_response(result, fmt, quality, base, 'rotated')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/effects', methods=['POST'])
def effects():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    try:
        img, orig_fmt, base = load_file(request.files['file'])
        brightness = float(request.form.get('brightness', 1.0))
        contrast = float(request.form.get('contrast', 1.0))
        saturation = float(request.form.get('saturation', 1.0))
        sharpness = float(request.form.get('sharpness', 1.0))

        if brightness != 1.0: img = ImageEnhance.Brightness(img).enhance(brightness)
        if contrast != 1.0: img = ImageEnhance.Contrast(img).enhance(contrast)
        if saturation != 1.0: img = ImageEnhance.Color(img).enhance(saturation)
        if sharpness != 1.0: img = ImageEnhance.Sharpness(img).enhance(sharpness)

        ftype = request.form.get('filter', 'none')
        if ftype == 'grayscale':
            gray = ImageOps.grayscale(img)
            img = gray.convert('RGBA' if img.mode == 'RGBA' else 'RGB')
        elif ftype == 'sepia':
            img = sepia(img)
        elif ftype == 'invert':
            if img.mode == 'RGBA':
                r, g, b, a = img.split()
                inv = ImageOps.invert(Image.merge('RGB', (r, g, b)))
                ir, ig, ib = inv.split()
                img = Image.merge('RGBA', (ir, ig, ib, a))
            else:
                img = ImageOps.invert(img.convert('RGB'))
        elif ftype == 'blur':
            radius = max(0.1, float(request.form.get('blur_radius', 2)))
            img = img.filter(ImageFilter.GaussianBlur(radius=radius))
        elif ftype == 'sharpen':
            img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        elif ftype == 'emboss':
            img = img.filter(ImageFilter.EMBOSS)
        elif ftype == 'edge':
            img = img.filter(ImageFilter.FIND_EDGES)
        elif ftype == 'smooth':
            img = img.filter(ImageFilter.SMOOTH_MORE)

        fmt_sel = request.form.get('output_format', 'auto')
        fmt = orig_fmt if fmt_sel == 'auto' else norm_fmt(fmt_sel)
        quality = int(request.form.get('quality', 90))
        return make_response(img, fmt, quality, base, 'edited')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/optimize', methods=['POST'])
def optimize():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    try:
        img, orig_fmt, base = load_file(request.files['file'])
        fmt_sel = request.form.get('output_format', 'auto')
        fmt = orig_fmt if fmt_sel == 'auto' else norm_fmt(fmt_sel)
        quality = int(request.form.get('quality', 80))
        mw = request.form.get('max_width', '').strip()
        mh = request.form.get('max_height', '').strip()
        if mw or mh:
            tw = int(mw) if mw else img.width
            th = int(mh) if mh else img.height
            img.thumbnail((tw, th), Image.Resampling.LANCZOS)
        return make_response(img, fmt, quality, base, 'optimized')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    try:
        img, orig_fmt, base = load_file(request.files['file'])
        fmt = norm_fmt(request.form.get('output_format', 'PNG'))
        quality = int(request.form.get('quality', 90))
        return make_response(img, fmt, quality, base, 'converted')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
