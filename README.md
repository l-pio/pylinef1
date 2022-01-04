# pyLineF1
An unofficial Python package to communicate with the **Status Pro µLine-f1** / **Lasertex HPI-3D** laser
measurement system.

Some features like measurement of dynamic or 3D data are not implemented yet.

## Installation
Please simply copy the package directory to your workspace, and install the requirements by running:
```
$ pip install -r requirements.txt
```

## Usage
```
with pylinef1.Device('COMx') as device:  # Replace x by comport number
    # Configure device
    device.read_distance_on(True)  # Hardware constraint: either distance or velocity measurement
    device.read_velocity_on(False)
    device.read_meteo_on(True)
    
    # Delete flags
    device.delete_velocity_overflow_flag()
    device.delete_small_signal_level_flag()
    
    # Set origin
    device.set_dist_to_origin()

    # Flush data queue to get the latest data
    device.flush_data_queue()
    
    # Blocking read of data
    # distance, velocity, meteo_air, and meteo_mat are data containers, e.g., containing the value and some flags.
    distance = device.read_distance()
    # velocity = device.read_velocity()
    meteo_air = device.read_meteo_air()
    meteo_mat = device.read_meteo_mat()
```

Another example can be found [here](./example.py).