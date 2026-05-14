"""
Template C: Off-white Archive
Cream paper background, image slightly upper,
title/location/date + EXIF at bottom — like archive card.
"""

from PIL import Image, ImageDraw

from .base import (
    BaseTemplate, RenderParams, ExifSource,
    get_merged_exif, calculate_canvas,
    draw_rounded_rect, draw_shadow, load_font, minimum_safe_margins,
    template_colors, mix_color,
)


class OffWhiteArchiveTemplate(BaseTemplate):
    name = 'Off-white Archive'
    description = 'Cream paper, title + location + date, archive card style'

    def render(self, image: Image.Image, exif: ExifSource, params: RenderParams) -> Image.Image:
        merged = get_merged_exif(exif, params)
        
        canvas_w, canvas_h, scale = calculate_canvas(
            image.width, image.height, params.ratio, params.target_long_edge
        )
        
        bg_color, font_color = template_colors(params, (236, 230, 216), (52, 49, 43))
        
        m_top = int(max(params.margin_top, 86) * canvas_h / 2048)
        m_side = int(max(params.margin_side, 96) * canvas_w / 2048)
        m_bottom = int(max(params.margin_bottom, 230) * canvas_h / 2048)
        min_top, min_bottom = minimum_safe_margins(canvas_w, canvas_h, params, 3)
        m_top = max(m_top, min_top)
        m_bottom = max(m_bottom, min_bottom)
        
        # Image area is in the upper portion
        avail_w = canvas_w - 2 * m_side
        avail_h = canvas_h - m_top - m_bottom
        
        img_scale = min(avail_w / image.width, avail_h / image.height)
        new_w = int(image.width * img_scale)
        new_h = int(image.height * img_scale)
        img_resized = image.resize((new_w, new_h), Image.LANCZOS)
        
        canvas = Image.new('RGB', (canvas_w, canvas_h), bg_color)
        
        img_x = (canvas_w - new_w) // 2
        img_y = m_top
        
        if params.image_shadow:
            canvas_rgba = canvas.convert('RGBA')
            img_box = (img_x, img_y, img_x + new_w, img_y + new_h)
            canvas_rgba = draw_shadow(canvas_rgba, img_box, params.image_corner_radius)
            canvas = canvas_rgba.convert('RGB')
        
        if params.image_corner_radius > 0:
            mask = Image.new('L', (new_w, new_h), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle(
                (0, 0, new_w, new_h), params.image_corner_radius, fill=255
            )
            canvas.paste(img_resized, (img_x, img_y), mask)
        else:
            canvas.paste(img_resized, (img_x, img_y))
        
        draw = ImageDraw.Draw(canvas)
        paper_line = mix_color(bg_color, (0, 0, 0), 0.18)
        faint_line = mix_color(bg_color, (0, 0, 0), 0.08)
        draw.rectangle(
            (img_x - 1, img_y - 1, img_x + new_w, img_y + new_h),
            outline=paper_line,
            width=max(1, canvas_w // 1000),
        )
        label_top = img_y + new_h + int(m_bottom * 0.10)
        draw.line(
            (m_side, label_top - max(6, canvas_h // 160), canvas_w - m_side, label_top - max(6, canvas_h // 160)),
            fill=faint_line,
            width=max(1, canvas_w // 1200),
        )
        archive_font = load_font(max(9, int(params.font_size * 0.58)), True)
        archive_id = f'ARCHIVE / {merged.get("date") or "UNDATED"}'
        draw.text((m_side, max(8, m_top // 2)), archive_id, fill=mix_color(font_color, bg_color, 0.22), font=archive_font)
        image_box = (img_x, img_y, img_x + new_w, img_y + new_h)
        original_font_color = params.font_color
        params.font_color = font_color
        logo_box = self._get_logo_box(canvas, merged, params, image_box, m_side, m_top, m_bottom)
        qr_box = self._get_gps_qr_box(canvas, merged, params, image_box, m_side, m_top, m_bottom, bg_color)
        
        # Build text lines
        text_y = label_top
        line_spacing = int(params.font_size * 1.6)
        
        # Line 1: Title / Location / Date
        line1_parts = []
        if merged.get('title'):
            line1_parts.append(merged['title'])
        if merged.get('location'):
            line1_parts.append(merged['location'])
        if merged.get('date'):
            line1_parts.append(merged['date'])
        line1 = '  /  '.join(line1_parts)
        
        # Line 2: EXIF
        line2 = self._build_exif_line(merged)
        
        # Line 3: Note
        line3 = merged.get('note', '')
        
        if params.font_size > 0:
            def draw_line(text, y, size, bold=False):
                if not text or y >= canvas_h - 8:
                    return 0
                line_h = max(12, int(size * 1.4))
                text_x, text_w = self._text_area_avoiding_boxes(
                    img_x, y, new_w, line_h, [logo_box, qr_box]
                )
                return self._draw_fitted_text(
                    draw, text, text_x, y, text_w,
                    size, font_color, bold, params.text_align,
                )
            
            if line1:
                draw_line(line1, text_y, params.font_size, params.font_bold)
                text_y += line_spacing
            
            if line2:
                draw_line(line2, text_y, max(params.font_size - 2, 10), False)
                text_y += line_spacing
            
            if line3:
                draw_line(line3, text_y, max(params.font_size - 2, 10), False)
        
        self._draw_brand_logo(
            canvas, merged, params,
            image_box,
            m_side, m_top, m_bottom,
        )
        self._draw_gps_qr(canvas, merged, params, image_box, m_side, m_top, m_bottom, bg_color)
        params.font_color = original_font_color
        return canvas
