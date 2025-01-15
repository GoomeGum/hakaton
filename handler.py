import os
import re
import sys
import yaml

def check_file_size(file_size):
    # Regular expression pattern to match a number followed by GB, MB, or B
    pattern = r"(\d+)(GB|MB|KB|B)?"
    match = re.fullmatch(pattern, file_size)
    
    if match:
        number = match.group(1)
        unit = match.group(2) if match.group(2) else "MB"  # Default to "MB" if no unit is provided
        return int(number), unit
    else:
        raise ValueError("Invalid file size format. Please provide a number followed by GB, MB (defualt), KB, or B.")


def get_send_file_size(file_path):
    try:
        file_size = os.path.getsize(file_path)
        return file_size
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def calculate_segments(file_size_in_bytes,file_to_send,buffer_size):
    file_size = get_send_file_size(file_to_send)
    real_size = min(file_size_in_bytes, file_size)
    print(f"File size: {real_size} bytes")
    num_segments = real_size // buffer_size
    if real_size % buffer_size != 0:
        num_segments += 1
    return num_segments, real_size

def get_file_size(unit, file_size):
    # Define conversion rates for different units
    unit_to_bytes = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 ** 2,
        'GB': 1024 ** 3
    }
    if unit not in unit_to_bytes:
        raise ValueError(f"Invalid unit: {unit}. Valid units are 'B', 'KB', 'MB', 'GB'.")

    file_size_in_bytes = file_size * unit_to_bytes[unit]
    return file_size_in_bytes

def get_file_segment(file_name, segment_size, start_byte):
    with open(file_name, 'rb') as file:
        file.seek(start_byte)
        segment_data = file.read(segment_size)
        return segment_data


class EmptyMessageException(Exception):
    """Exception raised for empty messages."""
    def __init__(self, message="The message is empty."):
        self.message = message
        super().__init__(self.message)


def save_bytes_to_text_file(file_path: str, received_data: bytes):
    """Saves received bytes data to a text file."""
    try:
        text_data = received_data.decode('utf-8')
    
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(text_data)
        print(f"Data saved to {file_path}")
    except UnicodeDecodeError:
        print("Error: Unable to decode the received data. Ensure it is UTF-8 encoded.")
    except Exception as e:
        print(f"An error occurred: {e}")

def read_yaml(file_path):
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    return data

def read_size(info,file_size,sent_data_len):
    buffer_size = int(info['general']['buffer_size'])
    header_size = int(info['payload']['header_size'])
    remaining_data = max(0, file_size - sent_data_len)
    effective_buffer_size = max(0, buffer_size - header_size)
    buffer_to_read = min(effective_buffer_size, remaining_data)
    return buffer_to_read

def wait_for_exit():
    try:
        print("Program is running. Press Ctrl+C to exit.")
        while True:
            pass  # Keeps the program running indefinitely
    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected. Closing the program.")
        sys.exit(0)  # Exit the program with a success status code