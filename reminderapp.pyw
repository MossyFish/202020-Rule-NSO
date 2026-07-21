"""
Draws the widget and functionality using the methods from the widget ui file.
"""
import ctypes
import importlib.util
import queue
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox

REQUIRED_PACKAGES = {"pystray": "pystray", "PIL": "Pillow"}

def _ensure_dependencies():
    # pip not in the exe
    if getattr(sys, "frozen", False):
        return 
    
    missing = [pip_name for module_name, pip_name in REQUIRED_PACKAGES.items() if importlib.util.find_spec(module_name) is None]

    if not missing:
        return
    
    result = subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", *missing], capture_output = True, text = True,)

    if result.returncode !=  0:
        messagebox.showerror(
            "20-20-20 Reminder Tool",
            "Couldn't automatically install required packages: " + ", ".join(missing) +
            "\n\Run this in your terminal:\n"
            "pip install -r requirements.txt\n\n" + result.stderr[-500:]
        )
        sys.exit(1)

_ensure_dependencies()

import pystray

from ui_elements import (
    THEME, ReminderPopup, _load_pixel_fonts, _rect, apply_theme,
    bind_icon_square, format_mmss, get_sec, make_button,
    make_chip, make_close, make_tray_icon, pixel_font,
    place_window, resize_window,
)
 
try:
    ctypes.windll.sh1core.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-5))
    except Exception:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(0)
        except Exception:
            pass

### Default settings
TIMER = 20
IDLE = 5
TICK_MS = 1000

APP_TITLE = "Eye Protector"
DRAG_CLICK_THRESHOLD = 4

NSO_DEFAULT = True

### Floating widget
class Widget(tk.Tk):
    COLLAPSED_W, COLLAPSED_H = 126, 36
    EXPANDED_W, EXPANDED_H = 329, 311

    # Creates the window and both its layouts
    def __init__(self):
        super().__init__()
        _load_pixel_fonts()
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        try:
            self.attributes("-alpha", 0.97)
        except tk.TclError:
            pass

        self.expanded = False
        self.timer_duration = TIMER * 60
        self.idle_threshold = IDLE * 60
        self.remaining = self.timer_duration
        self.manually_paused = False
        self.idle_paused = False
        self.popup_open = False
        self.NSO_theme = NSO_DEFAULT

        self._drag_data = {"x": 0, "y": 0, "moved": False}
        self._placed = False
        self._tray_icon = None
        self._tray_queue = queue.Queue()

        self._build_collapsed()
        self._build_expanded()
        apply_theme(self)
        self._refresh_layout()

        self.after(TICK_MS, self._tick)       

    ### Layout
    # Swaps between collapsed and expanded size + position
    def _refresh_layout(self):
        if self.expanded:
            self.collapsed.pack_forget()
            self.expanded_frame.pack()
            w, h = self.EXPANDED_W, self.EXPANDED_H
        else:
            self.expanded_frame.pack_forget()
            self.collapsed.pack()
            w, h = self.COLLAPSED_W, self.COLLAPSED_H

        if not self._placed:
            place_window(self, w, h)
            self._placed = True
        else:
            resize_window(self, w, h)
            
    ### Collapsed widget
    def _build_collapsed(self):
        W, H = self.COLLAPSED_W, self.COLLAPSED_H
        self.collapsed = tk.Frame(self, width = W, height = H)
        self.collapsed.pack_propagate(False) 

        self.c_border = self.collapsedself.c_gap = _rect(self.collapsed, 2, 2, W-4, H-4, "")
        self.c_fill = _rect(self.collapsed, 4, 4, W-8, H-8, "")
        self.c_icon = _rect(self.collapsed, 8, 8, 20, 20, "")
        self.time_label = tk.Label(self.collapsed, text = format_mmss(self.remaining), font = pixel_font(13, bold = True), cursor = "hand2")
        self.time_label.place(x = 32, y = 4, width = W-36, height = H-8)
        
        # Widget on click
        for w in (self.collapsed, self.c_gap, self.c_fill, self.time_label):
                  w.bind("<ButtonPress-1>", self._on_press)
                  w.bind("<B1-Motion>", self._on_drag)
                  w.bind("<ButtonRelease-1>", self._on_release)
                  
        # Square minimizes to system tray
        bind_icon_square(self.c_icon, self._on_press, self._on_drag, self._on_icon_release, self._theme)
                        
    ### Expanded widget
    def _build_expanded(self):
        W, H = self.EXPANDED_W, self.EXPANDED_H
        self.expanded_frame = tk.Frame(self, width = W, height = H)
        self.expanded_frame.pack_propagate(False)
        f = self.expanded_frame

        self.e_border = f
        self.e_gap = _rect(f, 3, 3, W-6, H-6, "")

        # Titlebar and content panel box
        self.e_titlebar_border = _rect(f, 7, 7, W-14, 35, "")
        self.e_titlebar = _rect(f, 9, 9, W-18, 31, "")

        self.e_panel_border = _rect(f, 7, 47, W-14, 245, "")
        self.e_panel = _rect(f, 9, 49, W-18, 241, "")

        self.e_icon = _rect(f, 15, 14, 21, 21, "")

        self.settings_label = tk.Label(f, text = "SETTINGS", font = pixel_font(10, bold = True), anchor = "w")
        self.settings_label.place(x = 42, y = 14, width = 210, height = 21)
        
        # Titlebar click expand/ collapse
        for w in (self.e_titlebar_border, self.e_titlebar,self.e_panel_border, self.e_panel, self.settings_label):
            w.bind("<ButtonPress-1>", self._on_press)
            w.bind("<B1-Motion>", self._on_drag)
            w.bind("<ButtonRelease-1>", self._on_release)

        # Square minimizes to system tray on click
        bind_icon_square(self.e_icon, self._on_press, self._on_drag, self._on_icon_release, self._theme)
        
        self.close_chip = make_close(f, 290, 13, 23, 23, lambda: (self.focus_set(), self.quit_app()), self._theme)

        self.star_chip = make_chip(f, 263, 13, 23, 23, "âœ¦", lambda: (self.focus_set(), self.toggle_theme()), self._theme)

        self.status_label = tk.Label(f, font = pixel_font(8))
        self.status_label.place(x = 9, y = 78, width = W - 18, height = 16)
        self.status_label.bind("<Button-1>", lambda e: self.focus_set())
                               
        self.big_time_label = tk.Label(f, text = format_mmss(self.remaining),font = pixel_font(22, bold = True))
        self.big_time_label.place(x = 9, y = 96, width = W - 18, height = 38)
        self.big_time_label.bind("<Button-1>", lambda e: self.focus_set())

        self.pause_shadow = _rect(f, 64, 156, 96, 35, "")
        self.pause_btn = make_button(f, 61, 153, 96, 35, "PAUSE", lambda: (self.focus_set(), self.toggle_pause()), self._theme)

        self.reset_shadow = _rect(f, 174, 156, 96, 36, "")
        self.reset_btn = make_button(f, 171, 153, 96, 36, "RESET", lambda: (self.focus_set(), self.reset_timer()), self._theme)

        self.timer_label = tk.Label(f, text = "REMIND EVERY (MIN)", font = pixel_font(10), anchor = "w")
        self.timer_label.place(x = 20, y = 203, width = 210, height = 20)
        self.timer_label.bind("<Button-1>", lambda e: self.focus_set())
        self.timer_spin = tk.Spinbox(f, from_ = 1, to = 180, justify = "center", font = pixel_font(11), command = self.apply_settings, relief = "flat")
        self.timer_spin.place(x = 234, y = 200, width = 70, height = 30)
        self.timer_spin.delete(0, "end")  
        self.timer_spin.insert(0, str(self.timer_duration // 60))
        self.timer_spin.bind("<FocusOut>", lambda e: self.apply_settings())
        self.timer_spin.bind("<Return>", lambda e: self.apply_settings())
        
        self.idle_label = tk.Label(f, text = "IDLE PAUSE (MIN)", font = pixel_font(10), anchor = "w")
        self.idle_label.place(x = 20, y = 245, width = 210, height = 20)
        self.idle_label.bind("<Button-1>", lambda e: self.focus_set())
        self.idle_spin = tk.Spinbox(f, from_ = 1, to = 60, justify = "center", font = pixel_font(11), command = self.apply_settings,relief = "flat")
        self.idle_spin.place(x = 234, y = 242, width = 70, height = 30)

        self.idle_spin.delete(0, "end")
        self.idle_spin.insert(0, str(self.idle_threshold // 60))
        self.idle_spin.bind("<FocusOut>", lambda e: self.apply_settings())
        self.idle_spin.bind("<Return>", lambda e: self.apply_settings())

        self.footer_chip = tk.Label(f, highlightthickness = 2)
        self.footer_chip.place(x = 10, y = 299, width = 51, height = 9)
        self.dots = []
        for i in range(3):
            border = _rect(f, 67 + i * 15, 299, 9, 9, "")
            inner = _rect(f, 69 + i * 15, 301, 5, 5, "")
            self.dots.append((border, inner))
                             
    ### Main loop
    # checks idle time and counts down then fires at 0 
    def _tick(self):
        idle = get_sec()

        if idle >= self.idle_threshold:
            if not self.manually_paused:
                self.idle_paused = True
        else:
            self.idle_paused = False 

        running = (not self.manually_paused and not self.idle_paused and not self.popup_open)
        
        if running:
            self.remaining -= 1
        
            if self.remaining <= 0:
                self._show_reminder()
                self._update_time_labels()  
        

        self._refresh_status()
        self.after(TICK_MS, self._tick)

        # Updates status textstate
        def _refresh_status(self):
            t = self._theme()
            if self.manually_paused:
                status_text = "PAUSED"
            elif self.idle_paused:
                status_text = "PAUSED (IDLE)"
            else:
                status_text = "RUNNING"

            color = t["hover"] if status_text != "RUNNING" else t["accent"]
            self.time_label.configure(fg=color)
            self.big_time_label.configure(fg=color)
            self.status_label.configure(text=status_text)
                
    def _update_time_labels(self):
        txt = format_mmss(self.remaining)
        self.time_label.configure(text=txt)
        self.big_time_label.configure(text=txt)
                            
    # Show popup n pause countdown
    def _show_reminder(self):
        self.popup_open = True
        minutes_passed = self.timer_duration // 60
        ReminderPopup(self, minutes_passed, on_close=self._on_reminder_closed, get_theme=self._theme)
                        
    # Reset countdown on close popup
    def _on_reminder_closed(self):
        self.popup_open = False
        self.remaining = self.timer_duration
        self._update_time_labels()
                        