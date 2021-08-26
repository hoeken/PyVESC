import pyvesc
from pyvesc.VESC.messages import GetValues, SetRPM, SetCurrent, SetRotorPositionMode
import serial
import time

def get_values_example():
    # Set your serial port here (either /dev/ttyX or COMX)
    serialport = '/dev/ttyACM1'
    
    with pyvesc.VESC(serial_port = serialport) as driver:
        try:
            print("Driver Firmware: ", driver.get_firmware_version(), " / UUID: ", hex(driver.uuid))

            while True:
                # Set the ERPM of the VESC motor
                #    Note: if you want to set the real RPM you can set a scalar
                #          manually in setters.py
                #          12 poles and 19:1 gearbox would have a scalar of 1/228
                driver.set_rpm(10000)

                # Request the current measurement from the vesc
                data = driver.get_measurements()

                print("RPM: ", data.rpm, " Voltage: ", data.v_in, " Motor Current: ", data.avg_motor_current, " Input Current: ", data.avg_input_current)
                time.sleep(0.25)

        except KeyboardInterrupt:
            # Turn Off the VESC
            driver.set_current(0)


if __name__ == "__main__":
    get_values_example()
