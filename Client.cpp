#include <iostream>
#include <cstring>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>

using namespace std;

int main() {
    int clientSocket = socket(AF_INET, SOCK_STREAM, 0);

    sockaddr_in serverAddress{};
    serverAddress.sin_family = AF_INET;
    serverAddress.sin_port = htons(8080);

    inet_pton(AF_INET, "127.0.0.1", &serverAddress.sin_addr);

    cout << "Before connect" << endl;

    connect(clientSocket, (sockaddr*)&serverAddress, sizeof(serverAddress));

    cout << "After connect" << endl;

    string message = "Hi Nithya!";
    send(clientSocket, message.c_str(), message.size(), 0);

    char buffer[1024] = {0};
    recv(clientSocket, buffer, sizeof(buffer), 0);

    cout << "Server: " << buffer << endl;

    close(clientSocket);

    return 0;
}