from machine import UART, Pin, ADC

# init bus

bus = UART(1, 9600)
bus.init(9600, bits=8, parity=None, stop=1, timeout=20)

# because pico w has the on-board led attached to the wireless module, this is valid
led = Pin("LED", Pin.OUT)

adc = ADC(1)

# serve loop

while True:
    cmd = bus.read(1)

    # periodic adc readback
    state = adc.read_u16()
    bus.write(state.to_bytes(2, 'little', signed=False))

    # noop - discard byte
    if cmd is None or cmd == b'\x00':
        continue

    # write cmd - set led status
    if cmd == b'w':
        req_state = bus.read(1)
        led.value(req_state != b'\x00')
