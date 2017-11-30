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

                    elif command == "JOINROOM":
                        roomName = message.split(" ", 1)[1]
                        self.joinRoom(roomName)

                    elif command == "LEAVEROOM":
                        roomName = message.split(" ", 1)[1]
                        self.leaveRoom(roomName)

                    elif command == "LISTCLIENTS":
                        self.listClients()

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