<div align="center">
  <img width="49%" alt="image" src="https://github.com/user-attachments/assets/15f7cc6c-3e40-43a5-9ddf-c43a3f78aa0f" />
  <img width="49%" alt="image" src="https://github.com/user-attachments/assets/98aba836-491b-4042-8071-5545c88d33cb" />
</div>

# 🚪 AI-Powered Smart Door Access Control System with FreeRTOS

This project features an automated smart door system using Face Recognition (AI), IoT (ESP32), and Real-Time Operating System (FreeRTOS) principles. It is designed to provide secure, non-blocking, and efficient access control.

## 🌟 Key Features

<table>
  <tr>
    <th align="left">Feature</th>
    <th align="left">Description</th>
  </tr>
  <tr>
    <td><b>Real-time Face Recognition</b></td>
    <td>Utilizes <code>face_recognition</code> and OpenCV on a Python Server to process video streams from the ESP32-CAM.</td>
  </tr>
  <tr>
    <td><b>Multitasking with FreeRTOS</b></td>
    <td>Implements Tasks, Queues, and Mutexes on the ESP32 to ensure network stability while controlling hardware.</td>
  </tr>
  <tr>
    <td><b>Streamlit Web Dashboard</b></td>
    <td>A user-friendly interface for live video streaming, system status monitoring, and access logging.</td>
  </tr>
  <tr>
    <td><b>Dual-Core Processing</b></td>
    <td>Specifically pins heavy hardware tasks to Core 1 to keep the network stack responsive.</td>
  </tr>
</table>

## 🏗 System Architecture
The system operates on a Client-Server model:

<table>
  <tr>
    <th align="left">Component</th>
    <th align="left">Function</th>
  </tr>
  <tr>
    <td><b>ESP32-CAM (Node Camera)</b></td>
    <td>Captures and streams MJPEG video over HTTP.</td>
  </tr>
  <tr>
    <td><b>Python Server (AI Engine)</b></td>
    <td>Analyzes the stream, recognizes faces, and sends control commands via HTTP requests.</td>
  </tr>
  <tr>
    <td><b>ESP32 Control Node (RTOS)</b></td>
    <td>Receives commands (e.g., <code>/open</code>, <code>/fail</code>) and manages the Servo and OLED without blocking the connection.</td>
  </tr>
</table>

## 🛠 Hardware Components

<table>
  <tr>
    <th align="left">Component</th>
    <th align="left">Function</th>
  </tr>
  <tr>
    <td><b>ESP32 DevKit V1</b></td>
    <td>Central controller running FreeRTOS</td>
  </tr>
  <tr>
    <td><b>ESP32-CAM (OV2640)</b></td>
    <td>Captures and transmits the video stream</td>
  </tr>
  <tr>
    <td><b>Servo SG90</b></td>
    <td>Physical actuator for the door latch</td>
  </tr>
  <tr>
    <td><b>OLED SSD1306</b></td>
    <td>Provides real-time status updates to the user</td>
  </tr>
  <tr>
    <td><b>PIR HC-SR501</b></td>
    <td>Motion sensor used to trigger the scanning process</td>
  </tr>
</table>

## 🧠 RTOS Implementation Details

The firmware utilizes FreeRTOS to handle high-latency hardware operations without crashing the WiFi connection:

<table>
  <tr>
    <th align="left">Concept</th>
    <th align="left">Implementation Detail</th>
  </tr>
  <tr>
    <td><b>Task Management</b></td>
    <td>The <code>TaskServoControl</code> is pinned to Core 1, allowing the <code>loop()</code> function to focus solely on handling web client requests on the same core via time-slicing.</td>
  </tr>
  <tr>
    <td><b>Inter-Task Communication (Queue)</b></td>
    <td>A <code>servoQueue</code> transmits <code>OpenCommand</code> structures (containing the user's name) from the WiFi handler to the Servo task.</td>
  </tr>
  <tr>
    <td><b>Resource Synchronization (Mutex)</b></td>
    <td>An <code>oledMutex</code> protects the I2C bus, ensuring that only one task writes to the OLED display at a time to prevent data corruption.</td>
  </tr>
</table>

## ⚙️ Installation & Usage

### 1. ESP32 and ESP32cam Firmware
1. Open `esp32.ino` and `esp32cam.ino` in the Arduino IDE.
2. Update your WiFi credentials:
   ```cpp
   const char* ssid = "Your_SSID";
   const char* password = "Your_Password"; 
   ```
3. Flash the code to your ESP32 DevKit and ESP32-CAM.
  
### 2. Python AI Server
1. Install dependencies:
   ```bash
   pip install opencv-python face_recognition streamlit requests
   ```
2. Run the application:
   ```bash
   streamlit run recognitionFace.py
   ```
