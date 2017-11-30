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
        self.roomClients = {} #Dictionary containing all clients that are part of the room


#Defines the IRC Server
class IRCServer(threading.Thread):
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        #Dictionay containing all clients connected to the server. Key: Socket Object. Value: Client name associated with the socket object
        self.clients = {}
        #List containing all rooms on the server. Can also be a set. Decide later
        self.rooms = []
    
    def run(self):
        #Create and bind socket to host and port
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverSocket.bind((self.host, self.port))

        #Check if server socket is in the clients list or not
        if("SERVER" in self.clients):
            print("Server is alredy active and running!")
            sys.exit(1)
        else:
            #Add server socket to dictionary
            self.clients[self.serverSocket] = "SERVER"

        self.serverSocket.listen(1)

        while True:
            try:
                read, write, error = select.select(list(self.clients.keys()), [], [])
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
                        self.clients[clientSocket] = clientSocket
                else:
                    try:
                        data = s.recv(1024)
                        print("Data Received: " + str(data.decode("UTF-8")))

                        if not data:
                            # Handles the unexpected connection closed by client
                            s.close()
                            del self.clients[s]
                            print("Connection closed by client")
                        else:
                            jsonData = json.loads(str(data.decode('UTF-8')))
                            command = jsonData["command"]

                            # Associate client name to socket object
                            if command == "NICK":
                                self.clients[s] = jsonData["name"]

                            #Client wants a list of all active rooms
                            elif command == "LISTROOMS":
                                if self.rooms:
                                    message = ""
                                    for room in self.rooms:
                                        message += "\n\t" + room.name

                                    s.send( ("<" + self.clients[self.serverSocket] + "> Available Rooms:" + message).encode("UTF-8") )
                                else:
                                    s.send( ("<" + self.clients[self.serverSocket] + "> No avaiable rooms").encode("UTF-8") )

                            #Client wants to create a room
                            elif command == "CREATEROOM":
                                allowCreate = True
                                for room in self.rooms:
                                    if jsonData["roomname"] == room.name:
                                        allowCreate = False
                                        s.send( ("<" + self.clients[self.serverSocket] + "> Room name already taken! Please enter a different room name!").encode("UTF-8") )
                                        break

                                if allowCreate == True:
                                    #Create new room with the given room name
                                    newRoom = IRCRoom(jsonData["roomname"])                                   

                                    #Add the client to the room list
                                    newRoom.roomClients[s] = self.clients[s]
                                    
                                    #Add room to list of rooms
                                    self.rooms.append(newRoom)

                                    #Send message to client
                                    s.send( ("<" + self.clients[self.serverSocket] + "> Room created succesfully! You have been added to the room!").encode("UTF-8") )
                            
                            #Client wants to join a room
                            elif command == "JOINROOM":
                                roomExists = False
                                #Add the client to a room if it exists
                                for room in self.rooms:
                                    if jsonData["roomname"] == room.name:
                                        #Check to make sure that user is not already in room:
                                        if s not in room.roomClients:
                                            #Add user to the room if it exists
                                            room.roomClients[s] = self.clients[s]

                                            #Notify client that they have joined the room succesfully
                                            s.send( ("<" + self.clients[self.serverSocket] + "> You have successfully joined the room!").encode("UTF-8") )

                                             #Notify other members in the room about new client joining
                                            for userSocket in room.roomClients:
                                                if userSocket != s:
                                                    userSocket.send( ("<" + room.name + "> " + self.clients[s] + " has joined the room!").encode("UTF-8") )
                                        else:
                                            s.send( ("<" + self.clients[self.serverSocket] + "> You are already in the room!").encode("UTF-8") )
                                        roomExists = True
                                        break
                                
                                #Notify client that the room doesn't exist!
                                if roomExists == False:
                                    s.send( ("<" + self.clients[self.serverSocket] + "> Unable to join room! The room may not exist. Try creating a room with the CREATEROOM [roomname] command").encode("UTF-8") )
            
                            #Client wants to leave a room
                            elif command == "LEAVEROOM":
                                #Find the room in the list of rooms
                                for room in self.rooms:
                                    if jsonData["roomname"] == room.name:
                                        #Attempt to remove client from the room
                                        try:
                                            del room.roomClients[s]
                                            #Inform client that they have left the room successfully
                                            s.send( ("<" + self.clients[self.serverSocket] + "> You have successfully left the room!").encode("UTF-8") )    
                                            
                                            #If there are no more clients in the room, delete the room
                                            if len(room.roomClients) == 0:
                                                self.rooms.remove(room)
                                            
                                            break
                                        except KeyError: #Client is not in the room!
                                            s.send( ("<" + self.clients[self.serverSocket] + "> Unable to leave room!").encode("UTF-8") ) 
                                            break

                            #Client wants a list of clients connected to the server
                            elif command == "LISTCLIENTS":
                                if self.clients and not self.serverSocket in self.clients:
                                    message = ""
                                    for personSocket, person in self.clients.items():
                                        if personSocket != s and personSocket != self.serverSocket:
                                            message += "\n\t" + person

                                    s.send( ("<" + self.clients[self.serverSocket] + "> Connected Clients:" + message).encode("UTF-8") )
                                else:
                                    #You are the only connected client on server
                                    s.send( ("<" + self.clients[self.serverSocket] + "> You are all alone! Go invite more people to join!!").encode("UTF-8") )

                            #Client wants to send a message to a room
                            elif command == "MSGROOM":
                                room = jsonData["room"]
                                message = jsonData["message"]
                                
                                """
                                #Search through rooms list
                                if self.rooms:
                                    for r in self.rooms:
                                        #Found room
                                        if r == room.name:
                                            #Send messages to all others in the room
                                            for userSocket in r.roomClients:
                                                if userSocket != s:
                                                    userSocket.send( ("<" + self.serverSocket + "> " + self.clients[s] + " in " + r.name + " says: " + message).encode("UTF-8") )
                                """

                    except Exception as e:
                        #Disconnect client from server and remove from connected clients list
                        print("ERROR: " + str(e))
                        s.close()
                        del self.clients[s]

                        #TODO: Remove person from all rooms here

                        continue

        self.serverSocket.close() #Technically, unreachable code. Leaving it here for now

def main():
    server = IRCServer(CONSTANTS.HOST, CONSTANTS.PORT)
    server.start()

if __name__ == "__main__":
    main()
