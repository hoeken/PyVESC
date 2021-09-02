from pyvesc.protocol.interface import encode_request, encode, decode
from pyvesc.VESC.messages import *
import time
import threading
from pprint import pprint
import serial.tools.list_ports
from serial.serialutil import *
	
# because people may want to use this library for their own messaging, do not make this a required package
try:
    import serial
except ImportError:
    serial = None

class VESC(object):

    fault_codes = (
        'FAULT_CODE_NONE',
        'FAULT_CODE_OVER_VOLTAGE',
        'FAULT_CODE_UNDER_VOLTAGE',
        'FAULT_CODE_DRV',
        'FAULT_CODE_ABS_OVER_CURRENT',
        'FAULT_CODE_OVER_TEMP_FET',
        'FAULT_CODE_OVER_TEMP_MOTOR',
        'FAULT_CODE_GATE_DRIVER_OVER_VOLTAGE',
        'FAULT_CODE_GATE_DRIVER_UNDER_VOLTAGE',
        'FAULT_CODE_MCU_UNDER_VOLTAGE',
        'FAULT_CODE_BOOTING_FROM_WATCHDOG_RESET',
        'FAULT_CODE_ENCODER_SPI',
        'FAULT_CODE_ENCODER_SINCOS_BELOW_MIN_AMPLITUDE',
        'FAULT_CODE_ENCODER_SINCOS_ABOVE_MAX_AMPLITUDE',
        'FAULT_CODE_FLASH_CORRUPTION',
        'FAULT_CODE_HIGH_OFFSET_CURRENT_SENSOR_1',
        'FAULT_CODE_HIGH_OFFSET_CURRENT_SENSOR_2',
        'FAULT_CODE_HIGH_OFFSET_CURRENT_SENSOR_3',
        'FAULT_CODE_UNBALANCED_CURRENTS',
        'FAULT_CODE_BRK',
        'FAULT_CODE_RESOLVER_LOT',
        'FAULT_CODE_RESOLVER_DOS',
        'FAULT_CODE_RESOLVER_LOS',
        'FAULT_CODE_FLASH_CORRUPTION_APP_CFG',
        'FAULT_CODE_FLASH_CORRUPTION_MC_CFG',
        'FAULT_CODE_ENCODER_NO_MAGNET'
    )


    def __init__(self, serial_port, has_sensor=False, start_heartbeat=True, baudrate=115200, timeout=0.05):
        """
        :param serial_port: Serial device to use for communication (i.e. "COM3" or "/dev/tty.usbmodem0")
        :param has_sensor: Whether or not the bldc motor is using a hall effect sensor
        :param start_heartbeat: Whether or not to automatically start the heartbeat thread that will keep commands
                                alive.
        :param baudrate: baudrate for the serial communication. Shouldn't need to change this.
        :param timeout: timeout for the serial communication
        """

        if serial is None:
            raise ImportError("Need to install pyserial in order to use the VESCMotor class.")

        self.serial_port = serial.Serial(port=serial_port, baudrate=baudrate, timeout=timeout)
        if has_sensor:
            self.serial_port.write(encode(SetRotorPositionMode(SetRotorPositionMode.DISP_POS_OFF)))

        # store message info for getting values so it doesn't need to calculate it every time
        msg = GetValues()
        self._get_values_msg = encode_request(msg)
        self._get_values_msg_expected_length = msg.fields.sizeof()

        #our keepalive message
        self._alive_msg = encode(Alive())        

        self.heart_beat_thread = threading.Thread(target=self._heartbeat_cmd_func)
        self._stop_heartbeat = threading.Event()

        if start_heartbeat:
            self.start_heartbeat()

        # some useful info for identifying the VESC
        self.firmware_info = self.get_firmware_version()
        self.version = str(self.firmware_info)
        self.uuid = self.firmware_info.uuid
        self.conf = self.get_motor_conf_simple()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_heartbeat()
        if self.serial_port.is_open:
            self.serial_port.flush()
            self.serial_port.close()

    def _heartbeat_cmd_func(self):
        """
        Continuous function calling that keeps the motor alive
        """
        while not self._stop_heartbeat.isSet():
            time.sleep(0.1)
            self.write(self._alive_msg)

    @staticmethod
    def get_vesc_serial_ports():
        """
        List all serial ports that match the vendor / product ID for VESC boards
        :return: a list of serial port path strings
        """
        ports = serial.tools.list_ports.comports()
        good_ports = []
        for port in ports:
            if '0483:5740' in port.hwid:
                good_ports.append(port.device)

        return good_ports		    

    @staticmethod
    def get_vesc_serial_port_by_uuid(uuid):
        """
        Get the port for connecting to a VESC identified by its UUID. It can be found on the firmware page of VESC Tool, or by using this library.
        :param uuid: the uuid as an integer. easiest to pass in as 24 digit hex, eg. 0x000000000000000000000000
        :return: the string path to the serial port, eg. /dev/ttyACM0
        """
        ports = VESC.get_vesc_serial_ports()
        for port in ports:
            try:
                obj = VESC(serial_port = port, start_heartbeat=False)
                if obj.uuid == uuid:
                    return port
            except SerialException as e:
                print("Error ecountered with port " + port)
                print(e)
        return None

    def start_heartbeat(self):
        """
        Starts a repetitive calling of the last set cmd to keep the motor alive.
        """
        self.heart_beat_thread.start()

    def stop_heartbeat(self):
        """
        Stops the heartbeat thread and resets the last cmd function. THIS MUST BE CALLED BEFORE THE OBJECT GOES OUT OF
        SCOPE UNLESS WRAPPING IN A WITH STATEMENT (Assuming the heartbeat was started).
        """
        if self.heart_beat_thread.is_alive():
            self._stop_heartbeat.set()
            self.heart_beat_thread.join()

    def write(self, data, num_read_bytes=None):
        """
        A write wrapper function implemented like this to try and make it easier to incorporate other communication
        methods than UART in the future.
        :param data: the byte string to be sent
        :param num_read_bytes: number of bytes to read for decoding response.  0 for unknown number of bytes
        :return: decoded response from buffer
        """
        
        reply = b''
        
        self.serial_port.write(data)
        if num_read_bytes is not None:
            #for some packets like 'get version' we don't know how long the response will be due to null terminated strings.
            if num_read_bytes == 0:
                while not bool(reply):
                	# add some delay to wait for the VESC to process
                	# honestly this whole response handling needs to be reworked since the packet header contains the length of the incoming packet.... delays are just a hack.
                    time.sleep(0.005) 
                    while self.serial_port.in_waiting == 0:
                        time.sleep(0.005)  # add some delay just to help the CPU
                    reply += self.serial_port.read(self.serial_port.in_waiting)
            #if we do know, then wait for exactly that # of bytes.
            else:
                while self.serial_port.in_waiting <= num_read_bytes:
                    time.sleep(0.000001)  # add some delay just to help the CPU
                    reply += self.serial_port.read(self.serial_port.in_waiting)

            response, consumed = decode(reply)
            return response

    def set_erpm(self, erpm):
        """
        Set the electronic RPM value (eg. the actual rpm * the number of pairs of poles)
        :param erpm: new erpm value
        """
        self.write(encode(SetRPM(int(erpm))))

    def set_rpm(self, rpm):
        """
        Set the actual RPM (must have correct motor poles # set in VESC Tool)(
        :param rpm: new rpm value
        """
        self.set_erpm(rpm * (self.conf.motor_poles / 2))
 
    def set_current(self, new_current):
        """
        :param new_current: new current in amps for the motor
        """
        self.write(encode(SetCurrent(new_current)))

    def set_brake_current(self, new_current):
        """
        :param new_current: new current in amps for the motor brake
        """
        self.write(encode(SetCurrentBrake(new_current)))

    def set_duty_cycle(self, new_duty_cycle):
        """
        :param new_duty_cycle: Value of duty cycle to be set (range [-1e5, 1e5]).
        """
        self.write(encode(SetDutyCycle(new_duty_cycle)))

    def set_servo(self, new_servo_pos):
        """
        :param new_servo_pos: New servo position. valid range [0, 1]
        """
        self.write(encode(SetServoPosition(new_servo_pos)))

    def get_measurements(self):
        """
        :return: A msg object with attributes containing the measurement values
        """
        #return self.write(self._get_values_msg, self._get_values_msg_expected_length)
        return self.write(self._get_values_msg, 0)

    def get_firmware_version(self):
        return self.write(encode_request(GetVersion()), 0)

    def get_motor_conf_simple(self):
        return self.write(encode_request(GetMCConfTemp()), 0)

    def get_erpm(self):
        """
        :return: Current motor erpm
        """
        return self.get_measurements().rpm

    def get_rpm(self):
        """
        :return: Current motor erpm
        """
        return self.get_measurements().rpm / (self.conf.motor_poles / 2)

    def get_duty_cycle(self):
        """
        :return: Current applied duty-cycle
        """
        return self.get_measurements().duty_cycle_now

    def get_v_in(self):
        """
        :return: Current input voltage
        """
        return self.get_measurements().v_in

    def get_motor_current(self):
        """
        :return: Current motor current
        """
        return self.get_measurements().avg_motor_current

    def get_incoming_current(self):
        """
        :return: Current incoming current
        """
        return self.get_measurements().avg_input_current
