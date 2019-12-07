import socket

BIND_TO_IP = "0.0.0.0"
PORT = 8999

DEFAULT_BUFFER_SIZE = 1024
BUFFER_SIZE = 1024
TRANSFER_RUNNING = False
REMAINING_DATA = None
DATAPREFIX = "DATA;"
MIN_CHUNK_SIZE = 6

"""
Methode die lauscht und guckt ob die antwort vollendet ist
replacet dann das recv?
"""

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((BIND_TO_IP, PORT))
while 1:
    s.listen(1)
    try:
        conn, addr = s.accept()
        print('Connection address:', addr)
        while 1:
            data = conn.recv(BUFFER_SIZE)

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
                        conn.send("SERVERREADY;".encode())
                    else:
                        raise Exception("Es läuft kein Transfer")
                else:
                    #Sende Dateichunk
                    if command == "GET":
                        DATASIZE = BUFFER_SIZE - len(DATAPREFIX) # "DATA;" abziehen
                        if REMAINING_DATA == "":
                            raise Exception("EOF")
                        dataToSend = REMAINING_DATA[:DATASIZE]
                        conn.send((DATAPREFIX+dataToSend).encode("utf-8")) # "DATA;" und Inhalt des Chunks verknüpfen und Absenden
                        REMAINING_DATA = REMAINING_DATA[DATASIZE:]
                    else:
                        raise Exception("Unerwartete Nachricht. Bitte Transfer neustarten.")
            except Exception as e:
                TRANSFER_RUNNING = False
                REMAINING_DATA = None
                BUFFER_SIZE = DEFAULT_BUFFER_SIZE
                conn.send(("ERROR;"+str(e)).encode())

    except ConnectionResetError as e:
        print(e)
        conn.close()