import socket
import threading
import time
import packet_formats
import yaml
import handler
info = {}
packet_factory = packet_formats.PacketFactory("configs/configs.yaml")

def read_yaml(yaml_path):
    with open(yaml_path, 'r') as file:
        info.update(yaml.safe_load(file))
    
def send_broadcast_message():
    
    # Create a UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Enable broadcasting mode
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    broadcast_address = (info["server"]["broadcast_ip"], info["server"]["broadcast_port"])
    offer_packet = packet_factory.build_message('offer',udp_port=info["server"]["udp_port"],tcp_port=info["server"]["tcp_port"])

    try:
        while True:
            server_socket.sendto(offer_packet, broadcast_address)
            time.sleep(2)  # Broadcast every 2 seconds
    except KeyboardInterrupt:
        print("Broadcast stopped.")
    finally:
        server_socket.close()

def tcp():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', info["server"]["tcp_port"]))
    server_socket.listen(info["server"]["tcp_backlog"])
    while True:
        connection_socket, address = server_socket.accept()
        print(f"Connection established with {address}")
        chunk = connection_socket.recv(info['general']['buffer_size'])
        try:
            parsed_msg = packet_factory.parse_message(chunk)
            if parsed_msg["message_type"] == info["request"]["message_type"]:
                file_size = parsed_msg["file_size"]
                print(f"Received request for file size {file_size} from {address}")
                total_segment_count, real_size = handler.calculate_segments(file_size,info["server"]["file_to_send"] ,info['general']['buffer_size'])
                current_segment = 0
                sent_data_len = 0
                while current_segment < total_segment_count:
                    buffer_to_read = handler.read_size(info,real_size,sent_data_len)
                    if(buffer_to_read == 0):
                        print("the file is smaller then asked, sending what we have")
                        break 
                    payload_data = handler.get_file_segment(info['server']['file_to_send'], buffer_to_read , sent_data_len)
                    sent_data_len += len(payload_data)
                    response = packet_factory.build_message('payload',total_segment_count=total_segment_count,current_segment=current_segment,payload_data=payload_data)
                    connection_socket.sendall(response)
                    print(f"Sent payload segment {current_segment+1} of {total_segment_count} to {address}")
                    current_segment += 1
                print(f"Sent file size {real_size} to {address}")
                connection_socket.close()
        except ValueError:
            print(f"Received unknown message: {chunk}")
        connection_socket.close()


def udp():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('', info["server"]["udp_port"]))
    while True:
        try:
            chunk, address = server_socket.recvfrom(info['general']['buffer_size'])
            parsed_msg = packet_factory.parse_message(chunk)
        except ValueError:
            print(f"Received unknown message: {chunk}")
            break
        if parsed_msg["message_type"] == info["request"]["message_type"]:
            file_size = parsed_msg["file_size"]
            print(f"Received request for file size {file_size} from {address}")
            total_segment_count, real_size = handler.calculate_segments(file_size,info["server"]["file_to_send"] ,info['general']['buffer_size'])
            current_segment = 0
            sent_data_len = 0
            while current_segment < total_segment_count:
                buffer_to_read = handler.read_size(info,real_size,sent_data_len)
                if(buffer_to_read == 0):
                    print("the file is smaller then asked, sending what we have")
                    break 
                payload_data = handler.get_file_segment(info['server']['file_to_send'], buffer_to_read , sent_data_len)
                sent_data_len += len(payload_data)
                response = packet_factory.build_message('payload',total_segment_count=total_segment_count,current_segment=current_segment,payload_data=payload_data)
                server_socket.sendto(response, address)
                print(f"Sent payload segment {current_segment+1} of {total_segment_count} to {address}")
                current_segment += 1
            
            print(f"Sent file size {real_size} to {address}")
        
    server_socket.close()
        #server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #server_socket.bind(('', info["server"]["udp_port"]))



def run_in_threads():
    # Create thread objects for both functions
    broadcast_thread = threading.Thread(target=send_broadcast_message)
    tcp_thread_obj = threading.Thread(target=tcp)
    udp_thread_obj = threading.Thread(target=udp)
    # Start both threads
    broadcast_thread.start()
    tcp_thread_obj.start()
    udp_thread_obj.start()

    # Wait for both threads to finish
    broadcast_thread.join()
    tcp_thread_obj.join()
    udp_thread_obj.join()  

if __name__ == "__main__":
    local_ip = socket.gethostbyname(socket.gethostname())
    print(f"Server started, listening on IP address {local_ip}")
    read_yaml("configs/configs.yaml")
    run_in_threads()

  
