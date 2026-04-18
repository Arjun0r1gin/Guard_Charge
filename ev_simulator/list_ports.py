import wmi

c = wmi.WMI()

print("USB Controllers and Ports on this laptop:")
print("=" * 60)

for hub in c.Win32_USBHub():
    print(f"\n  Hub          : {hub.Name}")
    print(f"  DeviceID     : {hub.DeviceID}")
    print(f"  Status       : {hub.Status}")

print()
print("=" * 60)
print("USB Port Connectors:")
print("=" * 60)

for port in c.Win32_USBController():
    print(f"\n  Controller   : {port.Name}")
    print(f"  DeviceID     : {port.DeviceID}")
    print(f"  Manufacturer : {port.Manufacturer}")
    print(f"  Status       : {port.Status}")