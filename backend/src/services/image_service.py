from PIL import Image
import base64
from io import BytesIO

class ImageService:
    @staticmethod
    def in_finder(x, y, n):
        # 7x7 finder at corners per spec
        corners = [(0, 0), (n - 7, 0), (0, n - 7)]
        for (fx, fy) in corners:
            if fx <= x < fx + 7 and fy <= y < fy + 7:
                return True
        return False

    @staticmethod
    def sample_color(cx_img, cy_img, n, module_px, pixels, img_width, img_height, color):
        if not pixels:
            return color
            
        if 0 <= cx_img < img_width and 0 <= cy_img < img_height:
            # Average over a small area (module footprint)
            r = max(1, module_px // 3)
            ix0 = max(0, int(cx_img - r))
            iy0 = max(0, int(cy_img - r))
            ix1 = min(img_width, int(cx_img + r))
            iy1 = min(img_height, int(cy_img + r))
            
            r_sum, g_sum, b_sum = 0, 0, 0
            count = 0
            
            for y in range(iy0, iy1):
                y_offset = y * img_width
                for x in range(ix0, ix1):
                    p = pixels[y_offset + x]
                    r_sum += p[0]
                    g_sum += p[1]
                    b_sum += p[2]
                    count += 1
                    
            if count > 0:
                return f'rgb({r_sum//count},{g_sum//count},{b_sum//count})'
        return color

    @staticmethod
    def get_image_b64(img):
        buf = BytesIO()
        img.save(buf, format='PNG')
        return base64.b64encode(buf.getvalue()).decode()
