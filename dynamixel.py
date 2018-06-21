import serial
import time
from time import sleep
import RPi.GPIO as GPIO
import operator
GPIO.setmode(GPIO.BCM)
GPIO.setup(18,GPIO.OUT)
GPIO.output(18,GPIO.HIGH)
port=serial.Serial("/dev/ttyS0",baudrate=1000000,timeout=3.0)
id=0x01
id2=0x03
l=4 #largo de datos
n=1 #numero de motores
length=l+3
key=[0xFF,0XFF,id,length,0x03,0x1E]
key1=[0xFF,0XFF,id2,length,0x03,0x1E]
checksum=0
checksum1=0
for i in range (0,n):
    #input_var= input("Enter ID:  ")
    #key.append(int(input_var))
    input_var_aux= input("Enter position:  ")
    input_var= (input_var_aux*1023)/300
    key.append(int(input_var) & 0xFF)
    input_var= (input_var >> 8)
    key.append(input_var)
    #input_var= input("Enter speed: ")
    input_var=100
    key.append(int(input_var) & 0xFF)
    input_var= (input_var >> 8)
    key.append(input_var)
    input_var_aux1= input("Enter position:  ")
    input_var1= (input_var_aux1*1023)/300
    key1.append(int(input_var1) & 0xFF)
    input_var1= (input_var1 >> 8)
    key1.append(input_var1)
    #input_var1= input("Enter speed: ")
    input_var1=100
    key1.append(int(input_var1) & 0xFF)
    input_var1= (input_var1 >> 8)
    key1.append(input_var1)
print ("ok")
for i in range (0,len(key)):
    checksum=checksum + key[i]
#checksum = key[0] + key[1] + key[2] + key[3] + key[4] + key[5] + key[6] + key[7] +
checksum= operator.invert(checksum)
checksum= checksum & 0x00FF
checksum = checksum -2
key.append(checksum)
#print checksum
print ("ok")
for i in range (0,len(key1)):
    checksum1=checksum1 + key1[i]
#checksum = key[0] + key[1] + key[2] + key[3] + key[4] + key[5] + key[6] + key[7] +
checksum1= operator.invert(checksum1)
checksum1= checksum1 & 0x00FF
checksum1 = checksum1 -2
key1.append(checksum1)
#print checksum
print ("ok")
#print hex(key)
#print ' '.join([hex(i) for i in key])#key = chr(key)
print (key)
print (key1)
for i in range(0,len(key)):
    #port.write(hex(key[i]))
    print (hex(key[i]))
port.write(bytearray(key))
sleep(0.1)
port.write(bytearray(key1))
port.close()
