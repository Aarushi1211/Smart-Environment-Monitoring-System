# SMART ENVIRONMENT MONITORING SYSTEM

## Overview

Smart Environment Monitoring System is an industrial-style real-time monitoring application developed using STM32 and PyQt5.

The system continuously monitors environmental and security parameters using multiple sensors and displays live data through a professional desktop GUI.

The application provides:

* Real-time sensor monitoring
* Industrial-style dashboard
* Alerts & logs system
* CSV/PDF report generation
* User authentication system
* Admin/User role management
* Dark/Light mode support
* UART serial communication with STM32

---

# Features

✔ Real-time STM32 UART communication
✔ Industrial PyQt5 GUI
✔ Live temperature & humidity monitoring
✔ LDR-based light intensity monitoring
✔ Intrusion detection system
✔ RGB status indication system
✔ Alarm logging & alert management
✔ CSV/PDF report export
✔ Login authentication system
✔ Admin/User role access
✔ Dark/Light theme switching
✔ Real-time serial data visualization

---

# Hardware Used

* STM32F103C8T6
* DHT11 Sensor
* LDR Sensor
* IR Tracking Sensor
* RGB LED
* Buzzer

---

# Software & Technologies Used

* STM32CubeIDE
* Python
* PyQt5
* SQLite
* PySerial
* QtAwesome
* PyQtGraph
* ReportLab

---

# STM32 Serial Data Format

```text
TEMP:29,HUM:62,LDR:301,TRACK:1,RGB:2,STATUS:NORMAL
```

---

# GUI Screenshots

## Login Page

![Login](assets/login.png)

---

## Dashboard

![Dashboard](assets/dashboard.png)

---

## Reports Page

![Reports](assets/reports.png)

---

## Alerts & Logs

![Alerts](assets/alerts.png)

---

# Demo Video

Watch the complete project demonstration here:

[▶ Smart Monitoring System Demo](videos/smart_monitoring.mp4)

---

# Sample Reports

The system supports professional report generation and export functionality.

Generated sample reports included in this repository:

* PDF Report: `150626.pdf`
* CSV Report: `report150626.csv`

Reports are available inside the `/exports` directory.

---


# How to Run

1. Connect STM32 board via USB
2. Open project in VS Code or PyCharm
3. Install required Python libraries
4. Run `main.py`
5. Ensure correct COM port is selected

---

# Future Scope

* IoT cloud integration
* Remote monitoring system
* Mobile application support
* Email/SMS alert system
* AI-based anomaly detection
* Wireless sensor integration
* Cloud database support

---


