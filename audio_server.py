import pyaudio
import socket
import threading

# Audio stream parameters
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
CHUNK = 1024

def print_ascii_art():
    print("""
 _____       _ _     _____               
|  _  |_ _ _| |_|___|   __|___ ___ _ _   
|     | | | . | | . |__   | -_|  _| | |  
|__|__|___|___|_|___|_____|___|_|   _/   
                                         

    """
    )

class AudioStreamer:
    def __init__(self, output_ips, output_port):
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.output_ips = output_ips
        self.output_port = output_port
        self.sockets = [socket.socket(socket.AF_INET, socket.SOCK_DGRAM) for _ in output_ips]

        self.paused = False
        self.terminate = False
        self.lock = threading.Lock()

    def start_stream(self):
        try:
            vb_cable_index = self.get_vb_cable_index()

            self.stream = self.p.open(format=FORMAT,
                                      channels=CHANNELS,
                                      rate=RATE,
                                      input=True,
                                      frames_per_buffer=CHUNK,
                                      input_device_index=vb_cable_index)

            while not self.terminate:
                with self.lock:
                    if not self.paused:
                        data = self.stream.read(CHUNK)
                        for sock in self.sockets:
                            for ip in self.output_ips:
                                sock.sendto(data, (ip, self.output_port))
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            self.p.terminate()
            for sock in self.sockets:
                sock.close()

    def get_vb_cable_index(self):
        device_count = self.p.get_device_count()

        for i in range(device_count):
            device_info = self.p.get_device_info_by_index(i)
            if "CABLE Output" in device_info['name']:
                return i

        raise ValueError("Failed to find the VB-Cable audio device")

    def pause_resume(self):
        self.paused = not self.paused

    def stop(self):
        self.terminate = True

def print_menu():
    print("\n=== Audio Streamer Menu ===")
    print("1. Pause/Resume")
    print("2. Exit")
    print("===========================")

def main():
    print_ascii_art()  # Print the ASCII art message

    try:
        # Directly assume unicast mode
        num_ips = int(input("Enter the number of target IP addresses: "))

        if num_ips <= 0:
            raise ValueError("Number of IP addresses must be greater than 0.")

        output_ips = []
        for i in range(num_ips):
            ip = input(f"Enter IP address {i + 1}: ").strip()
            output_ips.append(ip)

        output_port = 12345

        audio_streamer = AudioStreamer(output_ips, output_port)
        stream_thread = threading.Thread(target=audio_streamer.start_stream)
        stream_thread.start()

        while True:
            print_menu()
            choice = input("Enter your choice: ")

            if choice == '1':
                audio_streamer.pause_resume()
                if audio_streamer.paused:
                    print("Audio stream paused.")
                else:
                    print("Audio stream resumed.")
            elif choice == '2':
                audio_streamer.stop()
                break
            else:
                print("Invalid choice. Please enter a valid option.")

        stream_thread.join()

    except Exception as e:
        print(f"Exception: {e}")
    finally:
        pass  # Socket cleanup is handled within AudioStreamer

if __name__ == "__main__":
    main()
