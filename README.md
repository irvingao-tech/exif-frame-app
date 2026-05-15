# EXIF Frame Card — 摄影卡片边框

为照片自动添加高级 EXIF 摄影卡片边框的桌面应用。

风格参考：美术馆装帧、画廊展签、摄影档案卡、极简社交发布、复古明信片。

## 功能特性

- ✅ 拖拽导入图片（JPG/PNG/TIFF）
- ✅ 自动读取 EXIF 信息（相机、镜头、焦距、光圈、快门、ISO、日期、GPS）
- ✅ 5 个高级摄影展边框模板
- ✅ 8 种输出画布比例
- ✅ 手动编辑 EXIF 显示内容
- ✅ 实时预览
- ✅ 边框参数可调（边距、颜色、圆角、阴影、字体）
- ✅ 自动识别相机/镜头品牌 Logo（支持本地内置 Logo 资源）
- ✅ GPS 经纬度可生成地图二维码（Apple Maps / Google Maps / 通用 geo）
- ✅ 导出 JPG/PNG，支持多种分辨率
- ✅ 支持中文路径

### 模板风格
| 模板 | 风格 |
|------|------|
| Museum White | 暖白卡纸装裱，大留白与重底边，照片细压线，适合美术馆装帧感 |
| Gallery Black | 黑色展墙/影院风格，双层细边框，浅色 EXIF 文字，适合暗调作品 |
| Off-white Archive | 米色档案纸，顶部 ARCHIVE 编号、规则线、标题/地点/日期/EXIF 信息区 |
| Minimal Border | 极简白边，轻边线与小号文字，适合社交平台发布 |
| Vintage Postcard | 复古明信片纸张，照片纸框、邮票框、邮戳、邮政波浪线与地址横线 |

## 安装与运行

### 1. 安装 Python 依赖

```bash
# 推荐使用 Python 3.10+
pip install -r requirements.txt
```

### 2. 运行应用

```bash
python main.py
```

## 打包为 Windows .exe

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包为单个 exe
pyinstaller --onefile --windowed --name "EXIFFrame卡" --add-data "src;src" main.py

# 或者使用 spec 文件获得更精细控制
pyinstaller exif_frame.spec
```

### PyInstaller spec 文件示例 (`exif_frame.spec`):

```python
# -*- mode: python -*-
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('src', 'src')],
    hiddenimports=['PIL._tkinter_finder', 'piexif'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='EXIFFrame卡',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

## 项目结构

```
exif-frame-app/
├── main.py                      # 入口文件
├── requirements.txt             # 依赖
├── README.md
├── src/
│   ├── app.py                   # QApplication 初始化
│   ├── core/
│   │   ├── exif_reader.py       # EXIF 数据读取
│   │   ├── image_processor.py   # 图片处理 & 模板调度
│   │   └── exporter.py          # 导出功能
│   ├── templates/
│   │   ├── base.py              # 模板基类 & 工具函数
│   │   ├── museum_white.py      # 模板 A
│   │   ├── gallery_black.py     # 模板 B
│   │   ├── offwhite_archive.py  # 模板 C
│   │   ├── minimal_border.py    # 模板 D
│   │   └── contact_sheet.py     # 模板 E（Vintage Postcard）
│   └── ui/
│       ├── main_window.py       # 主窗口（三栏布局）
│       ├── image_list.py        # 左侧图片列表
│       ├── preview.py           # 中间预览区
│       └── controls.py          # 右侧控制面板
```

## 扩展模板

在 `src/templates/` 下创建新文件，继承 `BaseTemplate`：

```python
from src.templates.base import BaseTemplate, RenderParams, ExifSource

class MyTemplate(BaseTemplate):
    name = 'My Template'
    description = 'Description'
    
    def render(self, image, exif, params):
        # ... render logic
        return canvas_image
```

然后在 `src/core/image_processor.py` 的 `TEMPLATES` 字典中注册即可。

## 技术栈

- **Python 3.10+**
- **PySide6** — Qt for Python GUI
- **Pillow** — Image processing
- **piexif** — EXIF reading
- **qrcode** — GPS map QR code generation
- **PyInstaller** — Windows .exe packaging

## License

MIT
