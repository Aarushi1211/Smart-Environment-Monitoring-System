# SMART ENVIRONMENT MONITORING SYSTEM

## Overview

Smart Environment Monitoring System is an industrial-style monitoring application developed using STM32 and PyQt5.

The system performs real-time monitoring of:

* Temperature
* Humidity
* Light Intensity
* Intrusion Detection
* RGB Status Monitoring

The GUI provides:

* Live dashboard
* Alerts & logs
* Reports generation
* CSV/PDF export
* User management system
* Dark/Light mode
* Serial communication with STM32

---

# Features

✔ Real-time STM32 UART communication
✔ Industrial PyQt5 GUI
✔ Temperature & humidity monitoring
✔ LDR-based light monitoring
✔ Intrusion detection system
✔ RGB indication system
✔ Alarm logging system
✔ Reports export (CSV/PDF)
✔ Login authentication system
✔ Admin/User role management
✔ Dark/Light theme switching

---

# Hardware Used

* STM32F103C8T6
* DHT11 Sensor
* LDR Sensor
* IR Tracking Sensor
* RGB LED
* Buzzer
* Rotary Encoder

---

# Software Used

* STM32CubeIDE
* PyQt5
* Python
* SQLite
* QtAwesome
* PyQtGraph

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

Watch project demo here:

[Project Demo Video](https://your-video-link-here)

---

# Installation

```bash
pip install -r requirements.txt
```

Run:

```bash
python main.py
```

---

# Future Scope

* IoT cloud integration
* Mobile app support
* Email/SMS alerts
* AI-based anomaly detection
* Remote monitoring system

---



