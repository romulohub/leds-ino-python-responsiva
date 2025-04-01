#include <FastLED.h>
#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
#include <ESP8266mDNS.h>

// Definições LED
#define NUM_LEDS 280
#define DATA_PIN D3

// WiFi
const char* ssid = "nomeredewifi";
const char* password = "senharedewifi";
unsigned int localPort = 7778;  // Porta diferente!

// Variáveis globais
CRGB leds[NUM_LEDS];
WiFiUDP port;

// Variáveis para o efeito de onda
int centerLed = NUM_LEDS / 2;
float smoothedVolume = 0;      // Volume suavizado
const float SMOOTH_FACTOR = 0.8;  // Quanto menor, mais suave (0-1)

// Variáveis para suavização de cores
CRGB currentColor = CRGB::Black;  // Cor atual
CRGB targetColor = CRGB::Black;    // Cor alvo

// No início do arquivo
enum Effect {WAVE, SPEED, RAINBOW, SNAKE, SCROLL};  // Add SCROLL
Effect currentEffect = WAVE;  // Default effect

void setupWiFi() {
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    
    Serial.print("Conectando ao WiFi");
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println();
    Serial.print("Conectado! IP: ");
    Serial.println(WiFi.localIP());
}

// In setupMDNS() function:
void setupMDNS() {
    if (MDNS.begin("esp8266-audio")) {
        Serial.println("mDNS iniciado");
        
        // Use a more specific service name
        MDNS.addService("led-audio", "udp", localPort);
        Serial.println("Serviço UDP LED-Audio registrado");
    } else {
        Serial.println("Erro ao iniciar mDNS!");
    }
}

void setup() {
    Serial.begin(115200);
    Serial.println("\nIniciando Teste Audio LED");
    
    // Inicializa LED
    FastLED.addLeds<WS2812B, DATA_PIN, GRB>(leds, NUM_LEDS);
    FastLED.setBrightness(50);
    FastLED.clear();
    FastLED.show();
    
    // Inicializa WiFi
    setupWiFi();
    
    // Inicializa mDNS
    setupMDNS();
    
    // Inicializa UDP
    port.begin(localPort);
    Serial.printf("UDP escutando na porta %d\n", localPort);
    
    // Pisca LED para indicar que está pronto
    fill_solid(leds, NUM_LEDS, CRGB::Green);
    FastLED.show();
    delay(1000);
    FastLED.clear();
    FastLED.show();
}

CRGB blendColors(CRGB color1, CRGB color2, uint8_t blendAmount) {
    // Interpola entre duas cores
    return CRGB(
        (color1.r * (255 - blendAmount) + color2.r * blendAmount) / 255,
        (color1.g * (255 - blendAmount) + color2.g * blendAmount) / 255,
        (color1.b * (255 - blendAmount) + color2.b * blendAmount) / 255
    );
}

void audioWaveEffect(uint8_t volume, uint8_t lowFreq, uint8_t midFreq, uint8_t highFreq) {
    // Suaviza o volume
    smoothedVolume = (smoothedVolume * (1 - SMOOTH_FACTOR)) + (volume * SMOOTH_FACTOR);
    
    // Limpa LEDs
    FastLED.clear();
    
    // Define cores baseadas nas frequências
    CRGB lowColor = (lowFreq > 50) ? CRGB::Blue : CRGB::Black;  // Graves
    CRGB midColor = (midFreq > 50) ? CRGB::Green : CRGB::Black;  // Médios
    CRGB highColor = (highFreq > 50) ? CRGB::Red : CRGB::Black;  // Agudos

    // Mistura as cores
    CRGB mixedColor = CRGB::Black;
    mixedColor = blend(mixedColor, lowColor, lowFreq);  // Mistura com base na intensidade
    mixedColor = blend(mixedColor, midColor, midFreq);  // Mistura com base na intensidade
    mixedColor = blend(mixedColor, highColor, highFreq);  // Mistura com base na intensidade

    // Suaviza a transição de cores
    targetColor = mixedColor;  // Define a nova cor alvo
    currentColor = blendColors(currentColor, targetColor, 10);  // Suaviza a transição

    // Expande do centro para as extremidades
    leds[centerLed] = currentColor;  // Processa o LED central uma única vez
    leds[centerLed].fadeToBlackBy(255 - map(smoothedVolume, 0, 255, 0, 255));

    for(int offset = 1; offset <= NUM_LEDS/2; offset++) {  // Começa do 1 ao invés de 0
        uint8_t intensity = map(smoothedVolume, 0, 255, 0, 255) * (1.0 - (float)offset / (NUM_LEDS / 2));
        
        if(centerLed + offset < NUM_LEDS) {
            leds[centerLed + offset] = currentColor;
            leds[centerLed + offset].fadeToBlackBy(255 - intensity);
        }
        
        if(centerLed - offset >= 0) {
            leds[centerLed - offset] = currentColor;
            leds[centerLed - offset].fadeToBlackBy(255 - intensity);
        }
    }
    
    FastLED.show();
}

void speedEffect(uint8_t volume, uint8_t lowFreq, uint8_t midFreq, uint8_t highFreq) {
    // Smoothing
    static float smoothedLow = 0;
    static float smoothedMid = 0;
    static float smoothedHigh = 0;
    const float SMOOTH_FACTOR = 0.7;

    smoothedLow = (smoothedLow * SMOOTH_FACTOR) + (lowFreq * (1.0 - SMOOTH_FACTOR));
    smoothedMid = (smoothedMid * SMOOTH_FACTOR) + (midFreq * (1.0 - SMOOTH_FACTOR));
    smoothedHigh = (smoothedHigh * SMOOTH_FACTOR) + (highFreq * (1.0 - SMOOTH_FACTOR));

    // Dynamic colors based on frequencies
    CRGB bassColor = CRGB(
        smoothedLow,  // R
        smoothedMid,  // G
        smoothedHigh  // B
    );
    
    CRGB highColor = CRGB(
        smoothedHigh, // R
        smoothedLow,  // G
        smoothedMid   // B
    );

    // Process edges (0-93 and 187-279)
    static uint8_t wavePos = 0;
    for(int i = 0; i < 93; i++) {
        float waveIntensity = sin((i + wavePos) * 0.2) * 0.5 + 0.5;
        uint8_t brightness = map(smoothedLow * waveIntensity, 0, 255, 0, 200);
    
        leds[i] = bassColor;
        leds[i].fadeToBlackBy(255 - brightness);
    
        leds[NUM_LEDS - 1 - i] = bassColor;
        leds[NUM_LEDS - 1 - i].fadeToBlackBy(255 - brightness);
    }

    // Process center section (94-186)
    for(int i = 93; i < 187; i++) {
        float centerPos = abs(i - 140) / 46.0;
        uint8_t brightness = map(smoothedHigh * (1.0 - centerPos), 0, 255, 0, 200);
    
        leds[i] = highColor;
        leds[i].fadeToBlackBy(255 - brightness);
    }

    wavePos += map(smoothedLow, 0, 255, 1, 4);
    FastLED.show();
}

void rainbowEffect(uint8_t volume, uint8_t lowFreq, uint8_t midFreq, uint8_t highFreq) {
    const uint8_t MAX_WAVES = 500;
    const uint8_t BASS_THRESHOLD = 180;
    const uint8_t GOLDEN_ANGLE = 100;
    const uint8_t WAVE_SPEED = 1;
    
    static int16_t wavePositions[MAX_WAVES];
    static uint8_t waveIntensities[MAX_WAVES];
    static uint8_t waveHues[MAX_WAVES];
    static bool waveActive[MAX_WAVES];
    static bool complete[MAX_WAVES];
    static uint8_t nextHue = random8();
    
    if (lowFreq > BASS_THRESHOLD) {
        for (int i = 0; i < MAX_WAVES; i++) {
            if (!waveActive[i]) {
                wavePositions[i] = NUM_LEDS - 1;  // Start from right
                waveIntensities[i] = 255;
                waveHues[i] = nextHue + random8(-10, 10);
                nextHue += GOLDEN_ANGLE;
                waveActive[i] = true;
                complete[i] = false;
                break;
            }
        }
    }
    
    fadeToBlackBy(leds, NUM_LEDS, 60);
    
    for (int i = 0; i < MAX_WAVES; i++) {
        if (waveActive[i]) {
            wavePositions[i] -= WAVE_SPEED;  // Move left
            
            int pos = wavePositions[i];
            
            if (pos <= 0) {  // Check left boundary
                complete[i] = true;
            }
            
            if (complete[i]) {
                waveIntensities[i] = waveIntensities[i] * 0.90;
                if (waveIntensities[i] < 5) waveActive[i] = false;
            }
            
            uint8_t sat = map(highFreq, 0, 255, 180, 255);
            
            if (!complete[i] && pos >= 0 && pos < NUM_LEDS) {
                leds[pos] = CHSV(waveHues[i], sat, waveIntensities[i]);
            }
        }
    }
    
    FastLED.show();
}

void snakeEffect(uint8_t volume, uint8_t lowFreq, uint8_t midFreq, uint8_t highFreq) {
    const uint8_t MAX_WAVES = 500;
    const uint8_t CENTER = NUM_LEDS / 2;
    const uint8_t BASS_THRESHOLD = 180;
    const uint8_t GOLDEN_ANGLE = 61; // approximation of golden ratio * 256
    
    static int16_t wavePositions[MAX_WAVES];
    static uint8_t waveIntensities[MAX_WAVES];
    static uint8_t waveHues[MAX_WAVES];
    static bool waveActive[MAX_WAVES];
    static bool leftComplete[MAX_WAVES];
    static bool rightComplete[MAX_WAVES];
    static uint8_t nextHue = random8(); // Start with random color
    
    // Create new wave on bass hit
    if (lowFreq > BASS_THRESHOLD) {
        for (int i = 0; i < MAX_WAVES; i++) {
            if (!waveActive[i]) {
                wavePositions[i] = 0;
                waveIntensities[i] = 255;
                // Add variation to color + use full spectrum
                waveHues[i] = nextHue + random8(-10, 10);
                nextHue += GOLDEN_ANGLE; // Better color distribution
                waveActive[i] = true;
                leftComplete[i] = false;
                rightComplete[i] = false;
                
                leds[CENTER] = CHSV(waveHues[i], 255, waveIntensities[i]);
                break;
            }
        }
    }
    
    fadeToBlackBy(leds, NUM_LEDS, 40);
    
    // Update and draw waves
    for (int i = 0; i < MAX_WAVES; i++) {
        if (waveActive[i]) {
            wavePositions[i]++;
            
            int leftPos = CENTER - wavePositions[i];
            int rightPos = CENTER + wavePositions[i];
            
            if (leftPos <= 0) leftComplete[i] = true;
            if (rightPos >= NUM_LEDS-1) rightComplete[i] = true;
            
            if (leftComplete[i] && rightComplete[i]) {
                waveIntensities[i] = waveIntensities[i] * 0.95;
                if (waveIntensities[i] < 5) waveActive[i] = false;
            }
            
            uint8_t sat = map(highFreq, 0, 255, 180, 255);
            
            // Always light center LED with current wave's color
            leds[CENTER] = CHSV(waveHues[i], sat, waveIntensities[i]);
            
            if (!leftComplete[i] && leftPos >= 0) {
                leds[leftPos] = CHSV(waveHues[i], sat, waveIntensities[i]);
            }
            if (!rightComplete[i] && rightPos < NUM_LEDS) {
                leds[rightPos] = CHSV(waveHues[i], sat, waveIntensities[i]);
            }
        }
    }
    
    FastLED.show();
}

void scrollEffect(uint8_t volume, uint8_t lowFreq, uint8_t midFreq, uint8_t highFreq) {
    const uint8_t HISTORY_LENGTH = (NUM_LEDS / 2) + 100;  // Increased range
    static uint8_t colorHistory[3][HISTORY_LENGTH];
    static float smoothedVolume = 0;
    const float SMOOTH_FACTOR = 0.2;  // Less smoothing
    const float DECAY_FACTOR = 0.98;  // Slower decay
    
    smoothedVolume = smoothedVolume * SMOOTH_FACTOR + volume * (1.0 - SMOOTH_FACTOR);
    
    // Scroll do histórico
    for(int i = HISTORY_LENGTH-1; i > 0; i--) {
        for(int color = 0; color < 3; color++) {
            colorHistory[color][i] = colorHistory[color][i-1];
        }
    }
    
    float scaleFactor = 1.0;  // Increased intensity
    colorHistory[0][0] = lowFreq * scaleFactor;
    colorHistory[1][0] = midFreq * scaleFactor;
    colorHistory[2][0] = highFreq * scaleFactor;
    
    // Less smoothing, more expansion
    for(int i = 0; i < HISTORY_LENGTH; i++) {
        if(i > 0 && i < HISTORY_LENGTH-1) {
            for(int color = 0; color < 3; color++) {
                uint8_t avg = (colorHistory[color][i-1] + 2*colorHistory[color][i]) / 3;  // Less averaging
                colorHistory[color][i] = avg * DECAY_FACTOR;
            }
        }
        
        // Faster expansion from center
        float intensityFactor = 1.0 - (float)i / (HISTORY_LENGTH * 1.2);  // Wider spread
        intensityFactor = pow(intensityFactor, 0.7);  // More linear falloff
        
        if(centerLed + i < NUM_LEDS) {
            leds[centerLed + i] = CRGB(
                colorHistory[0][i] * intensityFactor,
                colorHistory[1][i] * intensityFactor,
                colorHistory[2][i] * intensityFactor
            );
        }
        if(centerLed - i >= 0) {
            leds[centerLed - i] = CRGB(
                colorHistory[0][i] * intensityFactor,
                colorHistory[1][i] * intensityFactor,
                colorHistory[2][i] * intensityFactor
            );
        }
    }

    FastLED.show();
}


void loop() {
    MDNS.update();
    
    int packetSize = port.parsePacket();
    if (packetSize == 5) {
        uint8_t volume, lowFreq, midFreq, highFreq, effect;
        port.read(&volume, 1);
        port.read(&lowFreq, 1);
        port.read(&midFreq, 1);
        port.read(&highFreq, 1);
        port.read(&effect, 1);
        
        switch(effect) {
            case 0: currentEffect = WAVE; break;
            case 1: currentEffect = SPEED; break;
            case 2: currentEffect = RAINBOW; break;
            case 3: currentEffect = SNAKE; break;
            case 4: currentEffect = SCROLL; break;
        }
        
        switch(currentEffect) {
            case WAVE:
                audioWaveEffect(volume, lowFreq, midFreq, highFreq);
                break;
            case SPEED:
                speedEffect(volume, lowFreq, midFreq, highFreq);
                break;
            case RAINBOW:
                rainbowEffect(volume, lowFreq, midFreq, highFreq);
                break;
            case SNAKE:
                snakeEffect(volume, lowFreq, midFreq, highFreq);
                break;
            case SCROLL:
                scrollEffect(volume, lowFreq, midFreq, highFreq);
                break;
        }
    }
}
