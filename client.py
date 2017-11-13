import socket
import sys
import threading
import select
import CONSTANTS

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
            #TODO: need to handle server response here
            print("Hello")
            # message = s.recv(1024)
            # if not message:
            #     print("No data from server")
            #     sys.exit(2)
            # else:
            #     sys.stdout.write(message.decode())
        else:
            message = sys.stdin.readline()
            print("Sending message")
            server_connection.sendall(message.encode())
