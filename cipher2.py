import random
import sys
from PIL import Image
from random import randint
import re
from numpy import uint64
from helper import *

im = Image.open('input/1.jpg')
pix = im.load()
m = im.size[0]
n = im.size[1]
alpha = 8
Kr = [randint(0, pow(2, alpha)-1) for i in range(m)]
Kc = [randint(0, pow(2, alpha)-1) for i in range(n)]
ITER_MAX = 31

print('Vector Kr : ', Kr)
print('Vector Kc : ', Kc)

f = open('keys.txt', 'w+')
f.write('Vector Kr : \n')
for a in Kr:
    f.write(str(a) + '\n')
f.write('Vector Kc : \n')
for a in Kc:
    f.write(str(a) + '\n')
f.write('ITER_MAX : \n')
f.write(str(ITER_MAX) + '\n')

# Obtaining the RGB matrices
r = []
g = []
b = []
for i in range(im.size[0]):
    r.append([])
    g.append([])
    b.append([])
    for j in range(im.size[1]):
        rgbPerPixel = pix[i, j]
        r[i].append(rgbPerPixel[0])
        g[i].append(rgbPerPixel[1])
        b[i].append(rgbPerPixel[2])


print("m", m)
print("n", n)

# define the SBox
S = [0xC, 0x5, 0x6, 0xB, 0x9, 0x0, 0xA, 0xD,
     0x3, 0xE, 0xF, 0x8, 0x4, 0x7, 0x1, 0x2]

# define the inverse SBox
invS = [0x5, 0xe, 0xf, 0x8, 0xC, 0x1, 0x2, 0xD,
        0xB, 0x4, 0x6, 0x3, 0x0, 0x7, 0x9, 0xA]

# define the permutation table

P = [0, 16, 32, 48, 1, 17, 33, 49, 2, 18, 34, 50, 3, 19, 35, 51,
     4, 20, 36, 52, 5, 21, 37, 53, 6, 22, 38, 54, 7, 23, 39, 55,
     8, 24, 40, 56, 9, 25, 41, 57, 10, 26, 42, 58, 11, 27, 43, 59,
     12, 28, 44, 60, 13, 29, 45, 61, 14, 30, 46, 62, 15, 31, 47, 63]


nibble1 = 4
nibble2 = 4


def fromHexStringToLong(block):
    block = fromLongToHexString(block)
    result = 0
    print("block", block)
    block = str(block)
    print("again block", block)

    # each character is 4 bits, there are 16 characters in a 64-bit block
    # the multiplication and addition are done the same way as before, with shifting and bitwise OR
    for i in range(len(block)):
        result = (result << 4) or (int(block[i])-1 if ((block[i] >= '1' and block[i] <= '9'))
                                   else (int(block[i]) + 10))
    return result


# function for converting a 64-bit integer to an array of bytes

def fromLongToHexString(block):
    hexString = 17 * sys.getsizeof(numpy.byte)
    # we print the integer in a String in hexadecimal format
    print(hexString, block)
    return hexString


def Sbox(input):
    return S[input]


def inverseSbox(input):
    return invS[input]


def getKeyLow(key):

    keyLow = 0
    key = str(key)
    # the least significant 16 bits are the last 4 characters of the key
    print("key", key)

    for i in range(len(key)-1):
        # again, multiplication and addition are done using bitwise left shift and bitwise OR
        if key[i] != '[' and key != ']' and key[i] != " " and key[i] != '\n':
            keyLow = (keyLow << 4) | (
                int(key[i]) if (key[i] >= '0' and key[i]
                                <= '9') else int(key[i]) & 0xF)
    return keyLow


def generateSubkeys(key):
    # the 80 bit key is placed in two integers, one that is 16-bit (keyLow) and the other one is 64-bit (keyHigh)
    keyHigh = fromHexStringToLong(key)
    keyLow = getKeyLow(key)
    subKeys = numpy.full(64, 64, dtype=uint64)

    # the first subkey is the high part of the original key
    subKeys[0] = keyHigh
    for i in range(1, 32):  # initially in range(1,32)
        # shifting the whole key (high and low) 61 bits to the left (temporary variables needed to preserve data
        temp1 = keyHigh
        temp2 = keyLow
        keyHigh = (keyHigh << 61) | (temp2 << 45) | (temp1 >> 19)
        keyLow = ((temp1 >> 3) & 0xFFFF)
        # the most significant nibble of the key goes through the SBox
        temp = Sbox(10)
        # the old value of the most significant nibble is set to zero using masking
        keyHigh = keyHigh & -1
        # new most significant nibble (output of the SBox) is placed on the most significant location
        keyHigh = keyHigh | temp << 60
        # key bits on positions k19, k18, k17, k16 and k15 XORed with round counter
        # k15 is the most significant bit in keyLow
        keyLow = keyLow ^ ((i & 0x01) << 15)
        keyHigh = keyHigh ^ (i >> 1)
        subKeys[i] = keyHigh % (10**9+7)

    return subKeys


k = 21 * sys.getsizeof(numpy.char)
key = 1000000000000000

print("length of kr", len(Kr))
print("length of Kc", len(Kc))

subkeys = generateSubkeys(key)

for iterations in range(31):
    subkeys = generateSubkeys(subkeys)
    print("round key is : ", subkeys)
    #subkeys = subkeys.split()
    print("split after : ", subkeys)
    subkeys = str(subkeys)
    print("subkeys afetr str - ", subkeys)
    chunks = re.split(' +', subkeys)
    print("chunks -  ", chunks)

    roundkey = []
    roundkey.append(12)

    for k in range(1, len(chunks)-1):
        if chunks[i] != '64\n' and chunks[i] != '64]':
            roundkey.append(int(chunks[i]))

        else:
            roundkey.append(64)

    roundkey.append(64)
    print("roundkey -  ", roundkey)

    # For each row
    for i in range(m):
        rTotalSum = sum(r[i])
        gTotalSum = sum(g[i])
        bTotalSum = sum(b[i])
        rModulus = rTotalSum % 2
        gModulus = gTotalSum % 2
        bModulus = bTotalSum % 2
        if(rModulus == 0):
            r[i] = numpy.roll(r[i], roundkey[i])
        else:
            r[i] = numpy.roll(r[i], -roundkey[i])
        if(gModulus == 0):
            g[i] = numpy.roll(g[i], roundkey[i])
        else:
            g[i] = numpy.roll(g[i], -roundkey[i])
        if(bModulus == 0):
            b[i] = numpy.roll(b[i], roundkey[i])
        else:
            b[i] = numpy.roll(b[i], -roundkey[i])
    # For each column
    for i in range(n):
        rTotalSum = 0
        gTotalSum = 0
        bTotalSum = 0
        for j in range(m):
            rTotalSum += r[j][i]
            gTotalSum += g[j][i]
            bTotalSum += b[j][i]
        rModulus = rTotalSum % 2
        gModulus = gTotalSum % 2
        bModulus = bTotalSum % 2
        if(rModulus == 0):
            upshift(r, i, roundkey[i])
        else:
            downshift(r, i, roundkey[i])
        if(gModulus == 0):
            upshift(g, i, roundkey[i])
        else:
            downshift(g, i, roundkey[i])
        if(bModulus == 0):
            upshift(b, i, roundkey[i])
        else:
            downshift(b, i, roundkey[i])
    # For each row
    for i in range(m):
        for j in range(n):
            if(i % 2 == 1):
                r[i][j] = r[i][j] ^ roundkey[j]
                g[i][j] = g[i][j] ^ roundkey[j]
                b[i][j] = b[i][j] ^ roundkey[j]
            else:
                r[i][j] = r[i][j] ^ rotate180(roundkey[j])
                g[i][j] = g[i][j] ^ rotate180(roundkey[j])
                b[i][j] = b[i][j] ^ rotate180(roundkey[j])
    # For each column
    for j in range(n):
        for i in range(m):
            if(j % 2 == 0):
                r[i][j] = r[i][j] ^ roundkey[i]
                g[i][j] = g[i][j] ^ roundkey[i]
                b[i][j] = b[i][j] ^ roundkey[i]
            else:
                r[i][j] = r[i][j] ^ rotate180(roundkey[i])
                g[i][j] = g[i][j] ^ rotate180(roundkey[i])
                b[i][j] = b[i][j] ^ rotate180(roundkey[i])

f = open('pair1.txt', 'w+')
f.write('Pixel : \n')

for i in range(64):
    for j in range(64):
        pix[i, j] = (r[i][j], g[i][j], b[i][j])
        f.write(str(pix[i, j]) + '\n')


im.save('encrypted_images/pic26.png')
