import sys
from PIL import Image
from random import randint

from numpy import uint64
from helper import *

im = Image.open('input/pic1.png')
pix = im.load()

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

m = im.size[0]
n = im.size[1]


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


def fromHexStringToBytes(block):
    bytes = 8*sys.getsizeof(bytes())

    for i in range(8):
        bytes[i].nibble1 = (block[2*i]-'0') if (block[2*i] >=
                                                '0' and block[2*i] <= '9') else (block[2*i]-'a' + 10)
        bytes[i].nibble2 = (block[2*i+1] - '0') if (block[2*i+1] >=
                                                    '0' and block[2*i+1] <= '9') else (block[2*i+1] - 'a' + 10)

    return bytes


def fromBytesToLong(bytes):
    result = 0
    # multiplication with 16 replaced with shifting right 4 times
    # addition replaced with bitwise OR, since one of the operands is always 0
    for i in range(8):
        result = (result << 4) or (bytes[i].nibble1 & 15)
        result = (result << 4) or (bytes[i].nibble2 & 15)

    return result

# function for converting Hex String to a 64-bit integer


def fromHexStringToLong(block):
    result = 0

    # each character is 4 bits, there are 16 characters in a 64-bit block

    # the multiplication and addition are done the same way as before, with shifting and bitwise OR
    for i in range(16):
        result = (result << 4) or (
            (block - 1) if ((block >= 1 and block <= 9)) else (block - 1 + 10))
    return result


# function for converting a 64-bit integer to an array of bytes
def fromLongToBytes(block):
    bytes = 8 * sys.getsizeof(bytes())

    # the nibbles for each byte are obtained by shifting the number to the right for appropriate number of places (a multiple of 4)
    # each nibble is obtained after masking the bits by performing bitwise AND with 1111 (all bits except the least significant 4 become 0)
    for i in range(7, -1):
        bytes[i].nibble2 = (block >> 2 * (7 - i) * 4) & 15
        bytes[i].nibble1 = (block >> (2 * (7 - i) + 1) * 4) & 15

    return bytes

# function for converting a 64-bit integer to a Hex String


def fromLongToHexString(block):
    hexString = 17 * sys.getsizeof(bytes())
    # we print the integer in a String in hexadecimal format
    print(hexString, block)
    return hexString

# function for converting a nibble using the SBox


def Sbox(input):
    return S[input]

# inverse function of the one above (used to obtain the original nibble)


def inverseSbox(input):
    return invS[input]


def permute(source):
    permutation = 0

    for i in range(0, 64):
        distance = 63 - i
        permutation = permutation or (
            (source >> distance and 0x1) << 63 - P[i])

    return permutation


def inversepermute(source):
    permutation = 0
    for i in range(0, 64):
        distance = 63 - P[i]
        permutation = (permutation << 1) | ((source >> distance) & 0x1)

    return permutation

# function that returns the low 16 bits of the key, which is given as input in a Hex String format


def getKeyLow(key):

    keyLow = 0
    key = str(key)
    # the least significant 16 bits are the last 4 characters of the key
    for i in range(len(key)):
        # again, multiplication and addition are done using bitwise left shift and bitwise OR
        keyLow = (keyLow << 4) | (
            int(key[i])) if (((key[i] >= '0' and key[i] <= '9'))) else int((key[i] + '10') & 0xF)
    return keyLow

# function that generates subKeys from the key according to the PRESENT key scheduling algorithm for a 80-bit key


def generateSubkeys(key):
    # the 80 bit key is placed in two integers, one that is 16-bit (keyLow) and the other one is 64-bit (keyHigh)
    keyHigh = fromHexStringToLong(key)
    keyLow = getKeyLow(key)
    subKeys = numpy.full(32, 32, dtype=uint64)

    # the first subkey is the high part of the original key
    subKeys[0] = keyHigh
    for i in range(1, 32):
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
        # the other bits are the least significant ones in keyHigh
        # according to the key scheduling algorithm, the values of keyHigh are used as 64-bit subkeys
        subKeys[i] = 0x000

    return subKeys

# function for encrypting a block using a key


k = 21 * sys.getsizeof(numpy.char)
key = 0x000
subkeys = generateSubkeys(key)

for i in range(31):
    # XOR the state with the round subkey
    #   state = state ^ subkeys[i]
    for i in range(m):
        for j in range(n):
            print("r[i][j]", r[i][j])
            print("subkeys[i]", subkeys[i])
            r[i][j] = r[i][j] ^ subkeys[i]
            g[i][j] = g[i][j] ^ subkeys[i]
            b[i][j] = b[i][j] ^ subkeys[i]

    for i in range(m):
        for j in range(n):
            pix[i, j] = (r[i][j], g[i][j], b[i][j])

im.save('encrypted_images/pic11.png')


def encrypt(pix, key):
    # generate the subkeys using the function defined above
    subkeys = generateSubkeys(key)
    # convert the plaintext from a Hex String to a 64-bit integer
    #state = fromHexStringToLong(plaintext)

    # apply first 31 rounds
    for i in range(31):
        # XOR the state with the round subkey
     #   state = state ^ subkeys[i]
        for i in range(m):
            for j in range(n):
                r[i][j] = r[i][j] ^ subkeys[i]
                g[i][j] = g[i][j] ^ subkeys[i]
                b[i][j] = b[i][j] ^ subkeys[i]

        # convert the state from a 64-bit integer to an array of bytes (nibbles)
      #  stateBytes = fromLongToBytes(state)
        # run each nibble through the SBox
        # for j in range(8):
         #   stateBytes[j].nibble1 = Sbox(stateBytes[j].nibble1)
          #  stateBytes[j].nibble2 = Sbox(stateBytes[j].nibble2)

        # return the nibbles in a 64-bit integer format and perform the permutation defined above
        #state = permute(fromBytesToLong(stateBytes))
        # free the memory of the byte array (not needed anymore)
        #del stateBytes

        for i in range(m):
            for j in range(n):
                pix[i, j] = (r[i][j], g[i][j], b[i][j])

    # the last round only XORs the state with the round key
    #state = state ^ subkeys[31]
    # free the memory of the subkeys (they are not needed anymore)
    #del subkeys
    # return fromLongToHexString(state)

# function for decrypting a block using a key


def decrypt(ciphertext, key):
    # generate the subkeys using the function defined above
    subkeys = generateSubkeys(key)
    # convert the plaintext from a Hex String to a 64-bit integer
    state = fromHexStringToLong(ciphertext)

    # apply first 31 rounds
    for i in range(31):
        # XOR the state with the round subkey (in decryption, order of subkeys is inversed)
        state = state ^ subkeys[31 - i]
        # perform the inverse permutation defined above
        state = inversepermute(state)
        # convert the state from a 64-bit integer to an array of bytes (nibbles)
        stateBytes = fromLongToBytes(state)
        # run each nibble through the inverse SBox
        for j in range(0, 8):
            stateBytes[j].nibble1 = inverseSbox(stateBytes[j].nibble1)
            stateBytes[j].nibble2 = inverseSbox(stateBytes[j].nibble2)

        # return the nibbles in a 64-bit integer format
        state = fromBytesToLong(stateBytes)
        # free the memory of the byte array (not needed anymore)
        free(stateBytes)

    # the last round only XORs the state with the round key
    state = state ^ subkeys[0]
    # free the memory of the subkeys (they are not needed anymore)
    del subkeys
    return fromLongToHexString(state)


'''
char = 'a'
plaintext = 17 * sys.getsizeof(char)
key = 21 * sys.getsizeof(char)
print("Enter the plaintext (64 bits) in hexadecimal format\nUse lower case characters and enter new line at the end\n")
plaintext = input()
print("Enter the key (80 bits) in hexadecimal format\nUse lower case characters and enter new line at the end\n")
key = input()
ciphertext = encrypt(plaintext, key)
print("The ciphertext is: ")
print(ciphertext)
print("The decrypted plaintext is: ")
print(decrypt(ciphertext, key))
del key
del plaintext
del ciphertext
'''
