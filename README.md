<img width="559" height="733" alt="image" src="https://github.com/user-attachments/assets/15f7cc6c-3e40-43a5-9ddf-c43a3f78aa0f" />
<img width="552" height="736" alt="image" src="https://github.com/user-attachments/assets/98aba836-491b-4042-8071-5545c88d33cb" />


🚪AI-Powered Smart Door Access Control System with FreeRTOSThis project features an automated smart door system using Face Recognition (AI), IoT (ESP32), and Real-Time Operating System (FreeRTOS) principles. It is designed to provide secure, non-blocking, and efficient access control.

🌟 Key FeaturesReal-time Face Recognition: Utilizes face_recognition and OpenCV on a Python Server to process video streams from the ESP32-CAM.

Multitasking with FreeRTOS: Implements Tasks, Queues, and Mutexes on the ESP32 to ensure network stability while controlling hardware.Streamlit Web Dashboard: A user-friendly interface for live video streaming, system status monitoring, and access logging.

Dual-Core Processing: Specifically pins heavy hardware tasks to Core 1 to keep the network stack responsive.

🏗 System ArchitectureThe system operates on a Client-Server model:

ESP32-CAM (Node Camera): Captures and streams MJPEG video over HTTP.

Python Server (AI Engine): Analyzes the stream, recognizes faces, and sends control commands via HTTP requests.

ESP32 Control Node (RTOS): Receives commands (e.g., /open, /fail) and manages the Servo and OLED without blocking the connection.

🛠 Hardware ComponentsComponentFunction

ESP32 DevKit V1: Central controller running FreeRTOS

ESP32-CAM (OV2640): Captures and transmits the video stream

Servo SG90: Physical actuator for the door latch

OLED SSD1306: Provides real-time status updates to the user

PIR HC-SR501: Motion sensor used to trigger the scanning process

🧠 RTOS Implementation Details

The firmware utilizes FreeRTOS to handle high-latency hardware operations without crashing the WiFi connection:

Task Management: The TaskServoControl is pinned to Core 1, allowing the loop() function to focus solely on handling web client requests on the same core via time-slicing.

Inter-Task Communication (Queue): A servoQueue transmits OpenCommand structures (containing the user's name) from the WiFi handler to the Servo task.

Resource Synchronization (Mutex): An oledMutex protects the I2C bus, ensuring that only one task writes to the OLED display at a time to prevent data corruption.

⚙️ Installation & Usage

1.ESP32 and ESP32cam Firmware
  1.Open esp32.ino and esp32cam.ino in the Arduino IDE.
  
  2.Update your WiFi credentials:
    const char* ssid = "Your_SSID";
    const char* password = "Your_Password"; 
  3. Flash the code to your ESP32 DevKit and ESP32-CAM.
  
2. Python AI Server
  1.Install dependencies:

   pip install opencv-python face_recognition streamlit requests

  2.Run the application:
  
  streamlit run recognitionFace.py
  
