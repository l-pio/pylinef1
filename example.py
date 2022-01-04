import pylinef1
from time import sleep


if __name__ == '__main__':
    with pylinef1.Device('COM7') as device:
        # Configure device
        device.read_distance_on(True)  # Hardware constraint: either distance or velocity measurement
        device.read_velocity_on(False)
        device.read_meteo_on(True)
        
        # Delete flags
        device.delete_velocity_overflow_flag()
        device.delete_small_signal_level_flag()
        
        # Set origin
        device.set_dist_to_origin()
        
        # Main loop
        duration = 1  # Duration in seconds
        for n in range(0, int(duration)):
            # Flush data queue to get the latest data every second
            device.flush_data_queue()
            
            # Distance
            distance = device.read_distance()
            print('Distance Value: %.8f m' % distance.value)
            print('Velocity overflow flag: %d' % distance.velocity_overflow_flag)
            print('Laser state flag: %d' % distance.laser_state_flag)
            print('Small signal level flag: %d' % distance.small_signal_level_flag)
            print('')
            
            # Velocity
            # velocity = device.read_velocity()
            # print('Velocity: %.8f m/s' % velocity.value)
            # print('Velocity overflow flag: %d' % velocity.velocity_overflow_flag)
            # print('Laser state flag: %d' % velocity.laser_state_flag)
            # print('Small signal level flag: %d' % velocity.small_signal_level_flag)
            # print('')
            
            # Meteo: Air
            meteo_air = device.read_meteo_air()
            print('Sensor ID: %d' % meteo_air.sensor_id)
            print('Air temperature: %.3f °C' % meteo_air.temperature)
            print('Air humidity: %d %%' % meteo_air.humidity)
            print('Battery: %d' % meteo_air.battery)  # Unknown unit
            print('Link: %d' % meteo_air.link)  # Unknown unit
            print('Air pressure: %d Pa' % meteo_air.pressure)
            print('')
            
            # Meteo: Material
            meteo_mat = device.read_meteo_mat()
            print('Sensor ID: %d' % meteo_mat.sensor_id)
            print('Material temperature: %.3f °C' % meteo_mat.temperature)
            print('Battery: %d' % meteo_mat.battery)  # Unknown unit
            print('Link: %d' % meteo_mat.link)  # Unknown unit
            print('')
            
            sleep(1)  # Here: one measurement per second
