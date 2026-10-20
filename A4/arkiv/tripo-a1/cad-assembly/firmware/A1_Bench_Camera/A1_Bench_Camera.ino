#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <esp_camera.h>
#include <esp_heap_caps.h>
#include <cstring>

constexpr uint8_t SHUTTER_PIN = 13;
constexpr uint32_t DEBOUNCE_MS = 40;
constexpr char AP_SSID[] = "A1-Camera";
constexpr char AP_PASSWORD[] = "A1camera2026";

WebServer server(80);
uint8_t *latestJpeg = nullptr;
size_t latestCapacity = 0;
size_t latestLength = 0;
uint32_t captureCount = 0;
uint32_t capturedAt = 0;
uint32_t changedAt = 0;
bool cameraReady = false;
bool accessPointReady = false;
bool stableButton = HIGH;
bool rawButton = HIGH;
String lastStatus = "No image yet";

const char PAGE[] PROGMEM = R"A1HTML(<!doctype html>
<html lang="nn"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>A1 kamera</title><style>[hidden]{display:none!important}body{font:18px system-ui,sans-serif;max-width:760px;margin:28px auto;padding:0 18px;color:#171717}button,a{font:inherit;padding:12px 18px;border:2px solid #171717;border-radius:8px;background:#fff;color:#171717;display:inline-block;text-decoration:none;margin:0 8px 12px 0}button:disabled{opacity:.45}img{display:block;width:100%;height:auto;border:1px solid #aaa;margin-top:20px}small{font-size:14px}#status{white-space:pre-line}strong{display:block}</style>
<h1>A1 kamera</h1><p>Prøveprogram for ESP32-CAM. Ta bilete på skjermen eller med utløysarknappen.</p>
<button id="capture">Ta bilete</button><a id="save" href="/download" hidden>Last ned siste JPEG</a>
<p id="status">Hentar status...</p><strong>Siste bilete finst berre i RAM.</strong><p>Last ned før du slår av straumen. Eit nytt bilete erstattar det førre.</p><img id="photo" alt="Siste kamerabilete" hidden>
<p><small>GPIO13 til GND via normalt open knapp. Ingen microSD. Wi-Fi-nettet har ikkje internettilgang. USB er straum og programmering.</small></p>
<script>let seen=-1,busy=false;const button=document.querySelector('#capture'),status=document.querySelector('#status'),photo=document.querySelector('#photo'),save=document.querySelector('#save');async function refresh(){if(busy)return;try{const r=await fetch('/status',{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);const s=await r.json();status.textContent='Bilete: '+s.count+' | '+s.status+'\nKamera: '+(s.camera?'klart':'feil')+' | JPEG: '+s.bytes+' byte';button.disabled=!s.camera;if(s.count===0){seen=-1;photo.hidden=true;save.hidden=true;photo.removeAttribute('src')}if(s.count>0&&s.count!==seen){seen=s.count;photo.src='/last.jpg?v='+seen;photo.hidden=false;save.hidden=false}}catch(e){status.textContent='Kontaktfeil. Kontroller A1-Camera og straum.'}}button.onclick=async()=>{if(busy)return;busy=true;button.disabled=true;try{const r=await fetch('/capture',{method:'POST'});if(!r.ok){const t=await r.text();status.textContent=t}}catch(e){status.textContent='Biletet kunne ikkje takast.'}finally{busy=false;await refresh()}};refresh();setInterval(refresh,1000);</script></html>)A1HTML";

void sendStatus() {
  char json[320];
  snprintf(json, sizeof(json),
           "{\"camera\":%s,\"count\":%lu,\"bytes\":%u,\"captured_at_ms\":%lu,\"status\":\"%s\"}",
           cameraReady ? "true" : "false", static_cast<unsigned long>(captureCount),
           static_cast<unsigned>(latestLength), static_cast<unsigned long>(capturedAt), lastStatus.c_str());
  server.sendHeader("Cache-Control", "no-store");
  server.send(200, "application/json", json);
}

bool captureImage() {
  if (!cameraReady || latestJpeg == nullptr) {
    lastStatus = "Camera or photo buffer unavailable";
    Serial.println(lastStatus);
    return false;
  }
  camera_fb_t *stale = esp_camera_fb_get();
  if (stale != nullptr) esp_camera_fb_return(stale);
  camera_fb_t *frame = esp_camera_fb_get();
  if (frame == nullptr) {
    lastStatus = "Camera capture failed";
    Serial.println(lastStatus);
    return false;
  }
  if (frame->buf == nullptr || frame->format != PIXFORMAT_JPEG || frame->len < 4 || frame->len > latestCapacity) {
    const size_t rejectedLength = frame->len;
    esp_camera_fb_return(frame);
    lastStatus = "JPEG invalid or larger than RAM limit";
    Serial.printf("Rejected image: %u bytes, limit %u\n", static_cast<unsigned>(rejectedLength), static_cast<unsigned>(latestCapacity));
    return false;
  }
  memcpy(latestJpeg, frame->buf, frame->len);
  latestLength = frame->len;
  esp_camera_fb_return(frame);
  ++captureCount;
  capturedAt = millis();
  lastStatus = "Capture OK";
  Serial.printf("Capture %lu OK: %u bytes\n", static_cast<unsigned long>(captureCount), static_cast<unsigned>(latestLength));
  return true;
}

void sendPhoto(bool download) {
  if (latestLength == 0 || latestJpeg == nullptr) {
    server.send(404, "text/plain", "No image yet. Press the shutter or Ta bilete.");
    return;
  }
  server.sendHeader("Cache-Control", "no-store");
  if (download) {
    server.sendHeader("Content-Disposition", "attachment; filename=\"A1-" + String(captureCount) + ".jpg\"");
  }
  server.setContentLength(latestLength);
  server.send(200, "image/jpeg", "");
  server.sendContent(reinterpret_cast<const char *>(latestJpeg), latestLength);
}

void initialiseCamera() {
  const bool hasPsram = psramFound();
  camera_config_t config = {};
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = 5;
  config.pin_d1 = 18;
  config.pin_d2 = 19;
  config.pin_d3 = 21;
  config.pin_d4 = 36;
  config.pin_d5 = 39;
  config.pin_d6 = 34;
  config.pin_d7 = 35;
  config.pin_xclk = 0;
  config.pin_pclk = 22;
  config.pin_vsync = 25;
  config.pin_href = 23;
  config.pin_sccb_sda = 26;
  config.pin_sccb_scl = 27;
  config.pin_pwdn = 32;
  config.pin_reset = -1;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = hasPsram ? FRAMESIZE_VGA : FRAMESIZE_QVGA;
  config.jpeg_quality = hasPsram ? 12 : 18;
  config.fb_count = hasPsram ? 2 : 1;
  config.grab_mode = hasPsram ? CAMERA_GRAB_LATEST : CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location = hasPsram ? CAMERA_FB_IN_PSRAM : CAMERA_FB_IN_DRAM;
  esp_err_t error = esp_camera_init(&config);
  if (error != ESP_OK) {
    lastStatus = "Camera initialisation failed";
    Serial.printf("Camera init failed: 0x%x\n", static_cast<unsigned>(error));
    return;
  }
  latestCapacity = hasPsram ? 256 * 1024 : 48 * 1024;
  latestJpeg = static_cast<uint8_t *>(heap_caps_malloc(latestCapacity,
                   hasPsram ? MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT : MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT));
  if (latestJpeg == nullptr) {
    latestCapacity = 0;
    esp_camera_deinit();
    lastStatus = "Not enough RAM for saved image";
    Serial.println(lastStatus);
    return;
  }
  cameraReady = true;
  lastStatus = "Ready - take first image";
  Serial.printf("Camera ready. PSRAM %s; photo limit %u bytes\n", hasPsram ? "yes" : "no", static_cast<unsigned>(latestCapacity));
}

void setup() {
  Serial.begin(115200);
  delay(500);
  pinMode(SHUTTER_PIN, INPUT_PULLUP);
  rawButton = digitalRead(SHUTTER_PIN);
  stableButton = rawButton;
  changedAt = millis();
  pinMode(4, OUTPUT);
  digitalWrite(4, LOW);
  initialiseCamera();
  WiFi.mode(WIFI_AP);
  accessPointReady = WiFi.softAP(AP_SSID, AP_PASSWORD, 1, false, 1);
  if (!accessPointReady) {
    Serial.println("Wi-Fi AP start failed. Reset and check power.");
    return;
  }
  server.on("/", HTTP_GET, []() {
    server.sendHeader("Cache-Control", "no-store");
    server.send_P(200, "text/html; charset=utf-8", PAGE);
  });
  server.on("/status", HTTP_GET, sendStatus);
  server.on("/capture", HTTP_POST, []() {
    if (captureImage()) sendStatus();
    else server.send(503, "text/plain", lastStatus);
  });
  server.on("/last.jpg", HTTP_GET, []() { sendPhoto(false); });
  server.on("/download", HTTP_GET, []() { sendPhoto(true); });
  server.onNotFound([]() { server.send(404, "text/plain", "Not found"); });
  server.begin();
  Serial.printf("Connect to %s with password %s\n", AP_SSID, AP_PASSWORD);
  Serial.print("Open http://");
  Serial.println(WiFi.softAPIP());
}

void loop() {
  if (accessPointReady) server.handleClient();
  const uint32_t now = millis();
  const bool reading = digitalRead(SHUTTER_PIN);
  if (reading != rawButton) {
    rawButton = reading;
    changedAt = now;
  }
  if (rawButton != stableButton && static_cast<uint32_t>(now - changedAt) >= DEBOUNCE_MS) {
    stableButton = rawButton;
    if (stableButton == LOW) captureImage();
  }
  delay(1);
}
