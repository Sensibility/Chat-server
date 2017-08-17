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

func checkHost(host *net.UDPAddr, knownHosts []net.UDPAddr) bool {
	for _, knownHost := range knownHosts {
		fmt.Println("Comparing '", host, "' to '", knownHost, "'")
		if compareIPs((*host).IP, knownHost.IP) {
			return true
		}
	}
	return false
}

func main() {
	ServerAddr,err := net.ResolveUDPAddr("udp4", ":6969")
	CheckError(err)

	ServerConn, err := net.ListenUDP("udp", ServerAddr)
	CheckError(err)
	defer ServerConn.Close()

	buffer := make([]byte, 1024)

	var knownHosts []net.UDPAddr

	for {
		n,addr,err := ServerConn.ReadFromUDP(buffer)
		fmt.Println("Received ",string(buffer[0:n]), " from ",addr)
		if !checkHost(addr, knownHosts) {
			knownHosts = append(knownHosts, *addr)
			fmt.Println("New host added: ", addr, "\n Known Hosts:")
			for _, host := range knownHosts {
				fmt.Println("\t", host)
			}

		}
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error: %s\n", err)
		}
	}
}