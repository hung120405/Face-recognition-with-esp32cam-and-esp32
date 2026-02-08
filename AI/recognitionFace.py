import streamlit as st
import cv2
import face_recognition
import numpy as np
import pandas as pd
import requests
import os
import time
from datetime import datetime

# ================= 1. CẤU HÌNH KẾT NỐI =================
ESP32_CAM_IP = "172.20.10.14"       
ESP32_CONTROL_IP = "172.20.10.2"    

URL_STREAM = f"http://{ESP32_CAM_IP}:81/stream"
URL_CHECK_PIR = f"http://{ESP32_CONTROL_IP}/check_pir"
URL_OPEN = f"http://{ESP32_CONTROL_IP}/open"
URL_FAIL = f"http://{ESP32_CONTROL_IP}/fail"

DATASET_DIR = "dataset"
TOLERANCE = 0.50 

if not os.path.exists(DATASET_DIR):
    os.makedirs(DATASET_DIR)

# ================= 2. QUẢN LÝ SESSION STATE =================
if 'system_state' not in st.session_state:
    st.session_state.system_state = "IDLE" 
if 'temp_reg_name' not in st.session_state:
    st.session_state.temp_reg_name = ""
if 'reg_step' not in st.session_state:
    st.session_state.reg_step = 0
if 'attendance_log' not in st.session_state:
    st.session_state.attendance_log = pd.DataFrame(columns=["Thời gian", "Họ tên", "Trạng thái", "Distance", "Time(ms)"])

# ================= 3. HÀM XỬ LÝ =================

@st.cache_resource
def load_database():
    known_encodings = []
    known_names = []
    if os.path.exists(DATASET_DIR):
        for file in os.listdir(DATASET_DIR):
            if file.endswith((".jpg", ".png", ".jpeg")):
                path = os.path.join(DATASET_DIR, file)
                try:
                    image = face_recognition.load_image_file(path)
                    encodings = face_recognition.face_encodings(image)
                    if len(encodings) > 0:
                        known_encodings.append(encodings[0])
                        name = os.path.splitext(file)[0].split('_')[0]
                        known_names.append(name)
                except Exception: pass
    return known_encodings, known_names

def reload_data():
    st.cache_resource.clear()
    return load_database()

def send_to_screen_success(name):
    try:
        now_str = datetime.now().strftime("%H:%M")
        requests.get(URL_OPEN, params={"name":f"{name}  {now_str}"}, timeout=2)
    except: pass

def send_to_screen_fail():
    try: requests.get(URL_FAIL, timeout=2)
    except: pass

# --- HÀM QUAN TRỌNG: STREAM VÀ TỰ ĐỘNG CHỤP ---
def auto_capture_stream(cam_placeholder, status_placeholder, step, name):
    """
    Hàm này stream camera liên tục. 
    Tối ưu hóa: Resize ảnh nhỏ để detect nhanh -> Video mượt.
    """
    cap = cv2.VideoCapture(URL_STREAM)
    if not cap.isOpened(): 
        st.error("❌ Không thể kết nối Camera ESP32!")
        return False, None
    
    msg = {1: "Nhìn THẲNG", 2: "Quay nhẹ TRÁI", 3: "Quay nhẹ PHẢI"}.get(step, "")
    
    stable_count = 0
    REQUIRED_STABLE = 10 
    captured_frame = None

    while True:
        ret, frame = cap.read()
        if not ret: 
            break

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        faces = face_recognition.face_locations(rgb_small)
        
        display_frame = frame.copy()
        h, w, _ = display_frame.shape
        
        if len(faces) == 1:
            stable_count += 1
            progress_width = int((stable_count / REQUIRED_STABLE) * w)
            cv2.rectangle(display_frame, (0, h-20), (progress_width, h), (0, 255, 0), -1)
            cv2.putText(display_frame, f"GIU YEN... {int((stable_count/REQUIRED_STABLE)*100)}%", (20, h-40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            if stable_count >= REQUIRED_STABLE:
                captured_frame = frame 
                break
        else:
            stable_count = 0 
            color = (0, 255, 255) # Vàng
            if len(faces) == 0: 
                txt = "KHONG THAY MAT"
                color = (0, 0, 255) # Đỏ
            elif len(faces) > 1: 
                txt = "CHI 1 NGUOI THOI"
                color = (0, 0, 255)
            else:
                txt = msg
                
            cv2.putText(display_frame, f"B{step}: {msg}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            cv2.putText(display_frame, txt, (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cam_placeholder.image(cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB), channels="RGB", use_container_width=True)
        
        time.sleep(0.01)
        
    cap.release()
    return True, captured_frame

def scan_face_slowly(cam_ph, status_ph, encodings, names):
    cap = cv2.VideoCapture(URL_STREAM)
    if not cap.isOpened():
        return None, None, None

    t0 = time.perf_counter()
    try:
        found = None
        found_dist = None
        max_attempts = 5

        COUNTDOWN_SECONDS = 5

        for i in range(max_attempts):
            start_time = time.time()
            while time.time() - start_time < COUNTDOWN_SECONDS:
                ret, frame = cap.read()
                if ret:
                    cv2.putText(frame, f"QUET LAN {i+1}...", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                    countdown = COUNTDOWN_SECONDS - int(time.time() - start_time)
                    if countdown < 0:
                        countdown = 0
                    cv2.putText(frame, str(countdown), (300, 240), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 255), 5)
                    cam_ph.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), channels="RGB", use_container_width=True)
                time.sleep(0.05)

            ret, frame = cap.read()
            if not ret:
                continue

            small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            locs = face_recognition.face_locations(rgb)
            encs = face_recognition.face_encodings(rgb, locs)

            attempt_best_dist = None

            if encs and len(encodings) > 0:
                dists = face_recognition.face_distance(encodings, encs[0])
                best = int(np.argmin(dists))
                attempt_best_dist = float(dists[best])

                matches = face_recognition.compare_faces(encodings, encs[0], tolerance=TOLERANCE)
                if matches[best]:
                    found = names[best]
                    found_dist = attempt_best_dist
                    break

            if not found:
                if attempt_best_dist is None:
                    status_ph.warning(f"⚠️ Lần {i+1}: Không khớp! (best distance=N/A)")
                else:
                    status_ph.warning(f"⚠️ Lần {i+1}: Không khớp! (best distance={attempt_best_dist:.4f})")

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return found, found_dist, float(elapsed_ms)
    finally:
        cap.release()

# ================= 4. GIAO DIỆN CHÍNH =================
st.set_page_config(page_title="Hệ Thống Chấm Công AI", layout="wide")
st.title("🛡️ Hệ Thống Chấm Công & Điểm Danh")

encodings, names = load_database()

col_L, col_R = st.columns([0.65, 0.35])

with col_L:
    st.subheader("🔴 Camera Monitor")
    cam_ph = st.empty()
    status_ph = st.empty()
    
    control_container = st.container()

with col_R:
    st.subheader("📋 Lịch sử Điểm danh")
    if st.button("🗑️ Xóa Lịch Sử"):
        st.session_state.attendance_log = pd.DataFrame(columns=["Thời gian", "Họ tên", "Trạng thái", "Distance", "Time(ms)"])
        st.rerun()
        
    st.dataframe(
        st.session_state.attendance_log, 
        use_container_width=True, 
        hide_index=True,
        height=400
    )

with st.sidebar:
    st.header("⚙️ Điều khiển")
    if st.button("🔄 RESET VỀ MẶC ĐỊNH"):
        st.session_state.system_state = "IDLE"
        st.rerun()
    st.info(f"Đã học: {len(names)} khuôn mặt")

# --- STATE MACHINE ---
if st.session_state.system_state == "IDLE":
    status_ph.info("💤 Đang chờ cảm biến chuyển động...")
    cam_ph.image("https://media.tenor.com/On7kvXhzml4AAAAj/loading-gif.gif", width=150)
    
    try:
        r = requests.get(URL_CHECK_PIR, timeout=0.5)
        if r.text.strip() == "1":
            st.session_state.system_state = "SCANNING"
            st.rerun()
    except: time.sleep(1)
    time.sleep(1)
    st.rerun()

# 2.(SCANNING)
elif st.session_state.system_state == "SCANNING":
    name, dist, elapsed_ms = scan_face_slowly(cam_ph, status_ph, encodings, names)
    
    if name:
        dist_txt = f"{dist:.4f}" if dist is not None else "N/A"
        time_txt = f"{elapsed_ms:.0f}ms" if elapsed_ms is not None else "N/A"
        status_ph.success(f"✅ Xác nhận: {name} | distance={dist_txt} | time={time_txt}")
        send_to_screen_success(name)
        
        row = {
            "Thời gian": datetime.now().strftime("%H:%M:%S"),
            "Họ tên": name,
            "Trạng thái": "Thành công",
            "Distance": round(float(dist), 5) if dist is not None else None,
            "Time(ms)": int(round(float(elapsed_ms))) if elapsed_ms is not None else None,
        }
        st.session_state.attendance_log = pd.concat([pd.DataFrame([row]), st.session_state.attendance_log], ignore_index=True)
        
        time.sleep(8)
        st.session_state.system_state = "IDLE"
        st.rerun()
    else:
        send_to_screen_fail()
        row = {
            "Thời gian": datetime.now().strftime("%H:%M:%S"),
            "Họ tên": "Unknown",
            "Trạng thái": "Thất bại",
            "Distance": round(float(dist), 5) if dist is not None else None,
            "Time(ms)": int(round(float(elapsed_ms))) if elapsed_ms is not None else None,
        }
        st.session_state.attendance_log = pd.concat([pd.DataFrame([row]), st.session_state.attendance_log], ignore_index=True)
        
        st.session_state.system_state = "FAIL_OPT"
        st.rerun()

# 3. (FAIL OPTION)
elif st.session_state.system_state == "FAIL_OPT":
    status_ph.error("❌ Không nhận diện được!")
    cam_ph.info("Bạn có muốn đăng ký khuôn mặt mới không?")
    
    with control_container:
        c1, c2 = st.columns(2)
        if c1.button("📝 Đăng ký ngay"):
            st.session_state.system_state = "REGISTER"
            st.session_state.reg_step = 1
            st.rerun()
        if c2.button("➡️ Bỏ qua"):
            st.session_state.system_state = "IDLE"
            st.rerun()

# 4.(REGISTER)
elif st.session_state.system_state == "REGISTER":
    if not st.session_state.temp_reg_name:
        cam_ph.empty()
        status_ph.info("Nhập tên nhân viên mới để bắt đầu:")
        with control_container:
            val = st.text_input("Họ và Tên (Viết liền, không dấu):")
            if st.button("📸 Bắt đầu chụp") and val:
                st.session_state.temp_reg_name = val
                st.rerun()
    else:
        name = st.session_state.temp_reg_name
        step = st.session_state.reg_step
        
        ok, frame = auto_capture_stream(cam_ph, status_ph, step, name)
        
        if ok and frame is not None:
            suffix = ["front", "left", "right"][step-1]
            cv2.imwrite(os.path.join(DATASET_DIR, f"{name}_{suffix}.jpg"), frame)
            
            st.toast(f"✅ Đã lưu góc {suffix}!", icon="💾")
            
            if step < 3:
                st.session_state.reg_step += 1
                st.rerun()
            else:
                reload_data()
                st.success("🎉 Đăng ký thành công! Đang tải lại dữ liệu...")
                
                row = {
                    "Thời gian": datetime.now().strftime("%H:%M:%S"),
                    "Họ tên": name,
                    "Trạng thái": "Đăng ký mới",
                    "Distance": None,
                    "Time(ms)": None,
                }
                st.session_state.attendance_log = pd.concat([pd.DataFrame([row]), st.session_state.attendance_log], ignore_index=True)

                st.session_state.temp_reg_name = ""
                st.session_state.reg_step = 0
                st.session_state.system_state = "IDLE"
                time.sleep(5)
                st.rerun()