# src/main.py
import sys
import os
import time
import ctypes
import hashlib

# --- libmpv DLL discovery ---
_dll_handles = []
_mpv_dll = None

if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if os.name == 'nt':
    libmpv_dir = os.path.join(base_dir, 'libs')
    dll_path = os.path.join(libmpv_dir, 'libmpv-2.dll')
    if os.path.isfile(dll_path):
        os.environ["PATH"] = libmpv_dir + os.pathsep + os.environ.get("PATH", "")
        try:
            _dll_handles.append(os.add_dll_directory(libmpv_dir))
        except (AttributeError, OSError):
            pass
        _mpv_dll = ctypes.CDLL(dll_path)
    else:
        print(f"WARNING: {dll_path} not found")

import mpv
import locale
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSizeGrip,
    QFileDialog, QPushButton, QSlider, QLabel, QSizePolicy, QStyle,
    QMenu, QDialog, QSpinBox, QDoubleSpinBox, QCheckBox,
    QColorDialog, QDialogButtonBox, QFormLayout, QFontComboBox
)
from PySide6.QtGui import (
    QAction, QActionGroup, QKeySequence, QShortcut, QFont, QFontDatabase,
    QPixmap, QImage, QPainter, QIcon, QColor, QCursor
)
from PySide6.QtCore import (
    Qt, QTimer, QBuffer, QByteArray, QPoint, QSettings, Signal, QSize,
    QPropertyAnimation, QEasingCurve, QRect
)
from PySide6.QtSvg import QSvgRenderer

locale.setlocale(locale.LC_NUMERIC, 'C')


# ==================================================================
# Colors
# ==================================================================

BG          = "#0B0A0F"
PRIMARY     = "#6EE7B7"
ON_PRIMARY  = "#064E3B"
WHITE       = "#FFFFFF"
TEXT        = "#E8E2F0"
TEXT_DIM    = "#C8BFD8"
SURFACE_HI  = "#181624"
SURFACE_TOP = "#221F30"
OUTLINE     = "#3D3650"

TITLE_H   = 38
CONTROL_H = 60

RESUME_MIN_DURATION = 60
RESUME_MIN_POS      = 10
RESUME_END_MARGIN   = 10

HDR_MODES = ('auto', 'on', 'off')

MAX_RECENT_FILES = 10


# ==================================================================
# Logo
# ==================================================================

LOGO_SVG = """<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <rect width="64" height="64" rx="14" fill="#0B0A0F"/>
  <path d="M18 21 L18 43 L34 32 Z" fill="#A78BFA" opacity="0.45"/>
  <path d="M28 17 L28 47 L48 32 Z" fill="#6EE7B7"/>
</svg>"""


# ==================================================================
# Assets
# ==================================================================

ASSETS_DIR = os.path.join(base_dir, 'assets')
FONTS_DIR = os.path.join(ASSETS_DIR, 'fonts')
ICON_PATH = os.path.join(ASSETS_DIR, 'icon.ico')


def custom_fonts_dir() -> str:
    """Folder where user-loaded custom fonts live."""
    path = os.path.join(
        os.environ.get('LOCALAPPDATA', os.path.expanduser('~')),
        'Chalchitra', 'fonts'
    )
    os.makedirs(path, exist_ok=True)
    return path


def load_fonts():
    # Bundled fonts
    if os.path.isdir(FONTS_DIR):
        for fn in os.listdir(FONTS_DIR):
            if fn.lower().endswith(('.ttf', '.otf')):
                QFontDatabase.addApplicationFont(os.path.join(FONTS_DIR, fn))

    # User's custom fonts
    cdir = custom_fonts_dir()
    for fn in os.listdir(cdir):
        if fn.lower().endswith(('.ttf', '.otf')):
            QFontDatabase.addApplicationFont(os.path.join(cdir, fn))


def font_available(family):
    return family in QFontDatabase.families()


def make_icon_font(size=20):
    f = QFont("Material Symbols Outlined")
    f.setPixelSize(size)
    return f


# ==================================================================
# Volume curve
# ==================================================================

def slider_to_mpv_volume(slider_val: int) -> float:
    if slider_val <= 0:
        return 0.0
    if slider_val <= 100:
        return 100.0 * (slider_val / 100.0) ** 0.5
    return float(slider_val)


def mpv_to_slider_volume(mpv_val) -> int:
    if mpv_val is None or mpv_val <= 0:
        return 0
    if mpv_val <= 100:
        return int(round(100.0 * (mpv_val / 100.0) ** 2))
    return int(round(mpv_val))


# ==================================================================
# Settings
# ==================================================================

def make_settings():
    config_dir = os.path.join(
        os.environ.get('LOCALAPPDATA', os.path.expanduser('~')),
        'Chalchitra'
    )
    os.makedirs(config_dir, exist_ok=True)
    return QSettings(os.path.join(config_dir, 'settings.ini'), QSettings.IniFormat)


DEFAULT_SUB = {
    'font': 'Roboto',
    'size': 55,
    'bold': False,
    'color': '#FFFFFF',
    'outline_color': '#000000',
    'outline_size': 3.0,
}


# ==================================================================
# SVG helpers
# ==================================================================

def render_svg_pixmap(svg, size):
    renderer = QSvgRenderer(QByteArray(svg.encode('utf-8')))
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    renderer.render(p)
    p.end()
    return pm


def render_svg_image(svg, size):
    renderer = QSvgRenderer(QByteArray(svg.encode('utf-8')))
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    renderer.render(p)
    p.end()
    return img


def render_material_icon(name, size, color):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.TextAntialiasing)
    f = QFont("Material Symbols Outlined")
    f.setPixelSize(int(size * 0.78))
    p.setFont(f)
    p.setPen(QColor(color))
    p.drawText(pm.rect(), Qt.AlignCenter, name)
    p.end()
    return pm


def ensure_icon():
    if os.path.exists(ICON_PATH):
        return ICON_PATH
    try:
        from PIL import Image
        import io
        os.makedirs(ASSETS_DIR, exist_ok=True)
        img = render_svg_image(LOGO_SVG, 256)
        buf = QBuffer()
        buf.open(QBuffer.WriteOnly)
        img.save(buf, "PNG")
        png_bytes = bytes(buf.data())
        buf.close()
        pil = Image.open(io.BytesIO(png_bytes))
        pil.save(ICON_PATH, format='ICO',
                 sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        return ICON_PATH
    except Exception as e:
        print(f"Icon generation skipped: {e}")
        return None


# ==================================================================
# Stylesheet
# ==================================================================

STYLESHEET = f"""
#ChalchitraRoot {{ background: {BG}; }}
QWidget {{ color: {TEXT}; font-size: 13px; }}

QPushButton#WinBtn {{
    background: transparent; color: {TEXT_DIM}; border: none; padding: 0;
}}
QPushButton#WinBtn:hover {{ background: {SURFACE_HI}; color: {WHITE}; }}
QPushButton#WinBtn:pressed {{ background: {SURFACE_TOP}; }}

QPushButton#CloseBtn {{
    background: transparent; color: {TEXT_DIM}; border: none; padding: 0;
}}
QPushButton#CloseBtn:hover {{ background: {PRIMARY}; color: {ON_PRIMARY}; }}
QPushButton#CloseBtn:pressed {{ background: {ON_PRIMARY}; color: {PRIMARY}; }}

QMenu {{
    background: {SURFACE_HI}; color: {TEXT};
    border: 1px solid {OUTLINE}; padding: 4px;
}}
QMenu::item {{ padding: 6px 24px 6px 12px; min-width: 200px; }}
QMenu::item:selected {{ background: {PRIMARY}; color: {ON_PRIMARY}; }}
QMenu::item:disabled {{ color: {OUTLINE}; }}
QMenu::separator {{ height: 1px; background: {OUTLINE}; margin: 4px 6px; }}

QPushButton#PlayerBtn {{
    background: transparent; color: {TEXT_DIM}; border: none; padding: 0;
}}
QPushButton#PlayerBtn:hover {{ color: {PRIMARY}; }}
QPushButton#PlayerBtn:pressed {{ color: {WHITE}; }}
QPushButton#PlayerBtn:disabled {{ color: {OUTLINE}; }}

QSlider#seekSlider::groove:horizontal {{
    height: 2px; background: {OUTLINE}; border-radius: 1px;
}}
QSlider#seekSlider::sub-page:horizontal {{
    background: {PRIMARY}; border-radius: 1px;
}}
QSlider#seekSlider::add-page:horizontal {{
    background: {OUTLINE}; border-radius: 1px;
}}
QSlider#seekSlider::handle:horizontal {{
    background: {WHITE}; width: 11px; height: 11px;
    margin: -5px 0; border-radius: 5px;
}}
QSlider#seekSlider::handle:horizontal:hover {{ background: {PRIMARY}; }}

QSlider#volumeSlider::groove:horizontal {{
    height: 2px; background: {OUTLINE}; border-radius: 1px;
}}
QSlider#volumeSlider::sub-page:horizontal {{
    background: {PRIMARY}; border-radius: 1px;
}}
QSlider#volumeSlider::add-page:horizontal {{
    background: {OUTLINE}; border-radius: 1px;
}}
QSlider#volumeSlider::handle:horizontal {{
    background: {WHITE}; width: 9px; height: 9px;
    margin: -4px 0; border-radius: 4px;
}}
QSlider#volumeSlider::handle:horizontal:hover {{ background: {PRIMARY}; }}

#TimeLabel {{ color: {TEXT_DIM}; font-size: 12px; }}

QDialog {{ background: {BG}; color: {TEXT}; }}
QDialog QLabel {{ color: {TEXT_DIM}; }}
QDialog QComboBox, QDialog QSpinBox, QDialog QDoubleSpinBox {{
    background: {SURFACE_HI}; color: {TEXT};
    border: 1px solid {OUTLINE}; border-radius: 6px;
    padding: 5px 8px; min-height: 22px;
}}
QDialog QComboBox:hover, QDialog QSpinBox:hover, QDialog QDoubleSpinBox:hover {{
    border-color: {PRIMARY};
}}
QDialog QComboBox::drop-down {{ border: none; width: 20px; }}
QDialog QComboBox QAbstractItemView {{
    background: {SURFACE_HI}; color: {TEXT};
    selection-background-color: {PRIMARY}; selection-color: {ON_PRIMARY};
    border: 1px solid {OUTLINE};
}}

/* Bigger, easier-to-click spinbox arrows with visible arrow glyphs */
QDialog QSpinBox::up-button, QDialog QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 24px;
    height: 14px;
    background: {SURFACE_TOP};
    border-left: 1px solid {OUTLINE};
    border-top-right-radius: 6px;
}}
QDialog QSpinBox::down-button, QDialog QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 24px;
    height: 14px;
    background: {SURFACE_TOP};
    border-left: 1px solid {OUTLINE};
    border-bottom-right-radius: 6px;
}}
QDialog QSpinBox::up-button:hover, QDialog QDoubleSpinBox::up-button:hover,
QDialog QSpinBox::down-button:hover, QDialog QDoubleSpinBox::down-button:hover {{
    background: {PRIMARY};
}}
QDialog QSpinBox::up-arrow, QDialog QDoubleSpinBox::up-arrow {{
    image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 8 8'><path d='M4 1 L7 6 L1 6 Z' fill='%23E8E2F0'/></svg>");
    width: 8px;
    height: 8px;
}}
QDialog QSpinBox::down-arrow, QDialog QDoubleSpinBox::down-arrow {{
    image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 8 8'><path d='M4 7 L1 2 L7 2 Z' fill='%23E8E2F0'/></svg>");
    width: 8px;
    height: 8px;
}}

QDialog QCheckBox {{ color: {TEXT_DIM}; }}
QDialog QCheckBox::indicator {{
    width: 16px; height: 16px;
    border: 1px solid {OUTLINE}; border-radius: 4px;
    background: {SURFACE_HI};
}}
QDialog QCheckBox::indicator:checked {{
    background: {PRIMARY}; border-color: {PRIMARY};
}}
QDialog QPushButton {{
    background: {SURFACE_HI}; color: {TEXT};
    border: 1px solid {OUTLINE}; border-radius: 6px;
    padding: 6px 16px; min-width: 70px;
}}
QDialog QPushButton:hover {{ border-color: {PRIMARY}; color: {PRIMARY}; }}
QDialog QPushButton:pressed {{ background: {SURFACE_TOP}; }}
"""


# ==================================================================
# Helpers
# ==================================================================

def format_time(seconds):
    if seconds is None or seconds < 0:
        seconds = 0
    s = int(seconds)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{h}:{m:02d}:{s:02d}" if h > 0 else f"{m}:{s:02d}"


def format_speed(s):
    if s == int(s):
        return f"{int(s)}×"
    return f"{s:g}×"


def format_delay(d):
    if d is None:
        d = 0
    return f"{d:+.2f}s" if abs(d) > 0.001 else "0.00s"


class SeekSlider(QSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            val = QStyle.sliderValueFromPosition(
                self.minimum(), self.maximum(),
                int(event.position().x()), self.width()
            )
            self.setValue(val)
            self.sliderMoved.emit(val)
        super().mousePressEvent(event)


# ==================================================================
# Video surface
# ==================================================================

class VideoSurface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_NativeWindow)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAutoFillBackground(False)
        self._idle = True

    def set_playing(self, playing: bool):
        self._idle = not playing
        self.update()

    def paintEvent(self, event):
        if not self._idle:
            return
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#000000"))
        p.end()


# ==================================================================
# Welcome overlay
# ==================================================================

class WelcomeOverlay(QWidget):
    import_requested = Signal()
    files_dropped = Signal(list)

    def __init__(self, logo_pixmap, icon_available, parent=None):
        super().__init__(parent)
        self.setObjectName("WelcomeOverlay")
        self.setStyleSheet(f"#WelcomeOverlay {{ background: {BG}; }}")
        self.setAcceptDrops(True)
        self.setAttribute(Qt.WA_NativeWindow)

        v = QVBoxLayout(self)
        v.setContentsMargins(24, 24, 24, 24)
        v.setSpacing(0)
        v.addStretch(1)

        if logo_pixmap is not None:
            logo = QLabel()
            logo.setPixmap(logo_pixmap)
            logo.setFixedSize(96, 96)
            logo.setAlignment(Qt.AlignCenter)
            logo.setStyleSheet("background: transparent;")
            v.addWidget(logo, alignment=Qt.AlignHCenter)
            v.addSpacing(20)

        title = QLabel("Chalchitra")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"color: {TEXT}; font-size: 26px; font-weight: 500; "
            f"letter-spacing: 0.5px; background: transparent;"
        )
        v.addWidget(title)
        v.addSpacing(4)

        sub = QLabel("by AirSilo")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(
            f"color: {TEXT_DIM}; font-size: 12px; background: transparent;"
        )
        v.addWidget(sub)

        v.addSpacing(32)

        self.import_btn = QPushButton("Import Media")
        self.import_btn.setCursor(Qt.PointingHandCursor)
        self.import_btn.setFixedHeight(44)
        self.import_btn.setMinimumWidth(190)
        if icon_available:
            self.import_btn.setIcon(QIcon(
                render_material_icon("add", 20, ON_PRIMARY)
            ))
            self.import_btn.setIconSize(QSize(20, 20))
        self.import_btn.setStyleSheet(f"""
            QPushButton {{
                background: {PRIMARY};
                color: {ON_PRIMARY};
                border: none;
                border-radius: 22px;
                font-size: 14px;
                font-weight: 600;
                padding: 0 26px;
            }}
            QPushButton:hover {{ background: {WHITE}; }}
            QPushButton:pressed {{ background: {ON_PRIMARY}; color: {PRIMARY}; }}
        """)
        self.import_btn.clicked.connect(self.import_requested.emit)
        v.addWidget(self.import_btn, alignment=Qt.AlignHCenter)

        v.addSpacing(20)

        hint = QLabel("or drag & drop video files anywhere")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(
            f"color: {OUTLINE}; font-size: 11px; background: transparent;"
        )
        v.addWidget(hint)

        v.addStretch(1)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [u.toLocalFile() for u in event.mimeData().urls()
                 if os.path.isfile(u.toLocalFile())]
        if paths:
            self.files_dropped.emit(paths)


# ==================================================================
# Subtitle settings dialog
# ==================================================================

class SubtitleSettingsDialog(QDialog):
    def __init__(self, parent, current: dict):
        super().__init__(parent)
        self.setWindowTitle("Subtitle Settings")
        self.setModal(True)
        self.setMinimumWidth(480)
        self._fonts_changed = False

        self.text_color = QColor(current.get('color', '#FFFFFF'))
        self.outline_color = QColor(current.get('outline_color', '#000000'))

        form = QFormLayout(self)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        form.setVerticalSpacing(10)
        form.setContentsMargins(16, 16, 16, 16)

        # --- Font family row: combo + "Load Font…" button ---
        font_row = QWidget()
        font_row.setStyleSheet("background: transparent;")
        font_row_layout = QHBoxLayout(font_row)
        font_row_layout.setContentsMargins(0, 0, 0, 0)
        font_row_layout.setSpacing(6)

        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont(current.get('font', 'Roboto')))
        font_row_layout.addWidget(self.font_combo, stretch=1)

        self.add_font_btn = QPushButton("Load Font…")
        self.add_font_btn.setToolTip("Load a custom .ttf or .otf font")
        self.add_font_btn.setFixedHeight(30)
        self.add_font_btn.setStyleSheet(f"""
            QPushButton {{
                background: {SURFACE_HI}; color: {TEXT};
                border: 1px solid {OUTLINE}; border-radius: 6px;
                padding: 4px 12px; font-size: 12px;
                min-width: 90px;
            }}
            QPushButton:hover {{ border-color: {PRIMARY}; color: {PRIMARY}; }}
            QPushButton:pressed {{ background: {SURFACE_TOP}; }}
        """)
        self.add_font_btn.clicked.connect(self._load_custom_font)
        font_row_layout.addWidget(self.add_font_btn)

        form.addRow("Font family", font_row)

        # --- Font size ---
        self.size_spin = QSpinBox()
        self.size_spin.setRange(10, 200)
        self.size_spin.setValue(int(current.get('size', 55)))
        form.addRow("Font size", self.size_spin)

        # --- Bold ---
        self.bold_check = QCheckBox("Bold")
        self.bold_check.setChecked(bool(current.get('bold', False)))
        form.addRow("", self.bold_check)

        # --- Text color ---
        self.text_color_btn = QPushButton()
        self._refresh_color_btn(self.text_color_btn, self.text_color)
        self.text_color_btn.clicked.connect(self._pick_text)
        form.addRow("Text color", self.text_color_btn)

        # --- Outline color ---
        self.outline_btn = QPushButton()
        self._refresh_color_btn(self.outline_btn, self.outline_color)
        self.outline_btn.clicked.connect(self._pick_outline)
        form.addRow("Outline color", self.outline_btn)

        # --- Outline size ---
        self.outline_size = QDoubleSpinBox()
        self.outline_size.setRange(0.0, 10.0)
        self.outline_size.setSingleStep(0.5)
        self.outline_size.setValue(float(current.get('outline_size', 3.0)))
        form.addRow("Outline size", self.outline_size)

        # --- Preview ---
        self.preview = QLabel("Chalchitra — subtitle preview")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumHeight(80)
        form.addRow("Preview", self.preview)

        # --- Buttons: Reset to Default | OK | Cancel ---
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        self.reset_btn = buttons.addButton(
            "Reset to Default", QDialogButtonBox.ButtonRole.ResetRole
        )
        self.reset_btn.setToolTip("Restore all subtitle settings to defaults")
        self.reset_btn.clicked.connect(self._reset_to_default)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

        # Live preview
        self.font_combo.currentFontChanged.connect(self._update_preview)
        self.size_spin.valueChanged.connect(self._update_preview)
        self.bold_check.toggled.connect(self._update_preview)
        self.outline_size.valueChanged.connect(self._update_preview)

        self._update_preview()

    # ---- Reset to defaults ----
    def _reset_to_default(self):
        self.font_combo.setCurrentFont(QFont(DEFAULT_SUB['font']))
        self.size_spin.setValue(int(DEFAULT_SUB['size']))
        self.bold_check.setChecked(bool(DEFAULT_SUB['bold']))

        self.text_color = QColor(DEFAULT_SUB['color'])
        self._refresh_color_btn(self.text_color_btn, self.text_color)

        self.outline_color = QColor(DEFAULT_SUB['outline_color'])
        self._refresh_color_btn(self.outline_btn, self.outline_color)

        self.outline_size.setValue(float(DEFAULT_SUB['outline_size']))
        self._update_preview()

    # ---- Custom font loader ----
    def _load_custom_font(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Custom Font", "",
            "Font Files (*.ttf *.otf);;All Files (*.*)"
        )
        if not path:
            return

        cdir = custom_fonts_dir()
        dest = os.path.join(cdir, os.path.basename(path))

        try:
            import shutil
            if os.path.abspath(path) != os.path.abspath(dest):
                shutil.copy2(path, dest)
        except Exception as e:
            print(f"Could not copy font: {e}")
            return

        fid = QFontDatabase.addApplicationFont(dest)
        if fid == -1:
            print(f"Failed to register font: {dest}")
            return

        families = QFontDatabase.applicationFontFamilies(fid)
        if families:
            new_family = families[0]
            self.font_combo.setCurrentFont(QFont(new_family))
            self._fonts_changed = True
            print(f"Loaded custom font: {new_family}")

    def fonts_changed(self) -> bool:
        return self._fonts_changed

    def _refresh_color_btn(self, btn, color: QColor):
        r, g, b, a = color.getRgb()
        fg = '#000' if (r * 0.299 + g * 0.587 + b * 0.114) > 128 else '#fff'
        btn.setText(color.name().upper())
        btn.setStyleSheet(
            f"background: {color.name()}; color: {fg};"
            f"border: 1px solid {OUTLINE}; border-radius: 6px;"
            f"padding: 6px 16px; min-height: 22px;"
        )

    def _pick_text(self):
        c = QColorDialog.getColor(self.text_color, self, "Text Color")
        if c.isValid():
            self.text_color = c
            self._refresh_color_btn(self.text_color_btn, c)
            self._update_preview()

    def _pick_outline(self):
        c = QColorDialog.getColor(self.outline_color, self, "Outline Color")
        if c.isValid():
            self.outline_color = c
            self._refresh_color_btn(self.outline_btn, c)
            self._update_preview()

    def _update_preview(self):
        f = self.font_combo.currentFont()
        f.setPointSize(16)
        f.setBold(self.bold_check.isChecked())
        self.preview.setFont(f)

        tc = self.text_color.name()
        oc = self.outline_color.name()
        ow = max(1, int(self.outline_size.value()))
        self.preview.setStyleSheet(
            f"color: {tc};"
            f"background: #000000;"
            f"padding: 10px;"
            f"border: 1px solid {OUTLINE};"
            f"border-radius: 6px;"
            f"text-shadow: "
            f"{-ow}px 0 {oc}, {ow}px 0 {oc}, 0 {-ow}px {oc}, 0 {ow}px {oc};"
        )

    def get_values(self) -> dict:
        return {
            'font': self.font_combo.currentFont().family(),
            'size': self.size_spin.value(),
            'bold': self.bold_check.isChecked(),
            'color': self.text_color.name(),
            'outline_color': self.outline_color.name(),
            'outline_size': self.outline_size.value(),
        }


# ==================================================================
# About dialog
# ==================================================================

class AboutDialog(QDialog):
    def __init__(self, parent=None, icon_available=False):
        super().__init__(parent)
        self.setWindowTitle("About Chalchitra")
        self.setModal(True)
        self.setFixedWidth(440)
        self.setStyleSheet(f"QDialog {{ background: {BG}; }}")

        v = QVBoxLayout(self)
        v.setContentsMargins(24, 22, 24, 20)
        v.setSpacing(0)

        # ---- Logo ----
        logo_pm = render_svg_pixmap(LOGO_SVG, 128)
        logo_pm.setDevicePixelRatio(2.0)
        logo = QLabel()
        logo.setPixmap(logo_pm)
        logo.setFixedSize(64, 64)
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("background: transparent;")
        v.addWidget(logo, alignment=Qt.AlignHCenter)
        v.addSpacing(12)

        # ---- Name ----
        name = QLabel("Chalchitra")
        name.setAlignment(Qt.AlignCenter)
        name.setStyleSheet(
            f"color: {TEXT}; font-size: 22px; font-weight: 600; "
            f"letter-spacing: 0.3px; background: transparent;"
        )
        v.addWidget(name)
        v.addSpacing(4)

        # ---- Tagline ----
        tagline = QLabel("A minimal, fully offline media player")
        tagline.setAlignment(Qt.AlignCenter)
        tagline.setStyleSheet(
            f"color: {TEXT_DIM}; font-size: 12px; background: transparent;"
        )
        v.addWidget(tagline)
        v.addSpacing(16)

        # ---- Info block ----
        info = QLabel(
            "<div style='line-height: 1.7;'>"
            f"<span style='color:{TEXT_DIM};'>Developed by</span> "
            f"<span style='color:{PRIMARY}; font-weight:600;'>AirSilo</span><br>"
            f"<span style='color:{TEXT_DIM};'>Website</span> "
            f"<a href='https://airsilo.space' style='color:{PRIMARY}; text-decoration:none;'>https://airsilo.space</a><br>"
            f"<span style='color:{TEXT_DIM};'>Licence</span> "
            f"<span style='color:{TEXT};'>GNU General Public License v3.0</span><br>"
            f"<span style='color:{TEXT_DIM};'>Playback engine</span> "
            f"<span style='color:{TEXT};'>mpv (libmpv)</span><br>"
            f"<span style='color:{TEXT_DIM};'>UI toolkit</span> "
            f"<span style='color:{TEXT};'>Qt 6 (PySide6)</span><br>"
            f"<span style='color:{TEXT_DIM};'>Version</span> "
            f"<span style='color:{TEXT};'>1.0.0</span>"
            "</div>"
        )
        info.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        info.setOpenExternalLinks(True)
        info.setTextFormat(Qt.RichText)
        info.setStyleSheet(f"background: transparent; font-size: 12px;")
        info.setContentsMargins(0, 0, 0, 0)

        info_wrap = QWidget()
        info_wrap.setStyleSheet(
            f"background: {SURFACE_HI}; border: 1px solid {OUTLINE}; "
            f"border-radius: 8px;"
        )
        wrap_layout = QVBoxLayout(info_wrap)
        wrap_layout.setContentsMargins(16, 14, 16, 14)
        wrap_layout.addWidget(info)
        v.addWidget(info_wrap)
        v.addSpacing(16)

        # ---- Legal note ----
        legal = QLabel(
            "This software is free and open source. "
            "It contains no telemetry, no analytics, and never connects to the internet."
        )
        legal.setWordWrap(True)
        legal.setAlignment(Qt.AlignCenter)
        legal.setStyleSheet(
            f"color: {OUTLINE}; font-size: 11px; background: transparent;"
        )
        v.addWidget(legal)
        v.addSpacing(18)

        # ---- Close button ----
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(32)
        close_btn.setMinimumWidth(90)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {PRIMARY}; color: {ON_PRIMARY};
                border: none; border-radius: 16px;
                padding: 0 20px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {WHITE}; }}
            QPushButton:pressed {{ background: {ON_PRIMARY}; color: {PRIMARY}; }}
        """)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        v.addLayout(btn_row)


# ==================================================================
# Title bar
# ==================================================================

class TitleBar(QWidget):
    def __init__(self, window, logo_pixmap, icon_available):
        super().__init__(window)
        self.window = window
        self.icon_available = icon_available
        self.setObjectName("TitleBar")
        self.setAttribute(Qt.WA_NativeWindow)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setAutoFillBackground(False)

        self._drag_press = None
        self._drag_window_start = None
        self._was_maximized_on_press = False

        h = QHBoxLayout(self)
        h.setContentsMargins(10, 0, 0, 0)
        h.setSpacing(8)

        if logo_pixmap is not None:
            logo = QLabel()
            logo.setPixmap(logo_pixmap)
            logo.setFixedSize(22, 22)
            logo.setStyleSheet("background: transparent;")
            h.addWidget(logo)

        self.title_label = QLabel("Chalchitra")
        self.title_label.setObjectName("TitleLabel")
        self.title_label.setStyleSheet(
            f"color: {TEXT_DIM}; font-size: 12px; font-weight: 500;"
            f"background: transparent;"
        )
        h.addWidget(self.title_label)
        h.addStretch(1)

        self.menu_btn = self._win_button("menu", "☰", "Menu", 18)
        self.menu_btn.clicked.connect(self._open_menu)
        h.addWidget(self.menu_btn)

        # Info / About button
        self.about_btn = self._win_button("info", "i", "About Chalchitra", 18)
        self.about_btn.clicked.connect(self.window._open_about_dialog)
        h.addWidget(self.about_btn)

        self.min_btn = self._win_button("remove", "—", "Minimize", 16)
        self.min_btn.clicked.connect(self.window.showMinimized)
        h.addWidget(self.min_btn)

        self.max_btn = self._win_button("crop_square", "□", "Maximize", 14)
        self.max_btn.clicked.connect(self.window._toggle_maximize)
        h.addWidget(self.max_btn)

        self.close_btn = self._win_button("close", "×", "Close", 16, is_close=True)
        self.close_btn.clicked.connect(self.window.close)
        h.addWidget(self.close_btn)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(BG))
        p.end()

    def _win_button(self, icon_name, fallback, tooltip, font_size, is_close=False):
        btn = QPushButton(icon_name if self.icon_available else fallback)
        btn.setObjectName("CloseBtn" if is_close else "WinBtn")
        btn.setToolTip(tooltip)
        btn.setFixedSize(46 if is_close else 42, TITLE_H)
        if self.icon_available:
            btn.setFont(make_icon_font(font_size))
        return btn

    def _open_menu(self):
        menu = QMenu(self)
        a = menu.addAction("Open File…")
        a.setShortcut("Ctrl+O")
        a.triggered.connect(self.window._open_file_dialog)
        menu.addSeparator()
        a = menu.addAction("Subtitle Settings…")
        a.setShortcut("Shift+V")
        a.triggered.connect(self.window._open_subtitle_settings)
        menu.addSeparator()

        resume_act = menu.addAction("Remember playback position")
        resume_act.setCheckable(True)
        resume_act.setChecked(
            self.window.settings.value("playback/resume_enabled", True, type=bool)
        )
        resume_act.triggered.connect(self.window._toggle_resume_enabled)

        menu.addSeparator()
        about_act = menu.addAction("About Chalchitra")
        about_act.triggered.connect(self.window._open_about_dialog)
        menu.addSeparator()

        a = menu.addAction("Quit")
        a.setShortcut("Ctrl+Q")
        a.triggered.connect(self.window.close)
        pos = self.menu_btn.mapToGlobal(QPoint(0, self.menu_btn.height()))
        menu.exec(pos)

    def set_title(self, text):
        self.title_label.setText(text)

    def set_maximized(self, is_max):
        if self.icon_available:
            self.max_btn.setText("filter_none" if is_max else "crop_square")
        else:
            self.max_btn.setText("❐" if is_max else "□")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_press = event.globalPosition().toPoint()
            self._drag_window_start = self.window.frameGeometry().topLeft()
            self._was_maximized_on_press = self.window._is_maximized
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_press is None:
            return
        if not (event.buttons() & Qt.LeftButton):
            return
        current = event.globalPosition().toPoint()
        delta = current - self._drag_press
        if self._was_maximized_on_press:
            if abs(delta.x()) < 6 and abs(delta.y()) < 6:
                return
            self.window._restore_from_max()
            self._was_maximized_on_press = False
            self._drag_press = current
            self._drag_window_start = self.window.frameGeometry().topLeft()
            return
        self.window.move(self._drag_window_start + delta)
        event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_press = None
        self._drag_window_start = None
        self._was_maximized_on_press = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.window._toggle_maximize()
            event.accept()


# ==================================================================
# Control bar
# ==================================================================

class ControlBar(QWidget):
    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(BG))
        p.end()


# ==================================================================
# Main window
# ==================================================================

class ChalchitraWindow(QWidget):
    context_menu_requested = Signal()

    def __init__(self, icon_available, settings: QSettings):
        super().__init__()
        self.setObjectName("ChalchitraRoot")
        self.setWindowTitle("Chalchitra")
        self.resize(1280, 720)
        self.setMinimumSize(720, 420)
        self.setAcceptDrops(True)

        self.icon_available = icon_available
        self.settings = settings
        self._current_file = None
        self._is_maximized = False
        self._normal_geometry = None
        self._speed = float(settings.value("playback/speed", 1.0))

        # Resume
        self._pending_resume = None
        self._save_counter = 0
        self._pending_eof_clear = False

        # HDR mode
        hdr = settings.value("playback/hdr_mode", "auto", type=str)
        self._hdr_mode = hdr if hdr in HDR_MODES else "auto"

        self._playlist = []
        self._playlist_index = -1

        self._last_cursor_pos = None
        self._last_activity = 0.0
        self._bars_visible = True
        self._last_toggle_time = 0.0
        self._cursor_hidden = False

        # --- Window state: READ only, do NOT apply in __init__ ---
        # (Applying geometry before the video surface exists corrupts some videos.)
        self._start_maximized = settings.value("window/maximized", False, type=bool)
        self._start_x = settings.value("window/x", None, type=int)
        self._start_y = settings.value("window/y", None, type=int)
        self._start_w = settings.value("window/w", None, type=int)
        self._start_h = settings.value("window/h", None, type=int)

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        # ---- Native children ----
        self.video_container = VideoSurface(self)

        welcome_logo = render_svg_pixmap(LOGO_SVG, 192)
        welcome_logo.setDevicePixelRatio(2.0)
        self.welcome_page = WelcomeOverlay(welcome_logo, icon_available, parent=self)
        self.welcome_page.import_requested.connect(self._open_file_dialog)
        self.welcome_page.files_dropped.connect(self._load_files)

        logo_pixmap = render_svg_pixmap(LOGO_SVG, 44)
        logo_pixmap.setDevicePixelRatio(2.0)
        self.title_bar = TitleBar(self, logo_pixmap, icon_available)

        self.control_bar = self._build_control_bar()

        self._size_grip = QSizeGrip(self)
        self._size_grip.setFixedSize(16, 16)

        # ---- Animations ----
        self._anim_title = QPropertyAnimation(self.title_bar, b"geometry", self)
        self._anim_title.setDuration(220)
        self._anim_title.setEasingCurve(QEasingCurve.OutCubic)
        self._anim_title.finished.connect(self._after_title_anim)

        self._anim_control = QPropertyAnimation(self.control_bar, b"geometry", self)
        self._anim_control.setDuration(220)
        self._anim_control.setEasingCurve(QEasingCurve.OutCubic)
        self._anim_control.finished.connect(self._after_control_anim)

        self._cursor_timer = QTimer(self)
        self._cursor_timer.setInterval(80)
        self._cursor_timer.timeout.connect(self._check_cursor_fullscreen)

        self._create_shortcuts()
        self._set_controls_enabled(False)

        self._ui_timer = QTimer(self)
        self._ui_timer.setInterval(250)
        self._ui_timer.timeout.connect(self._update_ui)
        self._ui_timer.start()

        self.context_menu_requested.connect(self._show_workspace_context_menu)

        self.show_welcome(True)
        QTimer.singleShot(0, self._layout_children)
        QTimer.singleShot(0, self._init_player)
        # Geometry is restored later, from __main__ (after mpv has settled)

    # ==============================================================
    # Window geometry persistence (SAFE — deferred)
    # ==============================================================

    def _apply_startup_window_state(self):
        """
        Applies the saved window geometry/maximize state.
        Called from __main__ AFTER mpv has fully initialized, so the
        video surface's native window handle is already stable.
        """
        # --- Maximize path ---
        if self._start_maximized:
            self._normal_geometry = self.geometry()
            self.showMaximized()
            self._is_maximized = True
            self.title_bar.set_maximized(True)
            self._size_grip.setVisible(False)
            self._layout_children()
            return

        # --- Normal geometry path ---
        if None in (self._start_x, self._start_y, self._start_w, self._start_h):
            return
        if self._start_w < 720 or self._start_h < 420:
            return

        rect = QRect(self._start_x, self._start_y,
                     self._start_w, self._start_h)

        # Verify the target rectangle overlaps a real screen
        try:
            for screen in QApplication.screens():
                if screen.availableGeometry().intersects(rect):
                    self.setGeometry(rect)
                    self._layout_children()
                    return
        except Exception as e:
            print(f"Could not apply window geometry: {e}")

    def _save_window_geometry(self):
        """Persist geometry + maximize state. Skips saving while in fullscreen."""
        if self.isFullScreen():
            return

        if self._is_maximized and self._normal_geometry is not None:
            g = self._normal_geometry
        else:
            g = self.geometry()

        self.settings.setValue("window/x", g.x())
        self.settings.setValue("window/y", g.y())
        self.settings.setValue("window/w", g.width())
        self.settings.setValue("window/h", g.height())
        self.settings.setValue("window/maximized", self._is_maximized)

    # ==============================================================
    # Resume helpers
    # ==============================================================

    def _resume_enabled(self) -> bool:
        return self.settings.value("playback/resume_enabled", True, type=bool)

    def _resume_key(self, path: str) -> str:
        try:
            st = os.stat(path)
            sig = f"{os.path.abspath(path).lower()}|{st.st_size}|{int(st.st_mtime)}"
        except OSError:
            sig = os.path.abspath(path).lower()
        return hashlib.md5(sig.encode('utf-8')).hexdigest()

    def _get_resume_position(self, path: str):
        if not self._resume_enabled() or not path:
            return None
        key = f"resume/pos/{self._resume_key(path)}"
        try:
            pos = self.settings.value(key, None, type=float)
        except Exception:
            return None
        return pos if pos and pos > 0 else None

    def _save_resume_position(self, path, pos, dur):
        if not self._resume_enabled() or not path:
            return
        if pos is None or dur is None or dur <= 0:
            return
        if dur < RESUME_MIN_DURATION:
            return
        if pos < RESUME_MIN_POS:
            return
        if pos > dur - RESUME_END_MARGIN:
            return
        key = f"resume/pos/{self._resume_key(path)}"
        self.settings.setValue(key, float(pos))
        self.settings.setValue("resume/last_path", path)

    def _clear_resume_position(self, path: str):
        if not path:
            return
        key = f"resume/pos/{self._resume_key(path)}"
        try:
            self.settings.remove(key)
        except Exception:
            pass

    def _save_current_position(self):
        if self._pending_resume is not None:
            return
        if not self._current_file or not hasattr(self, 'player'):
            return
        try:
            if self.player.idle_active:
                return
            pos = self.player.time_pos
            dur = self.player.duration
        except Exception:
            return
        self._save_resume_position(self._current_file, pos, dur)

    def _toggle_resume_enabled(self, checked: bool):
        self.settings.setValue("playback/resume_enabled", bool(checked))
        if not checked and self._current_file:
            self._clear_resume_position(self._current_file)

    # ==============================================================
    # Last import folder
    # ==============================================================

    def _last_folder(self) -> str:
        folder = self.settings.value("playback/last_folder", "", type=str)
        if folder and os.path.isdir(folder):
            return folder
        return ""

    def _remember_folder(self, path: str):
        if not path:
            return
        folder = os.path.dirname(os.path.abspath(path))
        if os.path.isdir(folder):
            self.settings.setValue("playback/last_folder", folder)

    # ==============================================================
    # Recent files
    # ==============================================================

    def _load_recent_files(self):
        val = self.settings.value("recent/files", [], type=list)
        if not isinstance(val, list):
            return []
        return [p for p in val if isinstance(p, str) and os.path.isfile(p)]

    def _add_recent_file(self, path: str):
        if not path or not os.path.isfile(path):
            return
        path = os.path.abspath(path)
        recent = self._load_recent_files()
        lower = path.lower()
        recent = [p for p in recent if p.lower() != lower]
        recent.insert(0, path)
        recent = recent[:MAX_RECENT_FILES]
        self.settings.setValue("recent/files", recent)

    def _clear_recent_files(self):
        self.settings.setValue("recent/files", [])

    def _open_recent_file(self, path: str):
        if os.path.isfile(path):
            self._load_files([path])

    # ==============================================================
    # HDR helpers
    # ==============================================================

    def _hdr_icon(self):
        if self._hdr_mode == 'on':
            return ("hdr_on", "HDR")
        if self._hdr_mode == 'off':
            return ("hdr_off", "HDR")
        return ("hdr_auto", "HDR")

    def _hdr_label(self):
        return {'auto': "Auto", 'on': "On (passthrough)", 'off': "Off (tone map)"}[self._hdr_mode]

    def _apply_hdr_mode(self, mode: str):
        if mode not in HDR_MODES:
            mode = 'auto'
        if not hasattr(self, 'player'):
            return
        try:
            if mode == 'on':
                self.player.target_colorspace_hint = 'yes'
            elif mode == 'off':
                self.player.target_colorspace_hint = 'no'
            else:
                try:
                    self.player.target_colorspace_hint = 'auto'
                except Exception:
                    self.player.target_colorspace_hint = 'no'
            print(f"HDR mode: {mode}")
        except Exception as e:
            print(f"Could not apply HDR mode: {e}")

    def _set_hdr_mode(self, mode: str):
        if mode not in HDR_MODES:
            return
        self._hdr_mode = mode
        self.settings.setValue("playback/hdr_mode", mode)
        self._apply_hdr_mode(mode)
        self._update_hdr_button()

    def _cycle_hdr(self):
        order = ['auto', 'on', 'off']
        try:
            idx = order.index(self._hdr_mode)
        except ValueError:
            idx = 0
        self._set_hdr_mode(order[(idx + 1) % len(order)])

    def _update_hdr_button(self):
        if not hasattr(self, 'hdr_btn'):
            return
        name, emoji = self._hdr_icon()
        self.hdr_btn.setText(self.icon(name, emoji))
        if self._hdr_mode == 'on':
            self.hdr_btn.setStyleSheet(f"color: {PRIMARY};")
        else:
            self.hdr_btn.setStyleSheet("")

    # ==============================================================
    # Icon helpers
    # ==============================================================

    def icon(self, material_name, emoji_fallback):
        return material_name if self.icon_available else emoji_fallback

    def _player_button(self, icon_name, emoji, tooltip, cb):
        btn = QPushButton(self.icon(icon_name, emoji))
        btn.setObjectName("PlayerBtn")
        btn.setToolTip(tooltip)
        btn.setFixedSize(38, 38)
        if self.icon_available:
            btn.setFont(make_icon_font(22))
        btn.clicked.connect(cb)
        return btn

    # ---- Control bar ----
    def _build_control_bar(self):
        bar = ControlBar(self)
        bar.setObjectName("ControlBar")
        bar.setAttribute(Qt.WA_NativeWindow)
        bar.setAttribute(Qt.WA_OpaquePaintEvent, True)
        bar.setAutoFillBackground(False)

        h = QHBoxLayout(bar)
        h.setContentsMargins(14, 0, 14, 0)
        h.setSpacing(4)

        self.play_btn = self._player_button("play_arrow", "▶", "Play / Pause (Space)", self._toggle_pause)
        h.addWidget(self.play_btn, alignment=Qt.AlignVCenter)

        self.stop_btn = self._player_button("stop", "■", "Stop", self._stop)
        h.addWidget(self.stop_btn, alignment=Qt.AlignVCenter)

        self.prev_btn = self._player_button("replay_10", "⏪", "Back 10s", lambda: self._seek(-10))
        h.addWidget(self.prev_btn, alignment=Qt.AlignVCenter)

        self.next_btn = self._player_button("forward_10", "⏩", "Forward 10s", lambda: self._seek(10))
        h.addWidget(self.next_btn, alignment=Qt.AlignVCenter)

        h.addSpacing(10)

        self.audio_btn = self._player_button("graphic_eq", "♫", "Audio track (A)", self._open_audio_menu)
        h.addWidget(self.audio_btn, alignment=Qt.AlignVCenter)

        self.sub_btn = self._player_button("subtitles", "CC", "Subtitles (V)", self._open_subtitle_menu)
        h.addWidget(self.sub_btn, alignment=Qt.AlignVCenter)

        hdr_icon_name, hdr_emoji = self._hdr_icon()
        self.hdr_btn = self._player_button(
            hdr_icon_name, hdr_emoji, "HDR mode (click to cycle)", self._cycle_hdr)
        h.addWidget(self.hdr_btn, alignment=Qt.AlignVCenter)
        self._update_hdr_button()

        h.addSpacing(10)

        self.mute_btn = self._player_button("volume_up", "🔊", "Mute (M)", self._toggle_mute)
        h.addWidget(self.mute_btn, alignment=Qt.AlignVCenter)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setObjectName("volumeSlider")
        self.volume_slider.setRange(0, 150)
        self.volume_slider.setValue(int(self.settings.value("playback/volume", 100)))
        self.volume_slider.setFixedSize(108, 24)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        h.addWidget(self.volume_slider, alignment=Qt.AlignVCenter)

        h.addSpacing(10)

        self.current_time = QLabel("0:00")
        self.current_time.setObjectName("TimeLabel")
        self.current_time.setFixedWidth(58)
        self.current_time.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        h.addWidget(self.current_time, alignment=Qt.AlignVCenter)

        self.seek_slider = SeekSlider(Qt.Horizontal)
        self.seek_slider.setObjectName("seekSlider")
        self.seek_slider.setRange(0, 1000)
        self.seek_slider.setValue(0)
        self.seek_slider.setFixedHeight(24)
        self.seek_slider.sliderReleased.connect(self._on_seek_released)
        self.seek_slider.sliderMoved.connect(self._on_seek_moved)
        h.addWidget(self.seek_slider, stretch=1, alignment=Qt.AlignVCenter)

        self.total_time = QLabel("0:00")
        self.total_time.setObjectName("TimeLabel")
        self.total_time.setFixedWidth(58)
        self.total_time.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        h.addWidget(self.total_time, alignment=Qt.AlignVCenter)

        h.addSpacing(10)

        self.fullscreen_btn = self._player_button("fullscreen", "⛶", "Fullscreen (F)", self._toggle_fullscreen)
        h.addWidget(self.fullscreen_btn, alignment=Qt.AlignVCenter)

        return bar

    # ---- Manual layout ----
    def _layout_children(self):
        w = self.width()
        h = self.height()
        full = self.isFullScreen()

        if full:
            self.video_container.setGeometry(0, 0, w, h)
            self.welcome_page.setGeometry(0, 0, w, h)
        else:
            self.video_container.setGeometry(0, TITLE_H, w, h - TITLE_H - CONTROL_H)
            self.welcome_page.setGeometry(0, TITLE_H, w, h - TITLE_H - CONTROL_H)

        if self._anim_title.state() != QPropertyAnimation.State.Running:
            ty = 0 if self._bars_visible else -TITLE_H
            self.title_bar.setGeometry(0, ty, w, TITLE_H)
        else:
            self.title_bar.setGeometry(0, self.title_bar.y(), w, TITLE_H)

        if self._anim_control.state() != QPropertyAnimation.State.Running:
            cy = (h - CONTROL_H) if self._bars_visible else h
            self.control_bar.setGeometry(0, cy, w, CONTROL_H)
        else:
            self.control_bar.setGeometry(0, self.control_bar.y(), w, CONTROL_H)

        self.video_container.lower()
        if self.welcome_page.isVisible():
            self.welcome_page.raise_()
        self.title_bar.raise_()
        self.control_bar.raise_()
        self._size_grip.move(w - 18, h - 18)
        self._size_grip.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._layout_children()

    def show_welcome(self, show: bool):
        if show:
            self.welcome_page.show()
            self.welcome_page.raise_()
            self.video_container.set_playing(False)
        else:
            self.welcome_page.hide()
            self.video_container.set_playing(True)

    def _set_controls_enabled(self, enabled):
        for w in (self.play_btn, self.stop_btn, self.prev_btn, self.next_btn,
                  self.audio_btn, self.sub_btn, self.hdr_btn,
                  self.mute_btn, self.volume_slider, self.seek_slider,
                  self.fullscreen_btn):
            w.setEnabled(enabled)

    # ---- Shortcuts ----
    def _make_shortcut(self, key, cb):
        sc = QShortcut(QKeySequence(key), self)
        sc.setContext(Qt.ApplicationShortcut)
        sc.setAutoRepeat(False)
        sc.activated.connect(cb)
        return sc

    def _create_shortcuts(self):
        self._shortcuts = [
            self._make_shortcut("Space", self._toggle_pause),
            self._make_shortcut("F",     self._toggle_fullscreen),
            self._make_shortcut("Esc",   self._handle_escape),
            self._make_shortcut("Left",  lambda: self._seek(-5)),
            self._make_shortcut("Right", lambda: self._seek(5)),
            self._make_shortcut("Up",    lambda: self._seek(30)),
            self._make_shortcut("Down",  lambda: self._seek(-30)),
            self._make_shortcut("M",     self._toggle_mute),
            self._make_shortcut("+",     lambda: self._adjust_volume(5)),
            self._make_shortcut("=",     lambda: self._adjust_volume(5)),
            self._make_shortcut("-",     lambda: self._adjust_volume(-5)),
            self._make_shortcut("Ctrl+O", self._open_file_dialog),
            self._make_shortcut("Ctrl+Q", self.close),
            self._make_shortcut("A",      self._cycle_audio),
            self._make_shortcut("V",      self._cycle_subtitle),
            self._make_shortcut("Shift+V", self._open_subtitle_settings),
            self._make_shortcut("[",      lambda: self._step_speed(-0.25)),
            self._make_shortcut("]",      lambda: self._step_speed(0.25)),
            self._make_shortcut("\\",     lambda: self._set_speed(1.0)),
            self._make_shortcut("N",      self._playlist_next),
            self._make_shortcut("P",      self._playlist_prev),
            self._make_shortcut("H",      self._cycle_hdr),
        ]

    # ---- Player init ----
    def _init_player(self):
        wid = str(int(self.video_container.winId()))
        self.player = mpv.MPV(
            wid=wid,
            input_default_bindings=False,
            input_vo_keyboard=True,
            hwdec='auto-safe',
            keep_open='yes',
            volume_max=150,
            sub_fonts_dir=custom_fonts_dir(),
            log_handler=print,
            loglevel='warn',
        )
        self.player.volume = slider_to_mpv_volume(self.volume_slider.value())
        self.player.speed = self._speed
        self._apply_subtitle_settings(self._load_sub_settings())
        self._apply_hdr_mode(self._hdr_mode)

        try:
            self.player.register_key_binding(
                "MBTN_RIGHT",
                lambda: self.context_menu_requested.emit()
            )
            print("Registered MBTN_RIGHT binding")
        except Exception as e:
            print(f"Could not register MBTN_RIGHT: {e}")

        try:
            @self.player.property_observer('eof-reached')
            def _on_eof(_name, value):
                if value:
                    self._pending_eof_clear = True
        except Exception as e:
            print(f"Could not attach eof observer: {e}")

    def contextMenuEvent(self, event):
        self._show_workspace_context_menu()
        event.accept()

    # ---- Subtitle settings ----
    def _load_sub_settings(self) -> dict:
        return {
            'font': self.settings.value("sub/font", DEFAULT_SUB['font'], type=str),
            'size': self.settings.value("sub/size", DEFAULT_SUB['size'], type=int),
            'bold': self.settings.value("sub/bold", DEFAULT_SUB['bold'], type=bool),
            'color': self.settings.value("sub/color", DEFAULT_SUB['color'], type=str),
            'outline_color': self.settings.value("sub/outline_color", DEFAULT_SUB['outline_color'], type=str),
            'outline_size': self.settings.value("sub/outline_size", DEFAULT_SUB['outline_size'], type=float),
        }

    def _apply_subtitle_settings(self, s: dict):
        if not hasattr(self, 'player'):
            return
        try:
            self.player.sub_font = s['font']
            self.player.sub_font_size = int(s['size'])
            self.player.sub_bold = bool(s['bold'])
            self.player.sub_color = f"{s['color']}FF"
            self.player.sub_border_color = f"{s['outline_color']}FF"
            self.player.sub_border_size = float(s['outline_size'])

            try:
                self.player.sub_ass_override = 'yes'
            except Exception:
                pass

            try:
                self.player.sub_border_style = 'outline-and-shadow'
            except Exception:
                pass

            try:
                self.player.sub_shadow_offset = 0
            except Exception:
                pass
        except Exception as e:
            print(f"Could not apply subtitle settings: {e}")

    def _save_sub_settings(self, s: dict):
        self.settings.setValue("sub/font", s['font'])
        self.settings.setValue("sub/size", int(s['size']))
        self.settings.setValue("sub/bold", bool(s['bold']))
        self.settings.setValue("sub/color", s['color'])
        self.settings.setValue("sub/outline_color", s['outline_color'])
        self.settings.setValue("sub/outline_size", float(s['outline_size']))

    def _open_subtitle_settings(self):
        dlg = SubtitleSettingsDialog(self, self._load_sub_settings())
        accepted = (dlg.exec() == QDialog.DialogCode.Accepted)
        fonts_added = dlg.fonts_changed()

        if accepted:
            values = dlg.get_values()
            self._save_sub_settings(values)
            self._apply_subtitle_settings(values)

            if fonts_added and self._current_file and not self.player.idle_active:
                try:
                    pos = self.player.time_pos or 0
                except Exception:
                    pos = 0
                self.player.play(self._current_file)
                if pos > 5:
                    self._pending_resume = pos

    # ---- About dialog ----
    def _open_about_dialog(self):
        dlg = AboutDialog(self, icon_available=self.icon_available)
        dlg.exec()

    # ---- Track listing ----
    def _get_tracks(self, kind: str):
        if not hasattr(self, 'player'):
            return []
        try:
            tl = self.player.track_list or []
        except Exception:
            return []
        return [t for t in tl if t.get('type') == kind]

    def _track_label(self, t: dict) -> str:
        parts = []
        lang = (t.get('lang') or '').strip()
        title = (t.get('title') or '').strip()
        codec = (t.get('codec') or '').strip()
        if title and lang:
            parts.append(f"{title} ({lang})")
        elif title:
            parts.append(title)
        elif lang:
            parts.append(lang)
        if codec:
            parts.append(f"[{codec}]")
        if t.get('external'):
            parts.append("(ext)")
        tid = t.get('id', '?')
        return f"#{tid}  " + "  ".join(parts) if parts else f"#{tid}  Track"

    # ---- Audio menu (control bar) ----
    def _open_audio_menu(self):
        menu = QMenu(self)
        header = menu.addAction("Audio Track")
        header.setEnabled(False)
        menu.addSeparator()
        group = QActionGroup(menu)
        group.setExclusive(True)
        try:
            current_aid = self.player.aid
        except Exception:
            current_aid = None
        tracks = self._get_tracks('audio')
        if not tracks:
            a = menu.addAction("(no audio tracks)")
            a.setEnabled(False)
        else:
            for t in tracks:
                tid = t.get('id')
                act = menu.addAction(self._track_label(t))
                act.setCheckable(True)
                is_current = (current_aid == tid) or (current_aid is None and t.get('selected'))
                act.setChecked(bool(is_current))
                group.addAction(act)
                act.triggered.connect(lambda _=False, i=tid: self._set_audio_track(i))
        pos = self.audio_btn.mapToGlobal(QPoint(0, -menu.sizeHint().height()))
        menu.exec(pos)

    def _set_audio_track(self, tid):
        if hasattr(self, 'player'):
            try:
                self.player.aid = str(tid)
            except Exception as e:
                print(f"set audio track failed: {e}")

    def _cycle_audio(self):
        tracks = self._get_tracks('audio')
        if len(tracks) < 2:
            return
        try:
            cur = self.player.aid
        except Exception:
            cur = None
        ids = [t.get('id') for t in tracks]
        try:
            idx = ids.index(cur)
        except ValueError:
            idx = -1
        self._set_audio_track(ids[(idx + 1) % len(ids)])

    # ---- Subtitle menu ----
    def _open_subtitle_menu(self):
        menu = QMenu(self)
        header = menu.addAction("Subtitles")
        header.setEnabled(False)
        menu.addSeparator()
        group = QActionGroup(menu)
        group.setExclusive(True)
        try:
            current_sid = self.player.sid
        except Exception:
            current_sid = None
        tracks = self._get_tracks('sub')
        off = menu.addAction("Off")
        off.setCheckable(True)
        off.setChecked(current_sid == 'no')
        group.addAction(off)
        off.triggered.connect(self._disable_subtitles)
        auto = menu.addAction("Auto")
        auto.setCheckable(True)
        auto.setChecked(current_sid == 'auto')
        group.addAction(auto)
        auto.triggered.connect(lambda: self._set_subtitle_track('auto'))
        menu.addSeparator()
        if not tracks:
            a = menu.addAction("(no subtitles found)")
            a.setEnabled(False)
        else:
            for t in tracks:
                tid = t.get('id')
                act = menu.addAction(self._track_label(t))
                act.setCheckable(True)
                is_current = (current_sid == tid) or (current_sid is None and t.get('selected'))
                act.setChecked(bool(is_current))
                group.addAction(act)
                act.triggered.connect(lambda _=False, i=tid: self._set_subtitle_track(i))
        menu.addSeparator()
        settings_act = menu.addAction("Subtitle Settings…")
        settings_act.triggered.connect(self._open_subtitle_settings)
        pos = self.sub_btn.mapToGlobal(QPoint(0, -menu.sizeHint().height()))
        menu.exec(pos)

    def _set_subtitle_track(self, tid):
        if hasattr(self, 'player'):
            try:
                self.player.sid = str(tid)
            except Exception as e:
                print(f"set subtitle track failed: {e}")

    def _disable_subtitles(self):
        if hasattr(self, 'player'):
            try:
                self.player.sid = "no"
            except Exception as e:
                print(f"disable subtitles failed: {e}")

    def _cycle_subtitle(self):
        if not hasattr(self, 'player'):
            return
        tracks = self._get_tracks('sub')
        if not tracks:
            return
        try:
            cur = self.player.sid
        except Exception:
            cur = None
        ids = [t.get('id') for t in tracks]
        if cur in ('no', None):
            self._set_subtitle_track(ids[0])
            return
        try:
            idx = ids.index(cur)
        except ValueError:
            self._set_subtitle_track(ids[0])
            return
        if idx + 1 < len(ids):
            self._set_subtitle_track(ids[idx + 1])
        else:
            self._disable_subtitles()

    # ---- Speed (menu-only now) ----
    def _open_speed_menu(self):
        menu = QMenu(self)
        header = menu.addAction("Playback Speed")
        header.setEnabled(False)
        menu.addSeparator()
        group = QActionGroup(menu)
        group.setExclusive(True)
        for s in [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 3.0, 4.0]:
            label = "Normal (1×)" if s == 1.0 else format_speed(s)
            act = menu.addAction(label)
            act.setCheckable(True)
            act.setChecked(abs(self._speed - s) < 0.001)
            group.addAction(act)
            act.triggered.connect(lambda _=False, val=s: self._set_speed(val))
        if hasattr(self, 'speed_btn'):
            pos = self.speed_btn.mapToGlobal(QPoint(0, -menu.sizeHint().height()))
        else:
            pos = QCursor.pos()
        menu.exec(pos)

    def _set_speed(self, value: float):
        value = max(0.25, min(4.0, float(value)))
        self._speed = value
        if hasattr(self, 'player'):
            try:
                self.player.speed = value
            except Exception as e:
                print(f"set speed failed: {e}")
        self.settings.setValue("playback/speed", value)

    def _step_speed(self, delta: float):
        self._set_speed(round(self._speed + delta, 2))

    # ---- Right-click context menu ----
    def _show_workspace_context_menu(self):
        if not hasattr(self, 'player'):
            return
        menu = QMenu(self)

        open_act = menu.addAction("Open Media…")
        open_act.setShortcut("Ctrl+O")
        open_act.triggered.connect(self._open_file_dialog)

        # ----- Recent Files submenu -----
        recent_list = self._load_recent_files()
        recent_menu = menu.addMenu(f"Recent Files ({len(recent_list)})")
        if not recent_list:
            a = recent_menu.addAction("(no recent files)")
            a.setEnabled(False)
        else:
            for path in recent_list:
                label = os.path.basename(path)
                act = recent_menu.addAction(label)
                act.setToolTip(path)
                act.triggered.connect(
                    lambda _=False, p=path: self._open_recent_file(p)
                )
            recent_menu.addSeparator()
            clear_act = recent_menu.addAction("Clear Recent List")
            clear_act.triggered.connect(self._clear_recent_files)

        menu.addSeparator()

        # Audio Sync
        sync_menu = menu.addMenu("Audio Sync")
        try:
            cur_delay = self.player.audio_delay or 0.0
        except Exception:
            cur_delay = 0.0
        hdr = sync_menu.addAction(f"Current: {format_delay(cur_delay)}")
        hdr.setEnabled(False)
        sync_menu.addSeparator()
        for label, delta in [("-1.0s", -1.0), ("-0.5s", -0.5), ("-0.1s", -0.1)]:
            a = sync_menu.addAction(label)
            a.triggered.connect(lambda _=False, d=delta: self._adjust_audio_delay(d))
        reset = sync_menu.addAction("Reset (0.00s)")
        reset.triggered.connect(lambda: self._set_audio_delay(0.0))
        for label, delta in [("+0.1s", 0.1), ("+0.5s", 0.5), ("+1.0s", 1.0)]:
            a = sync_menu.addAction(label)
            a.triggered.connect(lambda _=False, d=delta: self._adjust_audio_delay(d))

        # Video Track
        v_menu = menu.addMenu("Video Track")
        vtracks = self._get_tracks('video')
        try:
            cur_vid = self.player.vid
        except Exception:
            cur_vid = None
        if not vtracks:
            a = v_menu.addAction("(no video tracks)")
            a.setEnabled(False)
        else:
            group = QActionGroup(v_menu)
            group.setExclusive(True)
            for t in vtracks:
                tid = t.get('id')
                act = v_menu.addAction(self._track_label(t))
                act.setCheckable(True)
                is_cur = (cur_vid == tid) or (cur_vid is None and t.get('selected'))
                act.setChecked(bool(is_cur))
                group.addAction(act)
                act.triggered.connect(lambda _=False, i=tid: self._set_video_track(i))
            v_menu.addSeparator()
            a = v_menu.addAction("Disable video")
            a.triggered.connect(lambda: self._set_video_track("no"))

        # Audio Track
        a_menu = menu.addMenu("Audio Track")
        atracks = self._get_tracks('audio')
        try:
            cur_aid = self.player.aid
        except Exception:
            cur_aid = None
        if not atracks:
            a = a_menu.addAction("(no audio tracks)")
            a.setEnabled(False)
        else:
            a_group = QActionGroup(a_menu)
            a_group.setExclusive(True)
            for t in atracks:
                tid = t.get('id')
                act = a_menu.addAction(self._track_label(t))
                act.setCheckable(True)
                is_cur = (cur_aid == tid) or (cur_aid is None and t.get('selected'))
                act.setChecked(bool(is_cur))
                a_group.addAction(act)
                act.triggered.connect(lambda _=False, i=tid: self._set_audio_track(i))

        # Subtitle Track
        s_menu = menu.addMenu("Subtitle Track")
        stracks = self._get_tracks('sub')
        try:
            cur_sid = self.player.sid
        except Exception:
            cur_sid = None
        s_group = QActionGroup(s_menu)
        s_group.setExclusive(True)
        s_off = s_menu.addAction("Off")
        s_off.setCheckable(True)
        s_off.setChecked(cur_sid == 'no')
        s_group.addAction(s_off)
        s_off.triggered.connect(self._disable_subtitles)
        s_auto = s_menu.addAction("Auto")
        s_auto.setCheckable(True)
        s_auto.setChecked(cur_sid == 'auto')
        s_group.addAction(s_auto)
        s_auto.triggered.connect(lambda: self._set_subtitle_track('auto'))
        if stracks:
            s_menu.addSeparator()
            for t in stracks:
                tid = t.get('id')
                act = s_menu.addAction(self._track_label(t))
                act.setCheckable(True)
                is_cur = (cur_sid == tid) or (cur_sid is None and t.get('selected'))
                act.setChecked(bool(is_cur))
                s_group.addAction(act)
                act.triggered.connect(lambda _=False, i=tid: self._set_subtitle_track(i))
        s_menu.addSeparator()
        s_settings = s_menu.addAction("Subtitle Settings…")
        s_settings.triggered.connect(self._open_subtitle_settings)

        # HDR mode
        hdr_menu = menu.addMenu("HDR")
        hdr_group = QActionGroup(hdr_menu)
        hdr_group.setExclusive(True)
        for label, val in [("Auto", "auto"),
                            ("On (passthrough)", "on"),
                            ("Off (tone map to SDR)", "off")]:
            act = hdr_menu.addAction(label)
            act.setCheckable(True)
            act.setChecked(self._hdr_mode == val)
            hdr_group.addAction(act)
            act.triggered.connect(lambda _=False, m=val: self._set_hdr_mode(m))

        # Audio Mode
        am_menu = menu.addMenu("Audio Mode")
        try:
            cur_mode = self.player.audio_channels or "auto"
        except Exception:
            cur_mode = "auto"
        am_group = QActionGroup(am_menu)
        am_group.setExclusive(True)
        for label, val in [("Auto", "auto"), ("Mono", "mono"), ("Stereo", "stereo"),
                           ("5.1", "5.1"), ("7.1", "7.1")]:
            act = am_menu.addAction(label)
            act.setCheckable(True)
            act.setChecked(cur_mode == val)
            am_group.addAction(act)
            act.triggered.connect(lambda _=False, v=val: self._set_audio_mode(v))

        menu.addSeparator()

        # Resume toggle
        resume_act = menu.addAction("Remember playback position")
        resume_act.setCheckable(True)
        resume_act.setChecked(self._resume_enabled())
        resume_act.triggered.connect(self._toggle_resume_enabled)

        menu.addSeparator()

        # Playlist
        pl_menu = menu.addMenu(f"Playlist ({len(self._playlist)} items)")
        if not self._playlist:
            a = pl_menu.addAction("(empty)")
            a.setEnabled(False)
        else:
            prev_act = pl_menu.addAction("Previous")
            prev_act.setShortcut("P")
            prev_act.triggered.connect(self._playlist_prev)
            next_act = pl_menu.addAction("Next")
            next_act.setShortcut("N")
            next_act.triggered.connect(self._playlist_next)
            pl_menu.addSeparator()
            for i, path in enumerate(self._playlist):
                label = os.path.basename(path)
                if i == self._playlist_index:
                    label = "▶  " + label
                a = pl_menu.addAction(label)
                a.triggered.connect(lambda _=False, idx=i: self._playlist_play_index(idx))

        menu.addSeparator()

        # Playback Speed
        sp_menu = menu.addMenu("Playback Speed")
        sp_group = QActionGroup(sp_menu)
        sp_group.setExclusive(True)
        for s in [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 3.0, 4.0]:
            label = "Normal (1×)" if s == 1.0 else format_speed(s)
            act = sp_menu.addAction(label)
            act.setCheckable(True)
            act.setChecked(abs(self._speed - s) < 0.001)
            sp_group.addAction(act)
            act.triggered.connect(lambda _=False, val=s: self._set_speed(val))

        menu.exec(QCursor.pos())

    # ---- Audio delay / mode / video track ----
    def _set_audio_delay(self, value: float):
        if hasattr(self, 'player'):
            try:
                self.player.audio_delay = float(value)
            except Exception as e:
                print(f"set audio_delay failed: {e}")

    def _adjust_audio_delay(self, delta: float):
        try:
            cur = self.player.audio_delay or 0.0
        except Exception:
            cur = 0.0
        self._set_audio_delay(cur + delta)

    def _set_video_track(self, tid):
        if hasattr(self, 'player'):
            try:
                self.player.vid = str(tid)
            except Exception as e:
                print(f"set video track failed: {e}")

    def _set_audio_mode(self, mode: str):
        if hasattr(self, 'player'):
            try:
                self.player.audio_channels = mode
            except Exception as e:
                print(f"set audio channels failed: {e}")

    # ---- Playlist ----
    def _playlist_next(self):
        if not self._playlist:
            return
        self._playlist_play_index((self._playlist_index + 1) % len(self._playlist))

    def _playlist_prev(self):
        if not self._playlist:
            return
        self._playlist_play_index((self._playlist_index - 1) % len(self._playlist))

    def _playlist_play_index(self, idx):
        if 0 <= idx < len(self._playlist):
            self._playlist_index = idx
            self._load_file(self._playlist[idx])

    # ---- File loading ----
    def _open_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Open Media", self._last_folder(),
            "Video Files (*.mp4 *.mkv *.avi *.mov *.webm *.flv *.wmv "
            "*.m4v *.ts *.mpg *.mpeg *.m2ts *.ogv *.3gp);;All Files (*.*)"
        )
        if files:
            self._remember_folder(files[0])
            self._load_files(files)

    def _load_files(self, paths):
        paths = [p for p in paths if os.path.isfile(p)]
        if not paths:
            return
        self._playlist = paths
        self._playlist_index = 0
        self._load_file(paths[0])

    def _handle_startup_file(self, path: str):
        """
        Called from __main__ when Windows launches us with a file path
        (e.g. from 'Open with' or the right-click 'Play with Chalchitra' menu).
        Defers the load until mpv is initialised.
        """
        if not path or not os.path.isfile(path):
            print(f"Startup file not found: {path!r}")
            return

        def _play_when_ready():
            if hasattr(self, 'player'):
                self._load_files([path])
            else:
                # mpv not ready yet — try again shortly
                QTimer.singleShot(100, _play_when_ready)

        QTimer.singleShot(150, _play_when_ready)

    def _load_file(self, path):
        if not hasattr(self, 'player'):
            return
        if self._current_file and self._current_file != path:
            self._save_current_position()

        print(f"Playing: {path}")
        self._remember_folder(path)
        self._add_recent_file(path)

        resume = self._get_resume_position(path)
        self._pending_resume = resume
        if resume:
            print(f"Will resume at {format_time(resume)}")

        self._current_file = path
        self.player.play(path)
        name = os.path.basename(path)
        self.setWindowTitle(f"Chalchitra — {name}")
        self.title_bar.set_title(f"Chalchitra — {name}")
        self._set_controls_enabled(True)
        self.show_welcome(False)

    # ---- Maximize / restore ----
    def _toggle_maximize(self):
        if self._is_maximized:
            self._restore_from_max()
        else:
            self._normal_geometry = self.geometry()
            self.showMaximized()
            self._is_maximized = True
            self.title_bar.set_maximized(True)
            self._size_grip.setVisible(False)

    def _restore_from_max(self):
        self.showNormal()
        if self._normal_geometry:
            self.setGeometry(self._normal_geometry)
        self._is_maximized = False
        self.title_bar.set_maximized(False)
        if not self.isFullScreen():
            self._size_grip.setVisible(True)

    # ---- Actions ----
    def _toggle_pause(self):
        if not hasattr(self, 'player'):
            return
        if self._current_file and self.player.idle_active:
            self._load_file(self._current_file)
            return
        self.player.pause = not self.player.pause

    def _stop(self):
        self._save_current_position()

        if hasattr(self, 'player'):
            try:
                self.player.stop()
            except Exception:
                pass
            self.seek_slider.blockSignals(True)
            self.seek_slider.setValue(0)
            self.seek_slider.blockSignals(False)
            self.current_time.setText("0:00")
            self.total_time.setText("0:00")
            self.play_btn.setText(self.icon("play_arrow", "▶"))
            self.show_welcome(True)

    # ---- Fullscreen ----
    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self._exit_fullscreen()
        else:
            self._enter_fullscreen()

    def _enter_fullscreen(self):
        self.showFullScreen()
        self._size_grip.setVisible(False)
        self._bars_visible = True
        self._layout_children()

        self._last_cursor_pos = QCursor.pos()
        self._last_activity = time.time()
        self._last_toggle_time = time.time()
        self._cursor_timer.start()

    def _exit_fullscreen(self):
        self._cursor_timer.stop()
        if self._cursor_hidden:
            QApplication.restoreOverrideCursor()
            self._cursor_hidden = False
        self.showNormal()
        self._bars_visible = True
        self._layout_children()
        if not self._is_maximized:
            self._size_grip.setVisible(True)

    def _set_bars_visible(self, visible: bool, animate: bool = True):
        w = self.width()
        h = self.height()

        t_end = QRect(0, 0, w, TITLE_H) if visible else QRect(0, -TITLE_H, w, TITLE_H)
        c_end = QRect(0, h - CONTROL_H, w, CONTROL_H) if visible else QRect(0, h, w, CONTROL_H)

        if not animate:
            self._anim_title.stop()
            self._anim_control.stop()
            self.title_bar.setGeometry(t_end)
            self.control_bar.setGeometry(c_end)
            self._bars_visible = visible
            return

        self._anim_title.stop()
        self._anim_title.setStartValue(self.title_bar.geometry())
        self._anim_title.setEndValue(t_end)
        self._anim_title.start()

        self._anim_control.stop()
        self._anim_control.setStartValue(self.control_bar.geometry())
        self._anim_control.setEndValue(c_end)
        self._anim_control.start()

        self._bars_visible = visible

        if self.isFullScreen():
            if visible and self._cursor_hidden:
                QApplication.restoreOverrideCursor()
                self._cursor_hidden = False
            elif not visible and not self._cursor_hidden:
                QApplication.setOverrideCursor(Qt.BlankCursor)
                self._cursor_hidden = True

    def _after_title_anim(self):
        self.title_bar.update()
        self.update()

    def _after_control_anim(self):
        self.control_bar.update()
        self.update()

    def _check_cursor_fullscreen(self):
        if not self.isFullScreen():
            self._cursor_timer.stop()
            return
        now = time.time()
        cursor = QCursor.pos()
        if cursor != self._last_cursor_pos:
            self._last_cursor_pos = cursor
            self._last_activity = now
        local = self.mapFromGlobal(cursor)
        w = self.width()
        h = self.height()
        in_window = 0 <= local.x() < w and 0 <= local.y() < h
        in_bottom = in_window and local.y() >= h - 90
        in_top = in_window and local.y() <= 60
        want_visible = in_top or in_bottom
        if want_visible:
            self._last_activity = now
        idle = now - self._last_activity
        should_show = want_visible or (idle < 2.2)
        if should_show != self._bars_visible and (now - self._last_toggle_time) > 0.25:
            self._last_toggle_time = now
            self._set_bars_visible(should_show, animate=True)

    def _handle_escape(self):
        if self.isFullScreen():
            self._exit_fullscreen()

    # ---- Seek / volume ----
    def _seek(self, sec):
        if hasattr(self, 'player'):
            try:
                self.player.seek(sec, 'relative')
            except Exception:
                pass

    def _toggle_mute(self):
        if hasattr(self, 'player'):
            self.player.mute = not self.player.mute

    def _adjust_volume(self, delta):
        cur = self.volume_slider.value()
        self.volume_slider.setValue(max(0, min(150, cur + delta)))

    def _on_volume_changed(self, slider_val):
        if hasattr(self, 'player'):
            try:
                self.player.volume = slider_to_mpv_volume(slider_val)
            except Exception:
                pass
        self.settings.setValue("playback/volume", int(slider_val))

    def _on_seek_released(self):
        if not hasattr(self, 'player'):
            return
        if self.player.idle_active:
            return
        dur = self.player.duration or 0
        if dur > 0:
            self.player.seek((self.seek_slider.value() / 1000.0) * dur, 'absolute')
            self._save_current_position()

    def _on_seek_moved(self, v):
        if not hasattr(self, 'player'):
            return
        dur = self.player.duration or 0
        if dur > 0:
            self.current_time.setText(format_time((v / 1000.0) * dur))

    # ---- UI refresh ----
    def _update_ui(self):
        if not hasattr(self, 'player'):
            return
        try:
            if self._pending_resume is not None:
                try:
                    dur = self.player.duration or 0
                except Exception:
                    dur = 0
                if dur > 0:
                    pos = self._pending_resume
                    self._pending_resume = None
                    if 0 < pos < dur - 5:
                        try:
                            self.player.seek(pos, 'absolute')
                            print(f"Resumed at {format_time(pos)}")
                        except Exception as e:
                            print(f"resume seek failed: {e}")

            if self._pending_eof_clear:
                self._pending_eof_clear = False
                if self._current_file:
                    self._clear_resume_position(self._current_file)
                    print("Reached end — cleared resume position")
                try:
                    dur = self.player.duration or 0
                except Exception:
                    dur = 0
                self.seek_slider.blockSignals(True)
                self.seek_slider.setValue(1000)
                self.seek_slider.blockSignals(False)
                if dur > 0:
                    self.current_time.setText(format_time(dur))
                return

            if self.player.idle_active:
                return

            self.play_btn.setText(
                self.icon("play_arrow", "▶") if self.player.pause
                else self.icon("pause", "⏸")
            )
            vol = self.player.volume
            if vol is not None:
                sv = mpv_to_slider_volume(vol)
                if sv != self.volume_slider.value():
                    self.volume_slider.blockSignals(True)
                    self.volume_slider.setValue(sv)
                    self.volume_slider.blockSignals(False)
            self.mute_btn.setText(
                self.icon("volume_off", "🔇") if self.player.mute
                else self.icon("volume_up", "🔊")
            )
            try:
                sid = self.player.sid
                self.sub_btn.setStyleSheet(f"color: {PRIMARY};" if sid not in ('no', None) else "")
            except Exception:
                pass

            pos = self.player.time_pos or 0
            dur = self.player.duration or 0
            self.current_time.setText(format_time(pos))
            self.total_time.setText(format_time(dur))

            if not self.seek_slider.isSliderDown() and dur > 0:
                frac = pos / dur
                if pos >= dur - 0.5:
                    frac = 1.0
                self.seek_slider.blockSignals(True)
                self.seek_slider.setValue(int(frac * 1000))
                self.seek_slider.blockSignals(False)

            self._save_counter += 1
            if self._save_counter >= 8:
                self._save_counter = 0
                self._save_current_position()

        except Exception:
            pass

    # ---- Drag & drop ----
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [u.toLocalFile() for u in event.mimeData().urls()
                 if os.path.isfile(u.toLocalFile())]
        if paths:
            self._remember_folder(paths[0])
            self._load_files(paths)

    # ---- Cleanup ----
    def closeEvent(self, event):
        if self._cursor_hidden:
            QApplication.restoreOverrideCursor()
            self._cursor_hidden = False

        # Persist window geometry / maximize state
        try:
            self._save_window_geometry()
        except Exception as e:
            print(f"Could not save window geometry: {e}")

        self._save_current_position()
        self.settings.setValue("playback/volume", self.volume_slider.value())
        self.settings.setValue("playback/speed", self._speed)
        self.settings.setValue("playback/hdr_mode", self._hdr_mode)
        self.settings.sync()
        if hasattr(self, 'player'):
            try:
                self.player.terminate()
            except Exception:
                pass
        super().closeEvent(event)


# ==================================================================
# Entry
# ==================================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)

    load_fonts()
    icon_available = font_available("Material Symbols Outlined")
    if not icon_available:
        print("Material Symbols not loaded — falling back to emoji icons")

    app.setFont(QFont("Roboto", 10))
    app.setStyleSheet(STYLESHEET)

    ico = ensure_icon()
    if ico and os.path.exists(ico):
        app.setWindowIcon(QIcon(ico))

    settings = make_settings()
    window = ChalchitraWindow(icon_available, settings)
    window.show()

    QTimer.singleShot(0, window._apply_startup_window_state)

    # --- Handle file passed by Windows (Open with / Play with Chalchitra) ---
    # Skip sys.argv[0] (the exe itself). Find the first existing file path.
    startup_file = None
    for arg in sys.argv[1:]:
        # Strip surrounding quotes just in case
        clean = arg.strip('"').strip("'")
        if clean and os.path.isfile(clean):
            startup_file = clean
            break

    if startup_file:
        print(f"Startup file: {startup_file}")
        window._handle_startup_file(startup_file)

    sys.exit(app.exec())