
import socket

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

serverAddress = ("127.0.0.1", 8080)

print("Before connect")

clientSocket.connect(serverAddress)

print("After connect")

message = "Hi Nithya!"
clientSocket.send(message.encode())

buffer = clientSocket.recv(1024)

print("Server:", buffer.decode())

clientSocket.close()

