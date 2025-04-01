# Audio Visualizer Project

Este projeto implementa um visualizador de áudio que captura o áudio do dispositivo e envia dados para um ESP, controlado por uma interface gráfica feita com Flet.

## Estrutura do Projeto

- **py/audio_ui.py**  
  Responsável pela interface do usuário.  
  **Imports:**  
  - `flet as ft`  
  - `from audio_computer import ESPListener, main as audio_main, stop_capture, turn_off_leds`  
  - `threading`

- **py/audio_computer.py**  
  Responsável pela captura e processamento de áudio e envio para o ESP.  
  **Imports:**  
  - `time`  
  - `numpy as np`  
  - `pyaudiowpatch as pyaudio`  
  - `socket`  
  - `from zeroconf import Zeroconf, ServiceBrowser, ServiceListener`  
  - `sys`

- **arduino/arduino_audio/arduino_audio.ino**  
  Código para o ESP8266 que controla os LEDs com base nos dados recebidos via UDP.  
  **Bibliotecas Utilizadas:**  
  - `FastLED.h`  
  - `ESP8266WiFi.h`  
  - `WiFiUdp.h`  
  - `ESP8266mDNS.h`  

  **Principais Funcionalidades:**  
  - Conexão WiFi e configuração de mDNS para descoberta do dispositivo na rede.  
  - Recepção de pacotes UDP contendo informações de volume, frequências (graves, médios, agudos) e o efeito selecionado.  
  - Implementação de diferentes efeitos visuais para os LEDs, como:
    - **WAVE:** Expansão de cores a partir do centro com base no volume e frequências.  
    - **SPEED:** Efeito dinâmico com cores baseadas nas frequências.  
    - **RAINBOW:** Ondas coloridas que se movem pelos LEDs.  
    - **SNAKE:** Efeito de "cobras" coloridas que se expandem a partir do centro.  
    - **SCROLL:** Expansão de cores com histórico de frequências.  

## Dependências

Para instalar as bibliotecas necessárias no Python, use:

```bash
pip install flet numpy pyaudiowpatch zeroconf