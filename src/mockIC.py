
import random

class MockBME680:
    def __init__(self):
        self._temp = 24.5
        self._hum = 50.0
        self._press = 942
        self._alt = 200.0
        self._gas = 25

    @property
    def temperature(self):
        # Add a tiny random walk to simulate real sensor noise
        self._temp += random.uniform(-0.1, 0.1)
        return self._temp

    @property
    def relative_humidity(self):
        self._hum += random.uniform(-0.2, 0.2)
        return max(0.0, min(100.0, self._hum))

    @property
    def pressure(self):
        self._press += random.uniform(-0.05, 0.05)
        return self._press

    @property
    def altitude(self):
        self._alt += random.uniform(-0.02, 0.02)
        return self._alt
    
    @property
    def gas(self):
        self._gas += random.uniform(-0.02, 0.02)
        return self._gas

bme680 = MockBME680()
bme680.sea_level_pressure = 1017.9