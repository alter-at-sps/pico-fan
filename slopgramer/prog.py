from machine import Pin
from time import sleep_us, sleep_ms

class ATTiny13Programmer:
    """
    Bit-banged ATtiny13/ATtiny13A ISP programmer for Raspberry Pi Pico.

    Default Pico pins:
        GP2 -> MOSI -> ATtiny PB0
        GP3 <- MISO <- ATtiny PB1
        GP4 -> SCK  -> ATtiny PB2
        GP5 -> RESET -> ATtiny PB5

    The ATtiny13 flash is:
        1024 bytes
        512 words
        32-byte pages
        16 words/page
    """

    SIGNATURE = (0x1E, 0x90, 0x07)

    FLASH_SIZE = 1024
    PAGE_SIZE = 32

    def __init__(self,
                 mosi=2,
                 miso=3,
                 sck=4,
                 reset=5,
                 delay_us=3):

        self.mosi = Pin(mosi, Pin.OUT, value=0)
        self.miso = Pin(miso, Pin.IN)
        self.sck = Pin(sck, Pin.OUT, value=0)
        self.reset = Pin(reset, Pin.OUT, value=1)

        # Half-period of the software SPI clock.
        #
        # 3 us gives a deliberately slow clock, which is useful when
        # the target is running at the ATtiny13's default low clock.
        self.delay_us = delay_us

    # ------------------------------------------------------------
    # Low-level SPI
    # ------------------------------------------------------------

    def _clock_bit(self, bit):
        self.mosi.value(1 if bit else 0)

        sleep_us(self.delay_us)

        self.sck.value(1)
        sleep_us(self.delay_us)

        value = self.miso.value()

        self.sck.value(0)
        sleep_us(self.delay_us)

        return value

    def _transfer(self, value):
        """Transfer one byte MSB first and return received byte."""

        rx = 0

        for bit in range(7, -1, -1):
            rx <<= 1
            rx |= self._clock_bit((value >> bit) & 1)

        return rx

    def _command(self, b0, b1, b2, b3):
        """Send a four-byte AVR ISP command."""

        return (
            self._transfer(b0),
            self._transfer(b1),
            self._transfer(b2),
            self._transfer(b3),
        )

    # ------------------------------------------------------------
    # ISP session
    # ------------------------------------------------------------

    def enter(self):
        """
        Enter serial programming mode.

        The ATtiny13 requires RESET low before the programming-enable
        command. The 0x53 echo is checked as specified by the datasheet.
        """

        # Required idle states.
        self.sck.value(0)
        self.mosi.value(0)

        # Reset low.
        self.reset.value(0)

        # Datasheet recommends waiting >=20 ms after RESET.
        sleep_ms(25)

        # Programming Enable.
        r = self._command(
            0xAC,
            0x53,
            0x00,
            0x00
        )

        if r[2] != 0x53:
            # Try once more after a reset pulse.
            self.reset.value(1)
            sleep_ms(5)

            self.sck.value(0)
            self.mosi.value(0)

            self.reset.value(0)
            sleep_ms(25)

            r = self._command(
                0xAC,
                0x53,
                0x00,
                0x00
            )

            if r[2] != 0x53:
                self.reset.value(1)
                raise RuntimeError(
                    "ATtiny13 did not enter programming mode "
                    "(expected 0x53, got 0x%02X)" % r[2]
                )

        return True

    def exit(self):
        """Leave ISP mode."""

        self.reset.value(1)
        self.sck.value(0)
        self.mosi.value(0)
        sleep_ms(2)

    # ------------------------------------------------------------
    # Device identification
    # ------------------------------------------------------------

    def signature(self):
        """Read the three-byte device signature."""

        sig = []

        for address in range(3):
            r = self._command(
                0x30,
                0x00,
                address,
                0x00
            )

            sig.append(r[3])

        return bytes(sig)

    def check_device(self):
        sig = self.signature()

        if tuple(sig) != self.SIGNATURE:
            raise RuntimeError(
                "Unexpected signature: %02X %02X %02X"
                % tuple(sig)
            )

        return sig

    # ------------------------------------------------------------
    # Fuse access
    # ------------------------------------------------------------

    def read_low_fuse(self):
        """
        Read low fuse.

        AVR ISP command:
            0101 0000 0000 0000 xxxx xxxx xxxx xxxx
        """

        return self._command(
            0x50,
            0x00,
            0x00,
            0x00
        )[3]

    def read_high_fuse(self):
        """
        Read high fuse.
        """

        return self._command(
            0x58,
            0x08,
            0x00,
            0x00
        )[3]

    # ------------------------------------------------------------
    # Flash
    # ------------------------------------------------------------

    def read_flash_byte(self, address):
        """
        Read one byte from flash.

        The AVR programming interface addresses flash in WORDS,
        so byte address is divided by two.
        """

        if address < 0 or address >= self.FLASH_SIZE:
            raise ValueError("flash address out of range")

        word = address >> 1
        high = address & 1

        command = 0x28 if high else 0x20

        r = self._command(
            command,
            (word >> 8) & 0xFF,
            word & 0xFF,
            0x00
        )

        return r[3]

    def read_flash(self, size=FLASH_SIZE):
        """Read flash into a bytes object."""

        if size < 0 or size > self.FLASH_SIZE:
            raise ValueError("invalid flash size")

        data = bytearray(size)

        for address in range(size):
            data[address] = self.read_flash_byte(address)

        return bytes(data)

    def load_flash_byte(self, word_address, value, high=False):
        """
        Load one byte into the current flash page buffer.

        The ATtiny13 requires the low byte of a word to be loaded
        before its high byte.
        """

        command = 0x48 if high else 0x40

        self._command(
            command,
            (word_address >> 8) & 0xFF,
            word_address & 0xFF,
            value
        )

    def write_page(self, page_address, data):
        """
        Program one 32-byte flash page.

        page_address is a BYTE address and must be 32-byte aligned.
        """

        if len(data) != self.PAGE_SIZE:
            raise ValueError("page must contain exactly 32 bytes")

        if page_address % self.PAGE_SIZE:
            raise ValueError("page address is not 32-byte aligned")

        if page_address < 0 or page_address >= self.FLASH_SIZE:
            raise ValueError("page address out of range")

        # The serial interface addresses program memory in WORDS.
        base_word = page_address >> 1

        # Load the page buffer.
        #
        # IMPORTANT:
        # Low byte must be loaded before high byte.
        for i in range(0, self.PAGE_SIZE, 2):
            word = base_word + (i >> 1)

            low = data[i]
            high = data[i + 1]

            self.load_flash_byte(
                word,
                low,
                high=False
            )

            self.load_flash_byte(
                word,
                high,
                high=True
            )

        # Write Program Memory Page.
        #
        # The ATtiny13 page address is the word address.
        r = self._command(
            0x4C,
            (base_word >> 8) & 0xFF,
            base_word & 0xFF,
            0x00
        )

        # ATtiny13A specifies ~4.5 ms minimum flash programming
        # delay. Waiting 5 ms avoids relying on polling.
        sleep_ms(5)

    def erase(self):
        """Chip erase."""

        self._command(
            0xAC,
            0x80,
            0x00,
            0x00
        )

        # Datasheet minimum is approximately 9 ms for ATtiny13A.
        sleep_ms(10)

    def program(self, image, verify=True, erase=True):
        """
        Program a binary image.

        image:
            bytes/bytearray containing up to 1024 bytes.

        Bytes not supplied are left unchanged if erase=False.
        With erase=True, unspecified bytes are programmed as 0xFF.
        """

        if len(image) > self.FLASH_SIZE:
            raise ValueError(
                "image is larger than ATtiny13 flash"
            )

        image = bytes(image)

        if erase:
            self.erase()

            # After erase, unspecified flash is already 0xFF.
            padded = image + bytes(
                [0xFF] * (self.FLASH_SIZE - len(image))
            )
        else:
            # If not erasing, don't accidentally modify bytes outside
            # the supplied image.
            padded = image

        # Program complete pages.
        pages = (len(padded) + self.PAGE_SIZE - 1) // self.PAGE_SIZE

        for page in range(pages):
            start = page * self.PAGE_SIZE
            end = min(start + self.PAGE_SIZE, len(padded))

            chunk = padded[start:end]

            if len(chunk) < self.PAGE_SIZE:
                chunk += bytes(
                    [0xFF] * (self.PAGE_SIZE - len(chunk))
                )

            self.write_page(start, chunk)

            print(
                "programmed page %d/%d"
                % (page + 1, pages)
            )

        if verify:
            self.verify(image)

    def verify(self, image):
        """Verify an image against the target flash."""

        if len(image) > self.FLASH_SIZE:
            raise ValueError("image too large")

        for address, expected in enumerate(image):
            actual = self.read_flash_byte(address)

            if actual != expected:
                raise RuntimeError(
                    "VERIFY FAILED at 0x%03X: "
                    "expected 0x%02X, got 0x%02X"
                    % (address, expected, actual)
                )

        print("verify OK")

    # ------------------------------------------------------------
    # Intel HEX support
    # ------------------------------------------------------------

    @staticmethod
    def parse_hex(text):
        """
        Parse an Intel HEX file.

        Returns a 1024-byte bytearray initialized to 0xFF.

        Supports:
            00 - data
            01 - EOF
            04 - extended linear address
        """

        image = bytearray([0xFF] * 1024)
        upper = 0

        for line_number, line in enumerate(
            text.splitlines(), 1
        ):
            line = line.strip()

            if not line:
                continue

            if not line.startswith(":"):
                raise ValueError(
                    "HEX line %d does not start with ':'"
                    % line_number
                )

            try:
                raw = bytes.fromhex(line[1:])
            except ValueError:
                raise ValueError(
                    "invalid HEX line %d"
                    % line_number
                )

            if len(raw) < 5:
                raise ValueError(
                    "short HEX line %d"
                    % line_number
                )

            count = raw[0]
            address = (raw[1] << 8) | raw[2]
            record_type = raw[3]

            if len(raw) != count + 5:
                raise ValueError(
                    "invalid length on HEX line %d"
                    % line_number
                )

            # Intel HEX checksum.
            if (sum(raw) & 0xFF) != 0:
                raise ValueError(
                    "bad checksum on HEX line %d"
                    % line_number
                )

            data = raw[4:4 + count]

            if record_type == 0x00:
                absolute = upper + address

                for i, value in enumerate(data):
                    destination = absolute + i

                    if destination >= 1024:
                        raise ValueError(
                            "HEX image exceeds ATtiny13 flash"
                        )

                    image[destination] = value

            elif record_type == 0x01:
                break

            elif record_type == 0x04:
                if count != 2:
                    raise ValueError(
                        "bad extended address record"
                    )

                upper = (
                    ((data[0] << 8) | data[1])
                    << 16
                )

            else:
                # Other record types are harmless for this programmer,
                # so ignore them.
                pass

        return image

    # ------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------

    def info(self):
        """Print device information."""

        sig = self.signature()

        print(
            "Signature: %02X %02X %02X"
            % tuple(sig)
        )

        try:
            lfuse = self.read_low_fuse()
            hfuse = self.read_high_fuse()

            print("LFUSE:     0x%02X" % lfuse)
            print("HFUSE:     0x%02X" % hfuse)

        except Exception as e:
            print("Fuse read failed:", e)


# ------------------------------------------------------------
# Create programmer
# ------------------------------------------------------------

prog = ATTiny13Programmer()

print()
print("ATtiny13 Pico ISP programmer")
print("----------------------------")
print("MOSI  GP2")
print("MISO  GP3")
print("SCK   GP4")
print("RESET GP5")
print()
print("Call:")
print("  prog.enter()")
print("  prog.check_device()")
print("  prog.info()")
print("  prog.erase()")
print("  prog.program(image)")
print("  prog.exit()")
print()

prog.enter()
prog.info()

bin = open("prog.bin", "rb")

prog.program(bin.read())

bin.seek(0)
prog.verify(bin.read())

bin.close()