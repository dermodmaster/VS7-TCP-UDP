import socket
import random
import struct
BIND_TO_IP = "0.0.0.0"
PORT = 8998

DEFAULT_BUFFER_SIZE = 1024
BUFFER_SIZE = 1024
TRANSFER_RUNNING = False
REMAINING_DATA = None
DATAPREFIX = "DATA;"
MIN_CHUNK_SIZE = 11

#TODO: Transaction Timeout
TRANSACTION_KEY = None # KEY mit der die aktuelle Transaktion identifiziert wird

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

def sendData(input,addr):
    data = input.decode("utf-8")+";"+str(checksum_func(input))
    s.sendto(data.encode(),addr)

def receiveData(size):
    data,addr = s.recvfrom(size)

    message = data.decode("utf-8")
    checksum = message.split(";")
    checksum = checksum[-1] #letztes Element der Nachricht ist die Checksumme
    message = message[:len(message)-len(checksum)-1] #Checksumme aus Nachricht entfernen

    if verify_checksum(message.encode(), int(checksum)):
        return message.encode(), addr
    else:
        raise Exception("Wrong Checksum")
        return None

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((BIND_TO_IP, PORT))
while 1:
    data, msgAddr = receiveData(BUFFER_SIZE)
    print(data)

    if not data: break
    print("received data:", data)
    data = data.decode("utf-8").split(";")
    command = data[0]

    try:
        if not TRANSFER_RUNNING:
            if command == "INITX":
                if len(data) != 3:
                    raise Exception("INITX Anfrage inkorrekt.")
                # Überprüfe ob CHUNKSIZE realistisch gewählt ist
                if int(data[1]) < MIN_CHUNK_SIZE:
                    raise Exception("CHUNK SIZE ist zu klein. Erwartet werden mindestens "+str(MIN_CHUNK_SIZE)+" Bytes")
                BUFFER_SIZE = int(data[1])
                filename = data[2]
                with open(filename, "r") as file:
                    REMAINING_DATA = file.read()
                    file.close()
                TRANSFER_RUNNING = True
                TRANSACTION_KEY = random.randrange(100,999)
                sendData(("SERVERREADY;"+str(TRANSACTION_KEY)).encode(), msgAddr)
            else:
                raise Exception("Es läuft kein Transfer")
        else:
            #Sende Dateichunk
            if command == "GET":
                DATASIZE = BUFFER_SIZE - len(DATAPREFIX)+4 # "DATA;key;" abziehen
                if REMAINING_DATA == "":
                    raise Exception("EOF")
                dataToSend = REMAINING_DATA[:DATASIZE]
                sendData((DATAPREFIX+str(TRANSACTION_KEY)+dataToSend).encode("utf-8"), msgAddr) # "DATA;key;" und Inhalt des Chunks verknüpfen und Absenden
                REMAINING_DATA = REMAINING_DATA[DATASIZE:]
            elif command == "INITX":
                raise Exception("BUSY")
            else:
                raise Exception("Unerwartete Nachricht. Bitte Transfer neustarten.")
    except Exception as e:
        TRANSFER_RUNNING = False
        TRANSACTION_KEY = None
        REMAINING_DATA = None
        BUFFER_SIZE = DEFAULT_BUFFER_SIZE
        sendData(("ERROR;"+str(e)).encode(), msgAddr)
