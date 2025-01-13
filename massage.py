import struct

cookie = 0xabcddcba #cookie for the massage 4 bytes

class Offer:
    def __init__(self,udp_port,tcp_port):
        self.cookie = cookie
        self.massage_type = 0x2
        self.server_udp_port = udp_port
        self.server_tcp_port = tcp_port
        

    def create_offer(self):
        return struct.pack('!IBHH',self.cookie,self.massage_type,self.server_udp_port,self.server_tcp_port) #4 bytes 1 byte 2 bytes 2 bytes

class Request:
    def __init__(self,file_size):
        self.cookie = cookie
        self.massage_type = 0x1
        self.file_size = file_size

    def create_request(self):
        return struct.pack('!IBQ',self.cookie,self.massage_type,self.file_size) 
    
class payload:
    def __init__(self,total_segment_count,current_segment,payload_data):
        self.cookie = cookie
        self.massage_type = 0x4
        self.total_segment_count = total_segment_count
        self.current_segment = current_segment
        self.payload_data = payload_data

    def create_payload(self):
        return struct.pack('!IBQQQ',self.cookie,self.massage_type,self.total_segment_count,self.current_segment,self.payload_data) #4 bytes 1 byte 8 bytes 8 bytes 8 bytes


def create_offer(udp_port:int,tcp_port : int):
    if not (0 <= udp_port <= 65535) or not (0 <= tcp_port <= 65535):
        raise ValueError("Port numbers must be in the range 0-65535")
    offer = Offer(udp_port,tcp_port)
    return offer.create_offer()

def create_request(file_size:int):
    if not isinstance(file_size, int):
        raise ValueError("File size must be an integer")
    if not (0 <= file_size < 2**64):
        raise ValueError("File size must be a 64-bit integer (0 <= file_size < 2^64)")
    request = Request(file_size)
    return request.create_request()

def create_payload(total_segment_count : int, current_segment : int, payload_data : str):  
    
    if not (0 <= total_segment_count < 2**64) or not (0 <= current_segment < 2**64) or not (0 <= payload_data < 2**64):
        raise ValueError("Segment count and current segment must be 64-bit integers (0 <= total_segment_count, current_segment < 2^64)")
    if not isinstance(total_segment_count, int) or not isinstance(current_segment, int):
        raise ValueError("Segment count and current segment must be integers")
    payload = payload(total_segment_count,current_segment,payload_data)
    return payload.create_payload()

def parse_offer(offer_massage):
    cookie, massage_type, server_udp_port, server_tcp_port = struct.unpack('!IBHH', offer_massage)
    if cookie != cookie:
        raise ValueError("Invalid cookie")
    if massage_type != 0x2:
        raise ValueError("Invalid massage type")
    return server_udp_port, server_tcp_port
