#defines constants here
HOST='127.0.0.1'
PORT=10005

# required parameters for AES encryption
KEY='a1b4c6d1efgh5678'
INTERRUPT = u'\u0001' # Interrupt to detect padding start
PAD = u'\u0000'       # Padding (zero)
FIXED_BLOCK_SIZE = 16 # Must be 16 for Python AES.
