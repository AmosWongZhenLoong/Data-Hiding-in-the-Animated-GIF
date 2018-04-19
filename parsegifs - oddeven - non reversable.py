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
            if index % 100000 == 0:
                print(index)

def frameScan(filename,index):
    # parse bytes in the file of choice
    # reads and extracts
        # location of each graphics control block
        # delay value for each frame
        # location of the end of file
    # output:
        # array: indexes of every graphics control block
        # array: delay value of each graphics control block
        # int: index of the end of file
    binary_file = open(filename,'rb')
    GCBCart = []            # array of indexes of starting points of graphic control blocks
    delayTimeCart = []      # array of delay times for each frame
    fileTerminator = False
    while fileTerminator == False:
        print("graphic control block")
        print(index)
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

def msg2bits(msg):
    # convert text to bitstream
    # output: bitstream
    bitstream = ""
    for i in range(len(msg)):
        char = msg[i]
        charInt = ord(char)
        charBin = '{:08b}'.format(charInt)
        bitstream = bitstream + charBin
    return bitstream

def modifyDelayTimes(bitstream,delayTimeCart):
    # modify the delayTimeCart to store the message
    ## message representation:
    ### even number represents one(0)
    ### odd number represents zero(1)
    for i in range(len(bitstream)):
        if int(bitstream[i]) == 0:   # is even
            if delayTimeCart[i] % 2 == 1:   # is odd
                delayTimeCart[i] = delayTimeCart[i] + 1
        else:
            if delayTimeCart[i] % 2 == 0:   # is even
                delayTimeCart[i] = delayTimeCart[i] + 1
    return delayTimeCart

def nicePrint(thing,thingName):
    print(thingName + ":")
    print(thing)
    print("\n")

# file related variables
filename = "rotatingearthCopy.gif"
outfilename = 'modifiedgif.gif'
byteOrder = 'little'

# file extracted variables
header = None
width = None
height = None
bgColor = None
pixelaspectratio = None
graphicControl1 = None      # index location of the first graphic control block

GCBCart = None      # array of starting indexes of graphic control blocks
delayTimeCart = None    # array of delay time values for each graphic control block
end = None      # the end position of the last frame image data
frameCount = None       # the total number of frames
charCount = None        # total number of characters able to be stored

# input variables
msg = "abc123"      # the message to be hidden
msgCount = None     # the length of the message
msgCountBin = None  # the length of the message (in binary)
bitstream = ""      # the bitstream to be embedded in the frame delays

header = readHeader(filename)
nicePrint(header.decode('utf-8'),'file format')

width,height,bgColor,pixelaspectratio = readLogicalScreenDescriptor(filename)

graphicControl1 = filescan(filename)
GCBCart, delayTimeCart, end = frameScan(filename,graphicControl1)
frameCount = len(delayTimeCart)

print(GCBCart)
print(delayTimeCart)

# calculate how many characters can be stored
charCount = (frameCount - 8) / 8
if charCount % 1 != 0:
    charCount = math.floor(charCount)
print('the maximum character limit is: ' + str(charCount))

# let the user input a message
msg = str(input('type your message here: '))
if len(msg) > charCount:
    print('message is too many characters long')
    time.sleep(3)
    quit()

# message length to bits
msgCount = len(msg) * 8
msgCountBin = "{:08b}".format(msgCount)
bitstream = bitstream + msgCountBin

# message to bits
msgbitstream = msg2bits(msg)
# concatenate message length bits with message bits
bitstream = bitstream + msgbitstream

delayTimeCart = modifyDelayTimes(bitstream,delayTimeCart)

# change all values in delayTimeCart into bytes-like object
for i in range(len(delayTimeCart)):
    delayTimeCart[i] = intToBytes(delayTimeCart[i],byteOrder)

print(delayTimeCart)
# writing new delay times
with open(filename,"r+b") as binary_file:
    for i in range(len(delayTimeCart)):
        binary_file.seek(GCBCart[i]+4)
        binary_file.write(delayTimeCart[i])
    binary_file.close()

graphicControl1 = filescan(filename)
GCBCart, delayTimeCart, end = frameScan(filename,graphicControl1)
print(GCBCart)
print(delayTimeCart)


'''
with open("newtonscradle.gif","rb") as binary_file:
    index = 0
    for i in range(255):
        binary_file.seek(index)
        abyte = binary_file.read(4)
        pprint(abyte)
        index += 4
'''

'''
with open("newtonscradle.gif","rb") as binary_file:
    end = False
    index = 0
    while end == False:
        binary_file.seek(index)
        abyte = binary_file.read(1)
        if abyte == "":
            end = True
        pprint(abyte)
        pprint(type(abyte))
        index += 1
        

'''
'''
""" reading files binary way """
with open("newtonscradle.gif","rb") as binary_file:
    data = binary_file.read()
    pprint(data)
'''



'''
with open("newtonscradle.gif","rb") as binary_file:
    binary_file.seek(781)   # jump to 781th byte (application extension block)
    couple_bytes = binary_file.read(14) # read off 14 bytes
    pprint(couple_bytes)
'''
