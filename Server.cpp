#include <iostream>
#include <cstring>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include <stdexcept>
#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include <cstdint>
#include <stdexcept>
#include <algorithm>
#include <sys/stat.h>
#include <ctime>


using namespace std;

struct VN {
    uint32_t ip;
    uint16_t udpPort;
    int socketFd;
    bool connected;
};

bool recvAll (int fd , void* data , size_t len) {
    char* p = static_cast<char*>(data);
    size_t done = 0 ;

    while ( done < len) {
        ssize_t n = recv(fd , p + done  , len - done , 0);
        if ( n <= 0) 
            return false ;
        done += static_cast<size_t>(n);    
    }
    return true ;
}

bool sendAll(int fd, const void* data, size_t len) {
    const char* p = static_cast<const char*>(data);
    size_t done = 0;

    while (done < len) {
        ssize_t n = send(fd, p + done, len - done, 0);
        if (n <= 0)
            return false;
        done += static_cast<size_t>(n);
    }

    return true;
}


bool sendLinkState(int fd, int self,
                   const vector<vector<int>>& graph,
                   const vector<VN>& nodes) {
    int n = static_cast<int>(nodes.size());

   
    for (int j = 0; j < n; j++) {
        bool isSelf = (j == self);
        int cost = 0;

        if (!isSelf) {
            if (j < self)
                cost = graph[j][self - j - 1];
            else
                cost = graph[self][j - self - 1];

            if (cost == -1)
                continue;
        }

        if (!nodes[j].connected)
            continue;

        char alphabet = static_cast<char>('A' + j);
        uint32_t ip = nodes[j].ip;
        uint16_t port = nodes[j].udpPort;
        uint32_t wireCost = htonl(static_cast<uint32_t>(cost));

       
        if (!sendAll(fd, &alphabet, sizeof(alphabet)) ||
            !sendAll(fd, &ip, sizeof(ip)) ||
            !sendAll(fd, &port, sizeof(port)) ||
            !sendAll(fd, &wireCost, sizeof(wireCost))) {
            return false;
        }
    }

    return true;
}

vector<vector<int>> Node_Graph(const string & filename) {
        ifstream file(filename);
        if (!file) {
            throw runtime_error("File cannot be opened");
        }

        vector<vector<int>> graph ;
        string line;

        while (getline(file,line)) {
            size_t position = line.find('#');

            if ( position != string::npos) {
                line = line.substr(0,position);
            }

            istringstream ss(line);
            vector<int> row ;
            int cost;

            while ( ss >> cost) {
                row.push_back(cost);
            }

            if (!row.empty()) {
                graph.push_back(row);
            }

        }

        int n = static_cast<int>(graph.size()) +1;

        for ( int i = 0 ; i < static_cast<int>(graph.size()); i++) {
            if (graph[i].size() != static_cast<size_t>(n - i - 1)) {
                throw runtime_error("Invalid matrix");
            }

            for (int cost : graph[i]) {
                if (cost < -1 || cost == 0) {
                    throw runtime_error("Invalid link cost");
                }
            }
        }

        return graph ;

    }


int main(int argc, char* argv[]) {
    if ( argc != 2) {
        cerr << "Usage: " << argv[0] << " <config-file>\n";
        return 1;
    }
    

    vector<vector<int>> graph;

    try {
        graph = Node_Graph(argv[1]);
    } catch (const exception& e) {
        cerr << e.what() << '\n';
        return 1;
    }

    int nodeCount = static_cast<int>(graph.size()) + 1;
    

    int serverSocket = socket(AF_INET, SOCK_STREAM, 0);

    int opt = 1;
    setsockopt(serverSocket, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    if (serverSocket < 0) {
        perror("socket");
        return 1;
    }

    
    sockaddr_in serverAddress{};
    serverAddress.sin_family = AF_INET;
    serverAddress.sin_addr.s_addr = INADDR_ANY;
    serverAddress.sin_port = htons(5000);

    if (::bind(serverSocket, (sockaddr*)&serverAddress, sizeof(serverAddress)) < 0) {
        perror("bind");
        return 1;
    }

    if (listen(serverSocket, 26) < 0) {
        perror("listen");
        return 1;
    }

    vector<int> clientSockets;

    vector<VN> nodes(nodeCount);

    for (auto& node : nodes) {
    node.ip = 0;
    node.udpPort = 0;
    node.socketFd = -1;
    node.connected = false;
}

    int connectedCount = 0;

    while (connectedCount < nodeCount) {
    sockaddr_in clientAddress{};
    socklen_t addressLength = sizeof(clientAddress);

    int clientSocket = accept(
        serverSocket,
        reinterpret_cast<sockaddr*>(&clientAddress),
        &addressLength
    );

    if (clientSocket < 0) {
        perror("accept");
        continue;
    }

    int idx = connectedCount;
    nodes[idx].socketFd = clientSocket;
    nodes[idx].connected = false;

    cout << "Accepted VN " << char('A' + idx) << '\n';

    uint32_t ip;
    uint16_t port;

    if (!recvAll(clientSocket, &ip, sizeof(ip)) ||
        !recvAll(clientSocket, &port, sizeof(port))) {
        cerr << "Failed to receive CONNECT from VN "
             << char('A' + idx) << '\n';
        close(clientSocket);
        nodes[idx].socketFd = -1;
        continue;
    }

    nodes[idx].ip = ip;
    nodes[idx].udpPort = port;
    nodes[idx].connected = true;
    connectedCount++;

    cout << "Received CONNECT for VN "
         << char('A' + idx) << '\n';
}
    
    
cout << "All configured VNs connected. Sending LINK-STATE.\n";

for (int i = 0; i < nodeCount; i++) {
    if (!sendLinkState(nodes[i].socketFd, i, graph, nodes)) {
        cerr << "Failed to send LINK-STATE to VN "
             << char('A' + i) << '\n';
    }
}
    
    struct stat st;
    time_t lastMod = (stat(argv[1], &st) == 0) ? st.st_mtime : 0;

    while (true) {
        sleep(1);

        if (stat(argv[1], &st) == 0 && st.st_mtime != lastMod) {
            lastMod = st.st_mtime;
            try {
                vector<vector<int>> newGraph = Node_Graph(argv[1]);
                if (newGraph.size() + 1 == nodes.size()) {
                    graph = newGraph;
                    for (int i = 0; i < nodeCount; i++) {
                        if (nodes[i].connected)
                            sendLinkState(nodes[i].socketFd, i, graph, nodes);
                    }
                }
            } catch (const exception& e) {
                cerr << e.what() << '\n';
            }
        }
    }
}