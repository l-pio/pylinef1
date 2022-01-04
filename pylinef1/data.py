from .misc import bytearray_to_int


class Distance:
    """Container for distance data."""
    def __init__(self, data):
        """Setup data container with received bytearray."""
        self.value = float(bytearray_to_int(data[0:7])) * 100E-12  # (m)
        self.velocity_overflow_flag = bool(data[9] & 1 << 3)  # (bool)
        self.laser_state_flag = bool(data[10] & 1 << 0)  # (bool)
        self.small_signal_level_flag = not bool(data[10] & 1 << 3)  # (bool)
        self.level = data[11]  # (unknown unit)


class Velocity:
    """Container for velocity data."""
    def __init__(self, data):
        """Setup data container with received bytearray."""
        self.value = float(bytearray_to_int(data[0:4])) * 100E-9  # (m/s)
        self.velocity_overflow_flag = bool(data[9] & 1 << 3)  # (bool)
        self.laser_state_flag = bool(data[10] & 1 << 0)  # (bool)
        self.small_signal_level_flag = not bool(data[10] & 1 << 3)  # (bool)
        self.level = data[11]  # (unknown unit)


class Meteo:
    """Container for meteo (air/material) data."""
    def __init__(self, data):
        """Setup data container with received bytearray."""
        self.sensor_id = bytearray_to_int(data[0:1])  # = [0,1,2,...]
        self.temperature = float(bytearray_to_int(data[1:3])) * 0.01  # (°C)
        self.humidity = bytearray_to_int(data[3:4])  # (%)
        self.battery = bytearray_to_int(data[4:5])  # (unknown unit)
        self.link = bytearray_to_int(data[5:6])  # (unknown unit)
        self.pressure = float(bytearray_to_int(data[6:8])) * 10  # (Pa)
