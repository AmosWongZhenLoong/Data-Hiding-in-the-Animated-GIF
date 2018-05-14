from pprint import pprint
import struct
import codecs
import math
import time


def intFromBytes(someBytes, byteOrder):
    if str(type(someBytes)) == "<class 'list'>":
        for i in range(len(someBytes)):
            someBytes[i] = int.from_bytes(someBytes[i], byteorder=byteOrder)
        return someBytes

    return int.from_bytes(someBytes, byteorder=byteOrder)


def intToBytes(someInt, byteOrder, noBytes):
    return someInt.to_bytes(noBytes, byteorder=byteOrder, signed=False)


def parse(filename):
    delayLocations = []
    delayTimeCart = []
    GCBCart = []

    binary_file = open(filename, 'rb')
    binary_file.seek(0)
    index = 0

    # header
    header = binary_file.read(6)
    index += 6

    # logical screen descriptor
    logicalScreenDescriptor = binary_file.read(7)
    index += 7
    LCDpacked = ('{:08b}'.format(logicalScreenDescriptor[4]))
    globalColorTableFlag = LCDpacked[-1]
    globalColorTableSize = LCDpacked[:3]

    # global color table
    if globalColorTableFlag == '1':
        CTindex = index
        # handle parsing the global color table
        globalColorTable = binary_file.read(3 * (2 ** (int(globalColorTableSize, 2) + 1)))
        index += (3 * (2 ** (int(globalColorTableSize, 2) + 1)))
    else:
        CTindex = -1
        globalColorTable = -1

    # application extension block
    identifier = binary_file.read(2)
    index += 2
    if identifier[0] == 33 and identifier[1] == 255:
        blocksize = binary_file.read(1)
        index += 1
        applicationExtension = binary_file.read(blocksize[0])
        #print(applicationExtension)
        index += blocksize[0]
        print(index)
        blocksize = binary_file.read(1)
        index += 1
        while blocksize[0] != 0:
            applicationData = binary_file.read(blocksize[0])
            print(applicationData)
            index += blocksize[0] + 1
            blocksize = binary_file.read(1)

    while True:
        identifier = binary_file.read(2)
        if len(identifier)>1:
            print(identifier[0],identifier[1])
        else:
            print(identifier[0])
        index += 2
        if identifier[0] == 33 and identifier[1] == 249:    # graphics control extension
            GCBCart.append(index - 2)
            blocksize = binary_file.read(1)
            print(blocksize[0])
            index += 1
            graphicsControlExtension = binary_file.read(blocksize[0])
            print(graphicsControlExtension[0])

            delayTimeCart.append(graphicsControlExtension[1:2])
            delayLocations.append(index + 1)

            index += blocksize[0]
            blockTerminator = binary_file.read(1)
            index += 1
            while blockTerminator[0] != 0:
                blockTerminator = binary_file.read(1)
                index += 1

            # img descriptor
            identifier = binary_file.read(1)
            print(identifier[0])
            index += 1
            if identifier[0] == 44:
                imageDescriptor = binary_file.read(9)
                index += 9
            print(imageDescriptor)

            # Table based image data
            LZW = binary_file.read(1)
            print(LZW[0])
            index += 1
            blocksize = binary_file.read(1)
            index += 1
            while blocksize[0] != 0:
                imgData = binary_file.read(blocksize[0])
                #textfile = open('imgdataEARTHdebug.txt','a+')
                #or byte in range(len(imgData)):
                #    textfile.write(str(imgData[byte])+" ")
                #    if byte%40 == 0:
                #        textfile.write('\n')
                #textfile.write('\n')
                #textfile.write('\n')
                index += blocksize[0]
                blocksize = binary_file.read(1)
                index += 1
            print('\n')

        elif identifier[0] == 33 and identifier[1] == 254:      # comment extension block
            blocksize = binary_file.read(1)
            index += 1
            while blocksize[0] != 0:
                commentData = binary_file.read(blocksize[0])
                index += blocksize[0] + 1
                blocksize = binary_file.read(1)

        elif identifier[0] == 59:
            print('parse complete')
            break

    endIndex = index

    binary_file.close()

    return delayLocations, delayTimeCart, endIndex, GCBCart, CTindex, globalColorTableSize, globalColorTable


def getCharCapacity(delayTimeCart):
    # calculate how many characters can be stored
    # return: number of characters that can be stored
    frameCount = len(delayTimeCart)
    msgHeader = 8  # 8 bits to store msg length
    msgBits = frameCount - msgHeader  # number of bits remaining to store the message
    return math.floor(msgBits // 8)


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


def modifyDelayTimes(bitstream, delayTimeCart):
    # modify the delayTimeCart to store the message
    # message representation:
    # even number represents one(0)
    # odd number represents zero(1)
    for i in range(len(bitstream)):
        if int(bitstream[i]) == 0:  # is even
            if delayTimeCart[i] % 2 == 1:  # is odd
                delayTimeCart[i] = delayTimeCart[i] + 1
        else:
            if delayTimeCart[i] % 2 == 0:  # is even
                delayTimeCart[i] = delayTimeCart[i] + 1
    return delayTimeCart


def writeToFile(filename, delayTimeCart, delayLocations):
    with open(filename, "r+b") as binary_file:
        for i in range(len(delayTimeCart)):
            binary_file.seek(delayLocations[i])
            binary_file.write(delayTimeCart[i])
        binary_file.close()