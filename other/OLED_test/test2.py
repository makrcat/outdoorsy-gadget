import board
import busio
import digitalio
import time

from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.ssd1681 import Adafruit_SSD1681


spi = busio.SPI(clock=board.GP2, MOSI=board.GP3)

cs = digitalio.DigitalInOut(board.GP1)
dc = digitalio.DigitalInOut(board.GP4)
rst = digitalio.DigitalInOut(board.GP5)
busy = digitalio.DigitalInOut(board.GP0)

display = Adafruit_SSD1681(
    200,
    200,
    spi,
    cs_pin=cs,
    dc_pin=dc,
    sramcs_pin=None,
    rst_pin=rst,
    busy_pin=busy,
)

display.rotation = 1

WHITE = Adafruit_EPD.WHITE
BLACK = Adafruit_EPD.BLACK
RED = Adafruit_EPD.RED




display.fill(WHITE)

display.text(
    "hello world",
    10,
    10,
    RED
)


display.display()

print("Done")

while True:
    time.sleep(1)