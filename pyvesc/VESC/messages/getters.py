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
        'temp_fet' / Short,
        'temp_motor' / Short,
        'avg_motor_current' / Int32sb,
        'avg_input_current' / Int32sb,
        'avg_id' / Int32sb,
        'avg_iq' / Int32sb,
        'duty_cycle_now' / Int16sb,
        'rpm' / Int32sb,
        'v_in' / Short,
        'amp_hours' / Int,
        'amp_hours_charged' / Int,
        'watt_hours' / Int,
        'watt_hours_charged' / Int,
        'tachometer' / Int,
        'tachometer_abs' / Int,
        'mc_fault_code' / Byte,
        'pid_pos_now' / Int32sb,
        'app_controller_id' / Byte,
        'temp_mos1' / Short,
        'temp_mos2' / Short,
        'temp_mos3' / Short,
        'avg_vd' / Int32sb,
        'avg_vq' / Int32sb
    )

    scalars = {
        'temp_fet' : 10,
        'temp_motor': 10,
        'avg_motor_current': 100,
        'avg_input_current': 100,
        'avg_id': 100,
        'avg_iq': 100,
        'duty_cycle_now': 1000,
        'rpm': 1,
        'v_in': 10,
        'amp_hours': 10000,
        'amp_hours_charged': 10000,
        'watt_hours': 10000,
        'watt_hours_charged': 10000,
        'pid_pos_now': 1000000,
        'temp_mos1': 10,
        'temp_mos2': 10,
        'temp_mos3': 10,
        'avg_vd': 1000,
        'avg_vq': 1000
    }

class GetMCConfTemp(metaclass=VESCMessage):
    """ Gets a simplified version of the motor config
    """
    id = VedderCmd.COMM_GET_MCCONF_TEMP

    fields = Struct(
        'current_min_scale' / Float32b,
        'current_max_scale' / Float32b,
        'min_erpm' / Float32b,
        'max_erpm' / Float32b,
        'min_duty' / Float32b,
        'max_duty' / Float32b,
        'watt_min' / Float32b,
        'watt_max' / Float32b,
        'in_current_min' / Float32b,
        'in_current_max' / Float32b,
        'motor_poles' / Byte,
        'gear_ratio' / Float32b,
        'wheel_diameter' / Float32b
    )

class GetRotorPosition(metaclass=VESCMessage):
    """ Gets rotor position data
    
    Must be set to DISP_POS_MODE_ENCODER or DISP_POS_MODE_PID_POS (Mode 3 or 
    Mode 4). This is set by SetRotorPositionMode (id=21).
    """
    id = VedderCmd.COMM_ROTOR_POSITION

    fields = Struct(
    	'rotor_pos' / Int32ub
    )
    
    scalars = {
        'rotor_pos': 100000
    }
