# EXIF Frame Card

A lightweight desktop app for turning photos into styled EXIF frame cards.

The app reads photo metadata, renders a selected visual template, and exports a finished JPG or PNG. It is designed for local photo testing and small batch workflows.

## Features

- Import photos by file picker, folder picker, drag and drop.
- Show imported photos as a thumbnail list.
- Read common EXIF fields: camera, lens, focal length, aperture, shutter, ISO, date, and GPS when available.
- Manually edit displayed metadata per photo.
- Optional batch edit mode for applying visual settings across imported photos.
- Local EXIF and preview caching for faster switching between images.
- Responsive preview with scroll-wheel zoom and drag-to-pan viewing.
- Export JPG or PNG with selectable long-edge resolution, including original size.
- Camera brand logos from local assets, including Sony, Ricoh, and Apple.
- GPS QR code links for Apple Maps, Google Maps, or a universal geo URL.
- Template-specific controls are shown only when the selected template uses them.

## Templates

| Template | Style |
| --- | --- |
| Museum White | Warm museum mat with generous white space and refined EXIF text. |
| Gallery Black | Dark gallery wall look with quiet light typography. |
| Off-white Archive | Archival paper style with title, location, date, and EXIF details. |
| Minimal Border | Clean social-post frame with compact metadata. |
| Vintage Postcard | Warm postcard paper, movable postmark, address lines, logo, and map QR. |
| Color Reversal Film | Medium-format 120 reversal film border with subtle black frame texture and bright yellow EXIF markings. |
| Full Width Info Bar | Full-width photo with a clean bottom strip for camera, brand, exposure, and date. |

## Controls

- `Template`: choose style, canvas ratio, and preview quality.
- `Metadata`: edit the text that appears on the rendered card.
- `Frame`: background, margins, radius, and image shadow.
- `Typography`: text size, color, weight, and alignment.
- `Postcard`: only appears for Vintage Postcard; controls the postmark position.
- `Photo Zoom / Photo X / Photo Y`: only appears for Color Reversal Film; controls crop and composition inside the film window.
- `Logo & Map`: controls camera logo and GPS QR placement.
- `Export`: controls output format and resolution.

## Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the app:

```bash
python main.py
```

On Windows, you can also use:

```bat
Start EXIF Frame Card.bat
```

## Project Structure

```text
exif-frame-app/
├── main.py
├── requirements.txt
├── Start EXIF Frame Card.bat
├── src/
│   ├── assets/
│   │   ├── fonts/
│   │   ├── logos/
│   │   └── stamps/
│   ├── core/
│   │   ├── exif_reader.py
│   │   ├── image_processor.py
│   │   ├── local_cache.py
│   │   └── exporter.py
│   ├── templates/
│   │   ├── base.py
│   │   ├── contact_sheet.py
│   │   ├── color_reversal_film.py
│   │   └── ...
│   └── ui/
│       ├── main_window.py
│       ├── image_list.py
│       ├── preview.py
│       └── controls.py
```

## Build Notes

The app uses:

- Python 3.10+
- PySide6 for the desktop UI
- Pillow for image composition
- piexif for EXIF parsing
- qrcode for GPS map QR generation

Fonts bundled in `src/assets/fonts` are open fonts with their license files included.

## License

MIT
