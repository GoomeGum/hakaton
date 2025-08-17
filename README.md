# Client-Server Communication App – Network Speed Test (Hackathon Project)

##  Overview
This project was developed as part of the **Intro to Computer Networks Hackathon (2024)**.  
It implements a **real-time client-server system** in Python that compares **TCP and UDP download speeds** and demonstrates how they share the same network.

The system consists of:
- **Server**: broadcasts availability, accepts both TCP and UDP requests, and serves data accordingly.  
- **Client**: listens for server offers, requests file transfers, and measures performance metrics.

---

##  Features
- **TCP and UDP Support** – transfer requested file size over both protocols.  
- **Asynchronous & Multi-threaded** – handles multiple concurrent connections efficiently.  
- **Real-time Metrics** – measures:
  - Transfer completion time  
  - Effective throughput (bits/sec)  
  - For UDP: packet loss percentage  
- **Cross-team Compatibility** – works with any client/server implementation following the protocol.  
- **Error Handling** – manages timeouts, corrupted packets, and unexpected disconnects.  

---

##  Protocols & Packet Formats
### UDP
- **Offer** (server → client)  
- **Request** (client → server)  
- **Payload** (server → client with sequence numbers)  

### TCP
- Client sends requested file size (bytes + `\n`).  
- Server sends back the entire file.  
