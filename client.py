import socket
import massage
info = {"ip_server": "", 'port': 12345, "buffer": 1024, "tcp_socket": None}

def get_user_preferences():
    print("Good day, sir or madam! Might I trouble you to kindly provide the following details regarding your download preferences?")

    try:
        file_size = input("Would you be so kind as to specify the desired file size (for example, '1GB' or '500MB')? ").strip()
        tcp_connections = int(input("How many TCP connections would you deem appropriate for this task, sir or madam? (e.g., '1'): ").strip())
        udp_connections = int(input("And how many UDP connections would you prefer to utilise, if it's not too much trouble? (e.g., '2'): ").strip())
        print("\nExcellent choice, sir or madam! Your preferences have been duly noted.")
        return {
            "file_size": file_size,
            "tcp_connections": tcp_connections,
            "udp_connections": udp_connections,
        }
    except ValueError:
        print("I beg your pardon, but it appears there was an error with the input, sir or madam. Could you kindly verify your entries? Let us try again.")
        return get_user_preferences()


def listen_for_broadcast():
    # Create a UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Allow multiple clients to bind to this port
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind to all network interfaces and the specified port
    client_socket.bind(('', info['port']))
    
    print(f"“Client started, listening for offer requests...")
    message, address = client_socket.recvfrom(info["buffer"])
    print(message)
    try:
        info["server_tcp_port"],info["server_udp_port"] = massage.parse_offer(message)
        print(info["server_tcp_port"],info["server_udp_port"])
        print(f"Received offer from {address}")
        client_socket.close()
        return address
    except ValueError:
        print(f"Received unknown message: {message}")   
        client_socket.close()
 
def send_data_server():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((info["ip_server"], info["port"]))
    client_socket.sendall(massage.create_request(info["file_size"]))
    print(f"Sent request for file size {info['file_size']} to server {info['ip_server']}")
    response = client_socket.recv(info["buffer"])
    print(f"Received response: {response}")
    client_socket.close()


def create_tcp_massage():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((info["ip_server"], info["port"]))
    

if __name__ == "__main__":
    user_preferences = get_user_preferences()
    info.update(user_preferences)
    info["ip_server"] = listen_for_broadcast()
    


