import board
import busio
import displayio
import i2cdisplaybus
import terminalio
import time
from adafruit_display_text import label
import adafruit_displayio_sh1106
import adafruit_bmp280

# clear earlier connections?
displayio.release_displays()

# 400kHz I2C data highway for GP4 and GP5
i2c_sensor = busio.I2C(scl=board.GP5, sda=board.GP4, frequency=400_000)
# bmp data bus
bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c_sensor, address=0x77)

# 400kHz I2C data highway for GP6 and GP7, for the screen
screen = busio.I2C(scl=board.GP7, sda=board.GP6, frequency=400_000)
# wrap screen data bus around a displayio
screen_bus = i2cdisplaybus.I2CDisplayBus(screen, device_address=0x3C)

# there is an SH1106 OLED chip there with memory grid 132x64
display = adafruit_displayio_sh1106.SH1106(screen_bus, width=132, height=64)
# a grid. two left columns shifted
splash = displayio.Group(x=2, y=0)
# grid is assigned to the display memory
display.root_group = splash



# labels

bmp280.sea_level_pressure = 1017.7

temp_label = label.Label(terminalio.FONT, text="Temp: ---- C", color=0xFFFFFF, x=10, y=15)
splash.append(temp_label)

press_label = label.Label(terminalio.FONT, text="Press: ---- hPa", color=0xFFFFFF, x=10, y=32)
splash.append(press_label)

alt_label = label.Label(terminalio.FONT, text="Alt: ---- m", color=0xFFFFFF, x=10, y=49)
splash.append(alt_label)

# loop

def screen1():
    temp_label.text  = f"Temp:  {bmp280.temperature:.1f} C"
    press_label.text = f"Press: {bmp280.pressure:.1f} hPa"
    alt_label.text   = f"Alt:   {bmp280.altitude:.1f} m"

while True:

    screen1()
    
    ## updates here under the hood I guess
    # something.refresh()
    time.sleep(1.0)