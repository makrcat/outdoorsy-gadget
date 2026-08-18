import board
import busio
import displayio
import i2cdisplaybus
import terminalio
import time
from adafruit_display_text import label
import adafruit_displayio_sh1106
import adafruit_bmp280

displayio.release_displays()

i2c_sensor = busio.I2C(scl=board.GP5, sda=board.GP4, frequency=400_000)
bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c_sensor, address=0x76)

screen = busio.I2C(scl=board.GP7, sda=board.GP6, frequency=400_000)
screen_bus = i2cdisplaybus.I2CDisplayBus(screen, device_address=0x3C)

bmp280.sea_level_pressure = 1017.7

display = adafruit_displayio_sh1106.SH1106(screen_bus, width=132, height=64)

splash = displayio.Group(x=2, y=0)
display.root_group = splash

temp_label = label.Label(terminalio.FONT, text="Temp: ---- C", color=0xFFFFFF, x=10, y=15)
splash.append(temp_label)

press_label = label.Label(terminalio.FONT, text="Press: ---- hPa", color=0xFFFFFF, x=10, y=32)
splash.append(press_label)

alt_label = label.Label(terminalio.FONT, text="Alt: ---- m", color=0xFFFFFF, x=10, y=49)
splash.append(alt_label)

while True:
    temp_label.text  = f"Temp:  {bmp280.temperature:.1f} C"
    press_label.text = f"Press: {bmp280.pressure:.1f} hPa"
    alt_label.text   = f"Alt:   {bmp280.altitude:.1f} m"
    time.sleep(1.0)