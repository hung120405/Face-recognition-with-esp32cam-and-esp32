#include <WiFi.h>
#include <WebServer.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <ESP32Servo.h>

#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/queue.h>
#include <freertos/semphr.h>

const char* ssid = "hung";
const char* password = "12345678";

#define PIR_PIN 14
#define SERVO_PIN 13

#define SCREEN_TIMEOUT 5000
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

WebServer server(80);
Servo myservo;

QueueHandle_t servoQueue;
SemaphoreHandle_t oledMutex;

struct OpenCommand {
  char name[20];
};

void showMessage(const char* line1, const char* line2, int size1 = 1, int size2 = 2) {
  if (xSemaphoreTake(oledMutex, pdMS_TO_TICKS(100)) == pdTRUE) {
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    
    display.setTextSize(size1);
    display.setCursor(0, 0);
    display.println(line1);
    
    display.setTextSize(size2);
    display.setCursor(0, 20);
    display.println(line2);
    
    display.display();
    xSemaphoreGive(oledMutex); 
  }
}

void handleCheckPIR() {
  int val = digitalRead(PIR_PIN);
  server.send(200, "text/plain", val == HIGH ? "1" : "0");
}

void handleOpen() {
  String nameStr = "Khach";
  if (server.hasArg("name")) nameStr = server.arg("name");
  
  OpenCommand cmd;
  nameStr.toCharArray(cmd.name, 20);
  
  xQueueSend(servoQueue, &cmd, 0);
  server.send(200, "text/plain", "CMD_SENT");
}

void handleScan() {
  showMessage("HE THONG:", "DANG QUET...");
  server.send(200, "text/plain", "OK");
}

void handleFail() {
  OpenCommand cmd;
  
  strcpy(cmd.name, "!FAIL"); 
  
  xQueueSend(servoQueue, &cmd, 0);
  
  server.send(200, "text/plain", "FAIL_SENT");
}


// TASK SERVO (CHẠY CORE 1)
void TaskServoControl(void *parameter) {
  OpenCommand rcvCmd;
  for (;;) {
    if (xQueueReceive(servoQueue, &rcvCmd, portMAX_DELAY) == pdTRUE) {
      
      if (strcmp(rcvCmd.name, "!FAIL") == 0) {
        // === TRƯỜNG HỢP 1: BÁO LỖI ===
        if (xSemaphoreTake(oledMutex, portMAX_DELAY)) {
           display.clearDisplay();
           display.setTextSize(2);
           display.setCursor(0, 0);
           display.println("CANH BAO:"); 
           display.println("KHONG NHAN DIEN DUOC"); 
           display.display();
           xSemaphoreGive(oledMutex);
        }
        
        vTaskDelay(5000 / portTICK_PERIOD_MS); 
        
      } else {
        // === TRƯỜNG HỢP 2: MỞ CỬA (NGƯỜI QUEN) ===
    
        if (xSemaphoreTake(oledMutex, portMAX_DELAY)) {
           display.clearDisplay();
           display.setTextSize(1);
           display.setCursor(0, 0);
           display.println("XIN CHAO:");
           display.setTextSize(2);
           display.setCursor(0, 20);
           display.println(rcvCmd.name); 
           display.display();
           xSemaphoreGive(oledMutex);
        }

        myservo.attach(SERVO_PIN);
        myservo.write(180); 
        
        vTaskDelay(8000 / portTICK_PERIOD_MS);
        
        myservo.write(0);
        vTaskDelay(1000 / portTICK_PERIOD_MS);
        myservo.detach(); 
      }
      
      if (xSemaphoreTake(oledMutex, portMAX_DELAY)) {
        display.clearDisplay(); 
        display.display();      
        xSemaphoreGive(oledMutex);
      }
    }
  }
}

// SETUP - PHẦN QUAN TRỌNG NHẤT
void setup() {
  Serial.begin(115200);
  delay(100); 
  
  Serial.println("\n--- BAT DAU KHOI TAO ---");

  servoQueue = xQueueCreate(5, sizeof(OpenCommand));
  oledMutex = xSemaphoreCreateMutex();

  Wire.begin(21, 22); 
  
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { 
    Serial.println(F("ERROR: Khong tim thay OLED! Kiem tra day noi."));
    if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3D)) {
       Serial.println(F("ERROR."));
    }
  } else {
    Serial.println(F("OLED Init OK!"));
  }
  
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 10);
  display.println("Khoi tao...");
  display.setCursor(0, 30);
  display.println("Vui long doi");
  display.display();
  delay(1000);

  pinMode(PIR_PIN, INPUT);
  myservo.attach(SERVO_PIN);
  myservo.write(0);
  delay(500);
  myservo.detach();

  Serial.print("Connecting to Wifi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWifi Connected!");
  Serial.println(WiFi.localIP());

  server.on("/check_pir", handleCheckPIR);
  server.on("/scan", handleScan);
  server.on("/open", handleOpen);
  server.on("/fail", handleFail);
  server.begin();

  xTaskCreatePinnedToCore(
    TaskServoControl,   
    "ServoTask",        
    8192,               
    NULL,               
    1,                  
    NULL,               
    1 
  );

  Serial.println("HE THONG DA SANG SANG!");
  showMessage("HE THONG:", "DA SAN    SANG");
}

void loop() {
  server.handleClient();
  delay(2); 
}