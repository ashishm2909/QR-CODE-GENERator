import qrcode
from PIL import Image, ImageDraw
import base64
import math
from io import BytesIO
import logging
from .image_service import ImageService

logger = logging.getLogger(__name__)

class QRService:
    @staticmethod
    def generate_standard_qr(data, logo=None, artistic_mode=False):
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        if artistic_mode and logo:
            return QRService._generate_artistic_qr(qr, logo)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        if logo and not artistic_mode:
            img = QRService._add_logo(img, logo)
            
        return QRService._to_base64_data_url(img)

    @staticmethod
    def _add_logo(img, logo_file):
        try:
            logo = Image.open(logo_file)
            qr_width, qr_height = img.size
            logo_size = int(qr_width / 4)
            logo.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            logo_bg_size = int(logo_size * 1.1)
            logo_bg = Image.new('RGB', (logo_bg_size, logo_bg_size), 'white')
            
            logo_pos_on_bg = ((logo_bg_size - logo.size[0]) // 2, (logo_bg_size - logo.size[1]) // 2)
            
            if logo.mode == 'RGBA':
                logo_bg.paste(logo, logo_pos_on_bg, logo)
            else:
                logo_bg.paste(logo, logo_pos_on_bg)
            
            logo_pos = ((qr_width - logo_bg_size) // 2, (qr_height - logo_bg_size) // 2)
            img.paste(logo_bg, logo_pos)
            return img
        except Exception as e:
            logger.warning("Logo overlay failed, returning plain QR: %s", e)
            return img

    @staticmethod
    def _generate_artistic_qr(qr, logo_file):
        try:
            bg_image = Image.open(logo_file).convert('RGBA')
            qr_matrix = qr.get_matrix()
            module_count = len(qr_matrix)
            box_size = 20
            qr_size = module_count * box_size
            bg_image = bg_image.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
            
            bg_rgb = bg_image.convert('RGB')
            colors = bg_rgb.getcolors(qr_size * qr_size)
            if colors:
                colors.sort(reverse=True)
                dominant_color = colors[0][1]
                avg = sum(dominant_color) / 3
                dark_color = (0, 0, 0, 255) if avg > 128 else (255, 255, 255, 255)
            else:
                dark_color = (0, 0, 0, 255)
            
            qr_overlay = Image.new('RGBA', (qr_size, qr_size), (255, 255, 255, 0))
            draw = ImageDraw.Draw(qr_overlay)
            
            for y in range(module_count):
                for x in range(module_count):
                    if qr_matrix[y][x]:
                        module_color = dark_color[:3] + (200,)
                        draw.rectangle(
                            [x * box_size, y * box_size, (x + 1) * box_size - 1, (y + 1) * box_size - 1],
                            fill=module_color
                        )
            
            img = Image.alpha_composite(bg_image, qr_overlay)
            return QRService._to_base64_data_url(img.convert('RGB'))
        except Exception as e:
            logger.warning("Artistic QR generation failed, falling back to standard: %s", e)
            return QRService._to_base64_data_url(qr.make_image(fill_color="black", back_color="white"))

    @staticmethod
    def generate_artistic_svg(data, shape='circle', finder='bullseye', halftone=False, color='#000000', quiet_zone=4, module_px=14, logo=None, bg_opacity=0.95, pro_enabled=False):
        qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=1, border=0)
        qr.add_data(data)
        qr.make(fit=True)
        matrix = qr.get_matrix()
        n = len(matrix)
        
        bg_img = None
        pixels = None
        content_size = n * module_px
        total = (n + 2 * quiet_zone) * module_px

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total} {total}" width="{total}" height="{total}">',
            f'<rect width="100%" height="100%" fill="white"/>'
        ]

        if logo and pro_enabled:
            try:
                bg_img = Image.open(logo).convert('RGB')
                tmp = bg_img.resize((content_size, content_size), Image.Resampling.LANCZOS)
                pixels = list(tmp.getdata())
                b64 = ImageService.get_image_b64(tmp)
                svg_parts.append(f'<image x="{quiet_zone*module_px}" y="{quiet_zone*module_px}" width="{content_size}" height="{content_size}" href="data:image/png;base64,{b64}" preserveAspectRatio="xMidYMid slice" opacity="{bg_opacity}"/>')
            except Exception as e:
                logger.warning("Background image processing failed: %s", e)

        # Draw finders
        for fx, fy in [(0, 0), (n - 7, 0), (0, n - 7)]:
            QRService._append_finder_svg(svg_parts, fx, fy, quiet_zone, module_px, finder)

        # Draw modules
        for y in range(n):
            for x in range(n):
                if not matrix[y][x] or ImageService.in_finder(x, y, n):
                    continue
                
                cx_img = int(x * module_px + module_px/2)
                cy_img = int(y * module_px + module_px/2)
                
                fill = ImageService.sample_color(cx_img, cy_img, n, module_px, pixels, content_size, content_size, color)
                x0 = (x + quiet_zone) * module_px
                y0 = (y + quiet_zone) * module_px
                cxp, cyp = x0 + module_px/2, y0 + module_px/2

                # True Halftone Logic: Scaled shapes based on luminosity
                r_base = module_px * 0.45
                scale_factor = 1.0
                
                if halftone and pixels and pro_enabled:
                    if 0 <= cy_img < content_size and 0 <= cx_img < content_size:
                        idx = cy_img * content_size + cx_img
                        pix = pixels[idx]
                        lum = 0.2126*pix[0] + 0.7152*pix[1] + 0.0722*pix[2]
                        # Darker pixels = larger dots. Range from 0.3x to 1.1x module size.
                        scale_factor = 0.3 + (1 - lum/255.0) * 0.8
                
                r = r_base * scale_factor

                if shape == 'circle':
                    svg_parts.append(f'<circle cx="{cxp}" cy="{cyp}" r="{r:.2f}" fill="{fill}"/>')
                elif shape == 'diamond':
                    pad = module_px * 0.5 * (1 - scale_factor)
                    pts = f'{cxp},{y0+pad} {x0+module_px-pad},{cyp} {cxp},{y0+module_px-pad} {x0+pad},{cyp}'
                    svg_parts.append(f'<polygon points="{pts}" fill="{fill}"/>')
                elif shape == 'rounded':
                    s = module_px * scale_factor
                    rad = s * 0.4
                    off = (module_px - s) / 2
                    svg_parts.append(f'<rect x="{x0+off}" y="{y0+off}" width="{s}" height="{s}" rx="{rad}" ry="{rad}" fill="{fill}"/>')
                elif shape == 'star':
                    s = module_px * scale_factor * 0.5
                    pts = f'{cxp},{cyp-s} {cxp+s*0.3},{cyp-s*0.3} {cxp+s},{cyp} {cxp+s*0.3},{cyp+s*0.3} {cxp},{cyp+s} {cxp-s*0.3},{cyp+s*0.3} {cxp-s},{cyp} {cxp-s*0.3},{cyp-s*0.3}'
                    svg_parts.append(f'<polygon points="{pts}" fill="{fill}"/>')
                elif shape == 'hexagon':
                    s = module_px * scale_factor * 0.5
                    pts = f'{cxp},{cyp-s} {cxp+s*0.866},{cyp-s*0.5} {cxp+s*0.866},{cyp+s*0.5} {cxp},{cyp+s} {cxp-s*0.866},{cyp+s*0.5} {cxp-s*0.866},{cyp-s*0.5}'
                    svg_parts.append(f'<polygon points="{pts}" fill="{fill}"/>')
                elif shape == 'cross':
                    s = module_px * scale_factor * 0.5
                    w = s * 0.35
                    pts = f'{cxp-w},{cyp-s} {cxp+w},{cyp-s} {cxp+w},{cyp-w} {cxp+s},{cyp-w} {cxp+s},{cyp+w} {cxp+w},{cyp+w} {cxp+w},{cyp+s} {cxp-w},{cyp+s} {cxp-w},{cyp+w} {cxp-s},{cyp+w} {cxp-s},{cyp-w} {cxp-w},{cyp-w}'
                    svg_parts.append(f'<polygon points="{pts}" fill="{fill}"/>')
                elif shape == 'triangle':
                    s = module_px * scale_factor * 0.55
                    h = s * 0.866
                    pts = f'{cxp},{cyp-h*0.6} {cxp+s},{cyp+h*0.4} {cxp-s},{cyp+h*0.4}'
                    svg_parts.append(f'<polygon points="{pts}" fill="{fill}"/>')
                elif shape == 'petal':
                    s = module_px * scale_factor * 0.45
                    svg_parts.append(f'<ellipse cx="{cxp}" cy="{cyp-s*0.3}" rx="{s*0.55}" ry="{s}" fill="{fill}" transform="rotate(0,{cxp},{cyp})"/>')
                elif shape == 'heart':
                    s = module_px * scale_factor * 0.3
                    d = f'M{cxp},{cyp+s*1.2} C{cxp-s*2},{cyp-s*0.5} {cxp-s*0.5},{cyp-s*2} {cxp},{cyp-s*0.5} C{cxp+s*0.5},{cyp-s*2} {cxp+s*2},{cyp-s*0.5} {cxp},{cyp+s*1.2}Z'
                    svg_parts.append(f'<path d="{d}" fill="{fill}"/>')
                elif shape == 'teardrop':
                    s = module_px * scale_factor * 0.45
                    d = f'M{cxp},{cyp-s*1.3} C{cxp+s*1.1},{cyp-s*0.3} {cxp+s*1.1},{cyp+s*0.8} {cxp},{cyp+s} C{cxp-s*1.1},{cyp+s*0.8} {cxp-s*1.1},{cyp-s*0.3} {cxp},{cyp-s*1.3}Z'
                    svg_parts.append(f'<path d="{d}" fill="{fill}"/>')
                else: # square
                    s = module_px * scale_factor
                    off = (module_px - s) / 2
                    svg_parts.append(f'<rect x="{x0+off}" y="{y0+off}" width="{s}" height="{s}" fill="{fill}"/>')

        svg_parts.append('</svg>')
        return ''.join(svg_parts)

    @staticmethod
    def _append_finder_svg(svg_parts, cx, cy, qz, module_px, finder_style):
        size = 7 * module_px
        x0 = (cx + qz) * module_px
        y0 = (cy + qz) * module_px
        cxp, cyp = x0 + size/2, y0 + size/2
        
        if finder_style == 'bullseye':
            svg_parts.append(f'<circle cx="{cxp}" cy="{cyp}" r="{size/2}" fill="black"/>')
            svg_parts.append(f'<circle cx="{cxp}" cy="{cyp}" r="{size/2*0.66}" fill="white"/>')
            svg_parts.append(f'<circle cx="{cxp}" cy="{cyp}" r="{size/2*0.36}" fill="black"/>')
        elif finder_style == 'rounded':
            rad = module_px * 2
            svg_parts.append(f'<rect x="{x0}" y="{y0}" width="{size}" height="{size}" rx="{rad}" ry="{rad}" fill="black"/>')
            pad = module_px
            svg_parts.append(f'<rect x="{x0+pad}" y="{y0+pad}" width="{size-2*pad}" height="{size-2*pad}" rx="{rad}" ry="{rad}" fill="white"/>')
            pad2 = module_px * 2
            svg_parts.append(f'<rect x="{x0+pad2}" y="{y0+pad2}" width="{size-2*pad2}" height="{size-2*pad2}" rx="{rad}" ry="{rad}" fill="black"/>')
        elif finder_style == 'diamond':
            s = size / 2
            pts_outer = f'{cxp},{y0} {x0+size},{cyp} {cxp},{y0+size} {x0},{cyp}'
            svg_parts.append(f'<polygon points="{pts_outer}" fill="black"/>')
            s2 = s * 0.66
            pts_mid = f'{cxp},{cyp-s2} {cxp+s2},{cyp} {cxp},{cyp+s2} {cxp-s2},{cyp}'
            svg_parts.append(f'<polygon points="{pts_mid}" fill="white"/>')
            s3 = s * 0.36
            pts_inner = f'{cxp},{cyp-s3} {cxp+s3},{cyp} {cxp},{cyp+s3} {cxp-s3},{cyp}'
            svg_parts.append(f'<polygon points="{pts_inner}" fill="black"/>')
        elif finder_style == 'target':
            svg_parts.append(f'<circle cx="{cxp}" cy="{cyp}" r="{size/2}" fill="black"/>')
            svg_parts.append(f'<circle cx="{cxp}" cy="{cyp}" r="{size/2*0.78}" fill="white"/>')
            svg_parts.append(f'<circle cx="{cxp}" cy="{cyp}" r="{size/2*0.58}" fill="black"/>')
            svg_parts.append(f'<circle cx="{cxp}" cy="{cyp}" r="{size/2*0.38}" fill="white"/>')
            svg_parts.append(f'<circle cx="{cxp}" cy="{cyp}" r="{size/2*0.2}" fill="black"/>')
        elif finder_style == 'flower':
            petal_r = size * 0.22
            dist = size * 0.28
            svg_parts.append(f'<circle cx="{cxp}" cy="{cyp}" r="{size/2}" fill="black"/>')
            for angle in [0, 60, 120, 180, 240, 300]:
                px = cxp + dist * math.cos(math.radians(angle))
                py = cyp + dist * math.sin(math.radians(angle))
                svg_parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{petal_r:.1f}" fill="white"/>')
            svg_parts.append(f'<circle cx="{cxp}" cy="{cyp}" r="{size*0.18}" fill="black"/>')
        elif finder_style == 'nested':
            svg_parts.append(f'<circle cx="{cxp}" cy="{cyp}" r="{size/2}" fill="black"/>')
            svg_parts.append(f'<circle cx="{cxp}" cy="{cyp}" r="{size/2*0.75}" fill="white"/>')
            svg_parts.append(f'<circle cx="{cxp}" cy="{cyp}" r="{size/2*0.5}" fill="black"/>')
            svg_parts.append(f'<circle cx="{cxp}" cy="{cyp}" r="{size/2*0.28}" fill="white"/>')
            svg_parts.append(f'<circle cx="{cxp}" cy="{cyp}" r="{size/2*0.12}" fill="black"/>')
        else:  # classic
            svg_parts.append(f'<rect x="{x0}" y="{y0}" width="{size}" height="{size}" fill="black"/>')
            pad = module_px
            svg_parts.append(f'<rect x="{x0+pad}" y="{y0+pad}" width="{size-2*pad}" height="{size-2*pad}" fill="white"/>')
            pad2 = module_px * 2
            svg_parts.append(f'<rect x="{x0+pad2}" y="{y0+pad2}" width="{size-2*pad2}" height="{size-2*pad2}" fill="black"/>')

    @staticmethod
    def _to_base64_data_url(img):
        buf = BytesIO()
        img.save(buf, format='PNG')
        img_base64 = base64.b64encode(buf.getvalue()).decode()
        return f'data:image/png;base64,{img_base64}'
