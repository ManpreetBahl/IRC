import socket
import sys
import threading
import select
import CONSTANTS
import json
import os

def printMenu():
    print(30 * "-", "MENU", 30 * "-")
    print("1. List IRC Rooms")
    print("2. Exit")
    print(66 * "-")

class IRCClient():
    def __init__(self, name):
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
        sys.stdout.write("<" + self.name + "> ")
        sys.stdout.flush()
 
    def listRooms(self):
        serverMsg = {}
        serverMsg["command"] = "LISTROOMS"
        self.server_connection.send((json.dumps(serverMsg)).encode("UTF-8"))

    def createRoom(self, roomName):
        serverMsg = {}
        serverMsg["command"] = "CREATEROOM"
        serverMsg["roomname"] = roomName
        self.server_connection.send((json.dumps(serverMsg)).encode("UTF-8"))

    def run(self):
        socket_list = [sys.stdin, self.server_connection]
        self.prompt()
        while True:
            read, write, error = select.select(socket_list, [], [])
            for s in read:
                if s is self.server_connection:
                    # Get server response and display
                    message = s.recv(1024)
                    if not message:
                        print("Server Down")
                        sys.exit(1)
                    else:
                        print(message.decode())
                        self.prompt()

                elif s is sys.stdin:
                    message = sys.stdin.readline().replace("\n", "")
                    command = message.split(" ", 1)[0]

                    if command == "LISTROOMS":
                        self.listRooms()

                    elif command == "CREATEROOM":
                        roomName = message.split(" ", 1)[1]
                        self.createRoom(roomName)

                    elif command == "QUIT":
                        print("Terminating program...")
                        self.server_connection.close()
                        sys.exit(0)

def main():
    name = input("Please enter your name: ")
    client = IRCClient(name)
    client.run()

if __name__ == "__main__":
    main()


"""
print("Connecting to server...")
server_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_connection.connect((CONSTANTS.HOST, CONSTANTS.PORT))
print("Connected")

printMenu()

socket_list = [sys.stdin, server_connection]

while True:
    read, write, error = select.select(socket_list, [], [])
    for s in read:
        if s is server_connection:
            # Get server response and display
             message = s.recv(1024)
             if not message:
                 print("Server Down")
                 sys.exit(1)
             else:
                 print("SERVER RESPONSE: " + message.decode())
        else:
            #printMenu()
            printMenu()
            choice = input("Enter your choice [1-2]: ")

            if choice == "1": #Get a list of all rooms on IRC Server
                serverMsg = {}
                serverMsg["command"] = "LISTROOMS"
                server_connection.sendall((json.dumps(serverMsg)).encode("UTF-8"))
            elif choice == "2": 
                print("Terminating program...")
                server_connection.close()
                sys.exit(0)
        

            #message = sys.stdin.readline()
            #server_connection.sendall(message.encode())
            """

"""
            serverMsg = {}
            serverMsg["command"] = message.replace("\n", "")
            print(serverMsg)
            server_connection.sendall((json.dumps(serverMsg)).encode("UTF-8"))
"""


""" For Backup Purposes
# client establishes connection to the server
print("Connecting to server...\n")
server_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_connection.connect((CONSTANTS.HOST, CONSTANTS.PORT))
print("Connected.\n")

socket_list = [sys.stdin, server_connection]

while True:
    read, write, error = select.select(socket_list, [], [])
    for s in read:
        if s is server_connection:
            # Get server response and display
             message = s.recv(1024)
             if not message:
                 print("Server Down")
                 sys.exit(2)
             else:
                 sys.stdout.write(message.decode())
        else:
            message = sys.stdin.readline()
            #server_connection.sendall(message.encode())

            serverMsg = {}
            serverMsg["command"] = message.replace("\n", "")
            print(serverMsg)
            server_connection.sendall((json.dumps(serverMsg)).encode("UTF-8"))
"""