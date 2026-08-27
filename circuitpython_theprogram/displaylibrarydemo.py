# SPDX-FileCopyrightText: 2021 Jose David M.
# SPDX-License-Identifier: MIT

import time
import board
import busio
import displayio
import terminalio
import i2cdisplaybus
import adafruit_displayio_sh1106
import math
from adafruit_displayio_layout.widgets.cartesian import Cartesian

# Fonts used for the Dial tick labels
tick_font = terminalio.FONT


displayio.release_displays()

# my setup
i2c_oled = busio.I2C(scl=board.GP7, sda=board.GP6)
display_bus = i2cdisplaybus.I2CDisplayBus(i2c_oled, device_address=0x3C)
display = adafruit_displayio_sh1106.SH1106(display_bus, width=128, height=64)

display.auto_refresh = False

# Create a Cartesian widget
my_plane = Cartesian(
    x=40,
    y=10,
    width=110, 
    height=50,
    axes_color=0xFFFFFF,  # axes line color
    axes_stroke=1,  # axes lines width in pixels
    tick_color=0xFFFFFF,  # ticks color
    major_tick_stroke=1,  # ticks width in pixels
    major_tick_length=3,  # ticks length in pixels
    tick_label_font=tick_font,  # the font used for the tick labels
    font_color=0xFFFFFF,  # ticks line color
)


my_group = displayio.Group()
my_group.append(my_plane)
display.root_group = my_group   # add high level Group to the display

done = False

while not done:
    
    for i in range(0, 100, 2):
        my_plane.add_plot_line(i, 15 * math.sin(i / 5) + 40)
        my_plane.update_pointer(i, 15 * math.sin(i / 5) + 40)
        time.sleep(0.05)
    
        display.refresh()
    
    done = True
    