import math
from pprint import pprint

def intFromBytes(someBytes, byteOrder):
    return int.from_bytes(someBytes, byteorder=byteOrder)


def intToBytes(someInt, byteOrder):
    return someInt.to_bytes(2, byteorder=byteOrder, signed=False)


def parse(filename):
    binary_file = open(filename, 'rb')
    binary_file.seek(0)

    # header
    header = binary_file.read(6)

    # logical screen descriptor
    logicalScreenDescriptor = binary_file.read(7)
    LCDpacked = ('{:08b}'.format(logicalScreenDescriptor[4]))
    globalColorTableFlag = LCDpacked[-1]
    globalColorTableSize = LCDpacked[:3]

    # global color table
    if globalColorTableFlag == '1':
        # handle parsing the global color table
        globalColorTable = binary_file.read(3 * (2 ** (int(globalColorTableSize,2)+1)))
        print(len(globalColorTable))

    # application extension block
    identifier = binary_file.read(2)
    if identifier[0] == 33 and identifier[1] == 255:
        blocksize = binary_file.read(1)
        applicationExtension = binary_file.read(blocksize[0])
        blockTerminator = binary_file.read(1)
        while blockTerminator[0] != 0:
            blockTerminator = binary_file.read(1)

    # graphics control extension
    identifier = binary_file.read(2)
    if identifier[0] == 33 and identifier[1] == 249:
        blocksize = binary_file.read(1)
        graphicsControlExtension = binary_file.read(blocksize[0])
        blockTerminator = binary_file.read(1)
        while blockTerminator[0] != 0:
            blockTerminator = binary_file.read(1)

    # todo: data block?

    binary_file.close()


byteOrder = 'little'
filename = 'rotatingearthCopy.gif'
parse(filename)

def filescan(filename):
    # scan through the entire file once to find the positions of all the blocks
    with open(filename, "rb") as binary_file:
        index = 800

        binary_file.seek(index)
        while index < 400000:
            abyte = binary_file.read(2)
            try:
                if intFromBytes(abyte, byteOrder) == 63777:
                    # found the first block
                    binary_file.close()
                    return index

                index += 1
            except:
                index += 1


def frameScan(filename, index):
    # parse bytes in the file of choice
    # reads and extracts
    # location of each graphics control block
    # delay value for each frame
    # location of the end of file
    # output:
    # array: indexes of every graphics control block
    # array: delay value of each graphics control block
    # int: index of the end of file
    binary_file = open(filename, 'rb')
    GCBCart = []  # array of indexes of starting points of graphic control blocks
    delayTimeCart = []  # array of delay times for each frame
    fileTerminator = False
    while fileTerminator == False:
        print("graphic control block")
        print(index)
        binary_file.seek(index)
        GCBCart.append(index)

        # 8 bytes graphic control
        skipForward = binary_file.read(2)  # extension introducer, graphic control label
        print(skipForward)
        skipForward = binary_file.read(1)  # block size
        skipForward = binary_file.read(1)  # packed fields
        delayTime = binary_file.read(2)
        delayTimeCart.append(intFromBytes(delayTime, byteOrder))
        skipForward = (binary_file.read(2))  # transparent color index, block terminator
        # 10 bytes image descriptor
        skipForward = binary_file.read(10)
        index += 18
        LZW = binary_file.read(1)
        index += 1
        # nicePrint(LZW, 'LZW min code size')
        while True:
            noBytes = binary_file.read(1)
            noBytes = intFromBytes(noBytes, byteOrder)
            # print(noBytes)
            index += 1
            if noBytes == 0:  # end of frame
                break
            # nicePrint(noBytes,'no of bytes next')
            skipForward = binary_file.read(noBytes)
            index += noBytes
        terminateCheck = intFromBytes(binary_file.read(1), byteOrder)
        if terminateCheck == 59:
            fileTerminator = True
            binary_file.close()
            return (GCBCart, delayTimeCart, index)


def readHeader(filename):
    # header is always the first six bytes
    with open(filename, "rb") as binary_file:
        binary_file.seek(0)  # go to header (beginning of file)
        couple_bytes = binary_file.read(6)  # read off 6 bytes
        binary_file.close()
        return (couple_bytes)


def readLogicalScreenDescriptor(filename):
    # Logical Screen Descriptor comes after the header and takes the next 6 bytes
    # width: 2 bytes, height: 2 bytes, byteorder: 2 bytes, pixel aspect ratio: 2 bytes
    index = 6
    with open(filename, "rb") as binary_file:
        binary_file.seek(index)
        width = intFromBytes(binary_file.read(2), byteOrder)
        index += 2
        nicePrint(width, 'width')

        binary_file.seek(index)
        height = intFromBytes(binary_file.read(2), byteOrder)
        index += 2
        nicePrint(height, 'height')

        binary_file.seek(index)
        bgColor = intFromBytes(binary_file.read(1), byteOrder)
        index += 1
        nicePrint(bgColor, 'background color')

        binary_file.seek(index)
        pixelaspectratio = intFromBytes(binary_file.read(1), byteOrder)
        index += 1
        nicePrint(pixelaspectratio, 'pixel aspect ratio')

        binary_file.close()

        return (width, height, bgColor, pixelaspectratio)