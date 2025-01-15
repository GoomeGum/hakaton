import socket
import threading
from timeit import timeit
import packet_formats
import yaml
import handler
import time
info = {}
packet_factory = packet_formats.PacketFactory("configs/configs.yaml")


def read_yaml(yaml_path):
    with open(yaml_path, 'r') as file:
        info.update(yaml.safe_load(file))

def get_user_preferences():
    print("Good day, sir or madam! Might I trouble you to kindly provide the following details regarding your download preferences?")

    try:
        file_size,unit = handler.check_file_size(input("Would you be so kind as to specify the desired file size (for example, '1GB' or '500MB') where the defualt is MB ? ").strip())
        
        tcp_connections = int(input("How many TCP connections would you deem appropriate for this task, sir or madam? (e.g., '1'): ").strip())
        udp_connections = int(input("And how many UDP connections would you prefer to utilise, if it's not too much trouble? (e.g., '2'): ").strip())
        print("\nExcellent choice, sir or madam! Your preferences have been duly noted.")
        info.update( {
           "connection_info": {
        "file_size": handler.get_file_size(unit, file_size),
        "tcp_connections": tcp_connections,
        "udp_connections": udp_connections,
        }})
    except ValueError:
        print("I beg your pardon, but it appears there was an error with the input, sir or madam. Could you kindly verify your entries? Let us try again.")
        return get_user_preferences()


def listen_for_broadcast():
    # Create a UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Allow multiple clients to bind to this port
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind to all network interfaces and the specified port
    client_socket.bind(('', info['client']['broadcast_port']))
    
    print(f"“Client started, listening for offer requests...")
    message, address = client_socket.recvfrom(info['general']['buffer_size'])
    ip_address, _ = address
    try:
        parsed_msg = packet_factory.parse_message(message)
        if parsed_msg["message_type"] == info["offer"]["message_type"]:
            server_udp_port = parsed_msg["server_udp_port"]
            server_tcp_port = parsed_msg["server_tcp_port"]
            info["connection_info"].update({
                    "server_tcp_port": server_tcp_port,
                    "server_udp_port": server_udp_port,
                
            })
            print(f"Received offer from {ip_address}")
            client_socket.close()
            info["connection_info"]["ip_server"] = ip_address
    except ValueError:
        print(f"Received unknown message: {message}")   
        client_socket.close()
 
def tcp_thread(threadNum):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((info["connection_info"]["ip_server"], info["connection_info"]["server_tcp_port"]))
    request =  packet_factory.build_message('request' ,file_size = info["connection_info"]["file_size"])
    client_socket.sendall(request)
    print(f"tcp: Sent request for file size {info["connection_info"]['file_size']} to server {info["connection_info"]['ip_server']}")
    received_data = b""  # Data received from the server
    start_time = time.time()

    while True:
        if(len(received_data) >= info["connection_info"]['file_size'] ):
            break
        chunk = client_socket.recv(info['general']['buffer_size'])
        try:
            parsed_msg =  packet_factory.parse_message(chunk)
        except handler.EmptyMessageException:
            print("received empty message")
            handler.save_bytes_to_text_file(info['files']['output_file_tcp'], received_data)
            break
        if parsed_msg["message_type"] == info["payload"]["message_type"]: 
            print(f"Received payload segment {parsed_msg['current_segment']+1} of {parsed_msg['total_segment_count']} from server {info['connection_info']['ip_server']}")
            received_data += parsed_msg['payload_data']
            if parsed_msg['current_segment'] >= parsed_msg['total_segment_count'] - 1:
                break
    print(f"Received file size {len(received_data)} from server {info['connection_info']['ip_server']}")
    handler.save_bytes_to_text_file(info['files']['output_file_tcp'], received_data)
    client_socket.close()
    end_time = time.time()
    print(f"TCP transfer #{threadNum} finished, total time: {end_time - start_time:.2f} seconds, "
          f"total speeed:{len(received_data)*8 / (end_time - start_time):.2f} bps")    

   
def udp_thread(threadNum):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (info["connection_info"]["ip_server"], info["connection_info"]["server_udp_port"])
    client_socket.settimeout(info["client"]["timeout_udp"])
    request =  packet_factory.build_message('request' ,file_size = info["connection_info"]["file_size"])
    client_socket.sendto(request, server_address)
    print(f"udp: Sent request for file size {info["connection_info"]['file_size']} to server {info["connection_info"]['ip_server']}")
    received_data = b""  # Data received from the server
    start_time = time.time()
    count_packets = 0
    total_segment_count = 0
    while True:
        if(len(received_data) >= info["connection_info"]['file_size']):
            break
        try:
            chunk, _ = client_socket.recvfrom(info['general']['buffer_size'])
            if not chunk:
                break
            parsed_msg =  packet_factory.parse_message(chunk)
        except socket.timeout:
            print("No data received for 1 second. Closing transmission.")
            handler.save_bytes_to_text_file(info['files']['output_file_udp'], received_data)
            break
        except handler.EmptyMessageException:
            print("received empty message")
            handler.save_bytes_to_text_file(info['files']['output_file_udp'], received_data)
            break
        
        if parsed_msg["message_type"] == info["payload"]["message_type"]: 
            print(f"Received payload segment {parsed_msg['current_segment']+1} of {parsed_msg['total_segment_count']} from server {info["connection_info"]['ip_server']}")
            received_data += parsed_msg['payload_data']
            count_packets += 1
            total_segment_count = parsed_msg['total_segment_count']
            if parsed_msg['current_segment'] >= total_segment_count - 1:
                break

    print(f"Received file size {len(received_data)} from server {info['connection_info']['ip_server']}")
    handler.save_bytes_to_text_file(info['files']['output_file_udp'], received_data)

    client_socket.close()
    end_time = time.time()  
    print(f"UDP transfer #{threadNum} finished, total time: {end_time - start_time:.2f} "
      f"seconds, total speed: {len(received_data) * 8 / (end_time - start_time):.2f} bps") 
    print(f"Percentage of packets received successfully: {count_packets / total_segment_count:.2%}")


if __name__ == "__main__":
    data = read_yaml("configs/configs.yaml")
    get_user_preferences()
    count = 1
    while count<=1:
        listen_for_broadcast()
        tcp_connections = info["connection_info"]["tcp_connections"]
        udp_connections = info["connection_info"]["udp_connections"]
        threads = []
        threadNum = 1
        for i in range(tcp_connections):
            threads.append(threading.Thread(target=tcp_thread, args=(threadNum,)))
            threadNum += 1
        for i in range(udp_connections):
            threads.append(threading.Thread(target=udp_thread, args=(threadNum,)))
            threadNum += 1
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        print("All transfers completed.")
        count += 1




    


