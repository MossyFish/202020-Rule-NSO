# Everything aesthetic for the widget 

import ctypes 
import os
import tkinter as tk 
from PIL import Image, ImageDraw, ImageTk, ImageFont
import sys

# Pixel font used in NSO 
PIXEL_FONT_FAMILY = "PixelMplus10"

# Font load 
def _load_pixel_fonts():
    try:
        if getattr(sys, "frozen", False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        fonts_dir = os.path.join(base_dir, "fonts")
        FR_PRIVATE = 0x10
        for fname in ("PixelMplus10-Regular.ttf", "PixelMplus10-Bold.ttf"):
            path = os.path.join(fonts_dir, fname)
            if os.path.exists(path):
                ctypes.windll.gdi32.AddFontResourceExW(ctypes.c_wchar_p(path), FR_PRIVATE, 0)
    except Exception:
        pass

def pixel_font(size, bold=False):
    px = round(size * 96/72)
    return (PIXEL_FONT_FAMILY, -px, "bold" if bold else "normal")

# NSO Colors  
THEME = {   
    True: dict(
        border="#3617A5", widget_gap="#A2E9F1", popup_gap="#E8E0F7",
        fill="#EFCFED", panel="#FCF0FC", accent="#4D1DC0", hover="#E3A6ED",
        popup_titlebar="#E3E2E0", icon_hover="#3A1490",
    ),
    False: dict(
        border="#000000", widget_gap="#2a2a2a", popup_gap="#2a2a2a",
        fill="#242424", panel="#2b2b2b", accent="#ffffff", hover="#4a4a4a",
        popup_titlebar="#141414", icon_hover="#acacac",
    ),
}

# Idle detection 
class LAST_INPUT(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

# Get seconds since the last system wide input
def get_sec() -> float:
    lii = LAST_INPUT()
    lii.cbSize = ctypes.sizeof(LAST_INPUT) 
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
    millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime 
    return millis / 1000.0

def format_mmss(seconds: int) -> str:
    seconds = max(0, int(seconds))
    m, s = divmod(seconds, 60)
    return f"{m:02d}:{s:02d}"

# Fake processing 

def _rect(parent, x, y, w, h, bg):
    f = tk.Frame(parent, bg=bg)
    f.place(x=x, y=y, width=w, height=h)
    return f

def _text(parent, x, y, w, h, text, bg, fg, font, anchor = "center"):
    lbl = tk.Label(parent, text=text, bg=bg, fg=fg, font=font, anchor=anchor)
    lbl.place(x=x, y=y, width=w, height=h)
    return lbl

# Spawns the window in the top right
def place_window(win, w, h, margin=200, top=40):
    sw = win.winfo_screenwidth()
    x = sw - w - margin
    win.geometry(f"{w}x{h}+{x}+{top}")

def resize_window(win, w, h):
    x = win.winfo_x()
    y = win.winfo_y()
    win.geometry(f"{w}x{h}+{x}+{y}")

## Buttons 
def bind_icon_square(icon, on_press, on_drag, on_release, get_theme): 
    icon.configure(cursor="hand2")
    icon.bind("<ButtonPress-1>", on_press)
    icon.bind("<B1-Motion>", on_drag)
    icon.bind("<ButtonRelease-1>", on_release)
    icon.bind("<Enter>", lambda e: icon.configure(bg=get_theme()["icon_hover"]))
    icon.bind("<Leave>", lambda e: icon.configure(bg=get_theme()["accent"]))

def make_close(parent, x, y, w, h, command, get_theme):
    cv = tk.Canvas(parent, width=w, height=h, highlightthickness=2, bd=0, cursor="hand2")
    cv.place(x=x, y=y, width=w, height=h)
    cv.line1 = cv.create_line(1, 1, w-1, h-1, width=2)
    cv.line2 = cv.create_line(w-1, 1, 1, h-1, width=2)
    cv.bind("<Button-1>", lambda e: command())
    cv.bind("<Enter>", lambda e: cv.configure(bg=get_theme()["hover"]))
    cv.bind("<Leave>", lambda e: cv.configure(bg=get_theme()["fill"]))
    return cv

# redrawing this from scratch on every animation frame means re-reading the
# font file off disk ~60 times per click, which was noticeably janky - cache it
_toggle_font_cache = {}

def _get_toggle_font(scale):
    if scale in _toggle_font_cache:
        return _toggle_font_cache[scale]
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(base_dir, "fonts", "PixelMplus10-Bold.ttf")
        font = ImageFont.truetype(font_path, 14 * scale)
    except Exception:
        font = ImageFont.load_default()
    _toggle_font_cache[scale] = font
    return font


def _toggle_knob_x(canvas_w, canvas_h, scale, progress):
    left_x = scale * 4
    right_x = canvas_w - canvas_h + scale * 4
    return left_x + (right_x - left_x) * progress


def _render_toggle_image(colors, is_on, w, h, scale=4, progress=1.0):
    # draw big then shrink it to round the corners
    canvas_w, canvas_h = w * scale, h * scale
    img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    corner_radius = canvas_h // 2
    border_px = scale * 2

    track_color = colors["hover"] if is_on else colors["fill"]
    border_color = colors["border"]

    draw.rounded_rectangle([0, 0, canvas_w - 1, canvas_h - 1], radius=corner_radius, fill=border_color)
    draw.rounded_rectangle(
        [border_px, border_px, canvas_w - 1 - border_px, canvas_h - 1 - border_px],
        radius=corner_radius - border_px, fill=track_color,
    )

    label = "ON" if is_on else "OFF"
    font = _get_toggle_font(scale)
    bbox = draw.textbbox((0, 0), label, font=font)
    label_w, label_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

    if is_on:
        label_x = (canvas_w - canvas_h) // 2 - label_w // 2 + scale * 2
    else:
        label_x = canvas_w - (canvas_w - canvas_h) // 2 - label_w // 2 - scale * 2
    label_y = (canvas_h - label_h) // 2 - scale * 2

    draw.text((label_x, label_y), label, fill=colors["accent"], font=font)

    knob_diameter = canvas_h - scale * 8
    knob_x = _toggle_knob_x(canvas_w, canvas_h, scale, progress)
    knob_y = scale * 4
    draw.ellipse(
        [knob_x, knob_y, knob_x + knob_diameter, knob_y + knob_diameter],
        fill=colors["panel"], outline=border_color, width=border_px,
    )

    img = img.resize((w, h), Image.LANCZOS)
    return ImageTk.PhotoImage(img)

def make_toggle(parent, x, y, w, h, initial, command, get_theme):
    frame = tk.Frame(parent)
    frame.place(x=x, y=y, width=w, height=h)

    # The image switch
    switch = tk.Label(frame, cursor="hand2", bd=0)
    switch.place(x=0, y=0, width=w, height=h)
    switch.state = initial   
    switch.anim_progress = 1.0 if initial else 0.0
    switch.anim_id = None
    
    def render(progress):
        colors = get_theme()
        img = _render_toggle_image(colors, switch.state, w, h, scale=4, progress=progress)
        switch.image = img
        switch.configure(image=img, bg=colors["panel"])
        frame.configure(bg=colors["panel"])

    def animate():
        target = 1.0 if switch.state else 0.0
        diff = target - switch.anim_progress
        
        if abs(diff) < 0.05:
            switch.anim_progress = target
            render(switch.anim_progress)
            switch.anim_id = None
        else:
            switch.anim_progress += diff * 0.4
            render(switch.anim_progress)
            switch.anim_id = parent.after(16, animate)

    def redraw():
        if switch.anim_id is not None:
            parent.after_cancel(switch.anim_id)
            switch.anim_id = None
        switch.anim_progress = 1.0 if switch.state else 0.0
        render(switch.anim_progress)
        
    def on_click(e):
        switch.state = not switch.state
        if switch.anim_id is not None:
            parent.after_cancel(switch.anim_id)
            
        switch.anim_id = parent.after(16, animate)
        command(switch.state)
        
    switch.bind("<Button-1>", on_click)
    frame.redraw = redraw
    
    render(switch.anim_progress)
    return frame

def make_button(parent, x, y, w, h, text, command, get_theme):
    lbl = tk.Label(parent, text=text, font=pixel_font(10, bold=True), cursor="hand2", highlightthickness=1)
    lbl.place(x=x, y=y, width=w, height=h)
    lbl.bind("<Button-1>", lambda e: command())
    lbl.bind("<Enter>", lambda e: lbl.configure(bg=get_theme()["hover"]))
    lbl.bind("<Leave>", lambda e: lbl.configure(bg=get_theme()["fill"]))
    return lbl

def make_tray_icon(theme):
    size = 64
    pad = 12
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([pad, pad, size - pad, size - pad],
                    fill=theme["fill"], outline=theme["border"], width=6)
    return img

def make_chip(parent, x, y, w, h, text, command, get_theme):
    lbl = tk.Label(parent, text=text, font=pixel_font(9, bold=True), cursor="hand2", highlightthickness=2)
    lbl.place(x=x, y=y, width=w, height=h)
    lbl.bind("<Button-1>", lambda e: command())
    lbl.bind("<Enter>", lambda e: lbl.configure(bg=get_theme()["hover"]))
    lbl.bind("<Leave>", lambda e: lbl.configure(bg=get_theme()["fill"]))
    return lbl

# theme color change 
def apply_theme(app):
    t = app._theme()

    # Collapsed
    app.collapsed.configure(bg=t["border"])
    app.c_gap.configure(bg=t["widget_gap"])
    app.c_fill.configure(bg=t["fill"])
    app.c_icon.configure(bg=t["accent"])
    app.time_label.configure(bg=t["fill"], fg=t["accent"])

    # Expanded  
    app.expanded_frame.configure(bg=t["border"])
    app.e_gap.configure(bg=t["widget_gap"]) 
    app.e_titlebar_border.configure(bg=t["border"])
    app.e_titlebar.configure(bg=t["fill"])
    app.e_panel_border.configure(bg=t["border"])
    app.e_panel.configure(bg=t["panel"])
    app.e_icon.configure(bg=t["accent"])
    app.settings_label.configure(bg=t["fill"], fg=t["accent"])

    app.close_chip.configure(bg=t["fill"], highlightbackground=t["border"])
    app.close_chip.itemconfig(app.close_chip.line1, fill=t["accent"])
    app.close_chip.itemconfig(app.close_chip.line2, fill=t["accent"])
    app.star_chip.configure(bg=t["fill"], fg=t["accent"], highlightbackground=t["border"])

    app.status_label.configure(bg=t["panel"], fg=t["accent"])
    app.big_time_label.configure(bg=t["panel"], fg=t["accent"])

    app.pause_shadow.configure(bg=t["border"])
    app.reset_shadow.configure(bg=t["border"])
    app.pause_btn.configure(bg=t["fill"], fg=t["accent"], highlightbackground=t["border"])

    app.reset_btn.configure(bg=t["fill"], fg=t["accent"], highlightbackground=t["border"])

    app.timer_label.configure(bg=t["panel"], fg=t["accent"])
    app.idle_label.configure(bg=t["panel"], fg=t["accent"])
    for spin in (app.timer_spin, app.idle_spin):
        spin.configure(bg=t["fill"], fg=t["accent"], buttonbackground=t["fill"])

    app.footer_chip.configure(bg=t["hover"], highlightbackground=t["border"])

    for border, inner in app.dots:
            border.configure(bg=t["border"])
            inner.configure(bg=t["hover"])

    # Auto start button
    app.autostart_label.configure(bg=t["panel"], fg=t["accent"])
    app.autostart_toggle.redraw()
            
    app._refresh_status()

# Reminder popup
class ReminderPopup(tk.Toplevel):
    W, H = 486, 179
        
    # Draw popup layout with the theme 
    def __init__(self, master, minutes_passed, on_close, get_theme):
        super().__init__(master)
        self.on_close = on_close
        self.get_theme = get_theme    
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        
        t = get_theme()
        self.configure(bg=t["border"])
        self.body = tk.Frame(self, width=self.W, height=self.H, bg=t["border"])
        self.body.pack()
        self.body.pack_propagate(False)

        self.r_gap = _rect(self.body, 3, 3, self.W - 6, self.H - 6, t["popup_gap"])

        # Titlebar and content boxes
        self.r_titlebar_border = _rect(self.body, 5, 5, self.W - 10, 31, t["border"])
        self.r_titlebar = _rect(self.body, 7, 7, self.W - 14, 27, t["popup_titlebar"])

        self.r_content_border = _rect(self.body, 5, 41, self.W - 10, 124, t["border"])
        self.r_content = _rect(self.body, 7, 43, self.W - 14, 120, t["panel"])

        self.r_icon = _rect(self.body, 11, 11, 20, 20, t["accent"])
        self.alert_label = tk.Label(self.body, text="ALERT", font=pixel_font(10, bold=True), bg=t["popup_titlebar"], fg=t["accent"], anchor="w")
        self.alert_label.place(x=37, y=11, width=384, height=20)

        self.min_btn = self._chip(427, 11, 19, 18, "-", t["popup_titlebar"], self._close, anchor="sw", padx=3, pady=1)
        self.close_btn = self._chip(454, 11, 18, 18, "x", t["popup_titlebar"], self._close)
        
        msg = ( f"{minutes_passed} MINUTES HAVE PASSED.\n" "LOOK 20 FEET AWAY FOR 20 SECONDS NOW" )
        self.msg_label = tk.Label(self.body, text=msg, font=pixel_font(10), bg=t["panel"], fg=t["accent"], justify="left")
        self.msg_label.place(x=20, y=55, width=320, height=60)

        self.ok_shadow = _rect(self.body, 366, 125, 98, 30, t["border"])
        self.ok_btn = self._button(363, 122, 98, 30, "OK", self._close)

        self.footer_chip = tk.Label(self.body, bg=t["hover"], highlightbackground=t["border"], highlightthickness=2)
        self.footer_chip.place(x=7, y=167, width=58, height=9)
        self.dots = []
        
        for i in range(4):
            border = _rect(self.body, 71 + i * 12, 167, 9, 9, t["border"])
            inner = _rect(self.body, 73 + i * 12, 169, 5, 5, t["hover"])
            self.dots.append((border, inner))
        
        self.grab_set()
        self.focus_force()
        self._final_x = None    
        self._pop_in()

    # Popup minimize/ close icons
    def _chip(self, x, y, w, h, text, bg, command, anchor="center", padx=0, pady=0):
        t = self.get_theme()
        lbl = tk.Label(self.body, text=text, font=pixel_font(9, bold=True), bg=bg, fg=t["accent"], highlightbackground=t["border"], 
                       highlightthickness=2, cursor="hand2", anchor=anchor, padx=padx, pady=pady)
        lbl.place(x=x, y=y, width=w, height=h)
        lbl.bind("<Button-1>", lambda e: command())
        lbl.bind("<Enter>", lambda e: lbl.configure(bg=self.get_theme()["hover"]))
        lbl.bind("<Leave>", lambda e: lbl.configure(bg=bg))
        return lbl
    

    # Popup OK button
    def _button(self, x, y, w, h, text, command):
        t = self.get_theme()
        lbl = tk.Label(self.body, text=text, font=pixel_font(10, bold=True), bg=t["fill"], fg=t["accent"], highlightbackground=t["border"],
                        highlightthickness=1, cursor="hand2")
        lbl.place(x=x, y=y, width=w, height=h)
        lbl.bind("<Button-1>", lambda e: command())
        lbl.bind("<Enter>", lambda e: lbl.configure(bg=self.get_theme()["hover"]))
        lbl.bind("<Leave>", lambda e: lbl.configure(bg=self.get_theme()["fill"]))
        return lbl
    
    # Popup short animation 
    def _pop_in(self, step=0, total=8):
        if self._final_x is None:
            self.update_idletasks()
            sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
            self._final_x = (sw - self.W) // 2
            self._final_y = (sh - self.H) // 2

        frac = (step + 1) / total    
        try:
            self.attributes("-alpha", min(1.0, frac))
        except tk.TclError:
            pass    
        w = max(40, int(self.W * (0.6 + 0.4 * frac)))
        h = max(30, int(self.H * (0.6 + 0.4 * frac)))
        x = self._final_x + (self.W - w) // 2
        y = self._final_y + (self.H - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        if step < total - 1:
            self.after(15, lambda: self._pop_in(step + 1, total))
        else:
            self.geometry(f"{self.W}x{self.H}+{self._final_x}+{self._final_y}")

    # Callback then destroys the popup
    def _close(self):
        self.on_close()
        self.destroy()


            
