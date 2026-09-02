from flask import Blueprint, request, jsonify, current_app, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
import os
import uuid
import logging
from ..services.qr_service import QRService
from ..models import db, QRCode, User

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'mp3', 'wav', 'mp4', 'webm', 'pptx'}
ALLOWED_MIMETYPES = {
    'image/png', 'image/jpeg', 'image/gif',
    'application/pdf',
    'audio/mpeg', 'audio/wav', 'audio/x-wav',
    'video/mp4', 'video/webm',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation'
}

api_bp = Blueprint('api', __name__)

def _get_user_plan():
    """Get the user's actual plan from the database, not from cookies."""
    if current_user.is_authenticated:
        return current_user.plan
    return 'free'

def _allowed_file(filename):
    """Check if the file extension and type are allowed."""
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS

@api_bp.route('/api/plan')
def api_plan():
    plan = _get_user_plan()
    return jsonify({'plan': plan})

@api_bp.route('/render_artistic_svg', methods=['POST'])
def render_artistic_svg():
    try:
        data = request.form.get('data', '')
        if not data:
            return jsonify({'success': False, 'error': 'Missing data'}), 400
            
        shape = request.form.get('shape', 'circle')
        finder = request.form.get('finder', 'bullseye')
        halftone = request.form.get('halftone', 'off') == 'on'
        color = request.form.get('color', '#000000')
        qz = int(request.form.get('quiet_zone', 4))
        module_px = int(request.form.get('module_px', 14))
        bg_opacity = float(request.form.get('bg_opacity', 0.95))
        
        plan = _get_user_plan()
        pro_enabled = plan in ('trial', 'pro', 'business')

        # --- FREE PLAN RESTRICTIONS ---
        if not pro_enabled:
            # Clamp quality to Standard (16px)
            module_px = min(module_px, 16)
            # Block Pro-only shapes → fall back to circle
            if shape in ('star', 'hexagon'):
                shape = 'circle'
            # No halftone for free
            halftone = False
            # No background image for free → ignore logo
            logo = None
        else:
            logo = None
            if 'logo' in request.files and request.files['logo'].filename:
                logo = request.files['logo']

        svg = QRService.generate_artistic_svg(
            data=data,
            shape=shape,
            finder=finder,
            halftone=halftone,
            color=color,
            quiet_zone=qz,
            module_px=module_px,
            logo=logo,
            bg_opacity=bg_opacity,
            pro_enabled=pro_enabled
        )
        
        if current_user.is_authenticated:
            new_qr = QRCode(
                user_id=current_user.id,
                type='artistic',
                data=data,
                svg_content=svg,
                is_artistic=True
            )
            db.session.add(new_qr)
            db.session.commit()
        
        return jsonify({'success': True, 'svg': svg})
    except Exception as e:
        logger.exception("Error rendering artistic SVG")
        return jsonify({'success': False, 'error': 'An error occurred rendering the SVG'}), 500

@api_bp.route('/generate', methods=['POST'])
def generate():
    try:
        qr_type = request.form.get('type', 'url')
        qr_data = ""

        # File upload handling
        if qr_type in ['image', 'pdf', 'audio', 'video', 'pptx']:
            if 'file' not in request.files:
                return jsonify({'success': False, 'error': 'No file part'}), 400
            file = request.files['file']
            if file.filename == '':
                return jsonify({'success': False, 'error': 'No selected file'}), 400

            if not _allowed_file(file.filename):
                return jsonify({'success': False, 'error': 'File type not allowed. Allowed: ' + ', '.join(ALLOWED_EXTENSIONS)}), 400

            safe_name = secure_filename(file.filename)
            ext = safe_name.rsplit('.', 1)[1].lower() if '.' in safe_name else ''
            unique_filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
            qr_data = request.url_root.rstrip('/') + url_for('main.uploaded_file', filename=unique_filename)
        
        else:
            # Standard text types
            data_fields = request.form
            if qr_type == 'url': qr_data = data_fields.get('url', '')
            elif qr_type == 'text': qr_data = data_fields.get('text', '')
            elif qr_type == 'wifi':
                qr_data = f"WIFI:S:{data_fields.get('ssid', '')};T:{data_fields.get('encryption', 'WPA/WPA2')};P:{data_fields.get('password', '')};;"
            elif qr_type == 'mail':
                qr_data = f"mailto:{data_fields.get('email', '')}?subject={data_fields.get('subject', '')}&body={data_fields.get('body', '')}"
            elif qr_type == 'phone': qr_data = f"tel:{data_fields.get('phone', '')}"
            elif qr_type == 'sms': qr_data = f"smsto:{data_fields.get('phone', '')}:{data_fields.get('message', '')}"
            elif qr_type == 'whatsapp': qr_data = f"https://wa.me/{data_fields.get('phone', '')}?text={data_fields.get('message', '')}"
            elif qr_type == 'youtube': qr_data = data_fields.get('url', '')
            elif qr_type == 'instagram': qr_data = f"https://instagram.com/{data_fields.get('username', '')}"
            elif qr_type == 'facebook': qr_data = data_fields.get('url', '')
            elif qr_type == 'tiktok': qr_data = f"https://tiktok.com/{data_fields.get('username', '')}"
            elif qr_type == 'telegram': qr_data = f"https://t.me/{data_fields.get('username', '')}"
            elif qr_type == 'maps': qr_data = f"geo:{data_fields.get('latitude', '')},{data_fields.get('longitude', '')}"
            elif qr_type == 'app': qr_data = data_fields.get('play_store') or data_fields.get('app_store') or ''
            elif qr_type == 'vcard':
                qr_data = f"BEGIN:VCARD\nVERSION:3.0\nN:{data_fields.get('lastname', '')};{data_fields.get('firstname', '')}\nFN:{data_fields.get('firstname', '')} {data_fields.get('lastname', '')}\nORG:{data_fields.get('company', '')}\nTITLE:{data_fields.get('job', '')}\nTEL:{data_fields.get('phone', '')}\nEMAIL:{data_fields.get('email', '')}\nURL:{data_fields.get('website', '')}\nADR:{data_fields.get('address', '')}\nEND:VCARD"
            elif qr_type == 'event':
                start = data_fields.get('start_date', '').replace('-', '').replace(':', '')
                end = data_fields.get('end_date', '').replace('-', '').replace(':', '')
                qr_data = f"BEGIN:VEVENT\nSUMMARY:{data_fields.get('title', 'Event')}\nLOCATION:{data_fields.get('location', '')}\nDTSTART:{start}\nDTEND:{end}\nEND:VEVENT"
            elif qr_type == 'crypto':
                qr_data = f"{data_fields.get('currency', 'bitcoin')}:{data_fields.get('address', '')}?amount={data_fields.get('amount', '')}"
            else:
                qr_data = data_fields.get('url', 'https://qrnation.com')

        if not qr_data:
            return jsonify({'success': False, 'error': 'No data provided'})

        artistic_mode = request.form.get('artistic_mode', 'false') == 'true'
        logo = request.files.get('logo') if 'logo' in request.files and request.files['logo'].filename != '' else None
        
        qr_code = QRService.generate_standard_qr(qr_data, logo=logo, artistic_mode=artistic_mode)
        
        if current_user.is_authenticated:
            # For standard QR, we save the data and type. 
            # We also store the base64 as svg_content for easy display in dashboard (though it's technically a PNG base64)
            new_qr = QRCode(
                user_id=current_user.id,
                type=qr_type,
                data=qr_data,
                svg_content=qr_code, # Storing the base64 string here for simplicity in this MVP
                is_artistic=False
            )
            db.session.add(new_qr)
            db.session.commit()
            
        return jsonify({
            'success': True,
            'qr_code': qr_code
        })
    except Exception as e:
        logger.exception("Error generating QR code")
        return jsonify({'success': False, 'error': 'An error occurred generating the QR code'}), 500

@api_bp.route('/api/delete_qr/<int:qr_id>', methods=['DELETE'])
@login_required
def delete_qr(qr_id):
    qr = QRCode.query.get_or_404(qr_id)
    if qr.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    db.session.delete(qr)
    db.session.commit()
    return jsonify({'success': True})


@api_bp.route('/api/qr-svg/<int:qr_id>')
@login_required
def serve_qr_svg(qr_id):
    """Serve artistic SVG content with proper Content-Type.
    Loading SVG via <img> tag prevents script execution in browsers."""
    qr = QRCode.query.get_or_404(qr_id)
    if qr.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    if not qr.is_artistic or not qr.svg_content:
        return jsonify({'error': 'Not an artistic QR code'}), 404
    response = current_app.response_class(
        response=qr.svg_content,
        status=200,
        mimetype='image/svg+xml'
    )
    response.headers['Content-Security-Policy'] = "default-src 'none'; style-src 'unsafe-inline'; img-src data:;"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@api_bp.route('/api/scan-qr', methods=['POST'])
def scan_qr():
    """Decode QR code from an uploaded image."""
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No image provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No image selected'}), 400

    try:
        from PIL import Image
        from pyzbar.pyzbar import decode, ZBarSymbol

        img = Image.open(file.stream)

        # Try decoding QR codes
        decoded = decode(img, symbols=[ZBarSymbol.QRCODE])

        if not decoded:
            # Try converting to grayscale
            img_gray = img.convert('L')
            decoded = decode(img_gray, symbols=[ZBarSymbol.QRCODE])

        if not decoded:
            return jsonify({'success': False, 'error': 'No QR code found in this image'}), 404

        # Return first QR code found
        qr = decoded[0]
        data = qr.data.decode('utf-8', errors='replace')

        # Detect content type
        content_type = 'text'
        if data.startswith('http://') or data.startswith('https://'):
            content_type = 'url'
        elif data.startswith('WIFI:'):
            content_type = 'wifi'
        elif data.startswith('BEGIN:VCARD'):
            content_type = 'vcard'
        elif data.startswith('mailto:'):
            content_type = 'email'
        elif data.startswith('tel:'):
            content_type = 'phone'
        elif data.startswith('smsto:') or data.startswith('sms:'):
            content_type = 'sms'
        elif data.startswith('geo:'):
            content_type = 'location'
        elif data.startswith('BEGIN:VEVENT'):
            content_type = 'event'

        return jsonify({
            'success': True,
            'data': data,
            'type': content_type,
        })

    except ImportError:
        logger.error("pyzbar or Pillow not installed")
        return jsonify({'success': False, 'error': 'QR scanning library not available'}), 500
    except Exception as e:
        logger.exception("Error scanning QR code")
        return jsonify({'success': False, 'error': 'Failed to process image'}), 500

