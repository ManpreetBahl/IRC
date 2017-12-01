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
        self.lock = threading.Lock()
        self.host = host
        self.port = port
        #Dictionay containing all clients connected to the server. Key: Socket Object. Value: Client name associated with the socket object
        self.clients = {}
        #List containing all rooms on the server. Can also be a set. Decide later
        self.rooms = []
    
    def cleanup(self, socket):
        #Remove person from all rooms
        for room in self.rooms:
            #Go through all clients in a room
            for personSocket in room.roomClients:
                #Remove the client from the room, then check the next room
                if personSocket == socket:
                    del room.roomClients[personSocket]
                    break
            #Notify that the user has left the room 
            for personSocket in room.roomClients:
                if personSocket != socket:
                    personSocket.send( ("<" + room.name + "> " + self.clients[socket] + " has left the room!").encode("UTF-8") )

        #Remove client from list of clients
        del self.clients[socket]

    def run(self):
        #Create and bind socket to host and port
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverSocket.bind((self.host, self.port))

        #Check if server socket is in the clients list or not
        self.lock.acquire()
        if("SERVER" in self.clients):
            print("Server is alredy active and running!")
            sys.exit(1)
        else:
            #Add server socket to dictionary
            self.clients[self.serverSocket] = "SERVER"
        self.lock.release()

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
                        self.lock.acquire()
                        self.clients[clientSocket] = clientSocket
                        self.lock.release()
                else:
                    try:
                        data = s.recv(1024)
                        print("Data Received: " + str(data.decode("UTF-8")))

                        if not data:
                            # Handles the unexpected connection closed by client
                            print("Not data")
                            
                            self.lock.acquire()
                            #Remove client from all rooms and then from list of connected clients
                            self.cleanup(s)
                            self.lock.release()
                            s.close()
                            print("Connection closed by client")
                        else:
                            jsonData = json.loads(str(data.decode('UTF-8')))
                            command = jsonData["command"]

                            # Associate client name to socket object
                            if command == "NICK":
                                self.lock.acquire()
                                name = jsonData["name"]
                                if name in self.clients.values():
                                    s.send( ("<" + self.clients[self.serverSocket] + "> Name already in use!").encode("UTF-8") )
                                else:
                                    self.clients[s] = jsonData["name"]
                                    s.send( ("<" + self.clients[self.serverSocket] + "> Connected to server under username: " + name).encode("UTF-8") )
                                self.lock.release()

                            #Client wants a list of all active rooms
                            elif command == "LISTROOMS":
                                self.lock.acquire()
                                if self.rooms:
                                    message = ""
                                    for room in self.rooms:
                                        message += "\n\t" + room.name

                                    s.send( ("<" + self.clients[self.serverSocket] + "> Available Rooms:" + message).encode("UTF-8") )
                                else:
                                    s.send( ("<" + self.clients[self.serverSocket] + "> No avaiable rooms").encode("UTF-8") )
                                self.lock.release()

                            #Client wants to create a room
                            elif command == "CREATEROOM":
                                allowCreate = True
                                self.lock.acquire()
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
                                self.lock.release()

                            #Client wants to join a room
                            elif command == "JOINROOM":
                                roomExists = False
                                self.lock.acquire()
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
                                                    userSocket.send( ("<" + self.clients[self.serverSocket] + "> " + self.clients[s] + " has joined the room " + room.name + "!").encode("UTF-8") )
                                        else:
                                            s.send( ("<" + self.clients[self.serverSocket] + "> You are already in the room!").encode("UTF-8") )
                                        roomExists = True
                                        break
                                
                                #Notify client that the room doesn't exist!
                                if roomExists == False:
                                    s.send( ("<" + self.clients[self.serverSocket] + "> Unable to join room! The room may not exist. Try creating a room with the CREATEROOM [roomname] command").encode("UTF-8") )
                                self.lock.release()

                            #Client wants to leave a room
                            elif command == "LEAVEROOM":
                                self.lock.acquire()
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
                                self.lock.release()

                            #Client wants a list of clients connected to the server
                            elif command == "LISTCLIENTS":
                                self.lock.acquire()
                                if self.clients:
                                    message = ""
                                    for personSocket, person in self.clients.items():
                                        if personSocket != self.serverSocket:
                                            message += "\n\t" + person

                                    s.send( ("<" + self.clients[self.serverSocket] + "> Connected Clients:" + message).encode("UTF-8") )
                                else:
                                    #You are the only connected client on server
                                    s.send( ("<" + self.clients[self.serverSocket] + "> You are all alone! Go invite more people to join!!").encode("UTF-8") )
                                self.lock.release()

                            #Client wants a list of clients in the room 
                            elif command == "LISTRMCLIENTS":
                                self.lock.acquire()
                                room = jsonData["roomname"]
                                success = False
                                if self.rooms:
                                    message = ""
                                    #Find the room the get list of clients
                                    for r in self.rooms:
                                        if room == r.name:
                                            #Get the list of clients in the room
                                            for personSocket, person in r.roomClients.items():
                                                if personSocket != self.serverSocket:
                                                    message += "\n\t" + person
                                            s.send( ("<" + self.clients[self.serverSocket] + "> Connected Clients in " + room + ":" + message).encode("UTF-8") )
                                            success = True
                                            break
                                    if success == False:
                                        s.send( ("<" + self.clients[self.serverSocket] + "> Nobody in the room").encode("UTF-8") )
                                else:
                                    s.send( ("<" + self.clients[self.serverSocket] + "> No rooms exist!").encode("UTF-8") )
                                self.lock.release()

                            #Client wants to send a message to a room
                            elif command == "MSGROOM":
                                self.lock.acquire()

                                room = jsonData["roomname"]
                                message = jsonData["message"]
                                success = False

                                #Search through rooms list
                                if self.rooms:
                                    for r in self.rooms:
                                        #Found room
                                        if room == r.name:
                                            #Check to make sure that the client is part of the room first
                                            if s in r.roomClients:
                                                #Send messages to all others in the room
                                                for userSocket in r.roomClients.keys():
                                                    if userSocket != s:
                                                        userSocket.send( ("<" + self.clients[self.serverSocket] + "> " + self.clients[s] + " in " + r.name + " says: " + message).encode("UTF-8") )
                                                success = True
                                                break
                                #Send client a message indicating that the room does not exist or they are not part of the indicated room
                                if success == False:
                                    s.send( ("<" + self.clients[self.serverSocket] + "> Unable to send message! The room does not exist or you are not part of the room!").encode("UTF-8")  )
                                else:
                                     s.send( ("<" + self.clients[self.serverSocket] + "> Message sent to room").encode("UTF-8")  )
                                self.lock.release()

                            #Client wants to send a private message to another client
                            elif command == "PRIVMSG":
                                self.lock.acquire()
                                target = jsonData["target"]
                                message = jsonData["message"]
                                if self.clients:
                                    for personSocket, person in self.clients.items():
                                        if personSocket != self.serverSocket and person == target:
                                            s.send( ("<" + self.clients[self.serverSocket] + "> " + self.clients[s] + " sent a message to you: " + message).encode("UTF-8") )
                                else:
                                    #You are the only connected client on server
                                    s.send( ("<" + self.clients[self.serverSocket] + "> Unable to send private message! Nobody else is online!").encode("UTF-8") )
                                self.lock.release()

                    except Exception as e:
                        #Disconnect client from server and remove from connected clients list
                        print("ERROR: " + str(e))
                        s.close()

                        self.lock.acquire()
                        self.cleanup(s)
                        self.lock.release()
                        continue

        self.serverSocket.close() #Technically, unreachable code. Leaving it here for now

def main():
    server = IRCServer(CONSTANTS.HOST, CONSTANTS.PORT)
    server.start()

if __name__ == "__main__":
    main()
