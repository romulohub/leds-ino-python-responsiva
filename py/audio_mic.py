import pyaudio
import numpy as np
import socket
import time
from zeroconf import Zeroconf, ServiceBrowser, ServiceListener
from tkinter import *
from tkcolorpicker import askcolor
import threading

# Default color (RGB)
LED_COLOR = (100, 0, 255)
running = False

class ESPListener(ServiceListener):
    def __init__(self):
        self.esp_ip = None
        self.esp_port = None
        self.esp_found = False

    def add_service(self, zc, type_, name):
        info = zc.get_service_info(type_, name)
        if info:
            self.esp_ip = info.parsed_addresses()[0]
            self.esp_port = 7778
            self.esp_found = True
            print(f"ESP Mic found: {self.esp_ip}:{self.esp_port}")

def stop_capture():
    global running
    running = False

def send_audio_data(socket, esp_ip, esp_port, volume, low, mid, high):
    # Pack volume, frequencies and color into bytes
    data = bytes([
        int(volume),  # Volume
        int(low),     # Low freq
        int(mid),     # Mid freq
        int(high),    # High freq
        LED_COLOR[0], # Red
        LED_COLOR[1], # Green
        LED_COLOR[2]  # Blue
    ])
    socket.sendto(data, (esp_ip, esp_port))

def update_color_display(color_frame):
    hex_color = f'#{LED_COLOR[0]:02x}{LED_COLOR[1]:02x}{LED_COLOR[2]:02x}'
    color_frame.configure(bg=hex_color)

def choose_color(color_frame):
    global LED_COLOR
    color = askcolor(color=f'#{LED_COLOR[0]:02x}{LED_COLOR[1]:02x}{LED_COLOR[2]:02x}', title="Choose LED Color")
    if color[0] is not None:
        LED_COLOR = (int(color[0][0]), int(color[0][1]), int(color[0][2]))
        update_color_display(color_frame)

def toggle_audio(btn):
    global running
    running = not running
    btn.config(text="Stop Audio" if running else "Start Audio")
    if running:
        threading.Thread(target=start_audio_capture, daemon=True).start()

def start_audio_capture():
    global running
    # Configurações
    CHUNK = 2048
    FORMAT = pyaudio.paFloat32
    CHANNELS = 1
    RATE = 44100
    
    # Configuração do UDP
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Procura ESP
    zeroconf = Zeroconf()
    listener = ESPListener()
    browser = ServiceBrowser(zeroconf, "_esp8266-mic._udp.local.", listener)
    
    # Aguarda encontrar o ESP
    while not listener.esp_found:
        print("Procurando ESP...")
        time.sleep(1)
    
    # Configuração do PyAudio
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                   channels=CHANNELS,
                   rate=RATE,
                   input=True,
                   frames_per_buffer=CHUNK)
    
    print("Capturando áudio...")
    
    try:
        while running:
            # Lê dados do microfone
            data = np.frombuffer(stream.read(CHUNK), dtype=np.float32)

            # Calcula volume (0-255)
            volume = int(np.abs(data).mean() * 255 * 5)  # *5 para amplificar
            volume = min(255, volume)  # Limita a 255
            
            # Calcula FFT
            fft = np.abs(np.fft.fft(data)[:CHUNK//2])
            
            # Divide em 3 bandas de frequência
            # Adapte estes índices conforme necessário
            low_freq = int(np.mean(fft[0:20]) * 255)  # Graves
            mid_freq = int(np.mean(fft[20:50]) * 255)  # Médios
            high_freq = int(np.mean(fft[50:200]) * 255)  # Agudos
            
            # Limita valores entre 0-255
            low_freq = min(255, low_freq)
            mid_freq = min(255, mid_freq)
            high_freq = min(255, high_freq)
            
            # Envia os 4 parâmetros
            send_audio_data(udp_socket, listener.esp_ip, listener.esp_port, volume, low_freq, mid_freq, high_freq)
            
            # Debug
            print(f"Volume: {volume}")
            
            if not running:
                stream.stop_stream()
                stream.close()
                break
            
            time.sleep(0.001)  # Prevent CPU overload
            
    except KeyboardInterrupt:
        print("Encerrando...")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        zeroconf.close()

def main_menu():
    root = Tk()
    root.title("LED Audio Control")
    root.geometry("500x300")

    # Left Frame - Color Controls
    left_frame = Frame(root, width=250)
    left_frame.pack(side=LEFT, fill=Y, padx=10, pady=10)
    
    color_display = Frame(left_frame, width=200, height=100, bg='#%02x%02x%02x' % LED_COLOR)
    color_display.pack(pady=10)
    
    Button(left_frame, text="Choose Color", 
           command=lambda: choose_color(color_display)).pack(pady=10)

    # Right Frame - Audio Controls
    right_frame = Frame(root, width=250)
    right_frame.pack(side=RIGHT, fill=Y, padx=10, pady=10)
    
    audio_btn = Button(right_frame, text="Start Audio")
    audio_btn.config(command=lambda: toggle_audio(audio_btn))
    audio_btn.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main_menu()