import socket
import time
import massage

info = {
    "buffer": 1024,
    "udp_port": 12345,
    "tcp_port": 23456,
}
def broadcast_message():
    
    # Create a UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Enable broadcasting mode
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    broadcast_address = ('<broadcast>', info["udp_port"])
    offer_massge = massage.create_offer(info["tcp_port"], info["udp_port"])
    try:
        while True:
            server_socket.sendto(offer_massge, broadcast_address)
            print(f"Broadcasting message: {offer_massge}") #remove later
            time.sleep(2)  # Broadcast every 2 seconds
    except KeyboardInterrupt:
        print("Broadcast stopped.")
    finally:
        server_socket.close()

if __name__ == "__main__":
    print(f"Server started, listening on IP address {socket.AF_INET}")
    
    broadcast_message()
