import socket
import sys
import numpy as np
import cv2
import time
from datetime import datetime
from struct import *
import  cv2
from matplotlib import pyplot as m
import matplotlib.animation as animation
import CustomObject

fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('output3.avi',fourcc, 20.0, (160, 120))

cascade = cv2.CascadeClassifier('cascade.xml')

FrameBackup = []
ProcFrame = []
FrameCount = -1
Temperature = []
WriteCount = 0
DetCount=0


Output = m.imshow(np.zeros((120, 160), dtype=np.uint16), animated = True)
AckMsg = pack('ii', 0, 1)
CloseMsg = pack('ii', 2, 4)
UnpackCode = 'iiIIIQ38400sd'

HOST = '192.168.137.1'   # Symbolic name meaning all available interfaces
PORT = 5995 # Arbitrary non-privileged port

def TempCalc(Value, Temp):
    
    return ((Value + 272.15 - (Temp/100)) / 0.0217) + 8192

def OutputCalc(*args):
    
    global FrameCount, WriteCount, FrameBackup, Temperature, DetCount
    global Connect

    Xout=0
    Yout=0
    X=0
    Y=0
    MinTemp = 20
    Clo = 0.6
    Err = 20
    Pa = 6.45
    M = 102
    CoreTemp = 36.33333
    Connect.sendall(AckMsg)
    DataRec = Connect.recv(100000)
    if(len(DataRec) == 38440):
        RType, RStatus, FrameWidth, FrameHeight, BPP, FrameID, FrameData, Temp = unpack(UnpackCode, DataRec)
        FrameTemp = np.fromstring(FrameData, dtype = 'uint16')
        
        CheckCount = 0
        while(CheckCount < 19200):
            if(FrameTemp[CheckCount] != 0):
                break
            CheckCount += 1
            
        if(CheckCount < 19200):
            FrameTemp = np.reshape(FrameTemp, (120, 160))
            FrameCount += 1
            
            FrameBackup.append(FrameTemp)
            Temperature.append(Temp)
            SkinTemp = 12.156 + 0.064*((Temp/100 - 273.15)) + 0.194*Pa + 0.0029*M + 0.513*CoreTemp
            MinTemp = ((Temp/100 - 273.15) - (60*Clo*0.155) + SkinTemp)/2
            ProcFrame.append(FrameTemp)
            ProcFrame[FrameCount] = np.clip(ProcFrame[FrameCount], TempCalc(MinTemp, Temp) - Err, TempCalc(MinTemp, Temp) + 255 - Err)
            ProcFrame[FrameCount] -= (TempCalc(MinTemp, Temp) - Err)
            ProcFrame[FrameCount] = np.uint8(ProcFrame[FrameCount])
            Mask = cv2.inRange(ProcFrame[FrameCount], 0, 254)
            ProcFrame[FrameCount] = cv2.bitwise_and(ProcFrame[FrameCount], ProcFrame[FrameCount], mask = Mask)
            output = cv2.cvtColor(ProcFrame[FrameCount], cv2.COLOR_GRAY2RGB)
            out.write(output)
            gray = cv2.cvtColor(output, cv2.COLOR_BGR2GRAY)
            faces = cascade.detectMultiScale(ProcFrame[FrameCount], 1.3, 5)
            
            for (x,y,w,h) in faces:
                cv2.rectangle(ProcFrame[FrameCount],(x,y),(x+w,y+h),(255,0,0),2)
                Xout= -int((((w+x+x)/2)-80)*0.44*2.77)
                Yout= -int((((y+h+y)/2)-60)*0.47*2.77)
            if(Xout!=0 or Yout!=0):
                l=FrameBackup[FrameCount]/255
                cv2.imwrite("in.jpg",l.astype(int))
                cv2.imwrite("in2.jpg",gray)
                cv2.imwrite("out.jpg",ProcFrame[FrameCount])
                print(Temp)
                print(np.amax(FrameBackup[FrameCount]))
                print(np.amin(FrameBackup[FrameCount]))
                print(np.amax(gray))
                print(np.amin(ProcFrame[FrameCount]))
                print(Xout)
                print(Yout)
                print(x)
                print(y)
                print(w)
                print(h)
                Xout=0
                Yout=0
                DetCount+=1
            elif(Xout!=0 and Yout!=0 and DetCount==0):
                DetCount+=1
            if(DetCount>=8):
                DetCount=0
    Connect.sendall(pack('ii', int(Xout), int(Yout)))
    
    if(FrameCount != -1):
        
        Output = ProcFrame[FrameCount]
        
        
    else:
        Output = np.zeros((120, 160), dtype = np.uint16)
    
    return Output

def UpdateFig(*args):
    
    Output.set_array(OutputCalc())
    
    return Output,


try: 
    Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print ('Socket created')
    
except:
    print ('Error Creating Socket')

try:
    Sock.bind((HOST, PORT))
    print ('Socket Bound')
    
except:
    print ('Could not bind Socket')
    
Sock.listen(10)
print ('Listening for client...')

Connect, Addr = Sock.accept()     
print ('Socket connected')


print ('Data Transfer Started...')
try:
    while True:
        fig = m.figure()
        Output = m.imshow(OutputCalc(), animated = True)
        try:    
            Anim = animation.FuncAnimation(fig, UpdateFig, interval = 50, blit = True)  
           
        except KeyboardInterrupt:
            print ('Could not carry out process')
            break
        m.show()
            
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
except KeyboardInterrupt:
    print ('Could not carry out process')
    
print ('Connection Closed')
Connect.sendall(CloseMsg)
out.release()
m.close('all')
Connect.close()
Sock.close()

