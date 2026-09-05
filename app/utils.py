import re
import unicodedata
from functools import wraps
from flask import abort
from flask_login import current_user


def slugify(text):
    """Create URL-friendly slug from Nepali/English text."""
    if not text:
        return ''
    text = str(text).strip().lower()
    # Keep Devanagari and alphanumeric
    text = re.sub(r'[^\w\s\u0900-\u097F-]', '', text, flags=re.UNICODE)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text).strip('-')
    return text[:200] or 'item'


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated


def allowed_file(filename, allowed=None):
    if allowed is None:
        allowed = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


def upload_to_cloudinary(file, folder='puku-kosheli'):
    """Upload file to Cloudinary. Returns (url, public_id) or (None, None)."""
    try:
        import cloudinary.uploader
        result = cloudinary.uploader.upload(
            file,
            folder=folder,
            resource_type='image',
            transformation=[
                {'quality': 'auto', 'fetch_format': 'auto'}
            ]
        )
        return result.get('secure_url'), result.get('public_id')
    except Exception as e:
        print(f'Cloudinary upload error: {e}')
        return None, None


def delete_from_cloudinary(public_id):
    if not public_id:
        return False
    try:
        import cloudinary.uploader
        cloudinary.uploader.destroy(public_id)
        return True
    except Exception as e:
        print(f'Cloudinary delete error: {e}')
        return False


def cloudinary_transform(url, width=None, height=None, crop='fill'):
    """Apply Cloudinary transformations to an image URL."""
    if not url or 'cloudinary.com' not in url:
        return url
    transforms = []
    if width:
        transforms.append(f'w_{width}')
    if height:
        transforms.append(f'h_{height}')
    if crop:
        transforms.append(f'c_{crop}')
    transforms.append('q_auto')
    transforms.append('f_auto')
    transform_str = ','.join(transforms)
    # Insert transformation into URL
    parts = url.split('/upload/')
    if len(parts) == 2:
        return f'{parts[0]}/upload/{transform_str}/{parts[1]}'
    return url


def format_price(amount):
    try:
        return f'रु. {float(amount):,.0f}'
    except (TypeError, ValueError):
        return 'रु. 0'


def get_setting(key, default=''):
    from app.models import SiteSetting
    try:
        return SiteSetting.get(key, default) or default
    except Exception:
        return default
