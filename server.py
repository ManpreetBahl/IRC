import socket
import sys
import threading
import select

#Defines an IRC Room
class IRCRoom():
    def __init__(self, name):
        self.name = name #Name of the room
        self.roomClients = set() #Set containing list of clients in that room


#Defines the IRC Server
class IRCServer(threading.Thread):
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.clients = [] #List containing all clients connected to the server
        self.testRoom = IRCRoom('Room') #One room for now #TODO: Support dynamic room operations

    def run(self):
        #Create and bind socket to host and port
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverSocket.bind((self.host, self.port))
        #TODO: Check if socket already exists before adding
        self.clients.append(self.serverSocket) #Add server socket to list

        self.clients.append(sys.stdin); #NEEDED TO CONNECT TO SERVER WITH TELNET

        self.serverSocket.listen(1)

        while True:
            try:
                read, write, error = select.select(self.clients, [], [])
            except socket.error:
                continue

            for s in read:
                #Server socket is readable so have it listen to incoming client connections
                if s == self.serverSocket:
                    try:
                        clientSocket, clientAddr = self.serverSocket.accept()
                        print("ClientSocket: " + str(clientSocket) + " ClientAddr: " + str(clientAddr))
                    except socket.error:
                        break
                    #TODO: Check if client already exists in list of connected client
                    self.clients.append(clientSocket)
                    self.testRoom.roomClients.add(clientSocket)

                elif s == sys.stdin: #For testing with telnet
                    data = sys.stdin.readline()
                    print("Data is: " + data)
                    if data:
                        # Send message to everyone in the client (including the person sending it)
                        for person in self.testRoom.roomClients:
                            person.send(data)

                else:
                    try:
                        data = s.recv(1024)
                        print("Data Received: " + data + '\n')
                        if data:
                            #Send message to everyone in the client (including the person sending it)
                            for person in self.testRoom.roomClients:
                                person.send(data)

                    except:
                        #Disconnect client from server and remove from connected clients list
                        s.close()
                        self.clients.remove(s)

                        #For now:
                        self.testRoom.roomClients.remove(s)

                        continue

        self.serverSocket.close()

def main():
    server = IRCServer('127.0.0.1', 10000)
    server.start()

if __name__ == "__main__":
    main()