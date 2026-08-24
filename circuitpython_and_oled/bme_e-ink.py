import board 
import busio 
import displayio 
import fourwire
import terminalio 
import time 
from adafruit_display_text import label 
import adafruit_ssd1681
import adafruit_bme680
import digitalio
import math
import random



def calculate_true_rh(t_measured, rh_measured, t_actual):
    b = 17.67
    c = 243.5
    sat_p_measured = math.exp((b * t_measured) / (c + t_measured))
    actual_vapor_p = (rh_measured / 100.0) * sat_p_measured
    sat_p_actual = math.exp((b * t_actual) / (c + t_actual))
    return min(100.0, max(0.0, (actual_vapor_p / sat_p_actual) * 100.0))

class Reading:
    def __init__(self):
        self.log = []
        self.last_change = None
    
    def addReading(self, r):
        if len(self.log) == 6:
            self.log.pop(0)
        
        self.log.append(r)
    
    def shouldUpdate(self):
        if self.last_change == None:
            self.last_change = self.log[0]
            return True
        
        if len(self.log) == 6:
            mean = sum(self.log) / len(self.log)
            
            if abs(mean - self.log[5]) > 0.2 or (self.last_change and abs(self.last_change - mean) >= 0.1): # idk think about it
                self.last_change = self.log[5]
                return True
        
        return False
    
    def getVal(self):
        return self.log[-1]
    
    
### setup & sensors
displayio.release_displays() 

i2c_sensor = busio.I2C(scl=board.GP27, sda=board.GP26, frequency=400_000) 
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c_sensor, address=0x77) 

spi = busio.SPI(clock=board.GP2, MOSI=board.GP3)
display_bus = fourwire.FourWire(spi, command=board.GP4, chip_select=board.GP5, reset=board.GP1, baudrate=1000000)
time.sleep(1)
display = adafruit_ssd1681.SSD1681(display_bus, width=200, height=200, busy_pin=board.GP0, rotation=0)
display.auto_refresh = False





### state elements and stuff
temp_label = None
press_label = None
alt_label = None
hum_label = None

upd = False

temp = Reading()
press = Reading()
alt = Reading()
rh = Reading()



# GROUP 1

bme680.sea_level_pressure = 1014.9

splash1 = displayio.Group()
temp_label = label.Label(terminalio.FONT, text="Temp: ---- C", color=0x000000, scale=2, x=10, y=40)
hum_label = label.Label(terminalio.FONT, text="Hum: ---- %", color=0x000000, scale=2, x=10, y=90)

splash1.append(temp_label) 
splash1.append(hum_label)
    
# temp and hum
def initscreen1():
    global upd
    
    display.root_group = splash1
    upd = True

temp_offset = -2

def screen1():
    global temp, rh, temp_label, hum_label, upd
    
    t_temp = bme680.temperature
    t_rh = bme680.relative_humidity
    calibrated_temp = t_temp + temp_offset
    calibrated_rh = calculate_true_rh(t_temp, t_rh, calibrated_temp)
    
    temp.addReading(calibrated_temp)
    rh.addReading(calibrated_rh)
    
    if temp.shouldUpdate() or rh.shouldUpdate():
    
        temp_label.text = f"Temp:  {calibrated_temp:.1f} C"
        hum_label.text = f"Hum: {calibrated_rh:.1f} %"
    
        upd = True


# GROUP 2

splash2 = displayio.Group()
press_label = label.Label(terminalio.FONT, text="Press: ---- hPa", color=0x000000, scale=1, x=10, y=50)
alt_label = label.Label(terminalio.FONT, text="Alt: ---- m", color=0x000000, scale=1, x=10, y=90)
splash2.append(press_label)
splash2.append(alt_label)

#alt and press
def initscreen2():
    global upd
    
    display.root_group = splash2
    upd = True

def screen2():
    global press, alt, press_label, alt_label, upd
    
    press.addReading(bme680.pressure)
    alt.addReading(bme680.altitude)
    
    if press.shouldUpdate() or alt.shouldUpdate():
    
        press_label.text = f"Press: {press.getVal():.1f} hPa"
        alt_label.text = f"Alt: {alt.getVal():.1f} m"
        
        upd = True


# GROUP 3
# emoticons
def initscreen3():
    global upd
    
    splash3 = displayio.Group()
    emoticons_text = '''(^_^) (o_o) (>_<)
    (-_-) (TvT) (^o^)
(u_u) (^3^) (x_x)
    (._.) (*_*) (@v@)'''

    happy_label = label.Label(
        terminalio.FONT,
        text=emoticons_text,
        color=0x000000,
        scale=2,
        x=0, y=30
    )
    splash3.append(happy_label) 
    display.root_group = splash3
    
    upd = True

def screen3():
    pass


# GROUP 5
# volatile compounds?



### Loop Setup
next_button = digitalio.DigitalInOut(board.GP8) 
next_button.switch_to_input(pull=digitalio.Pull.UP)
page = 1

next_button_pressed_last = False

initscreen1()

def pagers():
    global page
    
    page += 1
    if page > 3:
        page = 1
        
    # each
    if page == 1:
        initscreen1()
    elif page == 2:
        initscreen2()
    elif page == 3:
        initscreen3()

while True:
    next_button_pressed = not (next_button.value)
    
    # BUTTON DOWN EVENT
    if next_button_pressed and not next_button_pressed_last:
        pagers()
        
    time.sleep(0.08) # button debounce
        
    next_button_pressed_last = next_button_pressed
    
    if page == 1: 
        screen1() 
    elif page == 2: 
        screen2()
    elif page == 3:
        screen3()
        
    if upd == True:
        display.refresh()
        upd = False

    time.sleep(0.05)