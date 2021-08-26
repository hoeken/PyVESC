from pyvesc.protocol.base import VESCMessage
from pyvesc.VESC.messages import VedderCmd
from construct import *

class GetVersion(metaclass=VESCMessage):
    """ Gets version fields
    """
    id = VedderCmd.COMM_FW_VERSION

    fields = Struct(
            'comm_fw_version' / Byte,
            'fw_version_major' / Byte,
            'fw_version_minor' / Byte,
            'hw_name' / CString('utf8'),
            'uuid' / BytesInteger(12),
            'pairing_done' / Byte,
            'fw_test_version_number' / Byte,
            'hw_type_vesc' / Byte,
            'custom_config' / Byte
    )
    
    def __str__(self):
        return f"{self.comm_fw_version}.{self.fw_version_major}.{self.fw_version_minor}"


class GetValues(metaclass=VESCMessage):
    """ Gets internal sensor data
    """
    id = VedderCmd.COMM_GET_VALUES

    fields = Struct(
        'temp_fet' / Int16ub,
        'temp_motor' / Int16ub,
        'avg_motor_current' / Int32ub,
        'avg_input_current' / Int32ub,
        'avg_id' / Int32ub,
        'avg_iq' / Int32ub,
        'duty_cycle_now' / Int16ub,
        'rpm' / Int32ub,
        'v_in' / Int16ub,
        'amp_hours' / Int32ub,
        'amp_hours_charged' / Int32ub,
        'watt_hours' / Int32ub,
        'watt_hours_charged' / Int32ub,
        'tachometer' / Int32ub,
        'tachometer_abs' / Int32ub,
        'mc_fault_code' / Byte,
        'pid_pos_now' / Int32ub,
        'app_controller_id' / Byte,
        'temp_mos1' / Int16ub,
        'temp_mos2' / Int16ub,
        'temp_mos3' / Int16ub,
        'avg_vd' / Int32ub,
        'avg_vq' / Int32ub
    )

    scalars = {
        'temp_fet' : 10,
        'temp_motor': 10,
        'avg_motor_current': 100,
        'avg_input_current': 100,
        'avg_id': 100,
        'avg_iq': 100,
        'duty_cycle_now': '1000',
        'v_in': 10,
        'amp_hours': 10000,
        'amp_hours_charged': 10000,
        'watt_hours': 10000,
        'watt_hours_charged': 10000,
        'pid_pos_now': 1000000
    }

class GetRotorPosition(metaclass=VESCMessage):
    """ Gets rotor position data
    
    Must be set to DISP_POS_MODE_ENCODER or DISP_POS_MODE_PID_POS (Mode 3 or 
    Mode 4). This is set by SetRotorPositionMode (id=21).
    """
    id = VedderCmd.COMM_ROTOR_POSITION

    fields = Struct(
    	'rotor_pos' / Int32ub
    )
