"""
Template A: Museum White
Warm white background, large margins, image centered,
EXIF line at bottom — like museum mount card.
"""

from PIL import Image, ImageDraw

from .base import (
    BaseTemplate, RenderParams, ExifSource,
    get_merged_exif, calculate_canvas,
    draw_rounded_rect, draw_shadow, load_font, minimum_safe_margins,
    template_colors, mix_color,
)


class MuseumWhiteTemplate(BaseTemplate):
    name = 'Museum White'
    description = 'Warm white mat, large margins, single-line EXIF at bottom'

    def render(self, image: Image.Image, exif: ExifSource, params: RenderParams) -> Image.Image:
        merged = get_merged_exif(exif, params)
        
        # Calculate canvas
        canvas_w, canvas_h, scale = calculate_canvas(
            image.width, image.height, params.ratio, params.target_long_edge
        )
        
        bg_color, font_color = template_colors(params, (247, 245, 239), (48, 48, 45))
        
        # Museum mat boards usually feel calmer with generous side and bottom weight.
        m_top = int(max(params.margin_top, 110) * canvas_h / 2048)
        m_side = int(max(params.margin_side, 130) * canvas_w / 2048)
        m_bottom = int(max(params.margin_bottom, 220) * canvas_h / 2048)
        min_top, min_bottom = minimum_safe_margins(canvas_w, canvas_h, params, 1)
        m_top = max(m_top, min_top)
        m_bottom = max(m_bottom, min_bottom)
        
        # Resize image to fit within canvas minus margins
        avail_w = canvas_w - 2 * m_side
        avail_h = canvas_h - m_top - m_bottom
        
        img_scale = min(avail_w / image.width, avail_h / image.height)
        new_w = int(image.width * img_scale)
        new_h = int(image.height * img_scale)
        img_resized = image.resize((new_w, new_h), Image.LANCZOS)
        
        # Create canvas
        canvas = Image.new('RGB', (canvas_w, canvas_h), bg_color)
        
        # Image position (centered horizontally, positioned in upper portion)
        img_x = (canvas_w - new_w) // 2
        img_y = m_top
        
        # Apply shadow if enabled
        if params.image_shadow:
            canvas_rgba = canvas.convert('RGBA')
            img_box = (img_x, img_y, img_x + new_w, img_y + new_h)
            canvas_rgba = draw_shadow(canvas_rgba, img_box, params.image_corner_radius)
            canvas = canvas_rgba.convert('RGB')
        
        # Paste image with rounded corners
        if params.image_corner_radius > 0:
            # Create rounded corner mask
            mask = Image.new('L', (new_w, new_h), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle(
                (0, 0, new_w, new_h), params.image_corner_radius, fill=255
            )
            canvas.paste(img_resized, (img_x, img_y), mask)
        else:
            canvas.paste(img_resized, (img_x, img_y))
        
        draw = ImageDraw.Draw(canvas)
        mat_line = mix_color(bg_color, (0, 0, 0), 0.12)
        highlight = mix_color(bg_color, (255, 255, 255), 0.55)
        draw.rectangle(
            (img_x - 1, img_y - 1, img_x + new_w, img_y + new_h),
            outline=mat_line,
            width=max(1, canvas_w // 900),
        )
        draw.line(
            (img_x - 2, img_y - 2, img_x + new_w + 1, img_y - 2),
            fill=highlight,
            width=max(1, canvas_w // 1100),
        )
        
        # Draw EXIF text at bottom
        exif_line = self._build_exif_line(merged)
        image_box = (img_x, img_y, img_x + new_w, img_y + new_h)
        original_font_color = params.font_color
        params.font_color = font_color
        logo_box = self._get_logo_box(canvas, merged, params, image_box, m_side, m_top, m_bottom)
        qr_box = self._get_gps_qr_box(canvas, merged, params, image_box, m_side, m_top, m_bottom, bg_color)
        
        if exif_line and params.font_size > 0:
            text_y = img_y + new_h + (m_bottom // 3)
            line_h = max(12, int(params.font_size * 1.4))
            text_x, text_w = self._text_area_avoiding_boxes(
                img_x, text_y, new_w, line_h, [logo_box, qr_box]
            )
            self._draw_fitted_text(
                draw, exif_line, text_x, text_y, text_w,
                params.font_size, font_color,
                params.font_bold, params.text_align,
            )
        
        self._draw_brand_logo(
            canvas, merged, params,
            image_box,
            m_side, m_top, m_bottom,
        )
        self._draw_gps_qr(canvas, merged, params, image_box, m_side, m_top, m_bottom, bg_color)
        params.font_color = original_font_color
        return canvas
