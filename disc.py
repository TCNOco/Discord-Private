import discord
import asyncio
import base64
import msvcrt
import time
import threading
from os import system, name 
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto import Random
import json
from pprint import pprint

#--------------------------------------------------------------------
#----- Variable definitions -----
#--------------------------------------------------------------------
timeout = 1 #Time in seconds between checking for messages

# v Do not change these v
user = "defaultuser" #Just a place holder
loop = asyncio.new_event_loop()
lastmessage = ""
inputrecieved = False
waitingtemp = ""
longmessagein = []
processinglong = False
completelongmessage = ""
juststartedlong = False

#--------------------------------------------------------------------
#----- Load settings from file -----
#--------------------------------------------------------------------
try:
    with open('settings.json') as f:
        jsondata = json.load(f)
except:
    print("ERROR: THE PROGRAM WAS UNABLE TO READ 'settings.json'")
    print("Please make sure that the program can access settings.json, and that the contents makes sense!")
    input("Press any key to close the program")
    exit()
print("Loading settings!")
pprint(jsondata)
my_password = bytes(jsondata["password"], "utf-8") #Load password from file
logintoken = jsondata["bottoken"]  #Load bot login token from file
discordchannelid = discord.Object(id=jsondata["channelid"]) #Load channel ID from file
print("-----------------")
print("Settings loaded!")

#--------------------------------------------------------------------
#----- Function definitions -----
#--------------------------------------------------------------------
#Clear screen function
def clear(): 
    # for windows 
    if name == 'nt': 
        _ = system('cls') 
    # for mac and linux(here, os.name is 'posix') 
    else: 
        _ = system('clear') 

#----------------------------
#----- Encrypt function -----
#----------------------------
def encrypt(key, source, encode=True):
    key = SHA256.new(key).digest()  # use SHA-256 over our key to get a proper-sized AES key
    IV = Random.new().read(AES.block_size)  # generate IV
    encryptor = AES.new(key, AES.MODE_CBC, IV)
    padding = AES.block_size - len(source) % AES.block_size  # calculate needed padding
    source += bytes([padding]) * padding  # Python 2.x: source += chr(padding) * padding
    data = IV + encryptor.encrypt(source)  # store the IV at the beginning and encrypt
    return base64.b64encode(data).decode("latin-1") if encode else data

#----------------------------
#----- Decrypt function -----
#----------------------------
def decrypt(key, source, decode=True):
    if decode:
        source = base64.b64decode(source.encode("latin-1"))
    key = SHA256.new(key).digest()  # use SHA-256 over our key to get a proper-sized AES key
    IV = source[:AES.block_size]  # extract the IV from the beginning
    decryptor = AES.new(key, AES.MODE_CBC, IV)
    data = decryptor.decrypt(source[AES.block_size:])  # decrypt
    padding = data[-1]  # pick the padding value from the end; Python 2.x: ord(data[-1])
    if data[-padding:] != bytes([padding]) * padding:  # Python 2.x: chr(padding) * padding
        raise ValueError("Invalid padding...")
    return data[:-padding]  # remove the padding

#---------------------------------
#----- set username function -----
#---------------------------------
async def setusername():
    global user
    olduser = user
    user = input("What is your username?: ")
    print("----------")
    print("Your username is now: " + user)
    print("----------")
    #Announce change (only if not changing from default username)
    if olduser != "defaultuser":
        msg = olduser + " is now: " + user
        msgout = encrypt(my_password, bytes(msg, "utf-8"))
        await client.send_message(discordchannelid, str(msgout))
    return

#------------------------------------
#----- change username function -----
#------------------------------------
async def usernamecommand(name):
    global user
    olduser = user
    user = name[12:]
    print("----------")
    print("Your username is now: " + user + "\n")
    print("----------")
    #Announce change (only if not changing from default username)
    if olduser != "defaultuser":
        msg = olduser + " is now: " + user
        msgout = encrypt(my_password, bytes(msg, "utf-8"))
        await client.send_message(discordchannelid, str(msgout))
    return

#--------------------------------------------
#----- Decode previous message function -----
#--------------------------------------------
def decodeprev(message):
    try:
        decoded = decrypt(my_password, message[8:])
    except:
        print("ERROR: Message was not able to be decoded")
    print("DECODED MESSAGE: " + str(decoded)[2:-1])
    return

async def decodemulti(msg):
    nom = int(msg[12:])
    async for message in client.logs_from(discordchannelid, limit=nom):
        try:
            print("PM | " + str(decrypt(my_password, message.content))[2:-1])
        except:
            print("ERROR ON: " + message.content)
            pass

#-------------------------------------------
#----- Check for new messages function -----
#-------------------------------------------
#- Even though this does nothing directly, it still gets Discord.py to fire the new message event if there is a new one.
#- Without this, it doesn't fire that event while in the waiting for user input loop
async def checknewmessages():
    global lastmessage
    async for message in client.logs_from(discordchannelid, limit=1):
        if message.content != lastmessage:
            newmessage(message)

#----------------------------------------
#----- Wait for user input function -----
#----------------------------------------
async def waitforinputloop():
    global inputrecieved 
    global waitingtemp
    print("PRESS ENTER TO INPUT SOMETHING", end='\r')

    waitingtemp = raw_input_with_timeout()
    return

#- Waits for user input. 
def raw_input_with_timeout(): 
    global inputrecieved
    finishat = time.time() + timeout
    result = []
    while True:
        if msvcrt.kbhit():
            result.append(msvcrt.getche())
            if result[-1] == '\r':
                return ''.join(result)
            inputrecieved = True
            print("                                ", end='\r')
            return None
        else:
            if time.time() > finishat:
                return None
#--------------------------------------------------------------------
#----- Main program -----
#--------------------------------------------------------------------
clear()
print("Welcome to another sketchy system by TechNobo")
print("Please wait while I connect to Discord...")
client = discord.Client() #Connect to Discord

#--------------------------------------------------------------------
#----- Discord event definitions -----
#--------------------------------------------------------------------
#----- Discord receiving message -----
@client.event
async def on_message(message):
    newmessage(message)

def newmessage(message):
    print("                                ", end='\r')
    global lastmessage
    global processinglong
    global longmessagein
    global completelongmessage
    global juststartedlong
    if str(message.channel.id) != str(discordchannelid.id):
        #Do nothing if not in dedzone
        return
    mgs = message.content
    lastmessage = message.content
    try:
        if processinglong == False:                                 #If not processing a long message
            incoming = str(decrypt(my_password, mgs))[2:-1]         #Try decrypt the message
            if incoming == "--longmess--":                          #If beginning of message, set processinglong to true
                processinglong = True
                juststartedlong = True
        else:                                                       
            try:                                                    #If it is a long message
                incoming = str(decrypt(my_password, mgs))[2:-1]     #Try decode the message
                if incoming == "--endmess--":                        #If decoding possible, and it is endmess, then process the entire message
                    processinglong = False
                    for m in longmessagein:
                        completelongmessage += m

                    decoded = decrypt(my_password, completelongmessage)
                    completelongmessage = ""
                    longmessagein = []
                    if str(decoded[:len(user)])[2:-1] == str(user):
                        return
                    print(str(decoded)[2:-1])
            except:
                pass
            
        if juststartedlong == True:
            juststartedlong = False
        else: 
            if processinglong == True:
                longmessagein.append(mgs)
            else:
                decoded = decrypt(my_password, mgs)
                #Only shows message if not from the current user!
                if str(decoded[:len(user)])[2:-1] == str(user):
                    return
                if str(decoded)[2:-1] == "--endmess--":
                    return
                print(str(decoded)[2:-1])
    except:
        pass


#----- Discord function that runs once initiated -----
@client.event
async def on_ready():
    global lastmessage
    print('Logging in complete!')
    print('------')
    print('->Logged in as')
    print('->Username: '+client.user.name)
    print('->User ID: '+client.user.id)
    print('------')
    print("Use /help for a list of commands")
    print()
    print()
    await setusername()
    async for message in client.logs_from(discordchannelid, limit=1):
        lastmessage = message.content

    while 1 == 1:
        global inputrecieved
        inputrecieved = False
        
        await waitforinputloop()
        
        if inputrecieved != False:
            await acceptmessage()
            inputrecieved = False

        await checknewmessages()
        

async def acceptmessage():
    msg = input(user + ": ")
    if msg[:1] == "/":
        if msg == "/help":
            print("Commands:\n")
            print("/changenick <name>: Changes username")
            print("/cls: Clears the screen")
            print("/decode <message>: Decodes a previous message")
            print("/decodeprev <number of messages>: Decodes a number of previous messages (PM = Previous Message)")
            print("/help: Displays help")
            print()
        elif msg[4:] == "/cls":
            clear()
        elif msg[:7] == "/decode" and msg[:11] != "/decodeprev":
            decodeprev(msg)
        elif msg[:11] == "/changenick":
            await usernamecommand(msg)
        elif msg[:11] == "/decodeprev":
            await decodemulti(msg)
    else:
        if msg != "":
            msg = user + ": " + msg
            msgout = encrypt(my_password, bytes(msg, "utf-8"))
            if len(msgout) >= 2000:
                await client.send_message(discordchannelid, str(encrypt(my_password, bytes("--longmess--", "utf-8"))))
                for m in [msgout[i:i+1995] for i in range(0, len(msgout), 1995)]:
                    await client.send_message(discordchannelid, str(m))
                await client.send_message(discordchannelid, str(encrypt(my_password, bytes("--endmess--", "utf-8"))))
            else:
                await client.send_message(discordchannelid, str(msgout))
    return

#--------------------------------------------------------------------
#----- Start the program -----
#--------------------------------------------------------------------
client.run(logintoken)