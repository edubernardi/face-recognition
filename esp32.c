#include <WiFi.h>
#include <HTTPClient.h>
#include "esp_camera.h"

const char* ssid = "";
const char* password = "";

const char* serverURL = "http://192.168.0.1:8000/identificar/";

#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

void setup() {
  Serial.begin(115200);
  
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  
  config.frame_size = FRAMESIZE_SVGA;
  config.jpeg_quality = 12;
  config.fb_count = 1;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Erro ao inicializar câmera: 0x%x", err);
    return;
  }

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi conectado");
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Falha ao tirar foto");
      return;
    }

    Serial.printf("Foto capturada com %d bytes | Heap heap: %d\n", fb->len, ESP.getFreeHeap());

    if (sendImage(fb)) {
      Serial.println("Imagem enviada com sucesso");
    } else {
      Serial.println("Falha ao enviar imagem");
    }

    esp_camera_fb_return(fb);
  } else {
    Serial.println("Reconectando na WiFi");
    WiFi.reconnect();
  }

  delay(10000);
}

// Função para enviar a imagem por HTTP
bool sendImage(camera_fb_t *fb) {
  HTTPClient http;
  http.begin(serverURL);

  String boundary = "ESP32CAMBoundary";
  String header = "--" + boundary + "\r\n";
  header += "Content-Disposition: form-data; name=\"file\"; filename=\"image.jpg\"\r\n";
  header += "Content-Type: image/jpeg\r\n\r\n";
  
  String footer = "\r\n--" + boundary + "--\r\n";

  size_t contentLength = header.length() + fb->len + footer.length();

  http.addHeader("Content-Type", "multipart/form-data; boundary=" + boundary);

  uint8_t* payload = new uint8_t[contentLength];
  if (!payload) {
    Serial.println("Falha ao alocar memório para o payload da requisição.");
    return false;
  }

  memcpy(payload, header.c_str(), header.length());
  memcpy(payload + header.length(), fb->buf, fb->len);
  memcpy(payload + header.length() + fb->len, footer.c_str(), footer.length());

  int httpCode = http.sendRequest("POST", payload, contentLength);

  delete[] payload;

  if (httpCode > 0 && httpCode < 300) {
    Serial.println("Imagem enviada. Resposta:");
    Serial.println(http.getString());
    return true;
  } else {
    Serial.print("Erro ao enviar a imagem. Código:");
    Serial.println(httpCode);
    Serial.println(http.errorToString(httpCode));
    return false;
  }
}
