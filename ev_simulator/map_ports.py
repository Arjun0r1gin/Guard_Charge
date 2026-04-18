import wmi
import time

c = wmi.WMI()

def get_apple_devices():
    devices = {}
    for device in c.Win32_PnPEntity():
        if device.Name and "Apple" in str(device.Name):
            devices[device.PNPDeviceID] = device.Name
    return devices

print("Step 1: Plug phone into PORT 1 (left port)")
input("Press Enter when plugged in and File Transfer mode is on...")
time.sleep(3)
port1_devices = get_apple_devices()
print("Port 1 devices:")
for pid in port1_devices:
    print(f"  {pid}")

print()
print("Step 2: Unplug and plug into PORT 2 (right port)")
input("Press Enter when plugged in and File Transfer mode is on...")
time.sleep(3)
port2_devices = get_apple_devices()
print("Port 2 devices:")
for pid in port2_devices:
    print(f"  {pid}")

print()
print("Port 1 unique ID:", set(port1_devices.keys()))
print("Port 2 unique ID:", set(port2_devices.keys()))