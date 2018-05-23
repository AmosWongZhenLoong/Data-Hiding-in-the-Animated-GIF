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
    frameTypeCart = []

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
        blocksize = binary_file.read(1)
        index += 1
        while blocksize[0] != 0:
            applicationData = binary_file.read(blocksize[0])
            index += blocksize[0] + 1
            blocksize = binary_file.read(1)

    while True:
        identifier = binary_file.read(2)
        index += 2
        if identifier[0] == 33 and identifier[1] == 249:    # graphics control extension
            GCBCart.append(index - 2)
            blocksize = binary_file.read(1)
            index += 1
            graphicsControlExtension = binary_file.read(blocksize[0])

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
            index += 1
            if identifier[0] == 44:
                imageDescriptor = binary_file.read(9)
                index += 9

            # Table based image data
            LZW = binary_file.read(1)
            index += 1
            blocksize = binary_file.read(1)

            # takes note of the transparent 1x1 pixel frames (for decoding purposes)
            if blocksize[0] == 4:
                frameTypeCart.append(1)
            else:
                frameTypeCart.append(0)

            index += 1
            while blocksize[0] != 0:
                imgData = binary_file.read(blocksize[0])
                index += blocksize[0]
                blocksize = binary_file.read(1)
                index += 1

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

    return delayLocations, delayTimeCart, endIndex, GCBCart, CTindex, globalColorTableSize, globalColorTable, frameTypeCart


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


def msgfrombits(bits):
    # convert bitstream to text
    # output: text
    msg = ""
    for i in range(len(bits)):
        if i % 8 == 0:
            byte = bits[i:i+8]
            char = chr(int(byte,2))
            msg = msg + char
    return msg


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


def encode(delayTimeCart,msg,minDelay):
    # encodes the structure of the new frames in the form of delay values
    # minimum frame delay for chrome, firefox, and opera: 0.02s
    # minimum frame delay safari and IE: 0.06s
    # info as of: http://nullsleep.tumblr.com/post/16524517190/animated-gif-minimum-frame-delay-browser
    # error handle -1: insufficient capacity to store message
    newDelayTimeCart = []
    group = []

    delayTimeCartIndex = 0
    i = 0

    delay = delayTimeCart[delayTimeCartIndex]
    group.append(minDelay)

    while i < len(msg):
        # original frame still has capacity
        if sum(group) < delay:
            # next appending frame exceeds capacity
            if int(msg[i])+(minDelay) + sum(group) > delay:
                pad_amount = delay - sum(group)
                group[0] = group[0] + pad_amount
                i -= 1
            else:
                group.append(int(msg[i])+minDelay)
        # last appended frame fits capacity perfectly
        # reset stuff
        if sum(group) == delay:
            newDelayTimeCart.append(group)
            group = []
            group.append(minDelay)
            delayTimeCartIndex += 1
            # out of original frames for storage
            if delayTimeCartIndex >= len(delayTimeCart):
                return -1
            delay = delayTimeCart[delayTimeCartIndex]
        i += 1

    # half an original frame filled
    if len(group) > 1:
        newDelayTimeCart.append(group)

    # pad the last frame so that total delay is correct
    pad_amount = delay - sum(newDelayTimeCart[-1])
    if pad_amount != 0:
        newDelayTimeCart[-1][0] = newDelayTimeCart[-1][0] + pad_amount


    return newDelayTimeCart


def writeOriginal(newFile, binary_file, GCBCart, i, byteOrder, delay):
    binary_file.seek(GCBCart[i-1])
    uChunk = binary_file.read(3)  # gcb identifier + blocksize
    packedfields = binary_file.read(1)  # packed fields
    dtChunk = binary_file.read(2)  # delay time
    tciChunk = binary_file.read(1)  # transparent color index
    nChunk = binary_file.read(6)  # terminator + identifier + img positions
    u21Chunk = binary_file.read(2)  # img width
    u22Chunk = binary_file.read(2)  # img height
    packedfields2 = binary_file.read(1)  # packed fields
    lChunk = binary_file.read(GCBCart[i] - GCBCart[i - 1] - 18)  # image data

    # changing disposal method so that each frame remains on screen
    packedfields = intToBytes(5, byteOrder, 1)

    # change delay
    if delay != -1:
        dtChunk = intToBytes(delay,byteOrder,2)  # delay time

    # test change transparent color flag
    #tciChunk = intToBytes(0,byteOrder,1)

    # append to file
    newFile.write(uChunk)
    newFile.write(packedfields)
    newFile.write(dtChunk)
    newFile.write(tciChunk)
    newFile.write(nChunk)
    newFile.write(u21Chunk)
    newFile.write(u22Chunk)
    newFile.write(packedfields2)
    newFile.write(lChunk)


def writeTransparent(newFile, binary_file, GCBCart, i, byteOrder, delay):
    binary_file.seek(GCBCart[i-1])
    uChunk = binary_file.read(3)  # gcb identifier + blocksize
    packedfields = binary_file.read(1)  # packed fields
    dtChunk = binary_file.read(2)  # delay time
    tciChunk = binary_file.read(1)  # transparent color index
    nChunk = binary_file.read(6)  # terminator + identifier + img positions
    u21Chunk = binary_file.read(2)  # img width
    u22Chunk = binary_file.read(2)  # img height
    packedfields2 = binary_file.read(1)  # packed fields

    # changing disposal method so that each frame remains on screen
    packedfields = intToBytes(5, byteOrder, 1)

    # change delay
    dtChunk = intToBytes(delay, byteOrder, 2)  # delay time

    # test change transparent color flag
    #tciChunk = intToBytes(0,byteOrder,1)

    # changing width and height of transparent frame to 1px
    u21Chunk = intToBytes(1, byteOrder, 2)
    u22Chunk = intToBytes(1, byteOrder, 2)

    # append to file
    newFile.write(uChunk)
    newFile.write(packedfields)
    newFile.write(dtChunk)
    newFile.write(tciChunk)
    newFile.write(nChunk)
    newFile.write(u21Chunk)
    newFile.write(u22Chunk)
    newFile.write(packedfields2)

    # writing image data of a transparent frame
    lChunk = intToBytes(8, byteOrder, 1)    #LZW
    newFile.write(lChunk)
    lChunk = intToBytes(4, byteOrder, 1)    #blocksize
    newFile.write(lChunk)
    lChunk = intToBytes(0, byteOrder, 1)    #byte1
    newFile.write(lChunk)
    lChunk = intToBytes(255, byteOrder, 1)  #byte2
    newFile.write(lChunk)
    lChunk = intToBytes(5, byteOrder, 1)    #byte3
    newFile.write(lChunk)
    lChunk = intToBytes(4, byteOrder, 1)    #byte4
    newFile.write(lChunk)
    lChunk = intToBytes(0, byteOrder, 1)    #end of LZW
    newFile.write(lChunk)


def getHidingCapacity(delayTimeCart,minDelay):
    # calculates average hiding capacity based on:
    # total number of frames, average additional frames per frame, minimum delay specified by user
    # returns average characters that can be hidden
    totalAvgPerFrame = 0
    for i in range(len(delayTimeCart)):
        frameCap = delayTimeCart[i]
        minBitsPerFrame = math.floor((frameCap - minDelay) / minDelay)
        maxBitsPerFrame = math.floor((frameCap - minDelay) / (minDelay + 1))
        avgBitsPerFrame = ((minBitsPerFrame + maxBitsPerFrame) / 2)
        totalAvgPerFrame += avgBitsPerFrame
    avgBitsPerFrame = (totalAvgPerFrame / len(delayTimeCart))
    estChars = math.floor((len(delayTimeCart) * avgBitsPerFrame) / 8)
    return estChars


def decodePrep(delayTimeCart,frameTypeCart):
    bitValuesUsed = []
    oriDelayTimeCart = []
    tempDelay = []

    for i in range(len(delayTimeCart)):
        if frameTypeCart[i] == 0 and len(tempDelay) == 0:
            tempDelay.append(delayTimeCart[i])
        elif frameTypeCart[i] == 1 and len(tempDelay) != 0:
            tempDelay.append(delayTimeCart[i])
            if delayTimeCart[i] not in bitValuesUsed:
                bitValuesUsed.append(delayTimeCart[i])
        elif frameTypeCart[i] == 0 and len(tempDelay) != 0:
            oriDelayTimeCart.append(tempDelay)
            tempDelay = []
            tempDelay.append(delayTimeCart[i])
        elif i == len(delayTimeCart) - 1:
            tempDelay.append(delayTimeCart[i])
            oriDelayTimeCart.append(tempDelay)
            delay = []
            if delayTimeCart[i] not in bitValuesUsed:
                bitValuesUsed.append(delayTimeCart[i])

    if len(tempDelay) > 0:
        oriDelayTimeCart.append(tempDelay)

    return bitValuesUsed,oriDelayTimeCart


def decode(bitValuesUsed,frameTypeCart,delayTimeCart):
    bits = ""
    msg = ""

    for i in range(len(frameTypeCart)):
        if frameTypeCart[i] == 1:
            if delayTimeCart[i] == bitValuesUsed[0]:
                bits += "0"
            elif delayTimeCart[i] == bitValuesUsed[1]:
                bits += "1"
            if len(bits) == 8:
                d = int(bits,2)
                char = chr(d)
                msg += char
                bits = ""

    return msg



