# FTP Client
# Contributed by L.A.A.M.
# ********************************************************************************
# **                   **
# ** References                                                                 **
# ** http://www.slacksite.com/other/ftp.html#active                             **
# ** https://www.ietf.org/rfc/rfc959.txt                                        **
# ** Computer-Networking Top-Down Approach 6th Edition by Kurose and Ross       **
# ** computer ftp client                                                        **
# **                                                                            **
# ** Tested with inet.cis.fiu.edu  -- FIXED Port 21                             **
# ** Commands are not case sensitive                                            **
# **                                                                            **
# ** Built for Python 2.7.x. FTP Client Active Mode Only                        **
# ** Usage: Python ftp.py hostname [username] [password]                        **
# ** username and password are optional when invoking ftp.py                    **
# ** if not supplied, use command LOGIN                                         **
# ** Inside of ftp client, you can type HELP for more information               **
# ********************************************************************************

#### This new version was modified by Francisco R. Ortega to work with Python 3
#### Beta version

#import necessary packages.
import os
import time
import os.path
import errno
import traceback
import threading 
import sys
from socket import *
from _operator import xor
from symbol import xor_expr
import ConfigFile

#Global constants
USAGE = "usage: Python ftp hostname [username] [password]"


RECV_BUFFER = 1024
FTP_PORT = 10000 #2025 #10000 #21
CMD_QUIT = "QUIT"
CMD_HELP = "HELP"
CMD_LOGIN = "LOGIN"
CMD_LOGOUT = "LOGOUT"
CMD_LS = "LS"
CMD_PWD = "PWD"
CMD_PORT = "PORT"
CMD_DELETE = "DELETE"
CMD_PUT = "PUT"
CMD_GET = "GET"
CMD_USER = "USER"
CMD_PASS = "PASS"
CMD_CWD = "CWD"
CMD_RETR = "RETR"
CMD_STOR = "STOR"
CMD_APPE = "APPE"
CMD_TYPE = "TYPE"
CMD_DELE = "DELE"
CMD_RNFR = "RNFR"
CMD_RNTO = "RNTO"
CMD_RMD = "RMD"
CMD_MKD = "MKD"
CMD_NOOP = "NOOP"
CMD_LLS = "LLS"
CMD_LPWD = "LPWD"
CMD_LCWD = "LCWD"
CMD_DEBUGGING = "DEBUG"
CMD_OPEN = "OPEN"
CMD_CDUP = "CDUP"

#The data port starts at high number (to avoid privileges port 1-1024)
#the ports ranges from MIN to MAX
DATA_PORT_MAX = 61000 #5499 #61000
DATA_PORT_MIN = 60020 #5000 #60020
#data back log for listening.
DATA_PORT_BACKLOG = 1

#global variables
#store the next_data_port use in a formula to obtain
#a port between DATA_POR_MIN and DATA_PORT_MAX
next_data_port = 1


#global 
username = ""
password = "" 
hostname = "127.0.0.1" #"cnt4713.cs.fiu.edu"
cwd = os.path.abspath('.')
debugging = 0

tList = []

#entry point main()
def main():
    global username
    global password
    global hostname
    global tList

    logged_on = False
    logon_ready = False
    print("FTP Client v1.0")
    if (len(sys.argv) < 2):
         print(USAGE)
    if (len(sys.argv) == 2):
        hostname = sys.argv[1]
    if (len(sys.argv) == 4):
        username = sys.argv[2]
        password = sys.argv[3]
        logon_ready = True
        
    myConfigFile = ConfigFile.ConfigFile('c')

    print("********************************************************************")
    print("**                        ACTIVE MODE ONLY                        **")
    print("********************************************************************")
    print(("You will be connected to host:" + hostname))
    print("Type HELP for more information")
    print("Commands are NOT case sensitive\n")


    ftp_socket = ftp_connecthost(hostname)
    ftp_recv = ftp_socket.recv(RECV_BUFFER)
    ftp_code = ftp_recv[:3]
    #
    #note that in the program there are many .strip('\n')
    #this is to avoid an extra line from the message
    #received from the ftp server.
    #an alternative is to use sys.stdout.write
    print(msg_str_decode(ftp_recv,True))
    #
    #this is the only time that login is called
    #without relogin
    #otherwise, relogin must be called, which included prompts
    #for username
    #
    if (logon_ready):
        logged_on = login(username,password,ftp_socket)

    keep_running = True

    while keep_running:
        try:
            for l in tList:
                if(not l.isAlive()):
                    print("Joining finished threads")
                    l.join()
            tList = [t for t in tList if not t.isAlive()]
            print(tList)
                    
            rinput = input("FTP>")
            if (rinput is None or rinput.strip() == ''):
                continue
            tokens = rinput.split()
            cmdmsg , logged_on, ftp_socket = run_cmds(tokens,logged_on,ftp_socket)
            if (cmdmsg != ""):
                print(cmdmsg)
                
            
                    
        except OSError as e:
        # A socket error
          print("Socket error:",e)
          strError = str(e)
          #this exits but it is better to recover
          if (strError.find("[Errno 32]") >= 0): 
              sys.exit()

    #print ftp_recv
    try:
        ftp_socket.close()
        print("Thank you for using FTP 1.0")
    except OSError as e:
        print("Socket error:",e)
    sys.exit()

def run_cmds(tokens,logged_on,ftp_socket):
    global username
    global password
    global hostname
    global debugging

    cmd = tokens[0].upper()
    if(debugging == 1):
        print(" --> " + cmd)
   
    if (cmd == CMD_QUIT):
        quit_ftp(logged_on,ftp_socket)
        return "",logged_on, ftp_socket
    
    if (cmd == CMD_HELP):
        help_ftp()
        return "",logged_on, ftp_socket

    if (cmd == CMD_PWD):
        pwd_ftp(ftp_socket)
        return "",logged_on, ftp_socket

    if (cmd == CMD_LS):
        #FTP must create a channel to received data before
        #executing ls.
        #also makes sure that data_socket is valid
        #in other words, not None
        data_socket = ftp_new_dataport(ftp_socket)
        if (data_socket is not None):
            ls_ftp(tokens,ftp_socket,data_socket)
            return "",logged_on, ftp_socket
        else:
            return "[LS] Failed to get data port. Try again.",logged_on, ftp_socket

    if (cmd == CMD_LOGIN):
        username, password, logged_on, ftp_socket \
        = relogin(username, password, logged_on, tokens, hostname, ftp_socket)
        return "",logged_on, ftp_socket

    if (cmd == CMD_LOGOUT or cmd == "BYE"):
        logged_on,ftp_socket = logout(logged_on,ftp_socket)
        return "",logged_on, ftp_socket

    if (cmd == CMD_DELETE):
        delete_ftp(tokens,ftp_socket)
        return "",logged_on, ftp_socket

    if (cmd == CMD_PUT or cmd == CMD_STOR):
        # FTP must create a channel to received data before
        # executing put.
        #  also makes sure that data_socket is valid
        # in other words, not None
        data_socket = ftp_new_dataport(ftp_socket)
        if (data_socket is not None):
            put_ftp(tokens,ftp_socket,data_socket)
            return "",logged_on, ftp_socket
        else:
            return "[PUT] Failed to get data port. Try again.",logged_on, ftp_socket

    if (cmd == CMD_GET or cmd == CMD_RETR):
        # FTP must create a channel to received data before
        # executing get.
        # also makes sure that data_socket is valid
        # in other words, not None
        data_socket = ftp_new_dataport(ftp_socket)
        if (data_socket is not None):
            get_ftp(tokens, ftp_socket, data_socket)
            return "",logged_on, ftp_socket
        else:
            return "[GET] Failed to get data port. Try again.",logged_on, ftp_socket
        
    if (cmd == CMD_USER):
        #Call command to enter username
        user_local = input("Enter username: ")
        user(user_local , ftp_socket)
        return "", logged_on,ftp_socket
    
    if(cmd == CMD_PASS):
        #Call command to enter password/provide password
        password_client(password)
        return "", logged_on, ftp_socket
    
    if(cmd == CMD_CWD):
        #implement CWD command here
        cwd_(tokens,ftp_socket)
        return "", logged_on, ftp_socket
    if(cmd == CMD_APPE):
        data_socket = ftp_new_dataport(ftp_socket)
        if (data_socket is not None):
            append_ftp(tokens, ftp_socket, data_socket)
            return "",logged_on, ftp_socket
        else:
            return "[PUT] Failed to get data port. Try again.",logged_on, ftp_socket
    if(cmd == CMD_TYPE):
        type_ftp(tokens, ftp_socket)
        return "", logged_on,ftp_socket
    
    if(cmd == CMD_DELE):
        dele_ftp(tokens, ftp_socket)
        return "", logged_on, ftp_socket
    
    if(cmd == CMD_RNFR or cmd == CMD_RNTO):
        rename_(tokens, ftp_socket)
        return "", logged_on, ftp_socket
    
    if(cmd == CMD_RMD):
        rmd_ftp(tokens, ftp_socket)
        return "", logged_on, ftp_socket
    
    if(cmd == CMD_MKD):
        mkd_ftp(tokens, ftp_socket)
        return "", logged_on, ftp_socket
    
    if(cmd == CMD_NOOP):
        noop_ftp(ftp_socket)
        return "", logged_on, ftp_socket
    
    if(cmd == CMD_LLS):
        localls_ftp()
        return "", logged_on, ftp_socket
    if(cmd == CMD_LPWD):
        localpwd_ftp()
        return "", logged_on, ftp_socket
    if(cmd == CMD_LCWD):
        localcwd_ftp(tokens)
        return "", logged_on, ftp_socket
    
    if(cmd == CMD_DEBUGGING):
        debugging = xor(debugging, 1)
        if(debugging == 1):
            print("Debugging on:")
        else:
            print("Debugging off:")
        return "", logged_on, ftp_socket
    
    if(cmd == CMD_OPEN):
        open_ftp(tokens, ftp_socket)
        return "", logged_on, ftp_socket
    if(cmd == CMD_CDUP):
        cdup_(ftp_socket)
        return "", logged_on, ftp_socket
    
    return "Unknown command", logged_on, ftp_socket

def msg_str_encode(strValue):
    msg = strValue.encode()
    return msg

def msg_str_decode(msg,pStrip=False):
    #print("msg_str_decode:" + str(msg))
    strValue = msg.decode()
    if (pStrip):
        strValue.strip('\n')
    return strValue

def ftp_connecthost(hostname):
    
    ftp_socket = socket(AF_INET, SOCK_STREAM)
    #to reuse socket faster. It has very little consequence for ftp client.
    ftp_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    ftp_socket.connect((hostname, FTP_PORT))
    print (ftp_socket)
    return ftp_socket

def ftp_new_dataport(ftp_socket):
    global next_data_port
    dport = next_data_port
    host = gethostname()
    host_address = gethostbyname(host)
    next_data_port = next_data_port + 1 #for next next
    dport = (DATA_PORT_MIN + dport) % DATA_PORT_MAX

    print(("Preparing Data Port: " + host + " " + host_address + " " + str(dport)))
    data_socket = socket(AF_INET, SOCK_STREAM)
    # reuse port
    data_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    data_socket.bind((host_address, dport))
    data_socket.listen(DATA_PORT_BACKLOG)

    #the port requires the following
    #PORT IP PORT
    #however, it must be transmitted like this.
    #PORT 192,168,1,2,17,24
    #where the first four octet are the ip and the last two form a port number.
    host_address_split = host_address.split('.')
    high_dport = str(dport // 256) #get high part
    low_dport = str(dport % 256) #similar to dport << 8 (left shift)
    port_argument_list = host_address_split + [high_dport,low_dport]
    port_arguments = ','.join(port_argument_list)
    cmd_port_send = CMD_PORT + ' ' + port_arguments + '\r\n'
    print(cmd_port_send)


    try:
        ftp_socket.send(msg_str_encode(cmd_port_send))
    except socket.timeout:
        print("Socket timeout. Port may have been used recently. wait and try again!")
        return None
    except socket.error:
        print("Socket error. Try again")
        return None
    msg = ftp_socket.recv(RECV_BUFFER)
    print(msg_str_decode(msg,True))
    return data_socket

def pwd_ftp(ftp_socket):
    ftp_socket.send(msg_str_encode("PWD\r\n"))
    msg = ftp_socket.recv(RECV_BUFFER)
    print(msg_str_decode(msg,True))


def get_ftp(tokens, ftp_socket, data_socket):
    global tList
    
    if (len(tokens) < 2):
        print("put [filename]. Please specify filename")
        return

    remote_filename = tokens[1]
    if (len(tokens) == 3):
        filename = tokens[2]
    else:
        filename = remote_filename

    ftp_socket.send(msg_str_encode("RETR " + remote_filename + "\r\n"))

    print(("Attempting to write file. Remote: " + remote_filename + " - Local:" + filename))

    msg = ftp_socket.recv(RECV_BUFFER)
    strValue = msg_str_decode(msg)
    tokens = strValue.split()
    if (tokens[0] != "150"):
        print("Unable to retrieve file. Check that file exists (ls) or that you have permissions")
        return

    print(msg_str_decode(msg,True))
    
    data_connection, data_host = data_socket.accept()
    filename = str(os.path.join(cwd,filename))
    file_bin = open(filename, "wb")
    t = threading.Thread(target =threadedDataWriteRead, args = (filename, data_connection, ftp_socket, file_bin, 'g'))
    t.start()
    tList.append(t)
    

### put_ftp
def put_ftp(tokens,ftp_socket,data_socket):
    
    global cwd

    if (len(tokens) < 2):
        print("put [filename]. Please specify filename")
        return

    local_filename = tokens[1]
    if (len(tokens) == 3):
        filename = tokens[2]
    else:
        filename = local_filename
    
    local_filename = str(os.path.join(cwd, local_filename))
    if (os.path.isfile(local_filename) == False):
        print(("Filename does not exisit on this client. Filename: " + filename + " -- Check file name and path"))
        return
    filestat = os.stat(local_filename)
    filesize = filestat.st_size

    ftp_socket.send(msg_str_encode("STOR " + filename + "\r\n"))
    msg = ftp_socket.recv(RECV_BUFFER)
    print(msg_str_decode(msg,True))

    print(("Attempting to send file. Local: " + local_filename + " - Remote:" + filename + " - Size:" + str(filesize)))

    data_connection, data_host = data_socket.accept()
    file_bin = open(filename,"rb") #read and binary modes
    
    t = threading.Thread(target =threadedDataWriteRead, args = (filename, data_connection, ftp_socket, file_bin, 'p'))
    t.start()
    tList.append(t)

#
def ls_ftp(tokens,ftp_socket,data_socket):
    global tList
    
    if (len(tokens) > 1):
        ftp_socket.send(msg_str_encode("LIST " + tokens[1] + "\r\n"))
    else:
        ftp_socket.send(msg_str_encode("LIST\r\n"))

    
    msg = ftp_socket.recv(RECV_BUFFER)
    print(msg_str_decode(msg,True))

    data_connection, data_host = data_socket.accept()
    
    t = threading.Thread(target =threadedDataWriteRead, args = ('', data_connection, ftp_socket, '', 'ls'))
    t.start()
    tList.append(t)


def delete_ftp(tokens, ftp_socket):

    if (len(tokens) < 2):
        print("You must specify a file to delete")
    else:
        print(("Attempting to delete " + tokens[1]))
        ftp_socket.send(msg_str_encode("DELE " + tokens[1] + "\r\n"))

    msg = ftp_socket.recv(RECV_BUFFER)
    print(msg_str_decode(msg,True))

def logout(lin, ftp_socket):
    if (ftp_socket is None):
        print("Your connection was already terminated.")
        return False, ftp_socket

    if (lin == False):
        print("You are not logged in. Logout command will be send anyways")

    print("Attempting to logged out")
    msg = ""
    try:
        ftp_socket.send(msg_str_encode("QUIT\r\n"))
        msg = ftp_socket.recv(RECV_BUFFER)
    except socket.error:
        print ("Problems logging out. Try logout again. Do not login if you haven't logged out!")
        return False
    print(msg_str_decode(msg,True))
    ftp_socket = None
    joinAll()
    return False, ftp_socket #it should only be true if logged in and not able to logout

def quit_ftp(lin,ftp_socket):
    print ("Quitting...")
    logged_on, ftp_socket = logout(lin,ftp_socket)
    print("Thank you for using FTP")
    try:
        if (ftp_socket is not None):
            ftp_socket.close()
    except socket.error:
        print ("Socket was not able to be close. It may have been closed already")
    sys.exit()


def relogin(username,password,logged_on,tokens,hostname,ftp_socket):
    if (len(tokens) < 3):
        print("LOGIN requires more arguments. LOGIN [username] [password]")
        print("You will be prompted for username and password now")
        username = input("User:")
        password = input("Pass:")
    else:
        username = tokens[1]
        password = tokens[2]

    if (ftp_socket is None):
        ftp_socket = ftp_connecthost(hostname)
        ftp_recv = ftp_socket.recv(RECV_BUFFER)
        
        print(msg_str_decode(ftp_recv,True))

    logged_on = login(username, password, ftp_socket)
    return username, password, logged_on, ftp_socket


def help_ftp():
    print("FTP Help")
    print("Commands are not case sensitive")
    print("")
    print((CMD_USER) + "\t\t Just enter USER and hit enter and follow the commands")
    print((CMD_PASS) + "\t\t not safely gives you your password or lets you set your password if it doesn't currently exist")
    print((CMD_QUIT + "\t\t Exits ftp and attempts to logout"))
    print((CMD_LOGIN + "\t\t Logins. It expects username and password. LOGIN [username] [password]"))
    print((CMD_LOGOUT + "\t\t Logout from ftp but not client"))
    print((CMD_LS + "\t\t prints out remote directory content"))
    print((CMD_PWD + "\t\t prints current (remote) working directory"))
    print((CMD_GET + "\t\t gets remote file. GET remote_file [name_in_local_system]"))
    print((CMD_PUT + "\t\t sends local file. PUT local_file [name_in_remote_system]"))
    print((CMD_DELETE + "\t\t deletes remote file. DELETE [remote_file]"))
    print((CMD_HELP + "\t\t prints help FTP Client"))
    print((CMD_TYPE + "\t\t Provide Type [typing] either as 'binary' or 'ascii' without the single quotes "))
    print((CMD_DELE + "\t\t Deletes a file from the directory: DELE [filename] is the proper way to do it."))
    print((CMD_RNFR + "\t \t Rename a file, used with an interface command RENAME [current name] [new name] "))
    print((CMD_RNTO + "\t \t Rename a file, used with an interface command RENAME [current name] [new name] "))
    print((CMD_RMD + "\t \t Remove directory with RMD [directory name] "))
    print((CMD_MKD + "\t \t Make a directory  with MKD [directory name]"))
    print((CMD_NOOP + "\t \t Verifies you're connected to the server"))
    print((CMD_CDUP + "\t\t Moves up to the parent directory"))
    print((CMD_OPEN + "\t\t Will prompt you to enter a hostname and port username and password and you will be connected to a new server."))
    print((CMD_APPE + "\t\t Append a file. [file to use] [file to append]"))
    print((CMD_DEBUGGING + "\t\t Toggle debugging mode"))

def user(user,ftp_socket):
    global username
    global password
    global hostname
    #If the case that you're providing a new user name or a username for the first time, go ahead and provide the new user name and a new password and then we'll log on
    if(user == None or user.strip() == "" or user != username):
        print("User name has changed, re-logging you in as different user")
        password_client("")
        
        relogin(user, password, False, [user,user,password], hostname, ftp_socket)
    else:
        print("You're already logged in as: " + username)
        
def open_ftp(tokens, ftp_socket):
    global username
    global password
    global hostname
    global FTP_PORT
    
    hostname = tokens[1] + "\r\n" #our first token is the hostname
    FTP_PORT = int(tokens[2])  #our second token is the PORT
    print("Attempting to log you out from this and log you into the new hostname")
    
    tempSock = logout(True, ftp_socket)
    
    ftp_socket = tempSock[1]
    relogin(username, password, False, [], hostname, ftp_socket) #have relogin handle the connection to our new hostname 
    
    

def password_client(passw):
    global password
    if(passw == None or passw.strip() ==""):
        password = input("Enter your password: ")
        
    else:
        print("your password is " + password)
    
    
def cwd_(tokens, ftp_socket):
    #if we're just calling CWD
    if (len(tokens) < 2):
        print("No directory was provided, so we're going to move up one")
        ftp_socket.send(msg_str_encode("CWD " + " .." + "\r\n"))
        #cdup_(ftp_socket)
    else:
        print("Switching to the desired directory: ")
        ftp_socket.send(msg_str_encode("CWD " + tokens[1] + "\r\n"))
    msg = ftp_socket.recv(RECV_BUFFER)
    print(msg_str_decode(msg,True))
    
    
#requires debugging for cdup to work correctly. Probably server to return a value that says we're at the home directory or move up then modify code.
def cdup_(ftp_socket):
    ftp_socket.send(msg_str_encode("CDUP" + "\r\n"))
    msg = ftp_socket.recv(RECV_BUFFER)
    print(msg_str_decode(msg, True))
    
#Will ask server to check to see if the file we want to check is non unique, and then modify that file name to make unique then send that token into put_ftp
def stou_ftp(tokens,ftp_socket,data_socket):
    if (len(tokens) < 2):
        print("put [filename]. Please specify filename")
        return

    local_filename = tokens[1]
    if (len(tokens) == 3):
        filename = tokens[2]
    else:
        filename = local_filename

    local_filename = str(os.path.join(cwd, local_filename))
    if (os.path.isfile(local_filename) == False):
        print(("Filename does not exisit on this client. Filename: " + filename + " -- Check file name and path"))
        return
    filestat = os.stat(local_filename)
    filesize = filestat.st_size

    ftp_socket.send(msg_str_encode("STOU " + filename + "\r\n"))
    msg = ftp_socket.recv(RECV_BUFFER)
    print(msg_str_decode(msg,True))

    print(("Attempting to send file. Local: " + local_filename + " - Remote:" + filename + " - Size:" + str(filesize)))

    data_connection, data_host = data_socket.accept()
    file_bin = open(filename,"rb") #read and binary modes

    t = threading.Thread(target =threadedDataWriteRead, args = (filename, data_connection, ftp_socket, file_bin, 'su'))
    t.start()
    tList.append(t)

        
#Append a file name 
def append_ftp(tokens,ftp_socket,data_socket):
    
    if (len(tokens) < 3):
        print("put [filename] [remote_filename]. Please specify filename")
        return
    
    local_filename = tokens[1]
    filename = tokens[2]

    if (os.path.isfile(local_filename) == False):
        print(("Filename does not exisit on this client. Filename: " + filename + " -- Check file name and path"))
        return
    filestat = os.stat(local_filename)
    filesize = filestat.st_size

    
    ftp_socket.send(msg_str_encode("APPE " + filename + "\r\n"))
    msg = ftp_socket.recv(RECV_BUFFER)
    print(msg_str_decode(msg,True))

    print(("Attempting to send file. Local: " + local_filename + " - Remote:" + filename + " - Size:" + str(filesize)))

    data_connection, data_host = data_socket.accept()
    file_bin = open(local_filename,"rb") #read and binary modes


    t = threading.Thread(target =threadedDataWriteRead, args = (filename, data_connection, ftp_socket, file_bin, 'A'))
    t.start()
    tList.append(t)
    
    
def type_ftp(tokens, ftp_socket):
    #change type from binary to ascii or vice versa.
    if(len(tokens) < 2):
        print("Provide the type [binary] or type [ascii]")
        return
    print("switching typing to: " + tokens[1])
    
    typing = tokens[1]
    if(typing.upper() == "ASCII" ):
        ftp_socket.send(msg_str_encode("TYPE A " + "\r\n"))
        msg = ftp_socket.recv(RECV_BUFFER)
    elif(typing.upper() == "BINARY"):
        ftp_socket.send(msg_str_encode("TYPE I " + "\r\n"))
        msg = ftp_socket.recv(RECV_BUFFER)
    print(msg_str_decode(msg, True))
        
    
def dele_ftp(tokens, ftp_socket):
    if(len(tokens) < 2):
        print("Not enough parameters: dele [filename] must be provided")
        return
    
    filename = tokens[1] 
    print("Attempting to delete the file :" + filename)
    
    
    ftp_socket.send(msg_str_encode("DELE " + filename + "\r\n"))
    msg = ftp_socket.recv(RECV_BUFFER)
    print(msg_str_decode(msg,True))
    
def rename_(tokens, ftp_socket):
    if(len(tokens) < 3):
        print("Please provide the file names as RNFR/RNTO [oldfilename] [newfilename]")
        return
    oldfileName = tokens[1]
    newFileName = tokens[2]
    rnfr_ftp(oldfileName, ftp_socket)
    rnto_ftp(newFileName, ftp_socket)
        
    
    
def rnfr_ftp(filename, ftp_socket):
    ftp_socket.send(msg_str_encode("RNFR " + filename + "\r\n"))
    msg = ftp_socket.recv(RECV_BUFFER)
    print(msg_str_decode(msg, True))

def rnto_ftp(filename, ftp_socket):
    ftp_socket.send(msg_str_encode("RNTO " + filename + "\r\n"))
    msg = ftp_socket.recv(RECV_BUFFER)
    print(msg_str_decode(msg, True))

def rmd_ftp(tokens, ftp_socket):
    if(len(tokens) < 2):
        print("Must provide the directory name to make")
        return
    
    directorToMake = tokens[1]
    ftp_socket.send(msg_str_encode("RMD " + directorToMake + "\r\n"))
    msg = ftp_socket.recv(RECV_BUFFER)
    print(msg_str_decode(msg, True))

def mkd_ftp(tokens, ftp_socket):
    if(len(tokens) < 2):
        print("Must provide the directory name to make")
        return
    
    directorToMake = tokens[1]
    ftp_socket.send(msg_str_encode("MKD " + directorToMake + "\r\n"))
    msg = ftp_socket.recv(RECV_BUFFER)
    print(msg_str_decode(msg, True))
    
def noop_ftp(ftp_socket):
    ftp_socket.send(msg_str_encode("NOOP" + "\r\n"))
    msg = ftp_socket.recv(RECV_BUFFER)
    print(msg_str_decode(msg, True))
    
def localcwd_ftp(tokens):
    global cwd
    chwd = tokens[1]
    if chwd=='/':
        cwd = os.path.abspath('.')
    elif chwd=="..":
        cwd=os.path.abspath(os.path.join(cwd,'..'))
    elif chwd[0]=='/':
        cwd=os.path.join(os.path.abspath('.'),chwd[1:])
    else:
        cwd=os.path.join(cwd,chwd)
        print("else " + cwd)

def localls_ftp():
    global cwd
    for t in os.listdir(cwd):
        k=toListItem(os.path.join(cwd,t))
        print(k + "\n")

#as seen from online example
def toListItem(fn):
    global cwd
    st=os.stat(fn)
    fullmode='rwxrwxrwx'
    mode=''
    for i in range(9):
        mode+=((st.st_mode>>(8-i))&1) and fullmode[i] or '-'
    d=(os.path.isdir(fn)) and 'd' or '-'
    ftime=time.strftime(' %b %d %H:%M ', time.gmtime(st.st_mtime))
    return d+mode+' 1 user group '+str(st.st_size)+ ftime + os.path.basename(fn)

def localpwd_ftp():
    global cwd
    print(cwd)
    
    
def login(user, passw, ftp_socket):
    if (user == None or user.strip() == ""):
        print("Username is blank. Try again")
        return False;


    print(("Attempting to login user " + user))
    #send command user
    ftp_socket.send(msg_str_encode("USER " + user + "\n"))
    msg = ftp_socket.recv(RECV_BUFFER)
    print(msg_str_decode(msg,True))
    ftp_socket.send(msg_str_encode("PASS " + passw + "\n"))
    msg = ftp_socket.recv(RECV_BUFFER)
    strValue = msg_str_decode(msg,False)
    tokens = strValue.split()
    print(msg_str_decode(msg,True))
    if (len(tokens) > 0 and tokens[0] != "230"):
        print("Not able to login. Please check your username or password. Try again!")
        return False
    else:
        return True


def threadedDataWriteRead(filename, data_connection, ftp_socket, file_bin, command):
    print ("Thread Client Entering Now...")
    print ("TID = ",threading.current_thread())
    
    
    if(command == 'g'):
        size_recv = 0
        sys.stdout.write("|")
        while True:
            sys.stdout.write("*")
            data = data_connection.recv(RECV_BUFFER)
            if (not data or data == '' or len(data) <= 0):
                file_bin.close()
                break
            else:
                file_bin.write(data)
                size_recv += len(data)
        sys.stdout.write("|")
        sys.stdout.write("\n")
        data_connection.close()
        
        msg = ftp_socket.recv(RECV_BUFFER)
        print(msg_str_decode(msg,True))
        
        
    elif(command == 'p' or command == 'su' or command == 'A'):
        size_sent = 0
        #use write so it doesn't produce a new line (like print)
        sys.stdout.write("|")
        while True:
            sys.stdout.write("*")
            data = file_bin.read(RECV_BUFFER)
            if (not data or data == '' or len(data) <= 0):
                file_bin.close()
                break
            else:
                data_connection.send(data)
                size_sent += len(data)
    
        sys.stdout.write("|")
        sys.stdout.write("\n")
        data_connection.close()
    
        msg = ftp_socket.recv(RECV_BUFFER)
        print(msg_str_decode(msg,True))
        
    elif(command == 'ls'):
        
        msg = data_connection.recv(RECV_BUFFER)
        while (len(msg) > 0):
            print(msg_str_decode(msg,True))
            msg = data_connection.recv(RECV_BUFFER)
    
        data_connection.close()
        msg = ftp_socket.recv(RECV_BUFFER)
        print(msg_str_decode(msg,True))
        
    
    threading.main_thread()
    
    
    
    
    
def joinAll():
    global tList 
    for t in tList:
        t.join()
    
#Calls main function.
main()
