package main

import (
	"fmt"
	"net"
	"os"
)

func CheckError(err error) {
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %s\n", err)
		os.Exit(1)
	}
}

func main() {
	ServerAddr,err := net.ResolveUDPAddr("udp4", ":6969")
	CheckError(err)

	ServerConn, err := net.ListenUDP("udp", ServerAddr)
	CheckError(err)
	defer ServerConn.Close()

	buffer := make([]byte, 1024)

	for {
		n,addr,err := ServerConn.ReadFromUDP(buffer)
		fmt.Println("Received ",string(buffer[0:n]), " from ",addr)

		if err != nil {
			fmt.Fprintf(os.Stderr, "Error: %s\n", err)
		}
	}
}