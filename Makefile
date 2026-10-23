
CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -O2

all: on

on: Server.cpp
	$(CXX) $(CXXFLAGS) Server.cpp -o on

clean:
	rm -f on

.PHONY: all clean
