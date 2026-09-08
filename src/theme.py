import displayio
import bitmaptools

BOX_PALETTE = displayio.Palette(2)
BOX_PALETTE[0] = 0x444444
BOX_PALETTE[1] = 0xFFFFFF

# Small Box (68x42)
SMALL_BOX_BITMAP = displayio.Bitmap(68, 42, 2)
bitmaptools.fill_region(SMALL_BOX_BITMAP, 0, 0, 68, 42, 1)
bitmaptools.fill_region(SMALL_BOX_BITMAP, 1, 1, 67, 41, 0)

# Desc Box (86x90)
DESC_BOX_BITMAP = displayio.Bitmap(86, 90, 2)
bitmaptools.fill_region(DESC_BOX_BITMAP, 0, 0, 86, 90, 1)
bitmaptools.fill_region(DESC_BOX_BITMAP, 1, 1, 85, 89, 0)