import socket
import sys
import threading
import select
import CONSTANTS
import json

#Defines an IRC Room
class IRCRoom():
    def __init__(self, name):
        self.name = name #Name of the room
        self.roomClients = set() #Set containing a list of clients in that room. Set allows for only unique clients


#Defines the IRC Server
class IRCServer(threading.Thread):
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.clients = [] #List containing all clients connected to the server. Can also be a set. Decide later
        self.rooms = [] #List containing all rooms on the server. Can also be a set. Decide later

    def run(self):
        #Create and bind socket to host and port
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverSocket.bind((self.host, self.port))

        #Check if server socket is in the clients list or not
        if(self.serverSocket in self.clients):
            print("Server is alredy active and running!")
            sys.exit(1)
        else:
            self.clients.append(self.serverSocket) #Add server socket to list

        self.serverSocket.listen(1)

        while True:
            try:
                read, write, error = select.select(self.clients, [], [])
            except socket.error as msg:
                #print("Socket Error: " + str(msg))
                continue

            for s in read:
                #Server socket is readable so have it listen to incoming client connections
                if s == self.serverSocket:
                    try:
                        clientSocket, clientAddr = self.serverSocket.accept()
                    except socket.error:
                        break
                    #If client is already connected to the server, send an appropriate message
                    if(clientSocket in self.clients):
                        clientSocket.send("You are already connected to the server!")
                    else:
                        # Add to list of all connected clients
                        self.clients.append(clientSocket)
                else:
                    try:
                        data = s.recv(1024)
                        print("Data Received: " + str(data.decode("UTF-8")))

                        if not data:
                            # Handles the unexpected connection closed by client
                            s.close()
                            self.clients.remove(s)
                            print("Connection closed by client")
                        else:
                            # TODO: Message parsing.
                            jsonData = json.loads(str(data.decode('UTF-8')))
                            command = jsonData["command"]

                            if command == "LISTROOMS": #Client wants a list of all active rooms
                                if self.rooms:
                                    s.send( ("Available Rooms:\n" + "\n\t".join(self.rooms)).encode("UTF-8") )
                                else:
                                    s.send( ("No avaiable rooms\n").encode("UTF-8") )

                            """Initial JSON parsing
                            print("Parsing JSON...")
                            jsonData = json.loads(str(data.decode('UTF-8')))
                            print(jsonData["command"])

                            #Initial Message Parsing
                            command = data.split(' ', 1)[0]
                            print("Command: " + repr(command))
                            if command == "/LIST":
                                s.send("YOU SENT A LIST COMMAND!")
                            

                            #Send message to everyone else connected to the server
                            for person in self.clients:
                                if(person != self.serverSocket and person != s):
                                    person.send(data)
                            """

                    except Exception as e:
                        #Disconnect client from server and remove from connected clients list
                        print("ERROR: " + str(e))
                        s.close()
                        self.clients.remove(s)

                        #TODO: Remove person from all rooms here

                        continue

        self.serverSocket.close() #Technically, unreachable code. Leaving it here for now

def main():
    server = IRCServer(CONSTANTS.HOST, CONSTANTS.PORT)
    server.start()

if __name__ == "__main__":
    main()
