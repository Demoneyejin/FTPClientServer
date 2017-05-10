'''
Created on Mar 6, 2017

@author: wolfw
'''

from socket import * 
import threading 
import time
import sys
import traceback 
import errno 
import os
import ConfigFile

## global variables
tList = []
allow_delete = False
local_ip = '127.0.0.1' # socket.gethostbyname(socket.gethostname())
local_port = 10000 #2025 #10000


rest=False

rnfn = ""

pasv_mode=False


def handleClient(connectionSocket, addr):
    
    try:    
        print ("Thread Client Entering Now...")
        print (addr)
        stra = threading.local()
        
        currdir= threading.local()
        basewd= threading.local()
        cwd= threading.local()
        mode = threading.local()
        logged_on = threading.local()
        dataAddr = threading.local()
        dataPort = threading.local()
        
        #make sure our our config is local to the thread
        ourConfigFile = threading.local()
        
        #create our configFile
        ourConfigFile = ConfigFile.ConfigFile('s')
        
        currdir=os.path.abspath('.')
        basewd=currdir
        cwd= basewd
        mode = "A"
        
        #logged on data
        logged_on = False; ##initially false
        
        #Data port stuff
        dataAddr =""
        dataPort = 0
        
        connectionSocket.send(msg_str_encode("Welcome to MY DOMAIN!!!!!"))
        while True: 
            
            print ("TID = ",threading.current_thread())
            msg = connectionSocket.recv(1024)
            msg = msg_str_decode(msg, True)
            msg = msg.rsplit()
            print(msg)
            
            if(logged_on == True):
                if(msg[0] == "QUIT"):
                    QUIT(connectionSocket)
                if(msg[0] == "NOOP"):
                    NOOP(connectionSocket)
                if(msg[0] == "TYPE"):
                    mode = TYPE(connectionSocket, msg, mode)
                if(msg[0] == "PWD"):             
                    PWD(connectionSocket, cwd)
                if(msg[0] == "CWD"):
                    cwd = CWD(connectionSocket, msg,cwd)
                if(msg[0] == "MKD"):
                    MKD(connectionSocket, msg, cwd)
                if(msg[0] == "RMD"):
                    RMD(connectionSocket, msg, cwd)
                if(msg[0] == "DELE"):
                    DELE(connectionSocket, msg, cwd)
                if(msg[0] == "RNFR"):
                    RNFR(connectionSocket, msg, cwd)
                if(msg[0] == "RNTO"):
                    RNTO(connectionSocket, msg, cwd)
                if(msg[0] == "PORT"):
                    dataAddr, dataPort = PORT(connectionSocket, msg, dataAddr, dataPort)
                if(msg[0] == "LIST"):
                    LIST(connectionSocket, msg, dataAddr, dataPort, cwd)
                if(msg[0] == "RETR"):
                    RETR(connectionSocket, msg, dataAddr, dataPort, cwd, mode)
                if(msg[0] == "STOU"):
                    STOU(connectionSocket, msg, dataAddr, dataPort, cwd, mode)
                if(msg[0] == "STOR"):
                    STOR(connectionSocket,msg, cwd, dataAddr, dataPort, mode)
                if(msg[0] == "APPE"):
                    APPE(connectionSocket, msg, cwd, dataAddr, dataPort, mode)
            if(logged_on == False):
                if(msg[0] == "USER"):
                    ourConfigFile = USER(connectionSocket, msg, ourConfigFile)
                elif(msg[0] == "PASS"):
                    logged_on = PASS(connectionSocket, msg, ourConfigFile)
                else:
                    connectionSocket.send(msg_str_encode('530 Please login with USER and PASS'))
            
    except OSError as e:
        # A socket error
          print("Socket error:",e)


def joinAll():
    global tList 
    for t in tList:
        t.join()

def main():
    try: 
        global tList
        
        serverPort = 10000
        serverSocket = socket(AF_INET,SOCK_STREAM)
        serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1) 
        serverSocket.bind(('127.0.0.1',serverPort))
        serverSocket.listen(15)
        print('The server is ready to receive') 

        while True:
            connectionSocket, addr = serverSocket.accept()
            t = threading.Thread(target=handleClient,args=(connectionSocket,addr))
            t.start()
            tList.append(t)
            print("Thread started")
            print("Waiting for another connection")
    except KeyboardInterrupt:
        print ("Keyboard Interrupt. Time to say goodbye!!!") 
        joinAll()

    print("The end")
    sys.exit(0)
    
    

def SYST(connectionSocket):
    connectionSocket.connectionSocket.conn.send(b'215 UNIX Type: L8\r\n')
    
    
def OPTS(connectionSocket, cmd):
    if cmd[5:-2].upper()=='UTF8 ON':
        connectionSocket.conn.send(b'200 OK.\r\n')
    else:
        connectionSocket.conn.send(b'451 Sorry.\r\n')
        
        
def PORT(connectionSocket, cmd, dataAddr, dataPort):
    l = cmd[1].split(',')
    dataAddr='.'.join(l[:4])
    print("dataAddr: " + str(dataAddr))
    dataPort=(int(l[4])<<8)+int(l[5])
    print("Data port: " + str(dataPort))
    connectionSocket.send(msg_str_encode("200 Get port."))
    return dataAddr, dataPort


def LIST(connectionSocket, cmd, dataAddr, dataPort, cwd):
    print("000")
    connectionSocket.send(msg_str_encode("150 Here comes the directory listing."))
    print("list: " + cwd)
    #start_datasock()
    print("0")
    datasock=socket(AF_INET,SOCK_STREAM)
    print("1")
    datasock.connect((dataAddr,dataPort))
    print("2")
    for t in os.listdir(cwd):
        st=os.stat(os.path.join(cwd,t))
        fullmode='rwxrwxrwx'
        mode=''
        for i in range(9):
            mode+=((st.st_mode>>(8-i))&1) and fullmode[i] or '-'
        d = (os.path.isdir(os.path.join(cwd,t))) and 'd' or '-'
        k = d+mode+' 1 user group '+str(st.st_size)+"\t"+os.path.basename(os.path.join(cwd,t))
        datasock.send(msg_str_encode(k))
    #stop_datasock()
    datasock.close()
    connectionSocket.send(msg_str_encode("226 Directory send OK."))


def STOR(connectionSocket,msg, cwd, dataAddr, dataPort, mode ):
    fn = os.path.join(cwd,msg[1])
    if(mode == "I"):
        fo = open(fn,'wb')
    else:
        fo = open(fn,'w')
    connectionSocket.send(msg_str_encode("150 Opening data connection."))
    datasock = socket(AF_INET,SOCK_STREAM)
    datasock.connect((dataAddr,dataPort))
    while True:
        data = datasock.recv(1024)
        if not data:
            break
        if(mode == "A"):
            data = msg_str_decode(data)
        fo.write(data)
    fo.close()
    datasock.close()
    connectionSocket.send(msg_str_encode("226 Transfer complete."))
    
def APPE(connectionSocket,msg, cwd, dataAddr, dataPort, mode ):
    fn = os.path.join(cwd,msg[1])
    if(mode == "I"):
        fo = open(fn,'wb')
    else:
        fo = open(fn,'w')
    connectionSocket.send(msg_str_encode("150 Opening data connection."))
    datasock = socket(AF_INET,SOCK_STREAM)
    datasock.connect((dataAddr,dataPort))
    while True:
        data = datasock.recv(1024)
        if not data:
            break
        if(mode == "A"):
            data = msg_str_decode(data)
        fo.write(data)
    fo.close()
    datasock.close()
    connectionSocket.send(msg_str_encode("226 Transfer complete."))
    

def STOU(connectionSocket, msg, dataAddr, dataPort, cwd, mode) :
    i = 0
    fa = os.path.join(cwd,msg[1])
    fn = fa
    while ((os.path.exists(fn)) == True):
        fn = (fa + str(i))
        i = (i + 1)
    if(mode == "I"):
        fo = open(fn,'wb')
    else:
        fo = open(fn,'w')
    connectionSocket.send(msg_str_encode("150 Opening data connection."))
    datasock = socket(AF_INET,SOCK_STREAM)
    datasock.connect((dataAddr,dataPort))
    while True:
        data = datasock.recv(1024)
        if not data:
            break
        if(mode == "A"):
            data = msg_str_decode(data)
        fo.write(data)
    fo.close()
    datasock.close()
    connectionSocket.send(msg_str_encode("226 Transfer complete."))
        
def RETR(connectionSocket, msg, dataAddr, dataPort, cwd, mode):
    print("entering into RETR")
    if(os.path.exists(str(os.path.join(cwd,msg[1])))):
        fn = os.path.join(cwd,msg[1])
        if(mode == "I"):
            fi = open(fn,'rb')
        else:
            fi = open(fn,'r')
        connectionSocket.send(msg_str_encode("150 Opening data connection."))
        data = fi.read(1024)
        print("Reading from fi")
        datasock = socket(AF_INET,SOCK_STREAM)
        datasock.connect((dataAddr,dataPort))
        print("Datasock enabled")
        while data:
            if(mode == "I"):
                datasock.send(data)
                print("Sending data")
            else:
                datasock.send(msg_str_encode(data))
                print("Sending data")
            data=fi.read(1024)
            print("Reading more data")
        fi.close()
        datasock.close()
        print("done sending data")
        msg = "226 Transfer complete."
    else:
        msg = "550 \'" + msg[1] + "\': No such file or directory."
    connectionSocket.send(msg_str_encode(msg))

        
        
def USER(connectionSocket, cmd, ourConfigFile):
    ourConfigFile.setUsername(cmd[1])
    connectionSocket.send(msg_str_encode('331 OK.\r\n'))
    return ourConfigFile
    
def PASS(connectionSocket, cmd, ourConfigFile):
    ourConfigFile.setPassword(cmd[1])
    if(ourConfigFile.checkConfig()):
        connectionSocket.send(msg_str_encode('230 OK You are logged in.\r\n'))
        return True
    else:
        connectionSocket.send(msg_str_encode('530 Incorrect Username or Password.\r\n'))
        return False
    
    
    
def QUIT(connectionSocket):
    connectionSocket.send(msg_str_encode('221 Goodbye.\r\n'))
    connectionSocket.close()
    
def NOOP(connectionSocket):
    connectionSocket.send(msg_str_encode('200 OK.\r\n'))
    
def TYPE(connectionSocket,cmd, mode):
    mode=cmd[1]
    print(mode)
    if(mode == "A"):
        connectionSocket.send(msg_str_encode("200 ASCII mode."))
    else:
        connectionSocket.send(msg_str_encode("200 Binary mode."))
    return mode
        
def CDUP(connectionSocket, cwd, basewd):
    if not os.path.samefile(cwd,basewd):
        #learn from stackoverflow
        connectionSocket.send(msg_str_encode('200 OK.\r\n'))
        
        
def PWD(connectionSocket, cwd):

    connectionSocket.send(msg_str_encode('257 \"%s\"\r\n' % cwd))
    

def CWD(connectionSocket,cmd, cwd):
    try:
        chwd=cmd[1]
        
        if chwd=='/':
            cwd = os.path.abspath('.')
            connectionSocket.send(msg_str_encode('250 OK.\r\n'))
        elif chwd=='..':
            if(os.path.isdir(str((os.path.join(cwd, '..'))))):
                cwd=os.path.abspath(os.path.join(cwd, '..'))
                connectionSocket.send(msg_str_encode('250 OK.\r\n'))
            else:
                connectionSocket.send(msg_str_encode('550 No  inside .. such file or directory.\r\n'))
                
        elif chwd[0]=='/':
            if(os.path.isdir(str(os.path.join(cwd,chwd[1:])))):
                cwd=os.path.abspath(os.path.join(cwd, chwd[1:]))
                connectionSocket.send(msg_str_encode('250 OK.\r\n'))
            else:
                connectionSocket.send(msg_str_encode('550 No such file or directory.\r\n'))
                
                
        else:
            connectionSocket.send(msg_str_encode('550 No such file or directory.\r\n'))
    
        return cwd

    except OSError as e:
        # A socket error
        connectionSocket.send(msg_str_encode('250 NOT OK.\r\n'))
        return cwd
    


def MKD(connectionSocket, cmd, cwd):
    try:
        dn=os.path.join(cwd,cmd[1])
        os.mkdir(dn)
        connectionSocket.send(msg_str_encode('257 Directory created.\r\n'))
        
    except OSError as e:
        # Directory already exists
        connectionSocket.send(msg_str_encode('550 directory already exists.\r\n'))


def RMD(connectionSocket, cmd, cwd):
    global allow_delete
    allow_delete = True #need some check for admin priv
    try:
        dn=os.path.join(cwd,cmd[1])
        if allow_delete:
            os.rmdir(dn)
            connectionSocket.send(msg_str_encode('250 Directory deleted.\r\n'))
        else:
            connectionSocket.send(msg_str_encode('450 Not allowed.\r\n'))
    except OSError as e:
        # A socket error
        connectionSocket.send(msg_str_encode('550 No such directory .\r\n'))

def DELE(connectionSocket,cmd, cwd):
    global allow_delete
    allow_delete = True #need some check for admin priv
    try:
        
        fn=os.path.join(cwd,cmd[1])
        if allow_delete:
            os.remove(fn)
            connectionSocket.send(msg_str_encode('250 Directory deleted.\r\n'))
        else:
             connectionSocket.send(msg_str_encode('450 Not allowed.\r\n'))
    except OSError as e:
        # A socket error
        connectionSocket.send(msg_str_encode('550 No such file or directory exists or File is in use .\r\n'))
    

def RNFR(connectionSocket,cmd, cwd):
    global rnfn
    
    rnfn=os.path.join(cwd,cmd[1])
    
    connectionSocket.send(msg_str_encode('350 Ready.\r\n'))

def RNTO(connectionSocket, cmd, cwd): #probably seperate into tokens
    global rnfn
    
    fn=os.path.join(cwd,cmd[1])
    os.rename(rnfn,fn)
    connectionSocket.send(msg_str_encode('250 File renamed.\r\n'))



def msg_str_encode(strValue):
    msg = strValue.encode()
    return msg

def msg_str_decode(msg,pStrip=False):
    #print("msg_str_decode:" + str(msg))
    strValue = msg.decode()
    if (pStrip):
        strValue.strip('\n')
    return strValue

if __name__ == "__main__":
    # execute only if run as a script
    main()