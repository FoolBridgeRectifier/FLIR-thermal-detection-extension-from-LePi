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


FrameBackup = []
ProcFrame = []
FrameCount = -1
Temperature = []

Output = m.imshow(np.zeros((120, 160), dtype=np.uint16), animated = True)
AckMsg = pack('ii', 0, 1)
CloseMsg = pack('ii', 2, 4)
UnpackCode = 'iiIIIQ38400sd'

HOST = '192.168.137.1'   # Symbolic name meaning all available interfaces
PORT = 5995 # Arbitrary non-privileged port

def TempCalc(Value, Temp):
    
    return ((Value + 272.15 - (Temp/100)) / 0.0217) + 8192

def OutputCalc(*args):
    
    global FrameCount, FrameBackup, Temperature
    global Connect
    
    MinTemp = 30
    
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
            
            ProcFrame.append(FrameTemp)
            ProcFrame[FrameCount] = np.clip(ProcFrame[FrameCount], TempCalc(MinTemp, Temp), TempCalc(MinTemp, Temp) + 255)
            ProcFrame[FrameCount] -= TempCalc(MinTemp, Temp)
            ProcFrame[FrameCount] = np.uint8(ProcFrame[FrameCount])
            
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
            
        Anim = animation.FuncAnimation(fig, UpdateFig, interval = 50, blit = True)  
            
        m.show()
            
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
except:
    print ('Could not carry out process')
    
print ('Connection Closed')
Connect.sendall(CloseMsg)    
m.close('all')
Connect.close()
Sock.close()

