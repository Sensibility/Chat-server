package main

import (
	"fmt"
	"net"
	"os"
)

type address struct {
	Network string;
	String string;
}

func CheckError(err error) {
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %s\n", err)
		os.Exit(1)
	}
}

func compareIPs(a net.IP, b net.IP) bool{
	if len(a) != len(b) {
		fmt.Fprintf(os.Stderr, "Malformed IP in IP pair: %s, %s\n", a, b)
	}
	for i := 0; i < len(a); i++ {
		if a[i] != b[i] {
			return false
		}
	}
	return true
}

func checkHost(host *net.UDPAddr, knownHosts []*net.UDPAddr) bool {
	for _, knownHost := range knownHosts {
		if compareIPs(host.IP, knownHost.IP) {
			return true
		}
	}
	return false
}

func relayMessage(msg []byte, sender net.IP, clients []*net.UDPAddr, server *net.UDPConn) {
	for _, client := range clients {
		if !compareIPs(client.IP, sender) {
			_, err := server.WriteToUDP(msg, client)
			if err != nil {
				fmt.Fprintf(os.Stderr, "Error writing message from %s to %s: %s", sender, client, err)
			}

		}
	}
}

func main() {
	ServerAddr,err := net.ResolveUDPAddr("udp4", ":6969")
	CheckError(err)

	ServerConn, err := net.ListenUDP("udp", ServerAddr)
	CheckError(err)
	defer ServerConn.Close()

	buffer := make([]byte, 1024)

	var knownHosts []*net.UDPAddr

	for {
		n,addr,err := ServerConn.ReadFromUDP(buffer)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error: %s\n", err)
		}
		fmt.Println("Received ",string(buffer[0:n]), " from ",addr)
		if !checkHost(addr, knownHosts) {
			knownHosts = append(knownHosts, addr)
			fmt.Println("New host added: ", addr, "\n Known Hosts:")
			for _, host := range knownHosts {
				fmt.Println("\t", host)
			}
		}
		relayMessage(buffer, addr.IP, knownHosts, ServerConn)
	}
}
