"""
Template E: Vintage Postcard
Warm paper background, framed image, postcard marks and stamped corner.
"""

import math

from PIL import Image, ImageDraw

from .base import (
    BaseTemplate, RenderParams, ExifSource,
    get_merged_exif, calculate_canvas,
    draw_shadow, load_font, minimum_safe_margins,
    template_colors, mix_color,
)


class ContactSheetTemplate(BaseTemplate):
    name = 'Vintage Postcard'
    description = 'Warm paper, postcard border, stamp mark and travel-card metadata'

    def render(self, image: Image.Image, exif: ExifSource, params: RenderParams) -> Image.Image:
        merged = get_merged_exif(exif, params)

        canvas_w, canvas_h, scale = calculate_canvas(
            image.width, image.height, params.ratio, params.target_long_edge
        )

        bg_color, font_color = template_colors(params, (232, 218, 190), (74, 58, 42))

        m_top = int(max(params.margin_top, 92) * canvas_h / 2048)
        m_side = int(max(params.margin_side, 96) * canvas_w / 2048)
        m_bottom = int(max(params.margin_bottom, 260) * canvas_h / 2048)
        min_top, min_bottom = minimum_safe_margins(canvas_w, canvas_h, params, 3)
        m_top = max(m_top, min_top)
        m_bottom = max(m_bottom, min_bottom)

        avail_w = canvas_w - 2 * m_side
        avail_h = canvas_h - m_top - m_bottom

        img_scale = min(avail_w / image.width, avail_h / image.height)
        new_w = int(image.width * img_scale)
        new_h = int(image.height * img_scale)
        img_resized = image.resize((new_w, new_h), Image.LANCZOS)

        canvas = Image.new('RGB', (canvas_w, canvas_h), bg_color)
        draw = ImageDraw.Draw(canvas)

        paper_edge = mix_color(bg_color, (94, 62, 32), 0.22)
        paper_faint = mix_color(bg_color, (94, 62, 32), 0.10)
        inset = max(10, canvas_w // 55)
        draw.rectangle(
            (inset, inset, canvas_w - inset, canvas_h - inset),
            outline=paper_edge,
            width=max(1, canvas_w // 900),
        )
        draw.rectangle(
            (inset + 5, inset + 5, canvas_w - inset - 5, canvas_h - inset - 5),
            outline=paper_faint,
            width=1,
        )

        img_x = (canvas_w - new_w) // 2
        img_y = m_top

        if params.image_shadow:
            canvas_rgba = canvas.convert('RGBA')
            img_box = (img_x, img_y, img_x + new_w, img_y + new_h)
            canvas_rgba = draw_shadow(canvas_rgba, img_box, params.image_corner_radius)
            canvas = canvas_rgba.convert('RGB')
            draw = ImageDraw.Draw(canvas)

        if params.image_corner_radius > 0:
            mask = Image.new('L', (new_w, new_h), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle(
                (0, 0, new_w, new_h), params.image_corner_radius, fill=255
            )
            canvas.paste(img_resized, (img_x, img_y), mask)
        else:
            canvas.paste(img_resized, (img_x, img_y))

        photo_frame = mix_color(bg_color, (92, 55, 26), 0.28)
        draw.rectangle(
            (img_x - 5, img_y - 5, img_x + new_w + 4, img_y + new_h + 4),
            outline=photo_frame,
            width=max(1, canvas_w // 720),
        )
        draw.rectangle(
            (img_x - 10, img_y - 10, img_x + new_w + 9, img_y + new_h + 9),
            outline=mix_color(bg_color, (255, 255, 255), 0.30),
            width=1,
        )

        stamp_w = max(54, canvas_w // 8)
        stamp_h = int(stamp_w * 0.68)
        stamp_x = canvas_w - inset - stamp_w - max(10, canvas_w // 70)
        stamp_y = inset + max(8, canvas_h // 90)
        self._draw_stamp_frame(draw, stamp_x, stamp_y, stamp_w, stamp_h, paper_edge)
        stamp_font = load_font(max(9, int(params.font_size * 0.55)), True)
        draw.text(
            (stamp_x + stamp_w * 0.18, stamp_y + stamp_h * 0.28),
            'AIR\nMAIL',
            fill=paper_edge,
            font=stamp_font,
            spacing=2,
        )

        postmark_cx = stamp_x - max(8, stamp_w // 8)
        postmark_cy = stamp_y + stamp_h + max(10, canvas_h // 70)
        postmark_r = max(18, canvas_w // 28)
        self._draw_postmark(
            draw, postmark_cx, postmark_cy, postmark_r,
            paper_edge, merged.get('date') or 'POSTCARD',
        )

        header_font = load_font(max(10, int(params.font_size * 0.62)), True)
        draw.text(
            (m_side, max(inset + 12, m_top // 2)),
            'CARTE POSTALE',
            fill=paper_edge,
            font=header_font,
        )

        image_box = (img_x, img_y, img_x + new_w, img_y + new_h)
        original_font_color = params.font_color
        params.font_color = font_color
        logo_box = self._get_logo_box(canvas, merged, params, image_box, m_side, m_top, m_bottom)
        qr_box = self._get_gps_qr_box(canvas, merged, params, image_box, m_side, m_top, m_bottom, bg_color)

        text_y = img_y + new_h + int(m_bottom * 0.14)
        line_spacing = int(params.font_size * 1.55)

        line1_parts = []
        if merged.get('title'):
            line1_parts.append(merged['title'])
        if merged.get('location'):
            line1_parts.append(merged['location'])
        if merged.get('date'):
            line1_parts.append(merged['date'])
        line1 = '  -  '.join(line1_parts)
        line2 = self._build_exif_line(merged)
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

        address_x = img_x + int(new_w * 0.58)
        address_top = img_y + new_h + int(m_bottom * 0.16)
        address_right = min(canvas_w - m_side, stamp_x + stamp_w)
        for i in range(3):
            y = address_top + int((i + 1) * params.font_size * 1.65)
            if y < canvas_h - inset:
                draw.line(
                    (address_x, y, address_right, y),
                    fill=paper_faint,
                    width=max(1, canvas_w // 1400),
                )

        self._draw_brand_logo(
            canvas, merged, params,
            image_box,
            m_side, m_top, m_bottom,
        )
        self._draw_gps_qr(canvas, merged, params, image_box, m_side, m_top, m_bottom, bg_color)
        params.font_color = original_font_color
        return canvas

    def _draw_stamp_frame(self, draw, x: int, y: int, w: int, h: int, color):
        """Draw a perforated stamp-style rectangle."""
        r = max(2, w // 24)
        step = max(6, w // 12)
        draw.rectangle((x, y, x + w, y + h), outline=color, width=2)
        for px in range(x + step // 2, x + w, step):
            draw.ellipse((px - r, y - r, px + r, y + r), fill=color)
            draw.ellipse((px - r, y + h - r, px + r, y + h + r), fill=color)
        for py in range(y + step // 2, y + h, step):
            draw.ellipse((x - r, py - r, x + r, py + r), fill=color)
            draw.ellipse((x + w - r, py - r, x + w + r, py + r), fill=color)

    def _draw_postmark(self, draw, cx: int, cy: int, r: int, color, label: str):
        """Draw a circular postmark with cancellation waves."""
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color, width=2)
        inner = int(r * 0.68)
        draw.ellipse((cx - inner, cy - inner, cx + inner, cy + inner), outline=color, width=1)

        font = load_font(max(8, r // 4), True)
        text = str(label)[:12].upper()
        bbox = draw.textbbox((0, 0), text, font=font)
        draw.text(
            (cx - (bbox[2] - bbox[0]) // 2, cy - (bbox[3] - bbox[1]) // 2),
            text,
            fill=color,
            font=font,
        )

        start_x = cx + int(r * 0.62)
        for i in range(4):
            y = cy - int(r * 0.42) + i * max(8, r // 5)
            points = []
            for t in range(0, r * 3, max(3, r // 10)):
                px = start_x + t
                py = y + int(math.sin(t / max(1, r) * math.pi * 2) * max(3, r // 12))
                points.append((px, py))
            if len(points) > 1:
                draw.line(points, fill=color, width=1)
