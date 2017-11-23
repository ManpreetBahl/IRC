import socket
import sys
import threading
import select
import CONSTANTS
import json

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
