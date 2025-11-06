import tkinter as tk
from tkinter import messagebox
import os
import math
import random
import time
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageTk, ImageSequence
except Exception:
    os.system("pip install pillow")
    from PIL import Image, ImageDraw, ImageTk, ImageSequence

try:
    import pygame
    pygame.mixer.init()
except Exception:
    os.system("pip install pygame")
    import pygame
    pygame.mixer.init()

try:
    from mutagen.mp3 import MP3
except Exception:
    os.system("pip install mutagen")
    from mutagen.mp3 import MP3


LIGHT_THEME = {
    'bg': '#dbeafe',
    'bg_top': '#e0f2ff',
    'bg_bottom': '#a5d8ff',
    'light': '#bfdbfe',
    'dark': '#3b82f6',
    'active': '#60a5fa',
    'text': '#1e3a8a',
    'grass': '#8ecae6',
    'slider_trough': '#c7d2fe',
    'slider_active': '#3b82f6'
}

DARK_THEME = {
    'bg': '#102542',
    'bg_top': '#152c52',
    'bg_bottom': '#0b1d33',
    'light': '#1e3a5c',
    'dark': '#7dd3fc',
    'active': '#93c5fd',
    'text': '#e2efff',
    'grass': '#18486a',
    'slider_trough': '#1f2f4a',
    'slider_active': '#60a5fa'
}

COLORS = dict(LIGHT_THEME)

CANVAS_SIZE = (240, 306)
GRASS_HEIGHT = 0
TAU = math.pi * 2.0


def hex_to_rgb(value):
    value = value.lstrip('#')
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    r, g, b = [max(0, min(255, int(round(c)))) for c in rgb]
    return f"#{r:02x}{g:02x}{b:02x}"


class SakuraBackground:
    def __init__(self, size):
        self.size = size
        self.base = self._build_base()

    def _build_base(self):
        w, h = self.size
        img = Image.new('RGBA', (w, h))
        draw = ImageDraw.Draw(img)
        top = hex_to_rgb(COLORS['bg_top'])
        bottom = hex_to_rgb(COLORS['bg_bottom'])
        for y in range(h):
            ratio = y / max(1, h - 1)
            r = int(top[0] * (1 - ratio) + bottom[0] * ratio)
            g = int(top[1] * (1 - ratio) + bottom[1] * ratio)
            b = int(top[2] * (1 - ratio) + bottom[2] * ratio)
            draw.line([(0, y), (w, y)], fill=(r, g, b, 255))
        return img

    def render(self, t):
        frame = self.base.copy()
        draw = ImageDraw.Draw(frame, 'RGBA')
        w, h = self.size
        radius = int(w * 0.48)
        cx = int(w * 0.55 + math.sin(t * 0.12) * 10)
        cy = int(h * 0.28 + math.cos(t * 0.1) * 6)
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=(255, 210, 235, 48))
        return frame


class SakuraPetalField:
    def __init__(self, size, count=28):
        self.w, self.h = size
        self.time = 0.0
        self.petals = [self._spawn(random.uniform(-self.h, self.h * 0.3)) for _ in range(count)]

    def _spawn(self, start_y=None):
        base_y = start_y if start_y is not None else random.uniform(-self.h, -10)
        shade = random.randint(-20, 25)
        color = (
            255,
            max(150, min(255, 200 + shade)),
            max(170, min(255, 220 + shade)),
            200
        )
        return {
            'x': random.uniform(0, self.w),
            'y': base_y,
            'vx': random.uniform(-22, 22),
            'vy': random.uniform(35, 60),
            'size': random.uniform(8, 14),
            'angle': random.uniform(0, TAU),
            'spin': random.uniform(-1.6, 1.6),
            'phase': random.uniform(0, TAU),
            'drift': random.uniform(0.6, 1.6),
            'wave_speed': random.uniform(0.6, 1.1),
            'color': color
        }

    def step(self, dt):
        self.time += dt
        for petal in self.petals:
            petal['x'] += (petal['vx'] + math.sin(self.time * petal['wave_speed'] + petal['phase']) * petal['drift']) * dt
            petal['y'] += petal['vy'] * dt
            petal['angle'] += petal['spin'] * dt
            if petal['y'] > self.h + 20:
                petal.update(self._spawn())
            elif petal['x'] < -15 or petal['x'] > self.w + 15:
                petal['x'] %= (self.w + 15)

    def render(self):
        img = Image.new('RGBA', (self.w, self.h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img, 'RGBA')
        for petal in self.petals:
            x = petal['x']
            y = petal['y']
            angle = petal['angle']
            size = petal['size']
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            half_w = size * 0.6
            half_h = size
            points = []
            for dx, dy in [(-half_w, 0), (0, -half_h), (half_w, 0), (0, half_h)]:
                px = x + dx * cos_a - dy * sin_a
                py = y + dx * sin_a + dy * cos_a
                points.append((px, py))
            draw.polygon(points, fill=petal['color'])
        return img


class GrassField:
    def __init__(self, w, h, blades=72):
        self.w = w
        self.h = h
        self.base_w = max(80, w // 3)
        self.base_h = max(40, h // 2)
        base_rgb = hex_to_rgb(COLORS['grass'])
        self.base_color = (base_rgb[0], base_rgb[1], base_rgb[2], 245)
        self.blades = []
        for _ in range(blades):
            base_x = random.uniform(0, self.base_w - 1)
            height = random.uniform(self.base_h * 0.45, self.base_h * 0.95)
            blade = {
                'x': base_x,
                'height': height,
                'width': random.uniform(0.9, 1.8),
                'amp': random.uniform(0.3, 1.1),
                'speed': random.uniform(0.35, 0.65),
                'phase': random.uniform(0, TAU),
                'color': self._shade_color()
            }
            self.blades.append(blade)

    def _shade_color(self):
        base_rgb = hex_to_rgb(COLORS['grass'])
        delta = random.randint(-18, 18)
        return (
            max(0, min(255, base_rgb[0] + delta)),
            max(0, min(255, base_rgb[1] + delta)),
            max(0, min(255, base_rgb[2] + delta)),
            235
        )

    def generate_frame(self, t):
        base = Image.new('RGBA', (self.base_w, self.base_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(base, 'RGBA')
        ground = self.base_h - 1
        draw.rectangle([0, ground - 1, self.base_w, self.base_h], fill=self.base_color)
        for blade in self.blades:
            sway = math.sin(t * blade['speed'] + blade['phase']) * blade['amp']
            bx = blade['x']
            top_x = bx + sway
            top_y = ground - blade['height']
            width = blade['width']
            points = [
                (bx - width, ground),
                (bx + width, ground),
                (top_x + width * 0.6, top_y + self.base_h * 0.18),
                (top_x, top_y),
                (top_x - width * 0.6, top_y + self.base_h * 0.18)
            ]
            draw.polygon([(int(px), int(py)) for px, py in points], fill=blade['color'])
        return base.resize((self.w, self.h), Image.Resampling.NEAREST)


class DecoManager:
    def __init__(self, folder, canvas_size, grass_height):
        self.folder = Path(folder)
        self.canvas_size = canvas_size
        self.ground = canvas_size[1] - grass_height
        self.scale = canvas_size[0] / 320.0
        self.items = []
        self._load_items()

    def _load_items(self):
        w, _ = self.canvas_size
        s = self.scale
        def scale_pos(x, y):
            return (int(x * s), self.ground + int(y * s)) if y is not None else (int(x * s), int(10 * s))

        definitions = [
            ('sakuratree.gif', {'anchor': 'sw', 'pos': scale_pos(22, 8), 'scale': 0.9 * s, 'bob': 0.5, 'speed': 0.55, 'layer': 0}),
            ('cutehouse.png', {'anchor': 's', 'pos': scale_pos(128, 8), 'scale': 0.9 * s, 'layer': 0}),
            ('sakurabranch.png', {'anchor': 'nw', 'pos': (int(8 * s), int(8 * s)), 'scale': 0.78 * s, 'bob': 0.35, 'speed': 0.75, 'layer': 0}),
            ('pinkstarcloud.png', {'anchor': 'ne', 'pos': (w - int(10 * s), int(48 * s)), 'scale': 0.92 * s, 'bob': 0.7, 'speed': 0.6, 'layer': 0}),
            ('bunnylay.png', {'anchor': 's', 'pos': scale_pos(w / s * 0.55, 2), 'scale': 1.05 * s, 'bob': 0.45, 'speed': 0.9, 'layer': 1}),
            ('miffyloaf.png', {'anchor': 's', 'pos': scale_pos(w / s * 0.28, 1.5), 'scale': 1.0 * s, 'bob': 0.4, 'speed': 1.05, 'layer': 1}),
            ('miffyicon.png', {'anchor': 's', 'pos': scale_pos(w / s * 0.86, 6), 'scale': 0.9 * s, 'bob': 0.45, 'speed': 0.85, 'layer': 1})
        ]
        for filename, cfg in definitions:
            image = self._load_image(self.folder / filename, cfg.get('scale', 1.0))
            if image is None:
                continue
            item = cfg.copy()
            item['image'] = image
            item.setdefault('phase', random.uniform(0, TAU))
            item.setdefault('bob', 0.0)
            item.setdefault('speed', 0.0)
            item.setdefault('layer', 0)
            item.setdefault('anchor', 'center')
            self.items.append(item)

    def _load_image(self, path, scale):
        if not path.exists():
            return None
        try:
            img = Image.open(path)
            if getattr(img, 'n_frames', 1) > 1:
                img.seek(0)
            img = img.convert('RGBA')
            if scale and scale != 1.0:
                new_size = (
                    max(1, int(img.width * scale)),
                    max(1, int(img.height * scale))
                )
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            return img
        except Exception:
            return None

    def render(self, t):
        layer = Image.new('RGBA', self.canvas_size, (0, 0, 0, 0))
        for item in sorted(self.items, key=lambda data: data['layer']):
            img = item['image']
            offset = 0.0
            if item.get('bob', 0.0) and item.get('speed', 0.0):
                offset = math.sin(t * item['speed'] + item['phase']) * item['bob']
            left, top = self._anchor_to_topleft(img.size, item.get('anchor', 'center'), item['pos'], offset)
            layer.paste(img, (left, top), img)
        return layer

    def _anchor_to_topleft(self, size, anchor, position, offset_y):
        anchor = (anchor or 'center').lower()
        w, h = size
        x, y = position
        if 'n' in anchor:
            top = y
        elif 's' in anchor:
            top = y - h
        else:
            top = y - h / 2
        if 'w' in anchor:
            left = x
        elif 'e' in anchor:
            left = x - w
        else:
            left = x - w / 2
        top += offset_y
        return int(round(left)), int(round(top))


class SakuraScene:
    def __init__(self, canvas_size):
        self.size = canvas_size
        self.time = 0.0
        self.frame = self._load_scene_image() or SakuraBackground(canvas_size).render(0.0)

    def step(self, dt):
        self.time += dt

    def render(self):
        return self.frame

    def _load_scene_image(self):
        deco_path = Path(__file__).parent / 'deco'
        for name in ('bigpixelrei.png', 'bigpixelrei.jpg'):
            candidate = deco_path / name
            if not candidate.exists():
                continue
            try:
                img = Image.open(candidate).convert('RGBA')
                if img.size != self.size:
                    img = img.resize(self.size, Image.Resampling.LANCZOS)
                try:
                    border_rgb = hex_to_rgb('#1e3a8a')
                    border_rgba = (border_rgb[0], border_rgb[1], border_rgb[2], 255)
                    border_width = max(2, int(min(img.size) * 0.012))
                    draw = ImageDraw.Draw(img)
                    for offset in range(border_width):
                        draw.rectangle(
                            [offset, offset, img.width - 1 - offset, img.height - 1 - offset],
                            outline=border_rgba
                        )
                except Exception:
                    pass
                return img
            except Exception:
                return None
        return None


class BlueScale(tk.Canvas):
    def __init__(
        self,
        master,
        from_=0.0,
        to=100.0,
        *,
        length=200,
        variable=None,
        command=None,
        bg=None,
        troughcolor=None,
        knob_color=None,
        active_color=None,
        knob_image=None,
        knob_width=None,
        knob_height=None,
        knob_offset=0.0,
        trough_height=6,
        extra_top=0.0,
        **kwargs
    ):
        bg = COLORS['bg'] if bg is None else bg
        super().__init__(master, bg=bg, highlightthickness=0, bd=0, **kwargs)
        self.from_ = float(from_)
        self.to = float(to)
        self.length = float(length)
        self.bg_color = bg
        self.variable = variable or tk.DoubleVar(value=self.from_)
        self.command = command
        self.trough_color = troughcolor or COLORS['slider_trough']
        self.knob_color = knob_color or COLORS['dark']
        self.active_color = active_color or COLORS['active']
        self.knob_image = knob_image
        self.knob_offset = float(knob_offset)
        self.extra_top = max(0.0, float(extra_top))
        if knob_width is None:
            if self.knob_image:
                knob_width = self.knob_image.width()
            else:
                knob_width = 16.0
        if knob_height is None:
            if self.knob_image:
                knob_height = self.knob_image.height()
            else:
                knob_height = 16.0
        self.knob_width = float(knob_width)
        self.knob_height = float(knob_height)
        self.trough_height = float(trough_height)
        self._suppress_trace = False
        self._dragging = False
        self._active_state = False

        margin = self.knob_width / 2.0 + 2.0
        self._margin = margin
        canvas_width = int(self.length + margin * 2)
        track_span = max(self.knob_height, self.trough_height)
        canvas_height = int(self.extra_top + track_span + 12)
        self.configure(width=canvas_width, height=canvas_height)
        self._center_y = self._compute_center(canvas_height)

        self.trough_id = self.create_rectangle(0, 0, 0, 0, fill=self.trough_color, outline=self.trough_color, width=0)
        self.knob_outline_id = None
        if self.knob_image:
            self.knob_id = self.create_image(0, 0, image=self.knob_image)
            self.knob_highlight_id = None
        else:
            self.knob_id = self.create_oval(0, 0, 0, 0, fill=self.knob_color, outline='', width=0)
            self.knob_outline_id = self.create_oval(0, 0, 0, 0, outline=COLORS['text'], width=1)
            self.knob_highlight_id = None

        self.bind('<Configure>', self._on_resize)
        self.bind('<Button-1>', self._on_press)
        self.bind('<B1-Motion>', self._on_drag)
        self.bind('<ButtonRelease-1>', self._on_release)

        self.variable.trace_add('write', self._on_variable_write)
        self._update_static()
        self.set(self.variable.get())

    # Canvas already provides bind/unbind semantics we rely on in the rest of the code.

    def _on_variable_write(self, *_):
        if self._suppress_trace:
            return
        try:
            value = float(self.variable.get())
        except Exception:
            value = self.from_
        self._update_knob(self._clamp(value))

    def _on_resize(self, event):
        available = max(event.width - self._margin * 2.0, 10.0)
        self.length = float(available)
        self._center_y = self._compute_center(event.height)
        self._update_static()
        self._update_knob(self.get())

    def _compute_center(self, canvas_height):
        desired = self.extra_top + self.knob_height / 2.0 - self.knob_offset
        min_center = self.knob_height / 2.0 - self.knob_offset
        max_center = canvas_height - self.knob_height / 2.0 - self.knob_offset
        return max(min_center, min(desired, max_center))

    def _on_press(self, event):
        self.focus_set()
        self._dragging = True
        self._set_active(True)
        self._update_from_event(event)

    def _on_drag(self, event):
        if not self._dragging:
            return
        self._update_from_event(event)

    def _on_release(self, _event):
        if not self._dragging:
            return
        self._dragging = False
        self._set_active(False)

    def _set_active(self, is_active):
        if self.knob_image:
            self._active_state = is_active
            return
        if self.knob_id:
            color = self.active_color if is_active else self.knob_color
            self.itemconfigure(self.knob_id, fill=color)
        if self.knob_highlight_id:
            self.itemconfigure(
                self.knob_highlight_id,
                state='normal' if is_active else 'hidden'
            )
        self._active_state = is_active

    def _update_from_event(self, event):
        span = self.to - self.from_
        if span == 0:
            return
        usable = max(self.length, 1.0)
        ratio = (event.x - self._margin) / usable
        value = self.from_ + max(0.0, min(1.0, ratio)) * span
        self.set(value)

    def _update_static(self):
        start = self._margin
        end = start + self.length
        top = self._center_y - self.trough_height / 2.0
        bottom = self._center_y + self.trough_height / 2.0
        self.coords(self.trough_id, start, top, end, bottom)

    def _update_knob(self, value):
        self._suppress_trace = True
        self.variable.set(value)
        self._suppress_trace = False
        center = round(self._value_to_x(value))
        knob_center_y = round(self._center_y + self.knob_offset)
        if self.knob_image:
            self.coords(self.knob_id, center, knob_center_y)
        else:
            x0 = center - self.knob_width / 2.0
            x1 = center + self.knob_width / 2.0
            y0 = knob_center_y - self.knob_height / 2.0
            y1 = knob_center_y + self.knob_height / 2.0
            self.coords(self.knob_id, x0, y0, x1, y1)
            if self.knob_outline_id:
                self.coords(self.knob_outline_id, x0, y0, x1, y1)
            if self.knob_highlight_id:
                shrink = 2.0
                self.coords(self.knob_highlight_id, x0 + shrink, y0 + shrink, x1 - shrink, y1 - shrink)
                if not self._active_state:
                    self.itemconfigure(self.knob_highlight_id, state='hidden')
        self.tag_raise(self.knob_id)
        if self.knob_outline_id:
            self.tag_raise(self.knob_outline_id)

    def _value_to_x(self, value):
        span = self.to - self.from_
        if span == 0:
            return self._margin
        ratio = (value - self.from_) / span
        ratio = max(0.0, min(1.0, ratio))
        return self._margin + ratio * self.length

    def _clamp(self, value):
        return max(min(value, max(self.from_, self.to)), min(self.from_, self.to))

    def set(self, value):
        try:
            value = float(value)
        except Exception:
            value = self.from_
        value = self._clamp(value)
        self._update_knob(value)
        if self.command:
            try:
                self.command(f"{value:.10g}")
            except Exception:
                pass

    def get(self):
        try:
            return float(self.variable.get())
        except Exception:
            return self.from_

    def apply_theme(self, *, bg=None, trough=None, knob=None, active=None, outline=None):
        if bg is not None:
            self.bg_color = bg
            self.configure(bg=bg)
        if trough is not None:
            self.trough_color = trough
            self.itemconfigure(self.trough_id, fill=trough, outline=trough)
        if not self.knob_image:
            if knob is not None:
                self.knob_color = knob
                if not self._active_state and self.knob_id:
                    self.itemconfigure(self.knob_id, fill=knob)
            if active is not None:
                self.active_color = active
                if self._active_state and self.knob_id:
                    self.itemconfigure(self.knob_id, fill=active)
        if self.knob_outline_id:
            outline_color = outline or COLORS['text']
            self.itemconfigure(self.knob_outline_id, outline=outline_color)
        self.tag_raise(self.knob_id)
        if self.knob_outline_id:
            self.tag_raise(self.knob_outline_id)

    def __getitem__(self, key):
        if key == 'from':
            return self.from_
        if key == 'to':
            return self.to
        raise KeyError(key)

    def cget(self, option):
        if option == 'sliderlength':
            return self.knob_width
        if option == 'from':
            return self.from_
        if option == 'to':
            return self.to
        if option == 'length':
            return self.length
        return super().cget(option)


class MiffyPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("REI Music Player")
        self.theme = 'light'
        self.light_mode_icon = None
        self.dark_mode_icon = None
        self.theme_button = None
        self.bg_widgets = []
        self.text_widgets = []
        self.button_widgets = []
        self.header_frame = None
        self.main_frame = None
        self.progress_frame = None
        self.left_fill = None
        self.spacer = None
        self.button_frame = None
        self.volume_frame = None
        self.vol_slider_holder = None
        self.canvas = None
        self.progress_slider = None
        self.vol_slider = None
        self.progress_deco_label = None
        self._theme_animation = None
        self._theme_animation_id = None
        self.canvas_size = CANVAS_SIZE
        width = max(420, self.canvas_size[0] + 120)
        height = self.canvas_size[1] + 380
        self.root.geometry(f"{width}x{height}")
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS['bg'])
        self.scene = SakuraScene(self.canvas_size)
        self._scene_photo = None
        self._scene_photo_source = None

        self.songs = []
        self.idx = 0
        self.playing = False
        self.scrubbing = False
        self.was_playing_before_seek = False
        self.elapsed = 0.0
        self.duration = 0.0
        self.play_start_offset = 0.0
        self.play_start_monotonic = 0.0
        self.last_anim_tick = time.perf_counter()

        self._suppress_vol_callback = False
        self.is_muted = False
        self.last_volume = 100.0

        self.play_img = None
        self.pause_img = None

        self.load_assets()
        self.setup_ui()
        self._refresh_theme_ui(refresh_scene=False)
        self.load_music()
        self.animate()
        self.update_display()


    def load_assets(self):
        assets_path = Path(__file__).parent / 'assets'
        self.play_img = self._load_photo(assets_path, 'blueresume-removebg-preview.png', (68, 68))
        self.pause_img = self._load_photo(assets_path, 'bluepause-removebg-preview.png', (68, 68))
        self.back_img = self._load_photo(assets_path, 'leftarrow-removebg-preview.png', (44, 44))
        self.next_img = self._load_photo(assets_path, 'rightarrow-removebg-preview.png', (44, 44))
        self.vol_on_img = self._load_photo(assets_path, 'volumeon-removebg-preview.png', (40, 40))
        self.vol_off_img = self._load_photo(assets_path, 'volumeoff-removebg-preview.png', (40, 40))

        deco_path = Path(__file__).parent / 'deco'
        self.vol_heart_img = None
        self.vol_knob_img = self._load_photo(deco_path, 'pixelreiheart-removebg-preview.png', (44, 44))
        self.progress_deco_img = self._load_photo(deco_path, 'shinjipixelchair-removebg-preview.png', (64, 64))
        self.progress_knob_img = self._load_photo(deco_path, 'reidrag-removebg-preview.png', (40, 40))
        self.light_mode_icon = self._load_photo(deco_path, 'lightmodestars-removebg-preview.png', (32, 32))
        self.dark_mode_icon = self._load_photo(deco_path, 'darkmodemoon-removebg-preview.png', (32, 32))
        self.vol_heart_label = None
        self.vol_heart_item = None

    def _load_photo(self, folder, filename, size):
        try:
            img = Image.open(folder / filename).convert('RGBA')
            img.thumbnail(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    def setup_ui(self):
        self.main_frame = tk.Frame(self.root, bg=COLORS['bg'])
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)
        main_frame = self.main_frame

        self.header_frame = tk.Frame(main_frame, bg=COLORS['bg'])
        self.header_frame.pack(fill=tk.X, pady=(0, 2))

        if self.dark_mode_icon or self.light_mode_icon:
            initial_icon = self.dark_mode_icon if self.theme == 'light' and self.dark_mode_icon else self.light_mode_icon
            self.theme_button = tk.Label(
                self.header_frame,
                image=initial_icon,
                bg=COLORS['bg'],
                cursor='hand2',
                bd=0,
                highlightthickness=0
            )
            if initial_icon:
                self.theme_button.image = initial_icon
            else:
                self.theme_button.config(text='🌙', fg=COLORS['text'])
            self.theme_button.pack(side=tk.RIGHT)
            self.theme_button.bind('<Button-1>', self.toggle_theme)
        else:
            self.theme_button = tk.Label(
                self.header_frame,
                text='🌙',
                bg=COLORS['bg'],
                fg=COLORS['text'],
                cursor='hand2'
            )
            self.theme_button.pack(side=tk.RIGHT)
            self.theme_button.bind('<Button-1>', self.toggle_theme)

        self.canvas = tk.Canvas(
            main_frame,
            width=self.canvas_size[0],
            height=self.canvas_size[1],
            bg=COLORS['bg'],
            highlightthickness=0
        )
        self.canvas.pack(pady=(0, 8))

        self.title_label = tk.Label(
            main_frame,
            text="No song",
            font=("Arial", 11, 'bold'),
            fg=COLORS['text'],
            bg=COLORS['bg'],
            wraplength=min(self.canvas_size[0] - 40, 520)
        )
        self.title_label.pack(pady=(0, 4))

        self.time_label = tk.Label(
            main_frame,
            text="00:00 / 00:00",
            font=("Courier", 9),
            fg=COLORS['text'],
            bg=COLORS['bg']
        )
        self.time_label.pack()

        self.progress_frame = tk.Frame(main_frame, bg=COLORS['bg'])
        self.progress_frame.pack(fill=tk.X, pady=6)
        progress_frame = self.progress_frame

        self.progress_var = tk.DoubleVar(value=0.0)
        self.left_fill = tk.Frame(progress_frame, bg=COLORS['bg'])
        self.left_fill.pack(side=tk.LEFT, padx=(0, 8), anchor='n')
        left_fill = self.left_fill

        if self.progress_deco_img:
            left_fill.pack_propagate(False)
            left_fill.configure(
                width=self.progress_deco_img.width(),
                height=self.progress_deco_img.height() + 20
            )
            self.progress_deco_label = tk.Label(
                left_fill,
                image=self.progress_deco_img,
                bg=COLORS['bg'],
                bd=0,
                highlightthickness=0
            )
            self.progress_deco_label.pack(anchor='n')
        else:
            self.progress_deco_label = None

        self.progress_slider = BlueScale(
            progress_frame,
            from_=0,
            to=100,
            length=self.canvas_size[0] - 120,
            variable=self.progress_var,
            bg=COLORS['bg'],
            troughcolor=COLORS['slider_trough'],
            knob_color=COLORS['dark'],
            active_color=COLORS['slider_active'],
            knob_image=self.progress_knob_img,
            knob_width=None,
            knob_height=None,
            knob_offset=18.0
        )
        self.progress_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.progress_slider.bind('<Button-1>', self.on_seek_start, add='+')
        self.progress_slider.bind('<B1-Motion>', self.on_seek_drag, add='+')
        self.progress_slider.bind('<ButtonRelease-1>', self.on_seek_end, add='+')

        self.spacer = tk.Frame(progress_frame, bg=COLORS['bg'], width=4)
        self.spacer.pack(side=tk.LEFT)

        self.button_frame = tk.Frame(main_frame, bg=COLORS['bg'])
        self.button_frame.pack(pady=(2, 0))
        button_frame = self.button_frame

        self.back_btn = tk.Label(
            button_frame,
            bg=COLORS['bg'],
            cursor='hand2',
            bd=0,
            highlightthickness=0
        )
        self.back_btn.pack(side=tk.LEFT, padx=4)
        if self.back_img:
            self.back_btn.config(image=self.back_img)
            self.back_btn.image = self.back_img
        else:
            self.back_btn.config(text='<<', fg=COLORS['text'], font=("Arial", 14, 'bold'))
            self.back_btn.image = None
        self.back_btn.bind('<Button-1>', lambda _e: self.prev())

        self.play_btn = tk.Label(
            button_frame,
            bg=COLORS['bg'],
            cursor='hand2',
            bd=0,
            highlightthickness=0
        )
        self.play_btn.pack(side=tk.LEFT, padx=8)
        self.play_btn.bind('<Button-1>', lambda _e: self.toggle_play())

        self.next_btn = tk.Label(
            button_frame,
            bg=COLORS['bg'],
            cursor='hand2',
            bd=0,
            highlightthickness=0
        )
        self.next_btn.pack(side=tk.LEFT, padx=4)
        if self.next_img:
            self.next_btn.config(image=self.next_img)
            self.next_btn.image = self.next_img
        else:
            self.next_btn.config(text='>>', fg=COLORS['text'], font=("Arial", 14, 'bold'))
            self.next_btn.image = None
        self.next_btn.bind('<Button-1>', lambda _e: self.next())

        self.volume_frame = tk.Frame(main_frame, bg=COLORS['bg'])
        self.volume_frame.pack(fill=tk.X, pady=(10, 0))
        volume_frame = self.volume_frame

        self.vol_btn = tk.Label(
            volume_frame,
            bg=COLORS['bg'],
            cursor='hand2',
            bd=0,
            highlightthickness=0
        )
        self.vol_btn.pack(side=tk.LEFT, padx=(24, 0), pady=(18, 0), anchor='n')
        self.vol_btn.bind('<Button-1>', lambda _e: self.toggle_mute())

        self.vol_slider_holder = tk.Frame(volume_frame, bg=COLORS['bg'])
        self.vol_slider_holder.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.vol_slider_holder.pack_propagate(False)

        self.vol_var = tk.DoubleVar(value=100.0)
        knob_height = self.vol_knob_img.height() if self.vol_knob_img else 24
        heart_pad = knob_height + 10

        heart_extra = 0.0
        self.vol_slider = BlueScale(
            self.vol_slider_holder,
            from_=0,
            to=100,
            length=260,
            variable=self.vol_var,
            command=self.vol_change,
            bg=COLORS['bg'],
            troughcolor=COLORS['slider_trough'],
            knob_color='#93c5fd',
            active_color='#bfdbfe',
            knob_image=self.vol_knob_img,
            extra_top=heart_extra
        )
        self.vol_slider.pack(anchor='w', pady=(16, 0), padx=(0, 0))
        self.vol_slider.bind('<Configure>', lambda _e: self._update_volume_heart_position(), add='+')
        holder_height = heart_pad + int(getattr(self.vol_slider, 'knob_height', 26) + abs(getattr(self.vol_slider, 'knob_offset', 0.0))) + 60
        self.vol_slider_holder.configure(height=holder_height)

        self.bg_widgets = [
            self.main_frame,
            self.header_frame,
            self.canvas,
            self.progress_frame,
            self.left_fill,
            self.spacer,
            self.button_frame,
            self.volume_frame,
            self.vol_slider_holder
        ]
        if self.progress_deco_label:
            self.bg_widgets.append(self.progress_deco_label)
        if self.theme_button:
            self.bg_widgets.append(self.theme_button)

        self.text_widgets = [self.title_label, self.time_label]
        self.button_widgets = [self.back_btn, self.play_btn, self.next_btn, self.vol_btn]

        self.vol_heart_item = None
        self._apply_volume(self.vol_var.get())
        self._update_play_button()
        self._update_volume_button()
        self.root.after(200, self._update_volume_heart_position)

    def toggle_theme(self, _event=None):
        target = 'dark' if self.theme == 'light' else 'light'
        self._set_theme(target, animate=True)

    def _set_theme(self, mode, refresh_scene=True, animate=False):
        theme_map = DARK_THEME if mode == 'dark' else LIGHT_THEME
        if animate:
            self._start_theme_animation(mode, theme_map, refresh_scene)
            return
        if self._theme_animation_id is not None:
            try:
                self.root.after_cancel(self._theme_animation_id)
            except Exception:
                pass
            self._theme_animation_id = None
        self._theme_animation = None
        self.theme = mode
        COLORS.clear()
        COLORS.update(theme_map)
        self._refresh_theme_ui(refresh_scene=refresh_scene)

    def _start_theme_animation(self, mode, theme_map, refresh_scene):
        if self._theme_animation_id is not None:
            try:
                self.root.after_cancel(self._theme_animation_id)
            except Exception:
                pass
            self._theme_animation_id = None
        start_colors = {key: hex_to_rgb(COLORS.get(key, theme_map.get(key, '#000000'))) for key in theme_map}
        target_colors = {key: hex_to_rgb(theme_map[key]) for key in theme_map}
        self._theme_animation = {
            'start_time': time.perf_counter(),
            'duration': 0.45,
            'start_colors': start_colors,
            'target_colors': target_colors,
            'target_map': theme_map,
            'refresh_scene': refresh_scene
        }
        self.theme = mode
        self._step_theme_animation()

    def _step_theme_animation(self):
        data = self._theme_animation
        if not data:
            return
        elapsed = time.perf_counter() - data['start_time']
        duration = max(0.05, data.get('duration', 0.3))
        progress = max(0.0, min(1.0, elapsed / duration))
        eased = progress * progress * (3.0 - 2.0 * progress)
        for key, target_rgb in data['target_colors'].items():
            start_rgb = data['start_colors'].get(key, target_rgb)
            mixed = tuple(start_rgb[i] + (target_rgb[i] - start_rgb[i]) * eased for i in range(3))
            COLORS[key] = rgb_to_hex(mixed)
        self._refresh_theme_ui(refresh_scene=False)
        if progress >= 1.0:
            COLORS.clear()
            COLORS.update(data['target_map'])
            self._refresh_theme_ui(refresh_scene=data['refresh_scene'])
            self._theme_animation = None
            self._theme_animation_id = None
            return
        self._theme_animation_id = self.root.after(16, self._step_theme_animation)

    def _refresh_theme_ui(self, refresh_scene=True):
        colors = COLORS
        self.root.configure(bg=colors['bg'])
        for widget in getattr(self, 'bg_widgets', []):
            if widget is not None:
                try:
                    widget.configure(bg=colors['bg'])
                except Exception:
                    pass
        for label in getattr(self, 'text_widgets', []):
            if label is not None:
                try:
                    label.configure(bg=colors['bg'], fg=colors['text'])
                except Exception:
                    pass
        for btn in getattr(self, 'button_widgets', []):
            if btn is not None:
                try:
                    btn.configure(bg=colors['bg'])
                    if not getattr(btn, 'image', None):
                        btn.configure(fg=colors['text'])
                except Exception:
                    pass

        if self.theme_button:
            try:
                self.theme_button.configure(bg=colors['bg'])
                icon = self.light_mode_icon if self.theme == 'dark' else self.dark_mode_icon
                if icon:
                    self.theme_button.configure(image=icon, text='')
                    self.theme_button.image = icon
                else:
                    self.theme_button.configure(
                        text='☀️' if self.theme == 'dark' else '🌙',
                        fg=colors['text']
                    )
            except Exception:
                pass

        if self.progress_deco_label:
            try:
                self.progress_deco_label.configure(bg=colors['bg'])
            except Exception:
                pass

        if self.canvas:
            try:
                self.canvas.configure(bg=colors['bg'])
            except Exception:
                pass

        if self.progress_slider:
            self.progress_slider.apply_theme(
                bg=colors['bg'],
                trough=colors['slider_trough'],
                knob=colors['dark'],
                active=colors['slider_active'],
                outline=colors['text']
            )
        if self.vol_slider:
            self.vol_slider.apply_theme(
                bg=colors['bg'],
                trough=colors['slider_trough'],
                outline=colors['text']
            )

        if refresh_scene:
            self.scene = SakuraScene(self.canvas_size)
            self._scene_photo = None
            self._scene_photo_source = None

    def load_music(self):
        try:
            music_dir = Path(__file__).parent / 'music'
            files = list(music_dir.glob('*.mp3'))

            def _song_priority(path):
                name = path.stem.lower()
                if "cruel" in name and "angel" in name:
                    return (0, name)
                if "komm" in name and "susser" in name:
                    return (1, name)
                return (2, name)

            self.songs = sorted(files, key=_song_priority)
            if self.songs:
                self.load_song(0)
            else:
                self.title_label.config(text="Add MP3s to the music folder")
        except Exception:
            self.songs = []

    def load_song(self, index):
        if not self.songs:
            return
        self.idx = index % len(self.songs)
        song_path = self.songs[self.idx]
        try:
            pygame.mixer.music.load(str(song_path))
        except Exception:
            messagebox.showerror("Playback Error", f"Could not load {song_path.name}")
            return
        try:
            audio = MP3(song_path)
            self.duration = float(audio.info.length)
        except Exception:
            self.duration = 0.0
        self.elapsed = 0.0
        self.playing = False
        self.play_start_offset = 0.0
        self.play_start_monotonic = 0.0
        self.progress_var.set(0.0)
        self.title_label.config(text=song_path.stem)
        self.update_time()
        self._update_play_button()

    def toggle_play(self):
        if not self.songs:
            messagebox.showwarning("No Songs", "No songs were found in the music folder.")
            return
        if self.playing:
            self._pause_playback()
        else:
            self._start_playback(self.elapsed)
        self._update_play_button()

    def _start_playback(self, start_time):
        start_time = max(0.0, min(start_time, self.duration if self.duration else start_time))
        try:
            pygame.mixer.music.play(loops=0, start=start_time)
        except Exception:
            pygame.mixer.music.play()
            try:
                pygame.mixer.music.set_pos(start_time)
            except Exception:
                pass
        self.play_start_offset = start_time
        self.play_start_monotonic = time.perf_counter()
        self.playing = True
        self._apply_volume(self.vol_var.get())

    def _pause_playback(self):
        try:
            current = self._current_playback_position()
            if current is not None:
                self.elapsed = current
        except Exception:
            pass
        try:
            pygame.mixer.music.pause()
        except Exception:
            pass
        self.playing = False

    def prev(self):
        if not self.songs:
            return
        was_playing = self.playing
        self._pause_playback()
        self.load_song(self.idx - 1)
        if was_playing:
            self._start_playback(0.0)
        self._update_play_button()

    def next(self):
        if not self.songs:
            return
        was_playing = self.playing
        self._pause_playback()
        self.load_song(self.idx + 1)
        if was_playing:
            self._start_playback(0.0)
        self._update_play_button()

    def _current_playback_position(self):
        try:
            pos = pygame.mixer.music.get_pos()
            if pos < 0:
                return self.elapsed
            return self.play_start_offset + (pos / 1000.0)
        except Exception:
            return self.elapsed

    def _slider_ratio_from_event(self, event):
        widget = event.widget
        width = widget.winfo_width()
        if hasattr(widget, 'length') and hasattr(widget, '_margin'):
            usable = max(1.0, float(getattr(widget, 'length', width)))
            margin = float(getattr(widget, '_margin', 0.0))
            ratio = (event.x - margin) / usable
        else:
            ratio = event.x / width if width else 0.0
        return max(0.0, min(1.0, ratio))

    def _update_elapsed_from_ratio(self, ratio):
        if self.duration > 0:
            self.elapsed = ratio * self.duration
        else:
            self.elapsed = 0.0
        self.progress_var.set(ratio * 100.0)

    def on_seek_start(self, event):
        if self.duration <= 0:
            return 'break'
        self.scrubbing = True
        self.was_playing_before_seek = self.playing
        if self.playing:
            self._pause_playback()
        ratio = self._slider_ratio_from_event(event)
        self._update_elapsed_from_ratio(ratio)
        self.update_time()
        return 'break'

    def on_seek_drag(self, event):
        if self.duration <= 0 or not self.scrubbing:
            return 'break'
        ratio = self._slider_ratio_from_event(event)
        self._update_elapsed_from_ratio(ratio)
        self.update_time()
        return 'break'

    def on_seek_end(self, event):
        if self.duration <= 0:
            self.scrubbing = False
            self.was_playing_before_seek = False
            return 'break'
        ratio = self._slider_ratio_from_event(event)
        self._update_elapsed_from_ratio(ratio)
        self.scrubbing = False
        self._start_playback(self.elapsed)
        if not self.was_playing_before_seek:
            self._pause_playback()
        self.was_playing_before_seek = False
        self.update_time()
        self._update_play_button()
        return 'break'

    def vol_change(self, value):
        if self._suppress_vol_callback:
            return
        try:
            level = float(value)
        except Exception:
            level = float(self.vol_var.get())
        self._apply_volume(level)

    def toggle_mute(self):
        if self.is_muted:
            restored = self.last_volume if self.last_volume > 0 else 100.0
            self._set_volume_slider(restored)
        else:
            current = self.vol_var.get()
            if current > 0:
                self.last_volume = current
            self._set_volume_slider(0.0)

    def _set_volume_slider(self, value):
        self._suppress_vol_callback = True
        self.vol_var.set(value)
        self.vol_slider.set(value)
        self._suppress_vol_callback = False
        self._apply_volume(value)

    def _apply_volume(self, value):
        value = max(0.0, min(100.0, float(value)))
        if value > 0:
            self.last_volume = value
        try:
            pygame.mixer.music.set_volume(value / 100.0)
        except Exception:
            pass
        self.is_muted = value <= 0
        self._update_volume_button()
        self._update_volume_heart_position()

    def _update_volume_button(self):
        img = self.vol_off_img if self.is_muted else self.vol_on_img
        if img:
            self.vol_btn.config(image=img, text="")
        else:
            self.vol_btn.config(image='', text="OFF" if self.is_muted else "ON")
        self.vol_btn.image = img

    def _update_volume_heart_position(self):
        slider = getattr(self, 'vol_slider', None)
        heart_item = getattr(self, 'vol_heart_item', None)
        if not self.vol_heart_img or slider is None or heart_item is None:
            return
        slider.update_idletasks()
        try:
            slider_from = float(slider['from'])
            slider_to = float(slider['to'])
        except Exception:
            slider_from = 0.0
            slider_to = 100.0
        span = slider_to - slider_from
        if span == 0:
            ratio = 0.0
        else:
            ratio = (float(self.vol_var.get()) - slider_from) / span
        ratio = max(0.0, min(1.0, ratio))
        if hasattr(slider, 'length') and hasattr(slider, '_margin'):
            usable = max(1.0, float(slider.length))
            margin = float(slider._margin)
            x_pos = margin + ratio * usable
            knob_center_y = float(getattr(slider, '_center_y', slider.winfo_height() / 2.0)) + float(getattr(slider, 'knob_offset', 0.0))
        else:
            width = max(1, slider.winfo_width())
            slider_len = float(slider.cget('sliderlength') or 0)
            usable = max(0.0, width - slider_len)
            x_pos = slider_len / 2.0 + ratio * usable
            knob_center_y = slider.winfo_height() / 2.0
        img_h = self.vol_heart_img.height()
        knob_h = float(getattr(slider, 'knob_height', img_h))
        desired_y = knob_center_y - knob_h / 2.0 - img_h / 2.0 - 4
        min_y = img_h / 2.0 + 2.0
        heart_y = max(min_y, desired_y)
        slider.coords(heart_item, x_pos, heart_y)
        slider.itemconfigure(heart_item, state='normal')
        slider.tag_raise(heart_item)

    def _update_play_button(self):
        img = self.play_img if self.playing else self.pause_img
        if img:
            self.play_btn.config(image=img, text="")
        else:
            self.play_btn.config(image='', text='>' if self.playing else '||')
        self.play_btn.image = img

    def update_time(self):
        elapsed = max(0, int(self.elapsed))
        total = max(0, int(self.duration))
        es = f"{elapsed // 60:02d}:{elapsed % 60:02d}"
        ts = f"{total // 60:02d}:{total % 60:02d}"
        self.time_label.config(text=f"{es} / {ts}")

    def animate(self):
        now = time.perf_counter()
        dt = now - self.last_anim_tick
        self.last_anim_tick = now
        dt = max(0.0, min(dt, 0.12))
        self.scene.step(dt)
        try:
            frame = self.scene.render()
            if self._scene_photo_source is not frame:
                self._scene_photo_source = frame
                self._scene_photo = ImageTk.PhotoImage(frame)
            photo = self._scene_photo
            if photo:
                self.canvas.delete('scene')
                self.canvas.create_image(
                    self.canvas_size[0] // 2,
                    self.canvas_size[1] // 2,
                    image=photo,
                    tags='scene'
                )
                self.canvas.image = photo
        except Exception:
            pass
        self.root.after(33, self.animate)

    def update_display(self):
        busy = False
        try:
            busy = pygame.mixer.music.get_busy()
        except Exception:
            busy = False
        if self.playing:
            current = self._current_playback_position()
            if current is not None:
                self.elapsed = min(current, self.duration) if self.duration else current
        if not busy and self.playing and self.duration and self.elapsed >= self.duration - 0.05:
            self.playing = False
            self.elapsed = self.duration
            self._update_play_button()
        if self.duration > 0 and not self.scrubbing:
            ratio = max(0.0, min(1.0, self.elapsed / self.duration))
            self.progress_var.set(ratio * 100.0)
        self.update_time()
        self.root.after(120, self.update_display)


def main():
    root = tk.Tk()
    MiffyPlayer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
