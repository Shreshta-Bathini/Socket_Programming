#include <iostream>
#include <cstring>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>

using namespace std;

int main() {
    int serverSocket = socket(AF_INET, SOCK_STREAM, 0);

    if (serverSocket < 0) {
        perror("socket");
        return 1;
    }

    sockaddr_in serverAddress{};
    serverAddress.sin_family = AF_INET;
    serverAddress.sin_addr.s_addr = INADDR_ANY;
    serverAddress.sin_port = htons(8080);
    if (::bind(serverSocket, (sockaddr*)&serverAddress, sizeof(serverAddress)) < 0) {
        perror("bind");
        return 1;
    }

    if (listen(serverSocket, 1) < 0) {
        perror("listen");
        return 1;
    }

    cout << "Waiting for connection..." << endl;

    int clientSocket = accept(serverSocket, nullptr, nullptr);

    if (clientSocket < 0) {
        perror("accept");
        return 1;
    }

    cout << "Shreshta connected!" << endl;

    char buffer[1024] = {0};

    int n = recv(clientSocket, buffer, sizeof(buffer), 0);

    if (n < 0) {
        perror("recv");
        return 1;
    }

    buffer[n] = '\0';

    cout << "Received: " << buffer << endl;

    string reply = "Hi Shreshta!";
    send(clientSocket, reply.c_str(), reply.size(), 0);

    close(clientSocket);
    close(serverSocket);

    return 0;
}