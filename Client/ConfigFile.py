'''
Created on Mar 17, 2017

@author: wolfw
Configuration file used for authentication of the server

'''
import configparser
import string




class ConfigFile:
    
    #globals
    username = ""
    password = ""
    config = None
    
    def setUsername(self, inc_username):
        self.username = inc_username
    
    def setPassword(self, inc_passw):
        self.password = inc_passw
        
        
    #called on server startup 
    def createConfig(self):
        
        self.config  = configparser.ConfigParser()
        
        self.config['DEFAULT'] = {'ServerAliveInterval' :'45',
                             'Compression': 'yes',
                             'CompressionLevel': '9'}
        
        #Test username and passwords
        Users_ = ['User1', 'User2', 'User3', 'User4']
        Passw_ = ['password1', 'password2', 'password3', 'password4']
        
        
        #Create a user data field in our config with username and password
        self.config['UserData'] = dict(zip(Users_,Passw_))
        
        #write out config file
        with open('./ftpserver/Configuration/example.ini', 'w') as configfile: 
            self.config.write(configfile)
            
        #return our config parser to the server   
        return self.config 
            
    #server calls this function, sends in the username and password to check inside config
    def checkConfig(self):
        if(self.username == '' or self.password ==''):
            print("Check1")
            return False #username or password was not provided
        
        
        self.config.read('./ftpserver/Configuration/example.ini')
        
        
        
        #verify that user exists
        for key in self.config['UserData']:
            if(key in str.lower(self.username)):
                if(self.config['UserData'][self.username] == self.password):
                    print(key)
                    print(self.config['UserData'][self.username])
                    print(self.password)
                    return True
                else:#Password is incorrect
                    return False
           
        return False #If we retireve a false, username or password is incorrect or user does not exist
    
    
    def createConfigClient(self):
        self.config  = configparser.ConfigParser()
        
        
        #Test username and passwords
        ClientLData_ = [ 'data_port_max' , 'data_port_min', 'default_ftp_port', 'default_mode', 'default_debug_mode', 'default_verbose_mode', 'default_test_file', 'default_log_file']
        ClientRData_ = ['51000', '50000', '21', 'passive', 'off', 'off', 'test1.txt', 'ftpclient.log']
        
        
        self.config['DEFAULT'] = dict(zip(ClientLData_,ClientRData_ ))
        
        
        #write out config file
        with open('client.ini', 'w') as configfile: 
            self.config.write(configfile)
        
        print()
            
    def getClientDefaultConfig(self):
        return self.config['DEFAULT'] #should return the dictionary of this config
    
    def __init__(self, typeC):
        if(typeC == 's'):
            self.config = self.createConfig()
        if(typeC == 'c'):
            self.createConfigClient()
            #client data
            

    
    