import socket
import sys
import threading
import select
import CONSTANTS
import json
import os
from Crypto.Cipher import AES
from Crypto import Random

# Adds padding to data keep block size = FIXED_BLOCK_SIZE
# which is must in AES
def add_padding(data, interrupt, pad, block_size):
    new_data = ''.join([data, interrupt])
    new_data_len = len(new_data)
    remaining_len = block_size - new_data_len
    to_pad_len = remaining_len % block_size
    pad_string = pad * to_pad_len
    return ''.join([new_data, pad_string])

# Removes extra padding added while AES encryption
def strip_padding(data, interrupt, pad):
    return data.rstrip(pad).rstrip(interrupt)

# Pads, encodes, and then encrypt the data
def encode_n_encrypt(data):
    IV = Random.new().read(16) # randomly generated Initialization vector
    padded_data = add_padding(data, CONSTANTS.INTERRUPT, CONSTANTS.PAD, CONSTANTS.FIXED_BLOCK_SIZE)
    padded_data = padded_data.encode('UTF-8')
    obj = AES.new(CONSTANTS.KEY, AES.MODE_CFB, IV)
    ciphertext = obj.encrypt(padded_data)
    return IV+ciphertext

# decrypts, decodes, and strips pads in data
def decrypt_n_decode(data):
    IV = data[:16] # extracts the Initialization Vector of size 16
    ciphertext = data[16:] # extracts the ciphertext
    obj = AES.new(CONSTANTS.KEY, AES.MODE_CFB, IV)
    decrypted_padded_data = obj.decrypt(ciphertext)
    decrypted_padded_data = decrypted_padded_data.decode('UTF-8')
    decrypted_data = strip_padding(decrypted_padded_data, CONSTANTS.INTERRUPT, CONSTANTS.PAD)
    # reads from JSON
    jsonData = json.loads(str(decrypted_data))
    decrypted_data = jsonData["message"]

    return decrypted_data

class IRCClient():
    def __init__(self,name):
        self.name = name
        self.server_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_connection.connect((CONSTANTS.HOST, CONSTANTS.PORT))
        serverMsg = {}
        serverMsg["command"] = "NICK"
        serverMsg["name"] = self.name
        self.server_connection.send(encode_n_encrypt(json.dumps(serverMsg)))

        print("Connected to Server!")

    def prompt(self):
        print("<" + self.name + "> ", end = '', flush=True)

    def listRooms(self):
        serverMsg = {}
        serverMsg["command"] = "LISTROOMS"
        self.server_connection.send(encode_n_encrypt(json.dumps(serverMsg)))

    def createRoom(self, roomName):
        serverMsg = {}
        serverMsg["command"] = "CREATEROOM"
        serverMsg["roomname"] = roomName
        self.server_connection.send(encode_n_encrypt(json.dumps(serverMsg)))

    def joinRoom(self, roomName):
        serverMsg = {}
        serverMsg["command"] = "JOINROOM"
        serverMsg["roomname"] = roomName
        self.server_connection.send(encode_n_encrypt(json.dumps(serverMsg)))

    def leaveRoom(self, roomName):
        serverMsg = {}
        serverMsg["command"] = "LEAVEROOM"
        serverMsg["roomname"] = roomName
        self.server_connection.send(encode_n_encrypt(json.dumps(serverMsg)))

    def listClients(self):
        serverMsg = {}
        serverMsg["command"] = "LISTCLIENTS"
        self.server_connection.send(encode_n_encrypt(json.dumps(serverMsg)))

    def listRoomClients(self, roomName):
        serverMsg = {}
        serverMsg["command"] = "LISTRMCLIENTS"
        serverMsg["roomname"] = roomName
        self.server_connection.send(encode_n_encrypt(json.dumps(serverMsg)))

    def msgRoom(self, roomName, message):
        serverMsg = {}
        serverMsg["command"] = "MSGROOM"
        serverMsg["roomname"] = roomName
        serverMsg["message"] = message
        self.server_connection.send(encode_n_encrypt(json.dumps(serverMsg)))

    def privateMsg(self, toMessage, message):
        serverMsg = {}
        serverMsg["command"] = "PRIVMSG"
        serverMsg["target"] = toMessage
        serverMsg["message"] = message
        self.server_connection.send(encode_n_encrypt(json.dumps(serverMsg)))

    def sendFileRoom(self, target, file_name):
        serverMsg = {}
        serverMsg["command"] = "SENDFILEROOM"
        serverMsg["target"] = target
        serverMsg["file_name"] = file_name
        serverMsg["file_size"] = os.stat(file_name).st_size
        self.server_connection.send(encode_n_encrypt(json.dumps(serverMsg)))

    def sendFilePriv(self, target, file_name):
        serverMsg = {}
        serverMsg["command"] = "SENDFILEPRIV"
        serverMsg["target"] = target
        serverMsg["file_name"] = file_name
        if(os.path.isfile(file_name)):
            serverMsg["file_size"] = os.stat(file_name).st_size
            self.server_connection.send(encode_n_encrypt(json.dumps(serverMsg)))
        else:
            print("File: '" + file_name + "'' doesn't exist. Please check!")
            self.prompt()

    def sendFileData(self, file_name):
        # file_data = open(file_name)
        with open(file_name) as file_data:
            read_data = file_data.read(1024)
            while read_data:
                self.server_connection.send(encode_n_encrypt(read_data))
                read_data = file_data.read(1024)
            file_data.close()

    def receiveFileData(self, message, FILE_NAME, FILE_SIZE):
        with open(self.name + '_' + FILE_NAME, 'wb') as f:
            total_received_data = 0
            while True:
                f.write(message.encode('UTF-8')) # explicitly encoded to write to file
                total_received_data += len(message.encode('UTF-8'))
                if(total_received_data < FILE_SIZE):
                    message = s.recv(1024)
                    message = decrypt_n_decode(message)
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
                        message = decrypt_n_decode(message)
                        # Sends file data when server is ready to recieve
                        if("RECEIVING FILE" in message):
                            self.sendFileData(message.split(" ", 4)[3])

                        # Switches to FILE_TRANSFER_MODE when server is sending a file
                        elif("SENDING FILE" in message):
                            FILE_TRANSFER_MODE = True
                            FILE_NAME = message.split(" ", 10)[8]
                            FILE_SIZE = int(message.split(" ", 10)[9])
                            display_msg = message
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
                            print("\n" + message)
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
