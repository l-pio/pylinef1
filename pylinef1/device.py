import serial
import threading
import queue
from time import sleep
from .misc import get_crc
from .data import Distance, Velocity, Meteo


# Commands to device
CMD_TD_READ_DISTANCE_ON = b'\xB0\x32'
CMD_TD_READ_DISTANCE_OFF = b'\xB0\x33'
CMD_TD_READ_VELOCITY_ON = b'\xB0\x34'
CMD_TD_READ_VELOCITY_OFF = b'\xB0\x35'
CMD_TD_DONT_SEND_ANY_STREAM_DATA = b'\xB0\x3C'
CMD_TD_DELETE_SMALL_SIGNAL_LEVEL_FLAG = b'\xB0\x3D'
CMD_TD_DELETE_VELOCITY_OVERFLOW_FLAG = b'\xB0\x3F'
CMD_TD_DELETE_EXTERNAL_CAPTURE_FLAG = b'\xB0\x40'
CMD_TD_METEO_ON = b'\xB0\x79'
CMD_TD_METEO_OFF = b'\xB0\x7A'
CMD_TD_CLEAR_MEASUREMENT_RESULTS = b'\xB0\x48'
# Commands from device
CMD_FD_DISTANCE_DATA = b'\xB0\x15'
CMD_FD_VELOCITY_DATA = b'\xB0\x16'
CMD_FD_METEO_DATA = b'\xB0\x0A'
# Misc
DATA_EMPTY = b'\x00\x00\x00\x00'
START_BYTE = b'\xAA'


class Device:
    """Interferometer Device."""
    # Timeout parameters
    default_timeout = 5
    default_retry_attempts = 10  # Total number of retry attempts on timeout

    def __init__(self, comport):
        """Open connection to a device via comport."""
        # Initialize serial device
        self.serial_device = serial.Serial(
            port=comport,
            baudrate=3000000,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            timeout=0.05,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False
        )

        # Initialize data queues
        self.distance_data = queue.Queue()
        self.velocity_data = queue.Queue()
        self.meteo_air_data = queue.Queue()
        self.meteo_mat_data = queue.Queue()

        # Initialize reader thread
        self.write_ack = threading.Event()
        self.stop_reader_thread = threading.Event()
        self.reader_thread_handle = threading.Thread(target=self.reader_thread)
        self.reader_thread_handle.start()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        """Close connection to the device."""
        # Join reader thread
        self.stop_reader_thread.set()
        self.reader_thread_handle.join()

        # Close serial connection
        self.serial_device.close()

    def read_distance_on(self, state):
        """Enable/disable reading distance data.

        Note: Either distance or velocity measurement can be enabled at the same time."""
        cmd = {True: CMD_TD_READ_DISTANCE_ON,
               False: CMD_TD_READ_DISTANCE_OFF}[state]
        data = DATA_EMPTY
        self.write_data(cmd, data, self.default_retry_attempts)

    def read_velocity_on(self, state):
        """Enable/disable reading velocity data.

        Note: Either distance or velocity measurement can be enabled at the same time."""
        cmd = {True: CMD_TD_READ_VELOCITY_ON,
               False: CMD_TD_READ_VELOCITY_OFF}[state]
        data = DATA_EMPTY
        self.write_data(cmd, data, self.default_retry_attempts)

    def read_meteo_on(self, state):
        """Enable/disable reading meteo data."""
        cmd = {True: CMD_TD_METEO_ON,
               False: CMD_TD_METEO_OFF}[state]
        data = DATA_EMPTY
        self.write_data(cmd, data, self.default_retry_attempts)

    def dont_send_any_stream_data(self):
        """Inactivate every data transfer."""
        cmd = CMD_TD_DONT_SEND_ANY_STREAM_DATA
        data = DATA_EMPTY
        self.write_data(cmd, data, self.default_retry_attempts)

    def delete_small_signal_level_flag(self):
        """Delete small signal level flag."""
        cmd = CMD_TD_DELETE_SMALL_SIGNAL_LEVEL_FLAG
        data = DATA_EMPTY
        self.write_data(cmd, data, self.default_retry_attempts)

    def delete_velocity_overflow_flag(self):
        """Delete velocity overflow flag."""
        cmd = CMD_TD_DELETE_VELOCITY_OVERFLOW_FLAG
        data = DATA_EMPTY
        self.write_data(cmd, data, self.default_retry_attempts)

    def set_dist_to_origin(self):
        """Set origin."""
        cmd = CMD_TD_CLEAR_MEASUREMENT_RESULTS
        data = DATA_EMPTY
        self.write_data(cmd, data, self.default_retry_attempts)

    def flush_data_queue(self):
        """Flush data queue."""
        with self.distance_data.mutex, self.velocity_data.mutex, self.meteo_air_data.mutex, self.meteo_mat_data.mutex:
            self.distance_data.queue.clear()
            self.velocity_data.queue.clear()
            self.meteo_air_data.queue.clear()
            self.meteo_mat_data.queue.clear()

    def read_distance(self, n=-1):
        """Read distance data n times.

        Note: The sampling rate is 25 Hz."""
        try:
            if n == -1:
                return self.distance_data.get(timeout=self.default_timeout)
            else:
                return [self.distance_data.get(timeout=self.default_timeout) for _ in range(n)]

        except queue.Empty:
            raise TimeoutError('Timeout while waiting for data!')

    def read_velocity(self, n=-1):
        """Read velocity data n times.

        Note: The sampling rate is 25 Hz."""
        try:
            if n == -1:
                return self.velocity_data.get(timeout=self.default_timeout)
            else:
                return [self.velocity_data.get(timeout=self.default_timeout) for _ in range(n)]

        except queue.Empty:
            raise TimeoutError('Timeout while waiting for data!')

    def read_meteo_air(self, n=-1):
        """Read meteo (air) data n times.

        Note: The sampling rate is 1 Hz."""
        try:
            if n == -1:
                return self.meteo_air_data.get(timeout=self.default_timeout)
            else:
                return [self.meteo_air_data.get(timeout=self.default_timeout) for _ in range(n)]

        except queue.Empty:
            raise TimeoutError('Timeout while waiting for data!')

    def read_meteo_mat(self, n=-1):
        """Read meteo (material) data n times.

        Note: The sampling rate is 1 Hz."""
        try:
            if n == -1:
                return self.meteo_mat_data.get(timeout=self.default_timeout)
            else:
                return [self.meteo_mat_data.get(timeout=self.default_timeout) for _ in range(n)]

        except queue.Empty:
            raise TimeoutError('Timeout while waiting for data!')

    def write_data(self, cmd, data, retry_attempts=0):
        """Write data to device."""
        # Reset acknowledgement event
        self.write_ack.clear()

        # Setup frame
        frame = START_BYTE + cmd + data  # |1START|2COMMAND|4DATA|1CRC|
        crc = get_crc(frame)
        frame += crc

        # Serial write
        self.serial_device.write(frame)

        try:
            # Wait for acknowledgement
            self.wait_for_write_ack()
        except TimeoutError:
            # Retry due to timeout
            if retry_attempts > 0:
                self.write_data(cmd, data, retry_attempts-1)
            else:
                raise ConnectionError('Maximum number of retries due to timeouts exceeded!')

    def wait_for_write_ack(self):
        """Wait for write acknowledgement."""
        ack = self.write_ack.wait(timeout=self.default_timeout)
        if not ack:
            raise TimeoutError('Timeout while waiting for acknowledgement!')

    def reader_thread(self):
        """Start main loop of reader."""
        # Reader loop
        while not self.stop_reader_thread.is_set():
            frame = self.serial_device.read(16)  # |1START|2COMMAND|12DATA|1CRC|

            # Check recveived framesize
            if len(frame) == 16:
                cmd = frame[1:3]
                data = frame[3:15]
                crc = frame[15:16]

                # Check CRC
                if get_crc(frame[0:15]) == crc:
                    try:
                        self.reader_handler(cmd, data)
                    except RuntimeError:
                        sleep(1e-3)
                        self.serial_device.reset_input_buffer()

    def reader_handler(self, cmd, data):
        """Handle read data."""
        # Check command type
        cmd_type = {
            # Data
            CMD_FD_DISTANCE_DATA: 'distance',
            CMD_FD_VELOCITY_DATA: 'velocity',
            CMD_FD_METEO_DATA: 'meteo',
            # Acknowledgement
            CMD_TD_READ_DISTANCE_ON: 'ack',
            CMD_TD_READ_DISTANCE_OFF: 'ack',
            CMD_TD_READ_VELOCITY_ON: 'ack',
            CMD_TD_READ_VELOCITY_OFF: 'ack',
            CMD_TD_DONT_SEND_ANY_STREAM_DATA: 'ack',
            CMD_TD_DELETE_SMALL_SIGNAL_LEVEL_FLAG: 'ack',
            CMD_TD_DELETE_VELOCITY_OVERFLOW_FLAG: 'ack',
            CMD_TD_DELETE_EXTERNAL_CAPTURE_FLAG: 'ack',
            CMD_TD_METEO_ON: 'ack',
            CMD_TD_METEO_OFF: 'ack',
            CMD_TD_CLEAR_MEASUREMENT_RESULTS: 'ack',
        }.get(cmd, None)

        # Evaluated command
        if cmd_type == 'distance':
            item = Distance(data)
            self.distance_data.put(item)
            
        elif cmd_type == 'velocity':
            item = Velocity(data)
            self.velocity_data.put(item)
            
        elif cmd_type == 'meteo':
            item = Meteo(data)
            if item.sensor_id == 0:
                self.meteo_air_data.put(item)
            else:  # ID: 1,2,3,...
                self.meteo_mat_data.put(item)
                
        elif cmd_type == 'ack':
            self.write_ack.set()
        
        else:
            raise RuntimeError('Invalid command received!')
