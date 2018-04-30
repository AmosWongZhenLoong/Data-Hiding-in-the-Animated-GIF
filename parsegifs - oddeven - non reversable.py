from pprint import pprint
import struct
import codecs
import math
import time

import FuncLib as FuncLib

# file related variables
filename = "modifiedgif.gif"
outfilename = 'modifiedgif.gif'
byteOrder = 'little'

# input variables
msg = "abc123"      # the message to be hidden
msgCount = None     # the length of the message
msgCountBin = None  # the length of the message (in binary)
bitstream = ""      # the bitstream to be embedded in the frame delays


delayLocations,delayTimeCart,endIndex,GCBCart = FuncLib.parse(filename)
delayTimeCart = FuncLib.intFromBytes(delayTimeCart,byteOrder)

print(delayLocations)
print(delayTimeCart)

charCount = FuncLib.getCharCapacity(delayTimeCart)

# let the user input a message
while True:
    print('maximum characters: %d' %(charCount))
    msg = str(input('type your message here: '))
    if len(msg) > charCount:
        print('message is too many characters long')
        print('\n')
        continue
    else:
        break

# message length to bits
msgCount = len(msg) * 8
msgCountBin = "{:08b}".format(msgCount)
bitstream = bitstream + msgCountBin

# message to bits
msgbitstream = FuncLib.msg2bits(msg)
# concatenate message length bits with message bits
bitstream = bitstream + msgbitstream

delayTimeCart = FuncLib.modifyDelayTimes(bitstream,delayTimeCart)

# change all values in delayTimeCart into bytes-like object
for i in range(len(delayTimeCart)):
    delayTimeCart[i] = FuncLib.intToBytes(delayTimeCart[i],byteOrder,2)

print(delayTimeCart)
# writing new delay times
FuncLib.writeToFile(filename,delayTimeCart,delayLocations)




