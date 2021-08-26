import pyvesc
from pprint import pprint

def uuid_example():
	#loop through all our ports and then open them to find out our firmware info and UUID
	ports = pyvesc.VESC.get_vesc_serial_ports()
	for port in ports:
		motor = pyvesc.VESC(serial_port = port, start_heartbeat=False)
		print("Port: ", port, " / Driver Firmware: ", motor.get_firmware_version(), " / UUID: ", hex(motor.uuid))

	#the UUID specific to your vesc		
	uuid = 0x400030001850524154373020
	
	#now, using the UUID that was displayed above, you can always connect to that exact VESC you want
	print ("Attempting to open VESC by UUID ", hex(uuid))
	motor_port = pyvesc.VESC.get_vesc_serial_port_by_uuid(uuid)
    
	#if there was an error, motor_port will be empty...
	if motor_port:
		motor = pyvesc.VESC(serial_port = motor_port, start_heartbeat=False)
		print("Driver Firmware: ", motor.get_firmware_version(), " / UUID: ", hex(motor.uuid))
	else:
		print("Could not find VESC.")
	
if __name__ == "__main__":
    uuid_example()
