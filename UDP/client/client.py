import socket
import struct
from time import sleep, time


SERVER_IP = "127.0.0.1"
PORT = 8998

DEFAULT_BUFFER_SIZE = 1024
MIN_CHUNK_SIZE = 16
BUFFER_SIZE = 1024
CHUNKSIZE = None
FILENAME = None

CHUNKPOSITION = 0

LAST_TIMEOUT_SET = None
TIMEOUTS = []

TRANSACTION_KEY = None
TRANSFER_RUNNING = False
RECEIVED_DATA = ""

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.settimeout(5)
try:
    s.connect((SERVER_IP, PORT))
except Exception as e:
    print("Es konnte keine Verbindung hergestellt werden.",e)
    exit()

# Quelle: https://github.com/houluy/UDP/blob/master/udp.py
def checksum_func(data):
    checksum = 0
    data_len = len(data)
    if (data_len % 2):
        data_len += 1
        data += struct.pack('!B', 0)

    for i in range(0, data_len, 2):
        w = (data[i] << 8) + (data[i + 1])
        checksum += w

    checksum = (checksum >> 16) + (checksum & 0xFFFF)
    checksum = ~checksum & 0xFFFF
    return checksum

# Quelle: https://github.com/houluy/UDP/blob/master/udp.py
def verify_checksum(data, checksum):
    data_len = len(data)
    if (data_len % 2) == 1:
        data_len += 1
        data += struct.pack('!B', 0)

    for i in range(0, data_len, 2):
        w = (data[i] << 8) + (data[i + 1])
        checksum += w
        checksum = (checksum >> 16) + (checksum & 0xFFFF)
    verify = checksum
    return verify == 0xFFFF

def sendData(input):
    data = input.decode("utf-8")+";"+str(checksum_func(input))
    s.sendto(data.encode(), (SERVER_IP,PORT))

def receiveData(size):
    warNachrichtFuerMich = False
    if TRANSACTION_KEY == None:
        data, addr = s.recvfrom(size)
    else:
        while not warNachrichtFuerMich:
            data, addr = s.recvfrom(size)
            tid = data.decode("utf-8").split(";")[1]
            if TRANSACTION_KEY == tid:
                warNachrichtFuerMich = True
            else:
                print("Nachricht war nicht für mich:",data,"Transactionkey:",TRANSACTION_KEY,"tid",tid)

    message = data.decode("utf-8")
    checksum = message.split(";")
    checksum = checksum[-1] #letztes Element der Nachricht ist die Checksumme
    message = message[:len(message)-len(checksum)-1] #Checksumme aus Nachricht entfernen

    if verify_checksum(message.encode(), int(checksum)):
        return message.encode(), addr
    else:
        raise Exception("Wrong Checksum")
        return None

def showMenu():
    global FILENAME, CHUNKSIZE
    while FILENAME is None:
        try:
            FILENAME = input("Bitte gebe den Namen der zu holenden Datei an:")
            if FILENAME.find(";") != -1:
                raise ValueError("Dateiname darf kein Semikolon enthalten.")
        except ValueError:
            print(e)

    while CHUNKSIZE is None:
        try:
            CHUNKSIZE = int(input("Bitte gebe die Größe eines Chunks in Bytes ein:"))
            if CHUNKSIZE < MIN_CHUNK_SIZE:
                CHUNKSIZE = None
                raise ValueError()
        except ValueError:
            print("Bitte gebe eine Zahl ein! Sie sollte als %d sein." % MIN_CHUNK_SIZE)


def sendInit(chunksize, filename):
    global BUFFER_SIZE, TRANSFER_RUNNING, TRANSACTION_KEY
    print("sendInit()")
    request = "INITX;"+str(CHUNKSIZE)+";"+filename
    if len(request) > BUFFER_SIZE:
        raise Exception("Dateiname ist zu lang.")
    sendData(request.encode())
    #BUFFER_SIZE = chunksize+9
    response, msgAddr = receiveData(BUFFER_SIZE)
    response = response.decode("utf-8")
    print(response)
    if response.startswith("ERROR;"):
        raise Exception("Server Error: "+response[6:]) # Fehlermeldung des Servers als Exception ausgeben.
    response = response.split(";")
    if response[0] == "SERVERREADY":
        TRANSACTION_KEY = response[1]
    TRANSFER_RUNNING = True

def getData():
    print("GET;"+str(TRANSACTION_KEY)+";"+str(CHUNKPOSITION))
    global RECEIVED_DATA, BUFFER_SIZE
    sendData(("GET;"+str(TRANSACTION_KEY)+";"+str(CHUNKPOSITION)).encode("utf-8"))
    response, msgAddr = receiveData(BUFFER_SIZE)
    print("ANTWORT", response)
    response = response.decode("utf-8")
    response = response.split(";")
    if(len(response) == 3 and response[0] == "DATA"):
        RECEIVED_DATA += response[2]
    else:
        if(response[0] == "ERROR" and response[2] == "EOF"):
            raise Exception("EOF")
        else:
            raise Exception("Servererror: "+response[1])


def handleTimeout():
    global LAST_TIMEOUT_SET, TIMEOUTS
    # Alle timeouts zurücksetzen, falls der letzte 10 Sekunden her ist
    if LAST_TIMEOUT_SET != None and LAST_TIMEOUT_SET + 10 > time():
        TIMEOUTS = []
    lastTimeoutSet = time()
    TIMEOUTS.append(time())
    if len(TIMEOUTS) >= 4:
        # Keine Verbindung mehr zum Server
        raise Exception("Verbindung zum Server unterbrochen")
    else:
        print("Keine Antwort. Sende Anfrage erneut.")


try:
    while CHUNKSIZE == None or FILENAME == None:
        showMenu()

    init = False
    while not init:
        try:
            sendInit(CHUNKSIZE, FILENAME)
            init = True
        except socket.timeout as e:
            handleTimeout()

    while TRANSACTION_KEY != None:
        sleep(1)
        try:
            getData()
            CHUNKPOSITION += 1
        except socket.timeout as e:
            handleTimeout()

except Exception as e:
    TRANSFER_RUNNING = False
    if str(e) == "EOF":
        with open(FILENAME,"w") as file:
            file.write(RECEIVED_DATA)
            file.close()
        print("Datei fertig übertragen!")
    else:
        RECEIVED_DATA = None
        print("Übertragung fehlgeschlagen:", e)

s.close()