# Everything aesthetic for the widget 

import ctypes 
import os

# Pixel font used in NSO 
PIXEL_FONT_FAMILY = "PixelMplus10"

def _load_pixel_fonts():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        fonts_dir = os.path.join(base_dir, "fonts")
        FR_PRIVATE = 0x10 
        for fname in ("PixelMplus10-Regular.ttf", "PixelMplus10-Bold.ttf"):
            path = os.path.join(fonts_dir, fname) 
            if os.path.exists(path):
                ctypes.windll.gdi32.AddFontResourceExW(ctypes.c_wchar_p(path), FR_PRIVATE, 0)
    except Exception:
        pass 