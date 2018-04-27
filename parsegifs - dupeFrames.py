from pprint import pprint
import struct
import codecs

def intFromBytes(someBytes, byteOrder):
    if str(type(someBytes)) == "<class 'list'>":
        for i in range(len(someBytes)):
            someBytes[i] = int.from_bytes(someBytes[i],byteorder=byteOrder)
        return someBytes

    return int.from_bytes(someBytes, byteorder=byteOrder)

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

def readImageDescriptor():
    #
    next()

def readImageData():
    #
    next()

def nicePrint(thing,thingName):
    print(thingName + ":")
    print(thing)
    print("\n")

filename = "rotatingearthCopy.gif"
outfilename = 'modifiedgif.gif'
byteOrder = 'little'

header = readHeader(filename)
nicePrint(header.decode('utf-8'),'file format')

width,height,bgColor,pixelaspectratio = readLogicalScreenDescriptor(filename)

graphicControl1 = filescan(filename)
GCBCart, delayTimeCart, end = frameScan(filename,graphicControl1)

print(GCBCart)
print(delayTimeCart)

# duplicate every frame
newFile = open(outfilename,'a+b')
with open(filename,'r+b') as binary_file:
    # write the beginning portion of the file up till the first graphic control block
    binary_file.seek(0)
    fileChunk = binary_file.read(GCBCart[0]-1)
    newFile.write(fileChunk)
    # duplicate each frame up till the second last frame
    for i in range(len(GCBCart)-1):
        fileChunk = binary_file.read(GCBCart[i+1]-GCBCart[i])
        newFile.write(fileChunk)
        newFile.write(fileChunk)
    # duplicate last frame
    fileChunk = binary_file.read(end-GCBCart[-1])
    newFile.write(fileChunk)
    newFile.write(fileChunk)
    # write the rest of the file
    while True:
        fileChunk = binary_file.read(1)
        if not fileChunk:
            break
        newFile.write(fileChunk)
newFile.close()
binary_file.close()

graphicControl1 = filescan(outfilename)
GCBCart, delayTimeCart, end = frameScan(outfilename,graphicControl1)

# half the duration for each frame
for i in range(len(delayTimeCart)):
    item = delayTimeCart[i]//2
    newitem = item.to_bytes(2,'little',signed=False)
    delayTimeCart[i] = newitem
print(delayTimeCart)

# writing new delay times
with open(outfilename,"r+b") as binary_file:
    for i in range(len(delayTimeCart)):
        binary_file.seek(GCBCart[i]+4)
        binary_file.write(delayTimeCart[i])
    binary_file.close()


graphicControl1 = filescan(outfilename)
GCBCart, delayTimeCart, end = frameScan(outfilename,graphicControl1)
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
