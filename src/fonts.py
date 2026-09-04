import os
from adafruit_bitmap_font import bitmap_font

font_path = os.path.join(os.path.dirname(__file__), "../fonts/HaxorMedium-12.bdf")
HAXOR = bitmap_font.load_font(font_path)

font_path = os.path.join(os.path.dirname(__file__), "../fonts/9x18B.bdf")
NINE = bitmap_font.load_font(font_path)

font_path = os.path.join(os.path.dirname(__file__), "../fonts/9x18.bdf")
NINE_REG = bitmap_font.load_font(font_path)

font_path = os.path.join(os.path.dirname(__file__), "../fonts/Pragati_22.bdf")
PRAGATI_22 = bitmap_font.load_font(font_path)

font_path = os.path.join(os.path.dirname(__file__), "../fonts/Pragati_42.bdf")
PRAGATI_42 = bitmap_font.load_font(font_path)

font_path = os.path.join(os.path.dirname(__file__), "../fonts/Pragati_54.bdf")
PRAGATI_54 = bitmap_font.load_font(font_path)

font_path = os.path.join(os.path.dirname(__file__), "../fonts/Bremlin-Regular-40.bdf")
BREMLIN_40 = bitmap_font.load_font(font_path)

font_path = os.path.join(os.path.dirname(__file__), "../fonts/Spleen5x8.bdf")
SPLEEN_EIGHT = bitmap_font.load_font(font_path)
