import socket
import sys
import threading
import select
import CONSTANTS
import json
import os

class IRCClient():
    def __init__(self,name):
        self.name = name
        self.server_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_connection.connect((CONSTANTS.HOST, CONSTANTS.PORT))
        serverMsg = {}
        serverMsg["command"] = "NICK"
        serverMsg["name"] = self.name
        self.server_connection.send((json.dumps(serverMsg)).encode("UTF-8"))

        print("Connected to Server!")

    def prompt(self):
        print("<" + self.name + "> ", end = '', flush=True)

    def listRooms(self):
        serverMsg = {}
        serverMsg["command"] = "LISTROOMS"
        self.server_connection.send((json.dumps(serverMsg)).encode("UTF-8"))

    def createRoom(self, roomName):
        serverMsg = {}
        serverMsg["command"] = "CREATEROOM"
        serverMsg["roomname"] = roomName
        self.server_connection.send((json.dumps(serverMsg)).encode("UTF-8"))

    def joinRoom(self, roomName):
        serverMsg = {}
        serverMsg["command"] = "JOINROOM"
        serverMsg["roomname"] = roomName
        self.server_connection.send((json.dumps(serverMsg)).encode("UTF-8"))

    def leaveRoom(self, roomName):
        serverMsg = {}
        serverMsg["command"] = "LEAVEROOM"
        serverMsg["roomname"] = roomName
        self.server_connection.send((json.dumps(serverMsg)).encode("UTF-8"))

    def listClients(self):
        serverMsg = {}
        serverMsg["command"] = "LISTCLIENTS"
        self.server_connection.send((json.dumps(serverMsg)).encode("UTF-8"))

    def listRoomClients(self, roomName):
        serverMsg = {}
        serverMsg["command"] = "LISTRMCLIENTS"
        serverMsg["roomname"] = roomName
        self.server_connection.send((json.dumps(serverMsg)).encode("UTF-8"))

    def msgRoom(self, roomName, message):
        serverMsg = {}
        serverMsg["command"] = "MSGROOM"
        serverMsg["roomname"] = roomName
        serverMsg["message"] = message
        self.server_connection.send((json.dumps(serverMsg)).encode("UTF-8"))

    def privateMsg(self, toMessage, message):
        serverMsg = {}
        serverMsg["command"] = "PRIVMSG"
        serverMsg["target"] = toMessage
        serverMsg["message"] = message
        self.server_connection.send((json.dumps(serverMsg)).encode("UTF-8"))

    def sendFileRoom(self, target, file_name):
        serverMsg = {}
        serverMsg["command"] = "SENDFILEROOM"
        serverMsg["target"] = target
        serverMsg["file_name"] = file_name
        serverMsg["file_size"] = os.stat(file_name).st_size
        self.server_connection.send((json.dumps(serverMsg)).encode("UTF-8"))

    def sendFilePriv(self, target, file_name):
        serverMsg = {}
        serverMsg["command"] = "SENDFILEPRIV"
        serverMsg["target"] = target
        serverMsg["file_name"] = file_name
        serverMsg["file_size"] = os.stat(file_name).st_size
        self.server_connection.send((json.dumps(serverMsg)).encode("UTF-8"))

    def sendFileData(self, file_name):
        file_data = open(file_name)
        read_data = file_data.read(1024)
        while read_data:
            self.server_connection.send(read_data.encode("UTF-8"))
            read_data = file_data.read(1024)
        file_data.close()

    def receiveFileData(self, message, FILE_NAME, FILE_SIZE):
        with open(self.name + '_' + FILE_NAME, 'wb') as f:
            total_received_data = 0
            while True:
                f.write(message)
                total_received_data += len(message)
                if(total_received_data < FILE_SIZE):
                    message = s.recv(1024)
                else:
                    break
            f.close()
        print("File: " + FILE_NAME + " received successfully")


    def run(self):
        socket_list = [sys.stdin, self.server_connection]
        self.prompt()

        # File transfer parameters
        FILE_TRANSFER_MODE = False
        FILE_NAME = None
        FILE_SIZE = None

        while True:
            read, write, error = select.select(socket_list, [], [])
            for s in read:
                if s is self.server_connection:
                    # Get server response and display
                    message = s.recv(1024)

                    #No message so server is down
                    if not message:
                        print("Server Down")
                        sys.exit(1)
                    else:
                        # Sends file data when server is ready to recieve
                        if("RECEIVING FILE" in message.decode()):
                            self.sendFileData(message.decode().split(" ", 4)[3])

                        # Switches to FILE_TRANSFER_MODE when server is sending a file
                        elif("SENDING FILE" in message.decode()):
                            FILE_TRANSFER_MODE = True
                            FILE_NAME = message.decode().split(" ", 10)[8]
                            FILE_SIZE = int(message.decode().split(" ", 10)[9])
                            display_msg = message.decode()
                            display_msg = display_msg[:-len(str(FILE_SIZE))]
                            print("\n" + display_msg)

                        # Recieves file data and reset file parameters afterwards
                        elif(FILE_TRANSFER_MODE):
                            self.receiveFileData(message, FILE_NAME, FILE_SIZE)
                            self.prompt()
                            # Resetting the file parameters
                            FILE_TRANSFER_MODE = False
                            FILE_NAME = None
                            FILE_SIZE = None

                        # Print response from server and ask for client input
                        else:
                            print("\n" + message.decode())
                            self.prompt()

                elif s is sys.stdin:
                    message = sys.stdin.readline().replace("\n", "")
                    command = message.split(" ", 1)[0]

                    #Client wants a list of rooms
                    if command == "LISTROOMS":
                        self.listRooms()

                    #Client wants to create a room
                    elif command == "CREATEROOM":
                        roomName = message.split(" ", 1)[1]
                        self.createRoom(roomName)

                    #Client wants to join a room
                    elif command == "JOINROOM":
                        roomName = message.split(" ", 1)[1]
                        self.joinRoom(roomName)

                    #Client wants to leave a room
                    elif command == "LEAVEROOM":
                        roomName = message.split(" ", 1)[1]
                        self.leaveRoom(roomName)

                    #Client wants a list of all connected clients
                    elif command == "LISTCLIENTS":
                        self.listClients()

                    #Client wants a list of clients in a particular room
                    elif command == "LISTRMCLIENTS":
                        roomName = message.split(" ", 1)[1]
                        self.listRoomClients(roomName)

                    #Client wants to send a message to a room
                    elif command == "MSGROOM":
                        parse = message.split(" ", 2)
                        self.msgRoom(parse[1], parse[2])

                    #Client wants to send a private message
                    elif command == "PRIVMSG":
                        parse = message.split(" ", 2)
                        self.privateMsg(parse[1], parse[2])

                    #Client wants to send file to a room
                    elif command == "SENDFILEROOM":
                        parse = message.split(" ", 2)
                        self.sendFileRoom(parse[1], parse[2])

                    #Client wants to send file to another client
                    elif command == "SENDFILEPRIV":
                        parse = message.split(" ", 2)
                        self.sendFilePriv(parse[1], parse[2])

                    #Client wants to terminate the program
                    elif command == "QUIT":
                        print("Terminating program...")
                        self.server_connection.close()
                        sys.exit(0)

                    #Invalid command
                    else:
                        print("Invalid command! Please enter a valid command!")
                        self.prompt()

def main():
    name = input("Please enter your name: ")
    client = IRCClient(name)
    client.run()

if __name__ == "__main__":
    main()
