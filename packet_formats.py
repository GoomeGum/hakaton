import struct
import yaml

from handler import EmptyMessageException


def _load_yaml(yaml_path):
    """Reads the YAML file and returns the parsed data."""
    with open(yaml_path, 'r') as file:
        return yaml.safe_load(file)


class Packet:
    """Base class for all message types."""
    def __init__(self, message_type):
        self.cookie = _load_yaml("configs/configs.yaml")['general']['cookie']
        self.message_type = message_type

    def create_message(self,**kwargs):
        raise NotImplementedError("Subclasses must implement create_message")
    

class Offer(Packet):
    def __init__(self,message_type, udp_port, tcp_port):
        super().__init__(message_type)
        self.server_udp_port = udp_port
        self.server_tcp_port = tcp_port

    def create_message(self):
        return struct.pack('!IBHH', self.cookie, self.message_type, self.server_udp_port, self.server_tcp_port)
    
 
class Request(Packet):
    def __init__(self, file_size, message_type):
        super().__init__(message_type)
        self.file_size = int(file_size)

    def create_message(self):
        return struct.pack('!IBQ', self.cookie, self.message_type, self.file_size)


class Payload(Packet):
    def __init__(self, total_segment_count, current_segment, payload_data,message_type):
        super().__init__(message_type)
        self.total_segment_count = total_segment_count
        self.current_segment = current_segment
        self.payload_data = payload_data

    def create_message(self):
        payload_size = len(self.payload_data)
        return struct.pack(f'!IBQQ{payload_size}s', self.cookie, self.message_type, self.total_segment_count, self.current_segment, self.payload_data)
    
class PacketFactory:
    """Factory class to create messages."""
    def __init__(self, yaml_path):
        self.config = _load_yaml(yaml_path)
        self.cookie = self.config['general']['cookie']  
  
    def _create_offer(self,msg_type,**kwargs):
        udp_port = kwargs.get('udp_port')
        tcp_port = kwargs.get('tcp_port')
        if udp_port is None or tcp_port is None:
            raise ValueError("udp_port and tcp_port must be provided for offer message")
        if not (0 <= udp_port <= 65535) or not (0 <= tcp_port <= 65535):
            raise ValueError("Port numbers must be in the range 0-65535")
        return Offer(msg_type, udp_port, tcp_port).create_message()
    def _check_file_size(self,file_size):
        return file_size<2**(8*self.config['request']['max_file_size_bytes'])
    def _create_request(self,msg_type,file_size):
        if not self._check_file_size(file_size):
            raise ValueError(f"File size exceeds the maximum allowed byte size of 8. Current byte size: {file_size}")
        return Request(file_size,msg_type).create_message()
    
    def _create_payload(self,message_type,total_segment_count,current_segment,payload_data):
        if not (0 <= total_segment_count < 2**64) or not (0 <= current_segment < 2**64) or not (0 <= len(payload_data) < 2**64):
            raise ValueError("Segment count and current segment must be 64-bit integers (0 <= total_segment_count, current_segment < 2^64)")
        if not isinstance(total_segment_count, int) or not isinstance(current_segment, int):
            raise ValueError("Segment count and current segment must be integers")
        return Payload(total_segment_count,current_segment,payload_data,message_type).create_message()
    
    def _parse_request(self, message):
        cookie, message_type, file_size = struct.unpack('!IBQ', message)
        if cookie != self.cookie:
            raise ValueError("Invalid cookie")
        return {
            "message_type": message_type,
            "file_size": file_size,
        }    
    
    def _parse_payload(self, message):
        fixed_fields = struct.unpack('!IBQQ', message[:self.config['payload']['header_size']])  # First 21 bytes correspond to the fixed fields
        cookie, message_type, total_segment_count, current_segment = fixed_fields
        
        # Extract the payload data using the payload size
        payload_data = message[self.config['payload']['header_size']:]  # The rest is the payload data
        if cookie != self.cookie:
            raise ValueError("Invalid cookie")
        return {
            "message_type": message_type,
            "total_segment_count": total_segment_count,
            "current_segment": current_segment,
            "payload_data": payload_data,
        }
    
    def _parse_offer(self, message):
        cookie, message_type, server_udp_port, server_tcp_port = struct.unpack('!IBHH', message)
        if cookie != self.cookie:
            raise ValueError("Invalid cookie")
        return{
            "message_type": message_type,
            "server_udp_port": server_udp_port,
            "server_tcp_port": server_tcp_port,
        }

    
    def parse_message(self, message):
        if(len(message) < 5):
            raise EmptyMessageException()
        message_type = message[4]
        if message_type == self.config['offer']['message_type']:
            return self._parse_offer(message)
        elif message_type == self.config['request']['message_type']:
            return self._parse_request(message)
        elif message_type == self.config['payload']['message_type']:
            return self._parse_payload(message)
        else:
            raise ValueError("Invalid message type")

    def build_message(self, message_type, **kwargs):
        data = self.config.get(message_type, {})
        message_type_sig = data.get('message_type')

        if message_type == 'offer':           
            return self._create_offer(message_type_sig, **kwargs)
        elif message_type == 'request':
            return self._create_request(message_type_sig, kwargs.get('file_size'))
        elif message_type == 'payload':
            return self._create_payload(message_type_sig, kwargs.get('total_segment_count'), kwargs.get('current_segment'), kwargs.get('payload_data'))
        else:
            raise ValueError("Invalid message type")
    