from zeroconf import Zeroconf, ServiceBrowser, ServiceListener
import socket
import time

class ESPListener(ServiceListener):
    def __init__(self):
        self.esp_found = False
        self.esp_ip = None
        self.esp_port = None

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            self.esp_ip = info.parsed_addresses()[0]
            self.esp_port = info.port
            self.esp_found = True
            print(f"\nDispositivo ESP encontrado!")
            print(f"IP: {self.esp_ip}")
            print(f"Porta: {self.esp_port}")

def main():
    print("Procurando ESP8266...")
    zeroconf = Zeroconf()
    listener = ESPListener()
    browser = ServiceBrowser(zeroconf, "_udp._udp.local.", listener)
    
    try:
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        while not listener.esp_found:
            print(".", end="", flush=True)
            time.sleep(1)
        
        print("\nComandos disponíveis:")
        print("0 - Desligar")
        print("1 - Vermelho")
        print("2 - Verde")
        print("3 - Azul")
        print("4 - Rainbow")
        print("5 - Rainbow com Glitter")
        print("6 - Confetti")
        print("7 - Sinelon")
        print("8 - Juggle")
        print("9 - BPM")
        print("q - Sair")
        
        while True:
            comando = input("Digite o comando: ")
            
            if comando.lower() == 'q':
                break
                
            if comando in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                valor = int(comando)
                buffer = bytearray([valor])
                udp_socket.sendto(buffer, (listener.esp_ip, listener.esp_port))
                print(f"Comando {valor} enviado!")
            else:
                print("Comando inválido!")
                
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        print("Encerrando...")
        zeroconf.close()
        udp_socket.close()

if __name__ == "__main__":
    main()
