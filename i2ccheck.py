# SPDX-FileCopyrightText: 2017 Limor Fried for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# pylint: disable=broad-except, eval-used, unused-import

# Slightly modified so that it checks all the pins

"""CircuitPython I2C Device Address Scan"""
import time
import board
import busio

# List of potential I2C busses
ALL_I2C = ["board.I2C()", "board.STEMMA_I2C()", "busio.I2C(scl=board.GP5, sda=board.GP4)"]

###

# Generate all valid Raspberry Pi Pico I2C hardware pairs
for gp in range(0, 22):
    # Skip GP16-GP21 if they don't map cleanly, but check 0-21 standard pairs
    # RP2040 maps SDA to even pins, SCL to the next odd pin (e.g., GP0/GP1, GP4/GP5)
    if gp % 4 == 0 or gp % 4 == 2:
        sda_pin = f"board.GP{gp}"
        scl_pin = f"board.GP{gp+1}"
        ALL_I2C.append(f"busio.I2C(scl={scl_pin}, sda={sda_pin})")
    
    # RP2040 also supports shifting SCL to the even pin and SDA to the odd pin 
    # for certain blocks (e.g., GP2 as SCL, GP3 as SDA)
    elif gp % 4 == 1 or gp % 4 == 3:
        pass 

# Clean up any potential duplicates or pin errors on your specific board build
###

# Determine which busses are valid
found_i2c = []
for name in ALL_I2C:
    try:
        print("Checking {}...".format(name), end="")
        bus = eval(name)
        bus.unlock()
        found_i2c.append((name, bus))
        print("ADDED.")
    except Exception as e:
        print("SKIPPED:", e)

# Scan valid busses
if len(found_i2c):
    print("-" * 40)
    print("I2C SCAN")
    print("-" * 40)
    while True:
        for bus_info in found_i2c:
            name = bus_info[0]
            bus = bus_info[1]

            while not bus.try_lock():
                pass

            print(
                name,
                "addresses found:",
                [hex(device_address) for device_address in bus.scan()],
            )

            bus.unlock()

        time.sleep(2)
else:
    print("No valid I2C bus found.")
