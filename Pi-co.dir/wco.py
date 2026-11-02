from machine import Pin, ADC

import network
import socket
import time

from machine import mem32

wlan = network.WLAN(network.STA_IF)

ssid = "Pi-co."
cred = "picoroporate"

# net init

wlan.active(True)
wlan.connect(ssid, cred)

print("connecting to AP", end="")
for i in range(5):
    print('.', end='')

    if wlan.status() < 0 or wlan.status() >= 3:
        break

    time.sleep(1)

print()

if wlan.status() != network.STAT_GOT_IP:
    raise RuntimeError(f"failed to connect to AP, wlan status: {wlan.status()}")

print(f"connection successful (ip: {wlan.ifconfig()[0]} RSSI: {wlan.status('rssi')})")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 5000))

# output

# because pico w has the on-board led attached to the wireless module, this is valid
led = Pin("LED", Pin.OUT)

adc = ADC(1)

# serve loop

sock.setblocking(False)
addr = None

while True:
    try:
        addr, pak = sock.recvfrom(16)
        cmd = pak[:1]
    except OSError:
        pak = None
        cmd = None

    try:
        # periodic adc readback
        if addr is not None:
            state = adc.read_u16()
            sock.sendto(b'r' + state.to_bytes(2, 'little', signed=False), addr) # "we can do it without `struct`." they said confidently.

        # noop - discard byte
        if cmd is None or cmd == b'\x00':
            continue

        # write cmd - set led status
        if cmd == b'w':
            req_state = pak[1:2]
            led.value(req_state != b'\x00')

    except:
        print("malformed packet or error during command execution, continuing...")