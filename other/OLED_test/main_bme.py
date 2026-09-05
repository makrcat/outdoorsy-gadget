import board 
import busio 
import displayio 
import i2cdisplaybus 
import terminalio 
import time 
from adafruit_display_text import label 
import adafruit_displayio_sh1106 
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

i2c_sensor = busio.I2C(scl=board.GP5, sda=board.GP4, frequency=400_000) 
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c_sensor, address=0x77) 

screen = busio.I2C(scl=board.GP7, sda=board.GP6, frequency=400_000) 
screen_bus = i2cdisplaybus.I2CDisplayBus(screen, device_address=0x3C) 
display = adafruit_displayio_sh1106.SH1106(screen_bus, width=132, height=64)
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

splash1 = displayio.Group(x=2, y=0)
temp_label = label.Label(terminalio.FONT, text="Temp: ---- C", color=0xFFFFFF, x=10, y=24)
hum_label = label.Label(terminalio.FONT, text="Hum: ---- %", color=0xFFFFFF, x=10, y=36)

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

splash2 = displayio.Group(x=2, y=0)
press_label = label.Label(terminalio.FONT, text="Press: ---- hPa", color=0xFFFFFF, x=10, y=24)
alt_label = label.Label(terminalio.FONT, text="Alt: ---- m", color=0xFFFFFF, x=10, y=35)
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
    
    splash3 = displayio.Group(x=2, y=0)
    emoticons_text = '''(^_^) (o_o) (>_<)
    (-_-) (TvT) (^o^)
(u_u) (^3^) (x_x)
    (._.) (*_*) (@v@)'''

    happy_label = label.Label(
        terminalio.FONT,
        text=emoticons_text,
        color=0xFFFFFF,
        x=0, y=5
    )
    splash3.append(happy_label) 
    display.root_group = splash3
    
    upd = True

def screen3():
    pass


# GROUP 4
# dino game lmao

splash4 = displayio.Group(x=2, y=0)

dino_txt = label.Label(terminalio.FONT, text="R", color=0xFFFFFF, x=15, y=45)
score_txt = label.Label(terminalio.FONT, text="Score: 0", color=0xFFFFFF, x=10, y=12)
ground_txt = label.Label(terminalio.FONT, text="_" * 22, color=0xFFFFFF, x=0, y=48)

splash4.append(dino_txt)
splash4.append(score_txt)
splash4.append(ground_txt)

floor_y = 45
cactus_speed = 4

cacti = []
game_score = 0
game_over = False
is_jumping = False
dino_txt.y = 45
dino_velocity = 0

distance_covered_by_cactus = 0
criteria_gap = 50
gap_range = 20

score_txt.text = "Score: 0"

def newCactusAt(here):
    global cacti
    cactusLabel = label.Label(terminalio.FONT, text="Y", color=0xFFFFFF, x=here, y=45)
    cacti.append(cactusLabel)
    splash4.append(cactusLabel)
    
def initscreen4():
    global upd, cacti, splash4
    global dino_velocity, dino_txt, is_jumping
    global distance_covered_by_cactus
    global game_score, game_over
    
    
    display.root_group = splash4
    
    for cactus in cacti:
        splash4.remove(cactus)


    ###
    cacti = []
    game_score = 0
    game_over = False
    is_jumping = False
    dino_txt.y = 45
    dino_velocity = 0
    
    distance_covered_by_cactus = 0
    dino_txt.text = "R"
    score_txt.text = "Score: 0"
    ###
    
    newCactusAt(120)
    
    upd = True
    

def screen4():
    global floor_y, dino_velocity, is_jumping
    global cacti, cactus_speed
    global distance_covered_by_cactus, criteria_gap, gap_range
    global game_score, game_over
    global upd

    print(cacti[-1].x)
    
    if game_over:
        return
    

    # spawning mechanic
    if cacti[-1].x <= 128:
        distance_covered_by_cactus = 128 - cacti[-1].x
        if distance_covered_by_cactus > criteria_gap:
            
            next_spawn = cacti[-1].x + criteria_gap + random.randint(0, gap_range)
            newCactusAt(next_spawn)
            distance_covered_by_cactus = 0 # for peace of mind
    
    
    remove = None
    # everything cactus I guess
    for cactus in cacti[::-1]:
        # moving it
        cactus.x -= cactus_speed
        

        # hitboxes
        if abs(cactus.x - dino_txt.x) < 6 and dino_txt.y > 38: #?????????????????????
            game_over = True
            dino_txt.text = ":("
            score_txt.text = f'''GG! Final: {game_score}\n\n\nLong press to exit'''
            
            upd = True
            break
        
        if cactus.x < -5:
            remove = cactus
            
    
    if remove != None:
        splash4.remove(remove)
        cacti.remove(remove)
        game_score += 1
        score_txt.text = f"Score: {game_score}"

        
    
    if is_jumping:
        dino_txt.y += dino_velocity
        dino_velocity += 1
        
        if dino_txt.y >= floor_y:
            dino_txt.y = floor_y
            is_jumping = False
            dino_velocity = 0
            
    
    upd = True
    
 
    '''
newCactusAt(100)

def screen4():
    global upd

    for cactus in cacti:
        cactus.x -= 4

    upd = True
'''
    
    
# GROUP 5
# volatile compounds?



### Loop Setup
next_button = digitalio.DigitalInOut(board.GP15) 
next_button.switch_to_input(pull=digitalio.Pull.UP)
page = 4

next_button_pressed_last = False
button_press_start = 0.0

initscreen4()

def pagers():
    global page
    
    page += 1
    if page > 4:
        page = 1
        
    # each
    if page == 1:
        initscreen1()
    elif page == 2:
        initscreen2()
    elif page == 3:
        initscreen3()
    elif page == 4:
        initscreen4()

while True:
    next_button_pressed = not (next_button.value)
    
    # BUTTON DOWN EVENT
    if next_button_pressed and not next_button_pressed_last:
        button_press_start = time.monotonic()
    
        if page == 4:
            if game_over:
                initscreen4() # reset if dead
            elif not is_jumping: # jump if alive!
                is_jumping = True
                dino_velocity = -5 
               
        else:
            # pages
            pagers()

    ## long press duration
    elif next_button_pressed:
        if page == 4:
            current_time = time.monotonic()
            press_duration = current_time - button_press_start
            
            if press_duration >= 3:  
                pagers()
                
                
                
                
    time.sleep(0.08) # button debounce
        
    next_button_pressed_last = next_button_pressed
    
    if page == 1: 
        screen1() 
    elif page == 2: 
        screen2()
    elif page == 3:
        screen3()
    elif page == 4:
        screen4()
        
    if upd == True:
        display.refresh()
        upd = False

    time.sleep(0.05)