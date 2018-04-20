from pprint import pprint
import struct
import codecs
import math
import time

def intFromBytes(someBytes, byteOrder):
    return int.from_bytes(someBytes, byteorder=byteOrder)

def intToBytes(someInt, byteOrder):
    return someInt.to_bytes(2, byteorder=byteOrder, signed=False)

def filescan(filename):
    # scan through the entire file once to find the positions of all the blocks
    with open(filename,"rb") as binary_file:
        index = 800
        
        binary_file.seek(index)
        while index < 400000:
            abyte = binary_file.read(2)
            try:
                if intFromBytes(abyte,byteOrder) == 63777:
                    # found the first block
                    binary_file.close()
                    return index

                index += 1
            except:
                index += 1


def frameScan(filename,index):
    binary_file = open(filename,'rb')
    GCBCart = []            # array of indexes of starting points of graphic control blocks
    delayTimeCart = []      # array of delay times for each frame
    fileTerminator = False
    while fileTerminator == False:
        binary_file.seek(index)
        GCBCart.append(index)
        
        # 8 bytes graphic control
        skipForward = binary_file.read(2)   # extension introducer, graphic control label
        print(skipForward)
        skipForward = binary_file.read(1)   # block size
        skipForward = binary_file.read(1)   # packed fields
        delayTime = binary_file.read(2)
        delayTimeCart.append(intFromBytes(delayTime,byteOrder))
        skipForward = (binary_file.read(2)) # transparent color index, block terminator
        # 10 bytes image descriptor
        skipForward = binary_file.read(10)
        index += 18
        LZW = binary_file.read(1)
        index += 1
        #nicePrint(LZW, 'LZW min code size')
        while True:
            noBytes = binary_file.read(1)
            noBytes = intFromBytes(noBytes,byteOrder)
            #print(noBytes)
            index += 1
            if noBytes == 0:    # end of frame
                break
            #nicePrint(noBytes,'no of bytes next')
            skipForward = binary_file.read(noBytes)
            index += noBytes
        terminateCheck = intFromBytes(binary_file.read(1),byteOrder)
        if terminateCheck == 59:
            fileTerminator = True
            binary_file.close()
            return (GCBCart, delayTimeCart, index)

def readHeader(filename):
    # header is always the first six bytes
    with open(filename,"rb") as binary_file:
        binary_file.seek(0)   # go to header (beginning of file)
        couple_bytes = binary_file.read(6) # read off 6 bytes
        binary_file.close()
        return (couple_bytes)

def readLogicalScreenDescriptor(filename):
    # Logical Screen Descriptor comes after the header and takes the next 6 bytes
    # width: 2 bytes, height: 2 bytes, byteorder: 2 bytes, pixel aspect ratio: 2 bytes
    index = 6
    with open(filename,"rb") as binary_file:
        binary_file.seek(index)
        width = intFromBytes(binary_file.read(2), byteOrder)
        index += 2
        nicePrint(width,'width')
        
        binary_file.seek(index)
        height = intFromBytes(binary_file.read(2), byteOrder)
        index += 2
        nicePrint(height,'height')

        binary_file.seek(index)
        bgColor = intFromBytes(binary_file.read(1), byteOrder)
        index += 1
        nicePrint(bgColor,'background color')

        binary_file.seek(index)
        pixelaspectratio = intFromBytes(binary_file.read(1), byteOrder)
        index += 1
        nicePrint(pixelaspectratio,'pixel aspect ratio')

        binary_file.close()

        return (width,height,bgColor,pixelaspectratio)

def nicePrint(thing,thingName):
    print(thingName + ":")
    print(thing)
    print("\n")

# file related variables
filename = "rotatingearthCopy.gif"
outfilename = 'modifiedgif.gif'
byteOrder = 'little'

charCount = None        # total number of characters able to be stored

# input variables
msg = "abc123"      # the message to be hidden
msgCount = None     # the length of the message
msgCountBin = ""  # the length of the message (in binary)
bitstream = ""      # the bitstream to be embedded in the frame delays

# decoding extracted variables
bitsToRead = None   # number of bits that contains the message
msgExtractBin = ""  # extracted message in binary
msgExtract = ""     # extracted message in text

header = readHeader(filename)
nicePrint(header.decode('utf-8'),'file format')

width,height,bgColor,pixelaspectratio = readLogicalScreenDescriptor(filename)

graphicControl1 = filescan(filename)
GCBCart, delayTimeCart, end = frameScan(filename,graphicControl1)
frameCount = len(delayTimeCart)

print(GCBCart)
print(delayTimeCart)

# get the length of the hidden message
for i in range(8):
    if delayTimeCart[i] % 2 == 0:   # even number represents 0
        msgCountBin = msgCountBin + '0'
    else:                           # odd number represents 1
        msgCountBin = msgCountBin + '1'
msgCount = int(msgCountBin,2)

# get the message in binary
for i in range(8,msgCount+8):
    if delayTimeCart[i] % 2 == 0:   # even value
        msgExtractBin = msgExtractBin + '0'
    else:   # odd value
        msgExtractBin = msgExtractBin + '1'
    if len(msgExtractBin) == 8:     # convert every 8 bits into integer
        msgExtract = msgExtract + chr(int(msgExtractBin,2)) # convert integer to ascii
        msgExtractBin = ""

print(msgExtract)

