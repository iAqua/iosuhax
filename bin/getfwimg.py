#!/usr/bin/python

#<3 How illegal
wiiu_common_key = "B5D8AB06ED7F6CFC529F2CE1B4EA32FD"
starbuck_ancast_key = "91C9D008312851EF6B228BF14BAD4322"

# Don't edit past here

import os, sys, zlib
import codecs
from Crypto.Cipher import AES

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

print("somewhat simple 5.5.1 fw.img downloader")

#prepare keys
wiiu_common_key = codecs.decode(wiiu_common_key, 'hex')
starbuck_ancast_key = codecs.decode(starbuck_ancast_key, 'hex')

if zlib.crc32(wiiu_common_key) & 0xffffffff != 0x7a2160de:
    print("wiiu_common_key is wrong")
    sys.exit(1)

if zlib.crc32(starbuck_ancast_key) & 0xffffffff != 0xe6e36a34:
    print("starbuck_ancast_key is wrong")
    sys.exit(1)

print("downloading osv10 cetk")

#download osv10 cetk
f = urlopen("http://ccs.cdn.wup.shop.nintendo.net/ccs/download/000500101000400A/cetk")
d = f.read()
if not d:
    print("cetk download failed!")
    sys.exit(2)

#get cetk encrypted key
enc_key = d[0x1BF:0x1BF + 0x10]

#decrypt cetk key using wiiu common key
iv = codecs.decode("000500101000400A0000000000000000", 'hex')
cipher = AES.new(wiiu_common_key, AES.MODE_CBC,iv)
dec_key = cipher.decrypt(enc_key)

print("downloading fw.img")
#download encrypted 5.5.1 fw img

f = urlopen("http://ccs.cdn.wup.shop.nintendo.net/ccs/download/000500101000400A/0000136e")
if not f:
    print("0000136e download failed!")
    sys.exit(2)

print("decrypt first")
#decrypt fw img with our decrypted key
with open("fw.img","wb") as fout:
    iv = codecs.decode("00090000000000000000000000000000", "hex")
    cipher = AES.new(dec_key, AES.MODE_CBC, iv)
    while True:
        dec = f.read(0x40000)
        if len(dec) < 0x10:
                break
        enc = cipher.decrypt(dec)
        fout.write(enc)

with open('fw.img', 'rb') as f:
    if (zlib.crc32(f.read()) & 0xffffffff) != 0xd674201b:
        print("fw.img is corrupt, try again")
        sys.exit(2)

print("decrypt second")
#decrypt ancast image with ancast key and (for now) wrong iv
with open("fw.img", "rb") as f:
    with open("fw.img.full.bin","wb") as fout:
        fout.write(f.read(0x200))
        fake_iv = codecs.decode("00000000000000000000000000000000", "hex")
        cipher = AES.new(starbuck_ancast_key, AES.MODE_CBC, fake_iv)
        while True:
            dec = f.read(0x40000)
            if len(dec) < 0x10:
                break
            enc = cipher.decrypt(dec)
            fout.write(enc)

print("decrypt third")
#fix up ancast image with correct iv
with open('fw.img.full.bin', 'rb+') as f:
    #grab iv from decrypted image
    f.seek(0x86B3C,0)
    starbuck_ancast_iv = f.read(0x10)
    if zlib.crc32(starbuck_ancast_iv) & 0xffffffff != 0xb3f79023:
        print("starbuck_ancast_iv is wrong")
        sys.exit(1)
    #save key and iv for later usage
    with open('../scripts/keys.py', 'w') as keys_store:
        keys_store.write("key=\""+codecs.encode(starbuck_ancast_key, 'hex')+"\"\n")
        keys_store.write("iv=\""+codecs.encode(starbuck_ancast_iv, 'hex')+"\"\n")
    #calculate correct first bytes with correct iv
    f.seek(0x200,0)
    starbuck_ancast_iv = bytearray(starbuck_ancast_iv)
    partToXor = bytearray(f.read(0x10))
    result = bytearray(0x10)
    for i in range(0x10):
        result[i] = partToXor[i]^starbuck_ancast_iv[i]
    f.seek(0x200,0)
    #write in corrected bytes
    f.write(str(result))

with open('fw.img.full.bin', 'rb') as f:
    if (zlib.crc32(f.read()) & 0xffffffff) != 0x9f2c91ff:
        print("fw.img.full.bin is corrupt, try again with better keys")
        sys.exit(2)

print("done!")
