from pprint import pprint
import struct
import codecs

import FuncLib as FuncLib



filename = "rotatingearthCopy.gif"
outputfilename = 'modifiedgif.gif'
byteOrder = 'little'


delayLocations,delayTimeCart,endIndex,GCBCart = FuncLib.parse(filename)
delayTimeCart = FuncLib.intFromBytes(delayTimeCart,byteOrder)

print(delayLocations)
print(delayTimeCart)
print(GCBCart)

newFile = open(outputfilename,'a+b')
binary_file = open(filename,'r+b')

# write the first part of the file up till the first graphics control block
binary_file.seek(0)
initialChunk = binary_file.read(GCBCart[0]-1)
newFile.write(initialChunk)
i = 1
while i < len(GCBCart):
    uChunk = binary_file.read(13)
    u21Chunk = binary_file.read(2)
    u22Chunk = binary_file.read(2)
    u3Chunk = binary_file.read(1)
    lChunk = binary_file.read(GCBCart[i]-GCBCart[i-1]-18)
    newFile.write(uChunk)
    newFile.write(u21Chunk)
    newFile.write(u22Chunk)
    newFile.write(u3Chunk)
    newFile.write(lChunk)

    u21Chunk = FuncLib.intToBytes(1,byteOrder,2)
    u22Chunk = FuncLib.intToBytes(1, byteOrder,2)

    newFile.write(uChunk)
    newFile.write(u21Chunk)
    newFile.write(u22Chunk)
    newFile.write(u3Chunk)
    lChunk = FuncLib.intToBytes(8, byteOrder, 1)
    newFile.write(lChunk)
    lChunk = FuncLib.intToBytes(1, byteOrder, 1)
    newFile.write(lChunk)
    lChunk = FuncLib.intToBytes(255, byteOrder, 1)
    newFile.write(lChunk)
    lChunk = FuncLib.intToBytes(0, byteOrder, 1)
    newFile.write(lChunk)

    i = i + 1
while True:
    fileChunk = binary_file.read(1)
    if not fileChunk:
        break
    newFile.write(fileChunk)

newFile.close()
binary_file.close()


#todo: put one pixel of the transparent color in between every frame
#todo: set original frame to delay = 1
#todo: stack as many transparent frames on top

'''
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

'''
