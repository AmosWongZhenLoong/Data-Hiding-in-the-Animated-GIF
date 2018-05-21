from pprint import pprint
import struct
import codecs
import time

import FuncLib as FuncLib



filename = "oilpump.gif"
outputfilename = 'modifiedgif.gif'
reconstructedfilename = 'reconstructedgif.gif'
byteOrder = 'little'

# get essentials
delayLocations,delayTimeCart,endIndex,GCBCart,CTindex,globalColorTableSize,globalColorTable,frameTypeCart = FuncLib.parse(filename)
delayTimeCart = FuncLib.intFromBytes(delayTimeCart,byteOrder)

print(delayLocations)
print(delayTimeCart)
print(GCBCart)
print(frameTypeCart)

# choose encode or decode
print("do you want to do encoding or decoding?")
action = str(input("type e for encoding, type d for decoding: "))

if action == 'e':       # do encoding

    # web browser compatibility selection
    print("Different browsers support different minimum delay values")
    print("Lower values increase hiding capacity, but decrease playback accuracy with some browsers")
    print("Reference guide for the 5 most popular browsers (values are in 1/100th of a second): ")
    print("Chrome/Firefox/Opera: 2 | Safari,IE: 6")
    minDelay = int(input("Enter desired minimum delay: "))

    # hiding capacity
    charCap = FuncLib.getHidingCapacity(delayTimeCart,minDelay)
    if charCap < 1:
        print("unable to hide data, as file contains delays that are too small")
        time.sleep(3)
        quit()
    else:
        print("the estimated text capacity is %d characters" % charCap)

    # get message from user
    userinput = str(input("Enter message here: "))

    # convert message to bits
    userinputbits = FuncLib.msg2bits(userinput)

    print(userinput)
    print(userinputbits)

    # encode the message
    print("encoding the message")
    newDelayTimeCart = FuncLib.encode(delayTimeCart,userinputbits,minDelay)
    if newDelayTimeCart == -1:
        print("insufficient capacity to store message")
        time.sleep(3)
        quit()
    print(newDelayTimeCart)

    # create a new file for writing
    newFile = open(outputfilename,'a+b')
    binary_file = open(filename,'r+b')

    # write the first part of the file up till the first graphics control block
    print("writing first part of file")
    binary_file.seek(0)
    initialChunk = binary_file.read(GCBCart[0])
    newFile.write(initialChunk)

    print("writing middle portion of file")
    i = 1
    j = 0

    while i < len(GCBCart):
        if j < len(newDelayTimeCart):
            sequence = newDelayTimeCart[j]
            for index in range(len(sequence)):
                delay = sequence[index]
                if index == 0:
                    FuncLib.writeOriginal(newFile,binary_file,GCBCart,i,byteOrder,delay)
                    print('wrote original"')
                else:
                    FuncLib.writeTransparent(newFile,binary_file,GCBCart,i,byteOrder,delay)
                    print('wrote transparent')
        else:
            FuncLib.writeOriginal(newFile,binary_file,GCBCart,i,byteOrder,-1)
            print('wrote unchanged')

        j += 1
        i += 1

    # write everything else after the last image data
    # up till the end of file
    print("writing last part of file")
    while True:
        fileChunk = binary_file.read(1)
        if not fileChunk:
            break
        newFile.write(fileChunk)

    newFile.close()
    binary_file.close()
    print("process complete")

elif action == 'd':     # do decoding
    # get some information necessary for msg decoding and original GIF reconstruction
    bitValuesUsed,oriDelayTimeCart = FuncLib.decodePrep(delayTimeCart,frameTypeCart)
    bitValuesUsed.sort()
    print(bitValuesUsed)
    print(len(oriDelayTimeCart))

    # recover proper delay values
    for i in range(len(oriDelayTimeCart)):
        oriDelayTimeCart[i] = sum(oriDelayTimeCart[i])
    print(len(oriDelayTimeCart))

    msg = FuncLib.decode(bitValuesUsed,frameTypeCart,delayTimeCart)
    print(msg)

    # reconstruct original GIF image
    file = open(reconstructedfilename,'a+b')
    file2 = open('modifiedgif.gif','r+b')

    # write everything up till the first graphics control block
    file2.seek(0)
    file_beginning = file2.read(GCBCart[0])
    file.write(file_beginning)

    # write all the original frames only
    j = 0
    for i in range(len(GCBCart)):
        if frameTypeCart[i] == 0 and i == len(GCBCart) - 1:
            file2.seek(GCBCart[i])
            fchunk = file2.read(4)
            dchunk = file2.read(2)
            lchunk = file2.read(endIndex - GCBCart[i] - 6)

            dchunk = FuncLib.intToBytes(oriDelayTimeCart[j],'little',2)
            j += 1

            file.write(fchunk)
            file.write(dchunk)
            file.write(lchunk)
        elif frameTypeCart[i] == 0:
            file2.seek(GCBCart[i])
            fchunk = file2.read(4)
            dchunk = file2.read(2)
            lchunk = file2.read(GCBCart[i + 1] - GCBCart[i] - 6)

            dchunk = FuncLib.intToBytes(oriDelayTimeCart[j], 'little', 2)
            j += 1

            file.write(fchunk)
            file.write(dchunk)
            file.write(lchunk)

    # write remainder of file
    if file2.tell() < endIndex - 1:
        file2.seek(endIndex - 1)
        chunk = file2.read(1)
        while chunk:
            file.write(chunk)
            chunk = file2.read(1)

    file.close()
    file2.close()

    print('decode complete')



else:                   # quit?
    print("invalid command")
    time.sleep(3)
    quit()


