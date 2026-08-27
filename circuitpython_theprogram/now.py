from machine import Pin
import time
from ssd1681_monochrome_driver import create_display, COLOR_BLACK, ORIENTATION_0

# --- Setup Display ---
# Using your working pins: cs=5, dc=4, rst=1, busy=0, sck=2, mosi=3
display = create_display(orientation=ORIENTATION_0)
display.init()

# --- Setup Button ---
# Button connected to GP8 (with internal pull-up)
next_button = Pin(8, Pin.IN, Pin.PULL_UP)

# State variables
page = 1
max_pages = 3

next_button_pressed_last = False
button_press_start = 0.0

def draw_screen(current_page):
    """Draw the content for the current page onto the e-paper buffer"""
    display.clear()  # Clear buffer to all white
    
    # Header showing page number
    display.text(f"--- PAGE {current_page} of {max_pages} ---", 10, 10, COLOR_BLACK, font_size=1)
    
    # Screen-specific content
    if current_page == 1:
        display.text("Temperature & Humidity", 10, 40, COLOR_BLACK, font_size=1)
        display.text("Temp: 22.5 C", 10, 70, COLOR_BLACK, font_size=2)
        display.text("Hum:  45.0 %", 10, 100, COLOR_BLACK, font_size=2)
    elif current_page == 2:
        display.text("Pressure & Altitude", 10, 40, COLOR_BLACK, font_size=1)
        display.text("Press: 1013 hPa", 10, 70, COLOR_BLACK, font_size=1)
        display.text("Alt:   120.0 m", 10, 100, COLOR_BLACK, font_size=1)
    elif current_page == 3:
        display.text("Status / Emoticons", 10, 40, COLOR_BLACK, font_size=1)
        display.text("(^_^)", 10, 70, COLOR_BLACK, font_size=2)
        display.text("System OK!", 10, 110, COLOR_BLACK, font_size=1)
        
    # Footer instruction
    display.text("Press button for next", 10, 175, COLOR_BLACK, font_size=1)
    
    # Push the buffer to the physical e-paper display
    display.show()
    print(f"Screen updated to Page {current_page}")

print("Starting e-paper screen flip test. Press your button on GP8!")

# Initial draw on startup
draw_screen(page)

while True:
    # Active low button (pressed = False/0)
    next_button_pressed = not next_button.value()
    
    # Button Down Event (Just pressed)
    if next_button_pressed and not next_button_pressed_last:
        button_press_start = time.ticks_ms()
        
        # Advance page
        page += 1
        if page > max_pages:
            page = 1
            
        # Update physical display
        draw_screen(page)

    # Optional: Long press detection example
    elif next_button_pressed:
        press_duration = time.ticks_diff(time.ticks_ms(), button_press_start)
        if press_duration >= 3000: # 3 seconds
            print("\n[Long Press Detected! Putting display to sleep...]")
            display.sleep()
            
    next_button_pressed_last = next_button_pressed
    
    # Small debounce delay
    time.sleep_ms(50)