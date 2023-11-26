import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
import time
import struct
import board
import usb_hid
# Initialize the keyboard
keyboard = Keyboard(usb_hid.devices)

# The code reader has the I2C ID of hex 0c, or decimal 12.
TINY_CODE_READER_I2C_ADDRESS = 0x0C

# How long to pause between sensor polls.
TINY_CODE_READER_DELAY = 0.2

TINY_CODE_READER_LENGTH_OFFSET = 0
TINY_CODE_READER_LENGTH_FORMAT = "H"
TINY_CODE_READER_MESSAGE_OFFSET = TINY_CODE_READER_LENGTH_OFFSET + \
                                  struct.calcsize(TINY_CODE_READER_LENGTH_FORMAT)
TINY_CODE_READER_MESSAGE_SIZE = 254
TINY_CODE_READER_MESSAGE_FORMAT = "B" * TINY_CODE_READER_MESSAGE_SIZE
TINY_CODE_READER_I2C_FORMAT = TINY_CODE_READER_LENGTH_FORMAT + TINY_CODE_READER_MESSAGE_FORMAT
TINY_CODE_READER_I2C_BYTE_COUNT = struct.calcsize(TINY_CODE_READER_I2C_FORMAT)

i2c = board.I2C()

#Toggle scroll to get status
keyboard.press(Keycode.SCROLL_LOCK)
time.sleep(0.1)
keyboard.release(Keycode.SCROLL_LOCK)
time.sleep(0.5)

#Now make sure its off
if(keyboard.led_on(Keyboard.LED_SCROLL_LOCK)):
    keyboard.press(Keycode.SCROLL_LOCK)
    time.sleep(0.1)
    keyboard.release(Keycode.SCROLL_LOCK)
    time.sleep(0.5)

while not i2c.try_lock():
    pass

output=""
i=0
while 1:
    # Is scroll lock on?
    if(keyboard.led_on(Keyboard.LED_SCROLL_LOCK)):
        print("[+] Attempting to read QR")
        i=0
        last_message_string = None
        last_code_time = 0.0
        retrieved = False
        while retrieved==False:
            read_data = bytearray(TINY_CODE_READER_I2C_BYTE_COUNT)
            i2c.readfrom_into(TINY_CODE_READER_I2C_ADDRESS, read_data)

            message_length,  = struct.unpack_from(TINY_CODE_READER_LENGTH_FORMAT, read_data,
                                                  TINY_CODE_READER_LENGTH_OFFSET)
            message_bytes = struct.unpack_from(TINY_CODE_READER_MESSAGE_FORMAT, read_data,
                                               TINY_CODE_READER_MESSAGE_OFFSET)

            if message_length > 0:
                message_string = bytearray(message_bytes)[0:message_length].decode("utf-8")
                is_same = (message_string == last_message_string)
                last_message_string = message_string
                current_time = time.monotonic()
                time_since_last_code = current_time - last_code_time
                last_code_time = current_time
                # Debounce the input by making sure there's been a gap in time since we
                # last saw this code.
                if (not is_same) or (time_since_last_code > 1.0):
                    print(message_string)
                    retrieved=True
                    print("\n")

        # Turn off scroll lock to indicate successfull retrieval
        #print("PRESS SCROLL LOCK")
        keyboard.press(Keycode.SCROLL_LOCK)
        time.sleep(0.1)
        keyboard.release(Keycode.SCROLL_LOCK)
        time.sleep(0.5)
    else:
        i+=1
        #print(i)
        #if i > 2000: quit()
    time.sleep(0.1)
