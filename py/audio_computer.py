import time
import numpy as np
import pyaudiowpatch as pyaudio
import socket
from zeroconf import Zeroconf, ServiceBrowser, ServiceListener
import sys

class ESPListener(ServiceListener):
    def __init__(self):
        self.esp_found = False
        self.esp_ip = None
        self.esp_port = 7778

    def add_service(self, zc, type_, name):
        info = zc.get_service_info(type_, name)
        if info:
            self.esp_ip = info.parsed_addresses()[0]
            self.esp_port = 7778
            self.esp_found = True
            print(f"ESP encontrado: {self.esp_ip}")

def find_default_output_device(p):
    """Encontra o dispositivo de saída padrão."""
    try:
        wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
    except OSError:
        print("WASAPI não disponível. Saindo...")
        p.terminate()
        sys.exit()

    default_output_device_index = wasapi_info["defaultOutputDevice"]
    default_output_device = p.get_device_info_by_index(default_output_device_index)

    if not default_output_device.get("isLoopbackDevice", False):
        for device in p.get_loopback_device_info_generator():
            if default_output_device["name"] in device["name"]:
                default_output_device = device
                break
        else:
            print("Dispositivo loopback padrão não encontrado. Saindo...")
            p.terminate()
            sys.exit()

    return default_output_device

running = True

def stop_capture():
    global running
    running = False

def turn_off_leds(listener):
    try:
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Send all zeros to turn off LEDs
        buffer = bytearray([0, 0, 0, 0])
        udp_socket.sendto(buffer, (listener.esp_ip, listener.esp_port))
        udp_socket.close()
    except Exception as e:
        print(f"Error turning off LEDs: {e}")

def main(effect_getter=lambda: 0):
    global running
    running = True

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    zeroconf = Zeroconf()
    listener = ESPListener()
    # Replace the generic UDP service with specific one
    browser = ServiceBrowser(zeroconf, "_led-audio._udp.local.", listener)
    
    while not listener.esp_found:
        print("Procurando ESP...")
        time.sleep(1)
    
    p = pyaudio.PyAudio()
    default_output_device = find_default_output_device(p)
    print(f"Capturando de: ({default_output_device['index']}) {default_output_device['name']}")

    CHUNK = 1024  # Tamanho do buffer
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 48000

    try:
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        input_device_index=default_output_device['index'],
                        frames_per_buffer=CHUNK)
    except OSError as e:
        print(f"Erro ao abrir o stream: {e}")
        p.terminate()
        sys.exit()

    print("Capturando áudio...")

    try:
        while running:
            data = np.frombuffer(stream.read(CHUNK), dtype=np.int16)
            data = data.astype(np.float32)

            # Calcular a FFT
            fft_data = np.fft.fft(data)
            fft_magnitude = np.abs(fft_data)

            # Dividir em bandas de frequência
            low_freq = np.mean(fft_magnitude[0:10])  # Graves
            mid_freq = np.mean(fft_magnitude[10:30])  # Médios
            high_freq = np.mean(fft_magnitude[30:50])  # Agudos

            # Normalizar as frequências para o intervalo de 0 a 255
            low_freq = min(max(int(low_freq / 8000), 0), 255)  # Aumentar o divisor
            mid_freq = min(max(int(mid_freq / 2500), 0), 255)  # Aumentar o divisor
            high_freq = min(max(int(high_freq / 2500), 0), 255)  # Aumentar o divisor

            # Calcular volume total
            volume = int(np.abs(data).mean() * 255 * 2)  # Reduzir o fator de amplificação
            volume = min(255, volume)  # Limita a 255
            
            # Enviar para o ESP
            current_effect = effect_getter()  # Get current effect value
            buffer = bytearray([volume, low_freq, mid_freq, high_freq, current_effect])  # Adicione um byte extra ao enviar os dados
            udp_socket.sendto(buffer, (listener.esp_ip, listener.esp_port))
            
            # Debug
            #print(f"Volume: {volume}, Graves: {low_freq}, Médios: {mid_freq}, Agudos: {high_freq}")
            #time.sleep(0.01)  # Pequeno delay para evitar sobrecarga de CPU
            
            if not running:
                stream.stop_stream()
                stream.close()
                break
            
    except KeyboardInterrupt:
        print("Encerrando...")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        zeroconf.close()

if __name__ == "__main__":
    main()