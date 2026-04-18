import wmi
import time

c = wmi.WMI()
before = {}
for device in c.Win32_PnPEntity():
    if device.Name:
        before[device.Name] = {
            "DeviceID": device.DeviceID,
            "PNPDeviceID": device.PNPDeviceID,
            "Description": device.Description,
            "Manufacturer": device.Manufacturer,
            "Status": device.Status,
        }

print("Watching for new devices...")
print("Plug phone in and set to File Transfer mode.")
print()

for i in range(30):
    time.sleep(1)
    after = {}
    for device in c.Win32_PnPEntity():
        if device.Name:
            after[device.Name] = {
                "DeviceID": device.DeviceID,
                "PNPDeviceID": device.PNPDeviceID,
                "Description": device.Description,
                "Manufacturer": device.Manufacturer,
                "Status": device.Status,
            }

    new = {k: v for k, v in after.items() if k not in before}

    if new:
        print("New devices detected:")
        for name, info in new.items():
            print()
            print(f"  Name         : {name}")
            print(f"  DeviceID     : {info['DeviceID']}")
            print(f"  PNPDeviceID  : {info['PNPDeviceID']}")
            print(f"  Description  : {info['Description']}")
            print(f"  Manufacturer : {info['Manufacturer']}")
            print(f"  Status       : {info['Status']}")
        break

    print(f"  Waiting... {i+1}s")