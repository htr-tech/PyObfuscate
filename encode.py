# -*- coding:utf8 -*-

# Supports python2 & python3
# Name   : PyObfuscate - Simple Python Code Obfuscator
# Author : HTR-TECH
# Date   : Sun Jul 19 00:19:27 2021

# Import Modules
import os
import sys
import zlib
import time
import base64
import marshal
import py_compile

# Select raw_input() or input()
if sys.version_info[0]==2:
    _input = "raw_input('%s')"
elif sys.version_info[0]==3:
    _input = "input('%s')"
else:
    sys.exit("\n Your Python Version is not Supported!")

# Encoding
zlb = lambda in_ : zlib.compress(in_)
b16 = lambda in_ : base64.b16encode(in_)
b32 = lambda in_ : base64.b32encode(in_)
b64 = lambda in_ : base64.b64encode(in_)
mar = lambda in_ : marshal.dumps(compile(in_,'<x>','exec'))
note = """# PyObfuscate
# ------------------------------------------
# Author: Tahmid Rayat
# Github: https://www.github.com/htr-tech
# ------------------------------------------

"""

def banner(): # Program Banner
    print(' ╔═════════════════════════════════╗\n ║          PyObfuscate            ║\n ║  Simple Python Code Obfuscator  ║\n ║  Author : Tahmid Rayat          ║\n ║  Github : Github.com/HTR-TECH   ║\n ╚═════════════════════════════════╝')

def menu(): # Program Menu
    print("""
 [01] Encode Marshal
 [02] Encode Zlib
 [03] Encode Base16
 [04] Encode Base32
 [05] Encode Base64
 [06] Encode Zlib,Base16
 [07] Encode Zlib,Base32
 [08] Encode Zlib,Base64
 [09] Encode Marshal,Zlib
 [10] Encode Marshal,Base16
 [11] Encode Marshal,Base32
 [12] Encode Marshal,Base64
 [13] Encode Marshal,Zlib,B16
 [14] Encode Marshal,Zlib,B32
 [15] Encode Marshal,Zlib,B64
 [16] Simple Encode
 [17] Exit
""")

def pause():
    print(" Press any key to continue ...")
    input()

class FileSize: # Gets the File Size
    def datas(self,z):
        for x in ['Byte','KB','MB','GB']:
            if z < 1024.0:
                return "%3.1f %s" % (z,x)
            z /= 1024.0
    def __init__(self,path):
        if os.path.isfile(path):
            dts = os.stat(path).st_size
            print(" [-] Encoded File Size : %s\n" % self.datas(dts))
# FileSize('rec.py')

# Encode Menu
def Encode(option,data,output):
    loop = int(eval(_input % " [-] Encode Count : "))
    if option == 1:
        xx = "mar(data.encode('utf8'))[::-1]"
        heading = "_ = lambda __ : __import__('marshal').loads(__[::-1]);"
    elif option == 2:
        xx = "zlb(data.encode('utf8'))[::-1]"
        heading = "_ = lambda __ : __import__('zlib').decompress(__[::-1]);"
    elif option == 3:
        xx = "b16(data.encode('utf8'))[::-1]"
        heading = "_ = lambda __ : __import__('base64').b16decode(__[::-1]);"
    elif option == 4:
        xx = "b32(data.encode('utf8'))[::-1]"
        heading = "_ = lambda __ : __import__('base64').b32decode(__[::-1]);"
    elif option == 5:
        xx = "b64(data.encode('utf8'))[::-1]"
        heading = "_ = lambda __ : __import__('base64').b64decode(__[::-1]);"
    elif option == 6:
        xx = "b16(zlb(data.encode('utf8')))[::-1]"
        heading = "_ = lambda __ : __import__('zlib').decompress(__import__('base64').b16decode(__[::-1]));"
    elif option == 7:
        xx = "b32(zlb(data.encode('utf8')))[::-1]"
        heading = "_ = lambda __ : __import__('zlib').decompress(__import__('base64').b32decode(__[::-1]));"
    elif option == 8:
        xx = "b64(zlb(data.encode('utf8')))[::-1]"
        heading = "_ = lambda __ : __import__('zlib').decompress(__import__('base64').b64decode(__[::-1]));"
    elif option == 9:
        xx = "zlb(mar(data.encode('utf8')))[::-1]"
        heading = "_ = lambda __ : __import__('marshal').loads(__import__('zlib').decompress(__[::-1]));"
    elif option == 10:
        xx = "b16(mar(data.encode('utf8')))[::-1]"
        heading = "_ = lambda __ : __import__('marshal').loads(__import__('base64').b16decode(__[::-1]));"
    elif option == 11:
        xx = "b32(mar(data.encode('utf8')))[::-1]"
        heading = "_ = lambda __ : __import__('marshal').loads(__import__('base64').b32decode(__[::-1]));"
    elif option == 12:
        xx = "b64(mar(data.encode('utf8')))[::-1]"
        heading = "_ = lambda __ : __import__('marshal').loads(__import__('base64').b64decode(__[::-1]));"
    elif option == 13:
        xx = "b16(zlb(mar(data.encode('utf8'))))[::-1]"
        heading = "_ = lambda __ : __import__('marshal').loads(__import__('zlib').decompress(__import__('base64').b16decode(__[::-1])));"
    elif option == 14:
        xx = "b32(zlb(mar(data.encode('utf8'))))[::-1]"
        heading = "_ = lambda __ : __import__('marshal').loads(__import__('zlib').decompress(__import__('base64').b32decode(__[::-1])));"
    elif option == 15:
        xx = "b64(zlb(mar(data.encode('utf8'))))[::-1]"
        heading = "_ = lambda __ : __import__('marshal').loads(__import__('zlib').decompress(__import__('base64').b64decode(__[::-1])));"
    else:
        sys.exit("\n Invalid Option!")
    
    for x in range(loop):
        try:
            data = "exec((_)(%s))" % repr(eval(xx))
        except TypeError as s:
            sys.exit(" TypeError : " + str(s))
    with open(output, 'w') as f:
        f.write(note + heading + data)
        f.close()

# Special Encode
def SEncode(data,output):
    for x in range(5):
        method = repr(b64(zlb(mar(data.encode('utf8'))))[::-1])
        data = "exec(__import__('marshal').loads(__import__('zlib').decompress(__import__('base64').b64decode(%s[::-1]))))" % method
    z = []
    for i in data:
        z.append(ord(i))
    sata = "_ = %s\nexec(''.join(chr(__) for __ in _))" % z
    with open(output, 'w') as f:
        f.write(note + "exec(str(chr(35)%s));" % '+chr(1)'*10000)
        f.write(sata)
        f.close()
    py_compile.compile(output,output)

# Main Menu
def MainMenu():
    while True:
        try:
            os.system('cls') # os.system('clear')
            banner()
            menu()
            try:
                option = int(eval(_input % " [-] Option : "))
            except ValueError:
                #sys.exit("\n Invalid Option !")
                print("\n Invalid Option !")
                pause()
                continue

            if option > 0 and option <= 17:
                if option == 17:
                    sys.exit("\n Thanks For Using this Tool")
                os.system('cls') # os.system('clear')
                banner()
            else:
                #sys.exit('\n Invalid Option !')
                print("\n Invalid Option !")
                pause()
                continue
            try:
                file = eval(_input % " [-] File Name : ")
                data = open(file).read()
            except IOError:
                #sys.exit("\n File Not Found!")
                print("\n File Not Found!")
                pause();
                continue;
            
            output = file.lower().replace('.py', '') + '_enc.py'
            if option == 16:
                SEncode(data,output)
            else:
                Encode(option,data,output)
            print("\n [-] Successfully Encrypted %s" % file)
            print(" [-] Saved as %s" % output)
            FileSize(output)
        except KeyboardInterrupt:
            time.sleep(1)
            sys.exit()

if __name__ == "__main__":
    MainMenu()
