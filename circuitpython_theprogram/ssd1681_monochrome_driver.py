# SSD1681 E-Paper Display Driver (No Red Buffer Version)
from machine import Pin, SPI
import time
from ssd1681_driver_fonts import FONT_8X8

CMD_SW_RESET = 0x12
CMD_GATE_DRIVING_VOLTAGE = 0x01
CMD_DATA_ENTRY_MODE = 0x11
CMD_SET_RAM_X_RANGE = 0x44
CMD_SET_RAM_Y_RANGE = 0x45
CMD_SET_RAM_X_COUNTER = 0x4E
CMD_SET_RAM_Y_COUNTER = 0x4F
CMD_WRITE_RAM_BW = 0x24
CMD_WRITE_RAM_RED = 0x26  # Kept as a dummy command so the hardware doesn't hang

CMD_LOAD_LUT = 0x22
CMD_ACTIVATE_DISPLAY = 0x20
CMD_DISPLAY_UPDATE = 0x22
CMD_MASTER_ACTIVATE = 0x20
CMD_DEEP_SLEEP = 0x10
CMD_SOFT_START = 0x0C

UPDATE_MODE_FULL = 0xF7  
DATA_ENTRY_MODE_DEFAULT = 0x03  

COLOR_WHITE = 0
COLOR_BLACK = 1

ORIENTATION_0 = 0    
ORIENTATION_90 = 1   
ORIENTATION_180 = 2  
ORIENTATION_270 = 3  

class SSD1681:
    
    def __init__(self, spi, cs, dc, rst, busy, width=200, height=200, orientation=ORIENTATION_0):
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.busy = busy
        self.width = width
        self.height = height
        self.orientation = orientation
        
 
        self._buffer_size = width * height // 8
        self.buffer = bytearray([0xFF] * self._buffer_size)  # White background
        
        self._init_pins()
    
    def _init_pins(self):
        self.cs.init(Pin.OUT, value=1)
        self.dc.init(Pin.OUT, value=0)
        self.rst.init(Pin.OUT, value=1)
        self.busy.init(Pin.IN, Pin.PULL_UP)
    
    def _command(self, cmd, data=None):
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytearray([cmd]))
        self.cs.value(1)
        time.sleep_ms(1)
        if data is not None:
            self._data(data)
    
    def _data(self, data):
        self.dc.value(1)
        self.cs.value(0)
        if isinstance(data, (list, tuple)):
            self.spi.write(bytearray(data))
        elif isinstance(data, (bytes, bytearray)):
            self.spi.write(data)
        else:
            self.spi.write(bytearray([data]))
        self.cs.value(1)
        time.sleep_ms(1)
    
    def _wait_busy(self, timeout_ms=15000):
        start = time.ticks_ms()
        while self.busy.value() and (time.ticks_diff(time.ticks_ms(), start) < timeout_ms):
            time.sleep_ms(50)
        return time.ticks_diff(time.ticks_ms(), start) < timeout_ms
    
    def _reset_ram_address(self):
        self._command(CMD_SET_RAM_X_COUNTER, [0x00])
        self._command(CMD_SET_RAM_Y_COUNTER, [0x00, 0x00])
    
    def _map_coordinates(self, x, y):
        if self.orientation == ORIENTATION_0:
            hw_x = self.width - 1 - x
            hw_y = self.height - 1 - y
        elif self.orientation == ORIENTATION_90:
            hw_x = y
            hw_y = self.width - 1 - x
        elif self.orientation == ORIENTATION_180:
            hw_x = x
            hw_y = y
        elif self.orientation == ORIENTATION_270:
            hw_x = self.height - 1 - y
            hw_y = x
        else:
            hw_x = self.width - 1 - x
            hw_y = self.height - 1 - y
        
        byte_index = (hw_y * self.width + hw_x) // 8
        bit_index = hw_x % 8
        return byte_index, bit_index
    
    def _set_pixel_buffer(self, x, y, buffer, value):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        byte_index, bit_index = self._map_coordinates(x, y)
        if value:
            buffer[byte_index] |= (0x80 >> bit_index)
        else:
            buffer[byte_index] &= ~(0x80 >> bit_index)
    
    def reset(self):
        self.rst.value(1)
        time.sleep_ms(200)
        self.rst.value(0)
        time.sleep_ms(10)
        self.rst.value(1)
        time.sleep_ms(200)
    
    def _power_on_sequence(self):
        self.reset()
        self._wait_busy()
        self._command(CMD_SW_RESET)
        self._wait_busy()
    
    def _configure_ram(self):
        self._command(CMD_GATE_DRIVING_VOLTAGE, [0xC7, 0x00, 0x00])
        self._command(CMD_DATA_ENTRY_MODE, [DATA_ENTRY_MODE_DEFAULT])
        x_end = (self.width // 8) - 1
        self._command(CMD_SET_RAM_X_RANGE, [0x00, x_end])
        y_end_low = (self.height - 1) & 0xFF
        y_end_high = ((self.height - 1) >> 8) & 0xFF
        self._command(CMD_SET_RAM_Y_RANGE, [0x00, 0x00, y_end_low, y_end_high])
        self._reset_ram_address()
    
    def _load_lut(self):
        self._command(CMD_LOAD_LUT, [0xB1])
        self._command(CMD_ACTIVATE_DISPLAY)
        self._wait_busy()
    
    def init(self):
        self._power_on_sequence()
        self._configure_ram()
        self._load_lut()
        self._wait_busy()
    
    def clear(self):
        """Clear only the main buffer to white"""
        for i in range(self._buffer_size):
            self.buffer[i] = 0xFF
    
    def pixel(self, x, y, color=COLOR_BLACK):
        x, y = int(x), int(y)
        if color == COLOR_WHITE:
            self._set_pixel_buffer(x, y, self.buffer, True)
        elif color == COLOR_BLACK:
            self._set_pixel_buffer(x, y, self.buffer, False)
    
    def custom_text(self, string, x, y, color=COLOR_BLACK, font_size=1):
        x, y = int(x), int(y)
        char_width = 8 * font_size
        for char_index, char in enumerate(string):
            char_x = x + (char_index * char_width)
            if char_x + char_width > self.width:
                break
            self._draw_char(char, char_x, y, color, font_size)
            
    def is_busy(self):
        return self.busy.value() == 1
    
    def _draw_char(self, char, x, y, color, font_size=1):
        char_data = FONT_8X8.get(char, FONT_8X8[' '])
        for row in range(8):
            for col in range(8):
                if char_data[7-col] & (1 << row):
                    for scale_row in range(font_size):
                        for scale_col in range(font_size):
                            pixel_x = x + (7 - col) * font_size + scale_col
                            pixel_y = y + row * font_size + scale_row
                            self.pixel(pixel_x, pixel_y, color)
    
    def show(self):
        """Push black/white buffer, and send dummy blank data to satisfy the red RAM requirement"""
        # Write black/white image data
        self._reset_ram_address()
        self._command(CMD_WRITE_RAM_BW, self.buffer)
        
        # Send a blank dummy payload to the red RAM so the tri-color controller doesn't complain
        self._reset_ram_address()
        dummy_red = bytearray([0x00] * self._buffer_size)
        self._command(CMD_WRITE_RAM_RED, dummy_red)
        
        # Trigger display update
        self._command(CMD_SOFT_START, [0xD7, 0xD6, 0x9D])
        self._command(CMD_DISPLAY_UPDATE, [UPDATE_MODE_FULL])
        self._command(CMD_MASTER_ACTIVATE)
        
        self._wait_busy()
    
    def sleep(self):
        self._command(CMD_DEEP_SLEEP, [0x01])

def create_display(
    cs_pin=5,
    dc_pin=4,
    rst_pin=1,
    busy_pin=0,
    sck_pin=2,
    mosi_pin=3,
    orientation=ORIENTATION_0,
    width=200,
    height=200
):
    spi = SPI(0, baudrate=1000000, polarity=0, phase=0, sck=Pin(sck_pin), mosi=Pin(mosi_pin))
    return SSD1681(
        spi=spi,
        cs=Pin(cs_pin),
        dc=Pin(dc_pin), 
        rst=Pin(rst_pin),
        busy=Pin(busy_pin),
        orientation=orientation,
        width=width,
        height=height
    )
