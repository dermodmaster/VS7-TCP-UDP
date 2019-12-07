import socket

SERVER_IP = "127.0.0.1"
PORT = 8999

DEFAULT_BUFFER_SIZE = 1024
MIN_CHUNK_SIZE = 6
BUFFER_SIZE = 1024
CHUNKSIZE = None
FILENAME = None

TRANSFER_RUNNING = False
RECEIVED_DATA = ""

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect((SERVER_IP, PORT))
except Exception as e:
    print("Es konnte keine Verbindung hergestellt werden.",e)
    exit()

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
    print("sendInit()")
    global TRANSFER_RUNNING
    request = "INITX;"+str(CHUNKSIZE)+";"+filename
    if len(request) > BUFFER_SIZE:
        raise Exception("Dateiname ist zu lang.")
    s.send(request.encode())
    response = s.recv(BUFFER_SIZE)
    response = response.decode("utf-8")
    if response.startswith("ERROR;"):
        raise Exception("Server Error: "+response[6:]) # Fehlermeldung des Servers als Exception ausgeben.
    TRANSFER_RUNNING = True

def receiveData():
    print("GET")
    global RECEIVED_DATA
    s.send("GET".encode("utf-8"))
    response = s.recv(BUFFER_SIZE)
    print("ANTWORT", response)
    response = response.decode("utf-8")
    response = response.split(";")
    if(len(response) == 2 and response[0] == "DATA"):
        RECEIVED_DATA += response[1]
    else:
        if(response[0] == "ERROR" and response[1] == "EOF"):
            raise Exception("EOF")
        else:
            raise Exception("Fehlerhafte Antwort. Daten wurden erwartet.")

try:
    while CHUNKSIZE == None or FILENAME == None:
        showMenu()
    sendInit(CHUNKSIZE, FILENAME)
    while True:
        receiveData()


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