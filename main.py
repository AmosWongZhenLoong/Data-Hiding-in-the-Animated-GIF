from pprint import pprint
import struct
import codecs
import time
import timeit
import os

import FuncLib as FuncLib





byteOrder = 'little'

# user input:hide or extract
print("do you want to do hiding or extracting?")
action = str(input("type h for hiding, type e for extracting: "))

if action == 'h':       # do hiding
    # user input: get the filenames
    filename = str(input("enter filename: "))
    outputfilename = 'E_%s' % filename

    # get essentials
    delayLocations, delayTimeCart, endIndex, GCBCart, CTindex, globalColorTableSize, globalColorTable, frameTypeCart = FuncLib.parse(
        filename)
    delayTimeCart = FuncLib.intFromBytes(delayTimeCart, byteOrder)

    # debugging prints
    '''
    print(delayLocations)
    print(delayTimeCart)
    print(GCBCart)
    print(frameTypeCart)
    '''

    # minimum delay for web browser compatibility
    minDelay = 2

    # hiding calculate average hiding capacity
    charCap = FuncLib.getHidingCapacity(delayTimeCart,minDelay)
    if charCap < 1:
        print("unable to hide data, as file contains delays that are too small")
        time.sleep(3)
        quit()
    else:
        print("the estimated text capacity is %d characters" % charCap)

    # get message from user
    userinput = str(input("Enter message here: "))

    etime = timeit.default_timer()

    # convert message to bits
    userinputbits = FuncLib.msg2bits(userinput)

    # encode the message
    print("encoding the message")
    newDelayTimeCart = FuncLib.encode(delayTimeCart,userinputbits,minDelay)
    if newDelayTimeCart == -1:
        print("insufficient capacity to store message")
        time.sleep(1)
        quit()

    # create a new file for writing
    if outputfilename in os.listdir():
        os.remove(outputfilename)
    newFile = open(outputfilename,'a+b')
    binary_file = open(filename,'r+b')

    # write the first part of the file up till the first graphics control block
    print("producing a file with the hidden message")
    binary_file.seek(0)
    initialChunk = binary_file.read(GCBCart[0])
    newFile.write(initialChunk)

    i = 1
    j = 0

    while i < len(GCBCart):
        if j < len(newDelayTimeCart):
            sequence = newDelayTimeCart[j]
            for index in range(len(sequence)):
                delay = sequence[index]
                if index == 0:
                    FuncLib.writeOriginal(newFile,binary_file,GCBCart,i,byteOrder,delay)
                else:
                    FuncLib.writeTransparent(newFile,binary_file,GCBCart,i,byteOrder,delay)
        else:
            FuncLib.writeOriginal(newFile,binary_file,GCBCart,i,byteOrder,-1)

        j += 1
        i += 1

    # write everything else after the last image data
    # up till the end of file
    while True:
        fileChunk = binary_file.read(1)
        if not fileChunk:
            break
        newFile.write(fileChunk)

    newFile.close()
    binary_file.close()
    etime = timeit.default_timer() - etime
    print("embed process completed in %.3f " % etime)

    ostat = os.stat(filename)
    osize = ostat.st_size
    estat = os.stat(outputfilename)
    esize = estat.st_size

    size_increase = ((esize-osize)/osize)*100

    print("the original file size is %d bytes" % osize)
    print("the new file size is %d bytes" % esize)
    print("the new file is %.3f percent larger than the original" % size_increase)

elif action == 'e':     # do extraction
    # get filenames
    outputfilename = str(input("enter filename: "))
    reconstructedfilename = 'R_%s' % outputfilename

    # get essentials
    delayLocations, delayTimeCart, endIndex, GCBCart, CTindex, globalColorTableSize, globalColorTable, frameTypeCart = FuncLib.parse(
        outputfilename)
    delayTimeCart = FuncLib.intFromBytes(delayTimeCart, byteOrder)

    # debugging purposes
    '''
    print(delayLocations)
    print(delayTimeCart)
    print(GCBCart)
    print(frameTypeCart)
    '''

    dtime = timeit.default_timer()

    # get some information necessary for msg decoding and original GIF reconstruction
    bitValuesUsed,oriDelayTimeCart = FuncLib.decodePrep(delayTimeCart,frameTypeCart)
    bitValuesUsed.sort()

    # recover proper delay values
    for i in range(len(oriDelayTimeCart)):
        oriDelayTimeCart[i] = sum(oriDelayTimeCart[i])

    msg = FuncLib.decode(bitValuesUsed,frameTypeCart,delayTimeCart)
    print("the hidden message is: %s" % msg)

    # reconstruct original GIF image
    if reconstructedfilename in os.listdir():
        os.remove(reconstructedfilename)
    file = open(reconstructedfilename,'a+b')
    file2 = open(outputfilename,'r+b')

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

    dtime = timeit.default_timer() - dtime
    print('decode completed in %.3f' % dtime)

    rstat = os.stat(reconstructedfilename)
    rsize = rstat.st_size

    print("the size of the reconstructed file is %d bytes" % rsize)


else:                   # quit?
    print("invalid command")
    time.sleep(3)
    quit()


