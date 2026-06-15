import sqlite3
import serial
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from datetime import datetime
import qtawesome as qta
import csv

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


# ==========================================
# PROFESSIONAL CIRCULAR GAUGE
# ==========================================

class CircularGauge(QWidget):

    def __init__(self, value=0, max_value=100, unit=""):
        super().__init__()
        self.value = value
        self.max_value = max_value
        self.unit = unit
        self.setFixedSize(260, 260)

    def setValue(self, value):
        self.value = value
        self.update()

    def paintEvent(self, event):
        width  = self.width()
        height = self.height()
        size   = min(width, height)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(width / 2, height / 2)

        radius = size / 2 - 20

        # ---- BACKGROUND ARC ----
        pen = QPen(QColor("#2E2E2E"), 14)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        rect = QRectF(-radius, -radius, radius * 2, radius * 2)
        painter.drawArc(rect, 225 * 16, 270 * 16)

        # ---- VALUE ARC ----
        gradient = QConicalGradient(0, 0, -90)
        gradient.setColorAt(0.0, QColor("#00F5FF"))
        gradient.setColorAt(1.0, QColor("#00C2FF"))

        pen = QPen(QBrush(gradient), 14)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        angle = int((self.value / self.max_value) * 270)
        painter.drawArc(rect, 225 * 16, -angle * 16)

        # ---- CENTER VALUE ----
        painter.setPen(Qt.white)
        font = QFont("Segoe UI", 28, QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(-100, -40, 200, 80), Qt.AlignCenter, f"{self.value}")

        # ---- UNIT ----
        font = QFont("Segoe UI", 14, QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(-100, 45, 200, 40), Qt.AlignCenter, self.unit)


# ==========================================
# DASHBOARD PAGE
# ==========================================

class DashboardPage(QWidget):

    def __init__(self, username):
        super().__init__()
        self.current_user  = username
        self.reports_page  = None   # set by MainWindow after construction
        self.alerts_page   = None   # set by MainWindow after construction

        # ---- SERIAL PORT ----
        try:
            self.serial_port = serial.Serial("COM6", 115200, timeout=1)
        except Exception as e:
            print(f"Serial open error: {e}")
            self.serial_port = None

        # ---- SERIAL TIMER ----
        self.serial_timer = QTimer()
        self.serial_timer.timeout.connect(self.read_serial_data)
        self.serial_timer.start(100)

        # ---- DATETIME TIMER ----
        self.dt_timer = QTimer()
        self.dt_timer.timeout.connect(self.update_datetime)
        self.dt_timer.start(1000)

        # ==========================================
        # MAIN LAYOUT
        # ==========================================
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(25)

        # ---- HEADER ----
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet("QFrame{ border-radius:15px; }")

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 10, 20, 10)

        self.datetime_label = QLabel(
            datetime.now().strftime("%d %b %Y | %I:%M %p")
        )
        self.datetime_label.setStyleSheet(
            "font-size:15px; font-weight:600; color:#EAEAEA;"
        )

        title = QLabel("SMART ENVIRONMENT MONITORING SYSTEM")
        title.setStyleSheet("font-size:24px; font-weight:bold; color:white;")

        self.user_label = QLabel(f"👋 Welcome, {self.current_user}")
        self.user_label.setStyleSheet(
            "font-size:15px; font-weight:600; color:#EAEAEA;"
        )

        header_layout.addWidget(self.datetime_label)
        header_layout.addStretch()
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.user_label)
        header.setLayout(header_layout)

        # ---- ALARM STATUS BAR ----
        self.alarm_bar = QFrame()
        self.alarm_bar.setFixedHeight(55)
        self.alarm_bar.setStyleSheet(
            "QFrame{ background-color:#008F39; border-radius:14px; }"
        )

        alarm_layout = QHBoxLayout()
        alarm_layout.setContentsMargins(20, 0, 20, 0)

        alarm_icon = QLabel("●")
        alarm_icon.setStyleSheet("font-size:22px; color:white;")

        self.alarm_text = QLabel("NORMAL OPERATION")
        self.alarm_text.setStyleSheet(
            "font-size:19px; font-weight:bold; color:white;"
        )

        alarm_layout.addStretch()
        alarm_layout.addWidget(alarm_icon)
        alarm_layout.addSpacing(10)
        alarm_layout.addWidget(self.alarm_text)
        alarm_layout.addStretch()
        self.alarm_bar.setLayout(alarm_layout)

        # ---- CENTER SECTION ----
        center_layout = QHBoxLayout()
        center_layout.setSpacing(25)

        # TEMPERATURE CARD
        temp_card = QFrame()
        temp_card.setObjectName("card")
        temp_card.setStyleSheet("QFrame{ border-radius:22px; }")

        temp_layout = QVBoxLayout()
        temp_layout.setContentsMargins(20, 20, 20, 20)

        temp_title = QLabel("TEMPERATURE")
        temp_title.setAlignment(Qt.AlignCenter)
        temp_title.setStyleSheet(
            "font-size:20px; font-weight:bold; color:white;"
        )

        self.temp_gauge = CircularGauge(value=0, max_value=100, unit="°C")

        self.temp_value = QLabel("0 °C")
        self.temp_value.setAlignment(Qt.AlignCenter)
        self.temp_value.setStyleSheet(
            "font-size:28px; font-weight:bold; color:#00F5FF;"
        )

        temp_layout.addWidget(temp_title)
        temp_layout.addSpacing(10)
        temp_layout.addWidget(self.temp_gauge, alignment=Qt.AlignCenter)
        temp_layout.addSpacing(10)
        temp_layout.addWidget(self.temp_value)
        temp_card.setLayout(temp_layout)

        # HUMIDITY CARD
        hum_card = QFrame()
        hum_card.setObjectName("card")
        hum_card.setStyleSheet("QFrame{ border-radius:22px; }")

        hum_layout = QVBoxLayout()
        hum_layout.setContentsMargins(20, 20, 20, 20)

        hum_title = QLabel("HUMIDITY")
        hum_title.setAlignment(Qt.AlignCenter)
        hum_title.setStyleSheet(
            "font-size:20px; font-weight:bold; color:white;"
        )

        self.hum_gauge = CircularGauge(value=0, max_value=100, unit="%")

        self.hum_value = QLabel("0 %")
        self.hum_value.setAlignment(Qt.AlignCenter)
        self.hum_value.setStyleSheet(
            "font-size:28px; font-weight:bold; color:#00F5FF;"
        )

        hum_layout.addWidget(hum_title)
        hum_layout.addSpacing(10)
        hum_layout.addWidget(self.hum_gauge, alignment=Qt.AlignCenter)
        hum_layout.addSpacing(10)
        hum_layout.addWidget(self.hum_value)
        hum_card.setLayout(hum_layout)

        center_layout.addWidget(temp_card)
        center_layout.addWidget(hum_card)

        # ---- STATUS SECTION ----
        status_frame = QFrame()
        status_frame.setObjectName("card")
        status_frame.setFixedHeight(120)

        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(30, 20, 30, 20)

        statuses = [
            ("SYSTEM",  "ACTIVE",  "#00FF66"),
            ("WARNING", "NORMAL",  "#FFD600"),
            ("ALARM",   "OFF",     "#FF2E2E"),
        ]

        for title_text, value_text, color in statuses:
            card = QFrame()
            card.setObjectName("card")
            card.setStyleSheet(
                "QFrame{ background-color:#252525; border-radius:15px; }"
            )

            card_layout = QVBoxLayout()

            led = QLabel("●")
            led.setAlignment(Qt.AlignCenter)
            led.setStyleSheet(f"font-size:34px; color:{color};")

            title_lbl = QLabel(title_text)
            title_lbl.setAlignment(Qt.AlignCenter)
            title_lbl.setStyleSheet(
                "font-size:14px; font-weight:bold; color:white;"
            )

            value_lbl = QLabel(value_text)
            value_lbl.setAlignment(Qt.AlignCenter)
            value_lbl.setStyleSheet("font-size:13px; color:#BDBDBD;")

            card_layout.addWidget(led)
            card_layout.addWidget(title_lbl)
            card_layout.addWidget(value_lbl)
            card.setLayout(card_layout)

            status_layout.addWidget(card)

        status_frame.setLayout(status_layout)

        # ---- ASSEMBLE MAIN LAYOUT ----
        main_layout.addWidget(header)
        main_layout.addWidget(self.alarm_bar)
        main_layout.addLayout(center_layout)
        main_layout.addWidget(status_frame)
        self.setLayout(main_layout)

    # ==========================================
    # UPDATE DATETIME LABEL
    # ==========================================

    def update_datetime(self):
        self.datetime_label.setText(
            datetime.now().strftime("%d %b %Y | %I:%M %p")
        )

    # ==========================================
    # READ STM32 SERIAL DATA
    # ==========================================

    def read_serial_data(self):
        try:
            if self.serial_port is None or not self.serial_port.in_waiting:
                return

            line = self.serial_port.readline().decode(errors="replace").strip()
            print("RAW:", line)

            # ==========================================
            # ONLY PROCESS COMPLETE SENSOR LINE
            # FORMAT:
            # TEMP:26,HUM:71,LDR:768,TRACK:1,RGB:2,STATUS:NORMAL
            # IGNORE: ENC:x  BTN:x  lines
            # ==========================================

            if not line.startswith("TEMP:"):
                return

            data = {}
            for item in line.split(","):
                if ":" in item:
                    key, value = item.split(":", 1)
                    data[key.strip()] = value.strip()

            # ---- SAFE VALUE EXTRACTION ----
            temp   = int(data.get("TEMP",   0))
            hum    = int(data.get("HUM",    0))
            ldr    = int(data.get("LDR",    0))
            track  = int(data.get("TRACK",  1))
            rgb    = int(data.get("RGB",    0))
            status = data.get("STATUS", "NORMAL")

            # ---- UPDATE GAUGES ----
            self.temp_gauge.setValue(temp)
            self.hum_gauge.setValue(hum)
            self.temp_value.setText(f"{temp} °C")
            self.hum_value.setText(f"{hum} %")

            # ---- FORWARD LIVE DATA TO REPORTS PAGE ----
            if self.reports_page is not None:
                self.reports_page.add_live_data(temp, hum, status)

            # ---- FORWARD ALARMS TO ALERTS PAGE ----
            if self.alerts_page is not None and status in ("INTRUSION", "WARNING"):
                alarm_name = (
                    "Intrusion Detected" if status == "INTRUSION"
                    else "High Temperature"
                )
                priority = (
                    "Critical" if status == "INTRUSION"
                    else "High"
                )
                self.alerts_page.add_real_alert(alarm_name, priority)

            # ---- UPDATE STATUS BAR ----
            if status == "WARNING":
                self.alarm_bar.setStyleSheet(
                    "QFrame{ background-color:#FF9500; border-radius:14px; }"
                )
                self.alarm_text.setText("⚠ HIGH TEMPERATURE")

            elif status == "INTRUSION":
                self.alarm_bar.setStyleSheet(
                    "QFrame{ background-color:#FF3B30; border-radius:14px; }"
                )
                self.alarm_text.setText("🚨 INTRUSION DETECTED")

            else:
                self.alarm_bar.setStyleSheet(
                    "QFrame{ background-color:#008F39; border-radius:14px; }"
                )
                self.alarm_text.setText("✓ NORMAL OPERATION")

            print(
                f"TEMP:{temp}  HUM:{hum}  LDR:{ldr}"
                f"  TRACK:{track}  RGB:{rgb}  STATUS:{status}"
            )

        except Exception as e:
            print("Serial Error:", e)


# ==========================================
# REPORTS PAGE
# ==========================================

class ReportsPage(QWidget):

    def __init__(self):
        super().__init__()

        self.logs       = []
        self.alarm_logs = []

        # ---- MAIN LAYOUT ----
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(25)

        # ---- HEADER ----
        header_layout = QHBoxLayout()

        title = QLabel("REPORTS")
        title.setStyleSheet("font-size:30px; font-weight:bold; color:white;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # ---- FILTER SECTION ----
        filter_frame = QFrame()
        filter_frame.setFixedHeight(180)
        filter_frame.setStyleSheet("QFrame{ border-radius:20px; }")

        filter_layout = QVBoxLayout()
        filter_layout.setContentsMargins(25, 20, 25, 20)
        filter_layout.setSpacing(18)

        # ROW 1 — date pickers
        row1 = QHBoxLayout()
        row1.setSpacing(20)

        from_layout = QVBoxLayout()
        from_label  = QLabel("From Date & Time")
        from_label.setStyleSheet("font-size:14px; font-weight:bold;")
        self.from_datetime = QDateTimeEdit()
        self.from_datetime.setCalendarPopup(True)
        self.from_datetime.setDateTime(QDateTime.currentDateTime())
        from_layout.addWidget(from_label)
        from_layout.addWidget(self.from_datetime)

        to_layout = QVBoxLayout()
        to_label  = QLabel("To Date & Time")
        to_label.setStyleSheet("font-size:14px; font-weight:bold;")
        self.to_datetime = QDateTimeEdit()
        self.to_datetime.setCalendarPopup(True)
        self.to_datetime.setDateTime(QDateTime.currentDateTime())
        to_layout.addWidget(to_label)
        to_layout.addWidget(self.to_datetime)

        row1.addLayout(from_layout)
        row1.addLayout(to_layout)

        # ROW 2 — controls
        row2 = QHBoxLayout()
        row2.setSpacing(20)

        interval_layout = QVBoxLayout()
        interval_label  = QLabel("Data Save Interval")
        interval_label.setStyleSheet("font-size:14px; font-weight:bold;")
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["5 sec","10 sec","30 sec","1 min","5 min"])
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_combo)

        export_layout = QVBoxLayout()
        export_label  = QLabel("Export Type")
        export_label.setStyleSheet("font-size:14px; font-weight:bold;")
        self.export_type_combo = QComboBox()
        self.export_type_combo.addItems([
            "Temperature & Humidity",
            "Alarm Logs",
            "Complete Report"
        ])
        self.export_type_combo.currentTextChanged.connect(self.change_report_view)
        export_layout.addWidget(export_label)
        export_layout.addWidget(self.export_type_combo)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        update_btn = QPushButton("Update Interval")
        update_btn.clicked.connect(self.update_interval)

        csv_btn = QPushButton("Export CSV")
        csv_btn.clicked.connect(self.export_csv)

        pdf_btn = QPushButton("Export PDF")
        pdf_btn.clicked.connect(self.export_pdf)

        for btn in [update_btn, csv_btn, pdf_btn]:
            btn.setFixedHeight(42)
            btn.setStyleSheet("""
                QPushButton{
                    background-color:#00C2FF; border:none; border-radius:10px;
                    font-size:14px; font-weight:bold;
                    padding-left:20px; padding-right:20px;
                }
                QPushButton:hover{ background-color:#00A8DD; }
            """)
            button_layout.addWidget(btn)

        row2.addLayout(interval_layout)
        row2.addLayout(export_layout)
        row2.addStretch()
        row2.addLayout(button_layout)

        # STYLE DATE/COMBO INPUTS
        for widget in [
            self.from_datetime, self.to_datetime,
            self.interval_combo, self.export_type_combo
        ]:
            widget.setFixedHeight(42)
            widget.setStyleSheet("""
                background-color:#2B2B2B; border:none; border-radius:10px;
                padding-left:12px; font-size:14px;
            """)

        filter_layout.addLayout(row1)
        filter_layout.addLayout(row2)
        filter_frame.setLayout(filter_layout)

        # ---- LIVE TABLE ----
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Time", "Temperature", "Humidity", "Status"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget{
                border:none; border-radius:15px;
                font-size:14px; gridline-color:#2B2B2B;
            }
            QHeaderView::section{
                background-color:#252525; border:none;
                padding:12px; font-size:14px; font-weight:bold;
            }
            QScrollBar:vertical{ width:10px; border:none; }
            QScrollBar::handle:vertical{ background:#00C2FF; border-radius:5px; }
        """)

        # ---- ASSEMBLE ----
        main_layout.addLayout(header_layout)
        main_layout.addWidget(filter_frame)
        main_layout.addWidget(self.table)
        self.setLayout(main_layout)

        self.change_report_view()

    # ==========================================
    # ADD LIVE DATA FROM STM32 (via DashboardPage)
    # ==========================================

    def add_live_data(self, temp, hum, status):
        """Called by DashboardPage with real STM32 sensor values."""

        current_time = datetime.now()

        # ALARM CLASSIFICATION
        if status == "INTRUSION":
            alarm_name = "Intrusion Detected"
            priority   = "Critical"
        elif status == "WARNING":
            alarm_name = "High Temperature"
            priority   = "High"
        else:
            alarm_name = "No Alarm"
            priority   = "None"

        # SENSOR LOG
        self.logs.append([
            current_time,
            f"{temp} °C",
            f"{hum} %",
            status
        ])

        # ALARM LOG
        self.alarm_logs.append([
            current_time.strftime("%d-%m-%Y %H:%M:%S"),
            alarm_name,
            priority
        ])

        # AUTO ROTATE — keep max 300 rows
        if len(self.logs) > 300:
            self.logs.pop(0)
        if len(self.alarm_logs) > 300:
            self.alarm_logs.pop(0)

        self.change_report_view()

    # ==========================================
    # CHANGE REPORT VIEW
    # ==========================================

    def change_report_view(self):
        report_type = self.export_type_combo.currentText()

        self.table.clear()
        self.table.setRowCount(0)

        # ---- TEMPERATURE & HUMIDITY ----
        if report_type == "Temperature & Humidity":
            self.table.setColumnCount(4)
            self.table.setHorizontalHeaderLabels(
                ["Time", "Temperature", "Humidity", "Status"]
            )

            for row_data in self.logs:
                row = self.table.rowCount()
                self.table.insertRow(row)

                display_data = [
                    row_data[0].strftime("%d-%m-%Y %H:%M:%S"),
                    row_data[1], row_data[2], row_data[3]
                ]

                for col, value in enumerate(display_data):
                    item = QTableWidgetItem(value)
                    item.setTextAlignment(Qt.AlignCenter)
                    if value == "WARNING":
                        item.setForeground(QColor("orange"))
                    elif value == "NORMAL":
                        item.setForeground(QColor("#00FF66"))
                    elif value == "INTRUSION":
                        item.setForeground(QColor("#FF3B30"))
                    self.table.setItem(row, col, item)

        # ---- ALARM LOGS ----
        elif report_type == "Alarm Logs":
            self.table.setColumnCount(3)
            self.table.setHorizontalHeaderLabels(
                ["Time", "Alarm Name", "Priority"]
            )

            for row_data in self.alarm_logs:
                row = self.table.rowCount()
                self.table.insertRow(row)

                for col, value in enumerate(row_data):
                    item = QTableWidgetItem(value)
                    item.setTextAlignment(Qt.AlignCenter)
                    if value == "Critical":
                        item.setForeground(QColor("#FF3B30"))
                    elif value == "High":
                        item.setForeground(QColor("#FF9500"))
                    elif value == "Medium":
                        item.setForeground(QColor("#FFD60A"))
                    self.table.setItem(row, col, item)

        # ---- COMPLETE REPORT ----
        else:
            self.table.setColumnCount(6)
            self.table.setHorizontalHeaderLabels([
                "Time", "Temperature", "Humidity",
                "Status", "Alarm", "Priority"
            ])

            for i in range(len(self.logs)):
                row = self.table.rowCount()
                self.table.insertRow(row)

                sensor = self.logs[i]

                if i < len(self.alarm_logs):
                    alarm_name = self.alarm_logs[i][1]
                    priority   = self.alarm_logs[i][2]
                else:
                    alarm_name = "No Alarm"
                    priority   = "-"

                display_data = [
                    sensor[0].strftime("%d-%m-%Y %H:%M:%S"),
                    sensor[1], sensor[2], sensor[3],
                    alarm_name, priority
                ]

                for col, value in enumerate(display_data):
                    item = QTableWidgetItem(value)
                    item.setTextAlignment(Qt.AlignCenter)
                    if value == "WARNING":
                        item.setForeground(QColor("orange"))
                    elif value == "NORMAL":
                        item.setForeground(QColor("#00FF66"))
                    elif value == "INTRUSION":
                        item.setForeground(QColor("#FF3B30"))
                    elif value == "Critical":
                        item.setForeground(QColor("#FF3B30"))
                    elif value == "High":
                        item.setForeground(QColor("#FF9500"))
                    elif value == "Medium":
                        item.setForeground(QColor("#FFD60A"))
                    elif value == "No Alarm":
                        item.setForeground(QColor("#7A7A7A"))
                    self.table.setItem(row, col, item)

        # ---- COLUMN SIZING ----
        self.table.horizontalHeader().setStretchLastSection(False)

        if report_type == "Temperature & Humidity":
            self.table.setColumnWidth(0, 240)
            self.table.setColumnWidth(1, 180)
            self.table.setColumnWidth(2, 180)
            self.table.setColumnWidth(3, 180)
        elif report_type == "Alarm Logs":
            self.table.setColumnWidth(0, 260)
            self.table.setColumnWidth(1, 420)
            self.table.setColumnWidth(2, 180)
        else:
            self.table.setColumnWidth(0, 220)
            self.table.setColumnWidth(1, 150)
            self.table.setColumnWidth(2, 150)
            self.table.setColumnWidth(3, 160)
            self.table.setColumnWidth(4, 260)
            self.table.setColumnWidth(5, 160)

    # ==========================================
    # UPDATE INTERVAL
    # ==========================================

    def update_interval(self):
        interval = self.interval_combo.currentText()
        QMessageBox.information(
            self,
            "Interval Updated",
            f"Data save interval set to {interval}"
        )

    # ==========================================
    # FILTER LOGS BY DATE RANGE
    # ==========================================

    def get_filtered_logs(self):
        from_dt = self.from_datetime.dateTime().toPyDateTime()
        to_dt   = self.to_datetime.dateTime().toPyDateTime()

        filtered = []
        for row in self.logs:
            if from_dt <= row[0] <= to_dt:
                filtered.append([
                    row[0].strftime("%d-%m-%Y %H:%M:%S"),
                    row[1], row[2], row[3]
                ])
        return filtered

    # # ==========================================
    # # EXPORT CSV
    # # ==========================================

    # def export_csv(self):
    #     report_type = self.export_type_combo.currentText()

    #     file_name, _ = QFileDialog.getSaveFileName(
    #         self, "Save CSV", "", "CSV Files (*.csv)"
    #     )
    #     if not file_name:
    #         return

    #     filtered_logs = self.get_filtered_logs()

    #     with open(file_name, "w", newline="") as file:
    #         writer = csv.writer(file)

    #         if report_type == "Temperature & Humidity":
    #             writer.writerow(["Time", "Temperature", "Humidity"])
    #             for row in filtered_logs:
    #                 writer.writerow([row[0], row[1], row[2]])

    #         elif report_type == "Alarm Logs":
    #             writer.writerow(["Time", "Status"])
    #             for row in filtered_logs:
    #                 writer.writerow([row[0], row[3]])

    #         else:
    #             writer.writerow(["Time", "Temperature", "Humidity", "Status"])
    #             writer.writerows(filtered_logs)

    #     QMessageBox.information(
    #         self, "Export Complete",
    #         f"{report_type} CSV exported successfully"
    #     )
    # ==========================================
    # EXPORT CSV
    # ==========================================

    def export_csv(self):

        file_name, _ = QFileDialog.getSaveFileName(

            self,

            "Save CSV",

            "report.csv",

            "CSV Files (*.csv)"

        )

        # ======================================
        # USER CANCELLED
        # ======================================

        if not file_name:
            return

        try:

            with open(
                file_name,
                "w",
                newline=""
            ) as file:

                writer = csv.writer(file)

                writer.writerow([

                    "Time",
                    "Temperature",
                    "Humidity",
                    "LDR",
                    "Track",
                    "RGB",
                    "Status"

                ])

                writer.writerows(
                    self.logs
                )

            QMessageBox.information(

                self,

                "Export Complete",

                "CSV exported successfully."

            )

        except Exception as e:

            QMessageBox.warning(

                self,

                "Export Error",

                str(e)

            )



    # # ==========================================
    # # EXPORT PDF
    # # ==========================================

    # def export_pdf(self):
    #     report_type = self.export_type_combo.currentText()

    #     file_name, _ = QFileDialog.getSaveFileName(
    #         self, "Save PDF", "", "PDF Files (*.pdf)"
    #     )
    #     if not file_name:
    #         return

    #     filtered_logs = self.get_filtered_logs()

    #     doc      = SimpleDocTemplate(file_name)
    #     styles   = getSampleStyleSheet()
    #     elements = []

    #     elements.append(Paragraph("SMART MONITOR REPORT", styles['Title']))
    #     elements.append(Spacer(1, 20))

    #     if report_type == "Temperature & Humidity":
    #         table_data = [["Time", "Temperature", "Humidity"]]
    #         for row in filtered_logs:
    #             table_data.append([row[0], row[1], row[2]])

    #     elif report_type == "Alarm Logs":
    #         table_data = [["Time", "Status"]]
    #         for row in filtered_logs:
    #             table_data.append([row[0], row[3]])

    #     else:
    #         table_data = [["Time", "Temperature", "Humidity", "Status"]]
    #         table_data.extend(filtered_logs)

    #     pdf_table = Table(table_data)
    #     pdf_table.setStyle(TableStyle([
    #         ('BACKGROUND', (0, 0), (-1, 0), colors.cyan),
    #         ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
    #         ('ALIGN',      (0, 0), (-1, -1), 'CENTER'),
    #         ('GRID',       (0, 0), (-1, -1), 1, colors.black),
    #         ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
    #         ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    #     ]))

    #     elements.append(pdf_table)
    #     doc.build(elements)

    #     QMessageBox.information(
    #         self, "Export Complete",
    #         f"{report_type} PDF exported successfully"
    #     )

  
    # ==========================================
    # EXPORT PDF
    # ==========================================

    def export_pdf(self):

        report_type = self.export_type_combo.currentText()

        file_name, _ = QFileDialog.getSaveFileName(

            self,

            "Save PDF",

            "report.pdf",

            "PDF Files (*.pdf)"

        )

        # ======================================
        # USER CANCELLED
        # ======================================

        if not file_name:
            return

        try:

            # ======================================
            # CREATE PDF
            # ======================================

            doc = SimpleDocTemplate(
                file_name
            )

            styles = getSampleStyleSheet()

            elements = []

            # ======================================
            # TITLE
            # ======================================

            title = Paragraph(

                "SMART ENVIRONMENT MONITOR REPORT",

                styles['Title']

            )

            elements.append(title)

            elements.append(
                Spacer(1, 20)
            )

            # ======================================
            # TABLE DATA
            # ======================================

            table_data = [[

                "Time",
                "Temperature",
                "Humidity",
                "LDR",
                "Track",
                "RGB",
                "Status"

            ]]

            # ======================================
            # ADD LOGS
            # ======================================

            for row in self.logs:

                table_data.append(row)

            # ======================================
            # CREATE TABLE
            # ======================================

            pdf_table = Table(table_data)

            pdf_table.setStyle(TableStyle([

                (
                    'BACKGROUND',
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#00C2FF")
                ),

                (
                    'TEXTCOLOR',
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),

                (
                    'ALIGN',
                    (0, 0),
                    (-1, -1),
                    'CENTER'
                ),

                (
                    'FONTNAME',
                    (0, 0),
                    (-1, 0),
                    'Helvetica-Bold'
                ),

                (
                    'BOTTOMPADDING',
                    (0, 0),
                    (-1, 0),
                    12
                ),

                (
                    'BACKGROUND',
                    (0, 1),
                    (-1, -1),
                    colors.beige
                ),

                (
                    'GRID',
                    (0, 0),
                    (-1, -1),
                    1,
                    colors.black
                )

            ]))

            # ======================================
            # ADD TABLE
            # ======================================

            elements.append(
                pdf_table
            )

            # ======================================
            # BUILD PDF
            # ======================================

            doc.build(elements)

            QMessageBox.information(

                self,

                "Export Complete",

                "PDF exported successfully."

            )

        except Exception as e:

            QMessageBox.warning(

                self,

                "PDF Export Error",

                str(e)

            )
  



# ==========================================
# ALERTS & LOGS PAGE
# ==========================================

class AlertsPage(QWidget):

    def __init__(self):
        super().__init__()

        self.alert_logs = []

        # ---- MAIN LAYOUT ----
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(20)

        # ---- HEADER ----
        header_layout = QHBoxLayout()

        title = QLabel("ALERTS & LOGS")
        title.setStyleSheet("font-size:28px; font-weight:bold; color:white;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        clear_btn = QPushButton("Clear Logs")
        clear_btn.clicked.connect(self.clear_logs)
        clear_btn.setFixedHeight(42)
        clear_btn.setStyleSheet("""
            QPushButton{
                background-color:#FF4444; border:none; border-radius:10px;
                font-size:14px; font-weight:bold;
                padding-left:15px; padding-right:15px;
            }
            QPushButton:hover{ background-color:#E53935; }
        """)
        header_layout.addWidget(clear_btn)

        # ---- SUMMARY CARDS ----
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(20)

        self.critical_card = self.create_summary_card("Critical", "0", "#FF3B30")
        self.high_card     = self.create_summary_card("High",     "0", "#FF9500")
        self.medium_card   = self.create_summary_card("Medium",   "0", "#FFD60A")
        self.low_card      = self.create_summary_card("Low",      "0", "#32ADE6")

        summary_layout.addWidget(self.critical_card)
        summary_layout.addWidget(self.high_card)
        summary_layout.addWidget(self.medium_card)
        summary_layout.addWidget(self.low_card)

        # ---- SEARCH BAR ----
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Alarm Name...")
        self.search_input.setFixedHeight(42)
        self.search_input.setStyleSheet("""
            border:none; border-radius:12px;
            padding-left:15px; font-size:14px;
        """)

        # ---- ALERT TABLE ----
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Sr No", "Time", "Alarm Name", "Priority"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget{
                border:none; border-radius:15px;
                font-size:14px; gridline-color:#2B2B2B;
            }
            QHeaderView::section{
                background-color:#252525; border:none;
                padding:12px; font-size:14px; font-weight:bold;
            }
            QScrollBar:vertical{ width:10px; border:none; }
            QScrollBar::handle:vertical{ background:#00C2FF; border-radius:5px; }
        """)

        # ---- ASSEMBLE ----
        main_layout.addLayout(header_layout)
        main_layout.addLayout(summary_layout)
        main_layout.addWidget(self.search_input)
        main_layout.addWidget(self.table)
        self.setLayout(main_layout)

    # ==========================================
    # CREATE SUMMARY CARD
    # ==========================================

    def create_summary_card(self, title, value, color):
        card = QFrame()
        card.setObjectName("card")
        card.setFixedHeight(110)
        card.setStyleSheet("QFrame{ border-radius:18px; }")

        layout = QVBoxLayout()

        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet(
            f"font-size:16px; font-weight:bold; color:{color};"
        )

        value_lbl = QLabel(value)
        value_lbl.setAlignment(Qt.AlignCenter)
        value_lbl.setStyleSheet("font-size:30px; font-weight:bold;")

        layout.addStretch()
        layout.addWidget(title_lbl)
        layout.addWidget(value_lbl)
        layout.addStretch()

        card.setLayout(layout)
        card.value_label = value_lbl   # store ref for updates
        return card

    # ==========================================
    # ADD REAL ALERT FROM STM32 (via DashboardPage)
    # ==========================================

    def add_real_alert(self, alarm_name, priority):
        """Called by DashboardPage on WARNING or INTRUSION status."""

        current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        sr_no        = self.table.rowCount() + 1
        row_position = self.table.rowCount()

        self.table.insertRow(row_position)

        data = [str(sr_no), current_time, alarm_name, priority]
        self.alert_logs.append(data)

        for col, value in enumerate(data):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignCenter)

            if value == "Critical":
                item.setForeground(QColor("#FF3B30"))
            elif value == "High":
                item.setForeground(QColor("#FF9500"))
            elif value == "Medium":
                item.setForeground(QColor("#FFD60A"))
            elif value == "Low":
                item.setForeground(QColor("#32ADE6"))

            self.table.setItem(row_position, col, item)

        self.table.scrollToBottom()
        self.update_summary_cards()

    # ==========================================
    # UPDATE SUMMARY CARDS
    # ==========================================

    def update_summary_cards(self):
        critical = high = medium = low = 0

        for row in self.alert_logs:
            p = row[3]
            if p == "Critical": critical += 1
            elif p == "High":   high += 1
            elif p == "Medium": medium += 1
            elif p == "Low":    low += 1

        self.critical_card.value_label.setText(str(critical))
        self.high_card.value_label.setText(str(high))
        self.medium_card.value_label.setText(str(medium))
        self.low_card.value_label.setText(str(low))

    # ==========================================
    # CLEAR LOGS
    # ==========================================

    def clear_logs(self):
        self.table.setRowCount(0)
        self.alert_logs.clear()
        self.update_summary_cards()
        QMessageBox.information(self, "Logs Cleared", "All alert logs removed.")


# ==========================================
# SETTINGS PAGE
# ==========================================

class SettingsPage(QWidget):

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.dark_mode   = True

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(25)

        title = QLabel("SETTINGS")
        title.setStyleSheet("font-size:30px; font-weight:bold;")

        subtitle = QLabel("Customize system preferences and controls")
        subtitle.setStyleSheet("font-size:14px; color:#9E9E9E;")

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        # ---- APPEARANCE CARD ----
        appearance_card = QFrame()
        appearance_card.setObjectName("card")
        appearance_card.setStyleSheet("QFrame{ border-radius:18px; }")

        appearance_layout = QVBoxLayout()
        appearance_layout.setContentsMargins(20, 20, 20, 20)

        appearance_title = QLabel("Appearance")
        appearance_title.setStyleSheet("font-size:20px; font-weight:bold;")

        toggle_layout = QHBoxLayout()
        toggle_label  = QLabel("Theme")
        toggle_label.setStyleSheet("font-size:15px; font-weight:600;")

        self.switch_frame = QFrame()
        self.switch_frame.setFixedSize(80, 36)
        self.switch_frame.setCursor(Qt.PointingHandCursor)
        self.switch_frame.setStyleSheet(
            "QFrame{ background-color:#00C2FF; border-radius:18px; }"
        )

        switch_layout = QHBoxLayout()
        switch_layout.setContentsMargins(5, 5, 5, 5)

        self.theme_icon = QLabel("☾")
        self.theme_icon.setFixedSize(26, 26)
        self.theme_icon.setAlignment(Qt.AlignCenter)
        self.theme_icon.setStyleSheet("""
            background-color:white; border-radius:13px;
            color:black; font-size:14px; font-weight:bold;
        """)

        switch_layout.addWidget(self.theme_icon, alignment=Qt.AlignLeft)
        self.switch_frame.setLayout(switch_layout)
        self.switch_frame.mousePressEvent = self.toggle_theme_switch

        toggle_layout.addWidget(toggle_label)
        toggle_layout.addStretch()
        toggle_layout.addWidget(self.switch_frame)

        appearance_layout.addWidget(appearance_title)
        appearance_layout.addSpacing(15)
        appearance_layout.addLayout(toggle_layout)
        appearance_card.setLayout(appearance_layout)

        # ---- SOUND CARD ----
        sound_card = QFrame()
        sound_card.setObjectName("card")
        sound_card.setStyleSheet("QFrame{ border-radius:18px; }")

        sound_layout = QVBoxLayout()
        sound_layout.setContentsMargins(20, 20, 20, 20)

        sound_title = QLabel("Sound Settings")
        sound_title.setStyleSheet("font-size:20px; font-weight:bold;")

        volume_layout = QHBoxLayout()
        volume_label  = QLabel("Alarm Volume")
        volume_label.setStyleSheet("font-size:15px; font-weight:600;")

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setFixedWidth(180)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal{ height:6px; background:#2B2B2B; border-radius:3px; }
            QSlider::handle:horizontal{ background:#00C2FF; width:14px; margin:-5px 0; border-radius:7px; }
            QSlider::sub-page:horizontal{ background:#00C2FF; border-radius:3px; }
        """)

        self.volume_value = QLabel("70%")
        self.volume_value.setStyleSheet("font-size:13px; font-weight:bold; color:#00C2FF;")
        self.volume_slider.valueChanged.connect(self.update_volume)

        volume_layout.addWidget(volume_label)
        volume_layout.addStretch()
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addSpacing(10)
        volume_layout.addWidget(self.volume_value)

        sound_layout.addWidget(sound_title)
        sound_layout.addSpacing(15)
        sound_layout.addLayout(volume_layout)
        sound_card.setLayout(sound_layout)

        # ---- SYSTEM INFO CARD ----
        info_card = QFrame()
        info_card.setObjectName("card")
        info_card.setStyleSheet("QFrame{ border-radius:18px; }")

        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(20, 20, 20, 20)

        info_title = QLabel("System Information")
        info_title.setStyleSheet("font-size:20px; font-weight:bold;")

        info_labels = [
            "Project : Smart Environment Monitoring System",
            "Version : 1.0.0",
            "Microcontroller : STM32",
            "GUI Framework : PyQt5",
            "Developer : Aarushi",
            "Communication : UART / Serial"
        ]

        info_layout.addWidget(info_title)
        info_layout.addSpacing(10)

        for text in info_labels:
            lbl = QLabel(text)
            lbl.setStyleSheet("font-size:14px; color:#D0D0D0; padding:4px;")
            info_layout.addWidget(lbl)

        info_card.setLayout(info_layout)

        # ---- SAVE BUTTON ----
        save_btn = QPushButton("Save Settings")
        save_btn.setFixedWidth(240)
        save_btn.setFixedHeight(48)
        save_btn.setStyleSheet("""
            QPushButton{
                background-color:#00C2FF; border:none; border-radius:12px;
                font-size:15px; font-weight:bold;
            }
            QPushButton:hover{ background-color:#00A8DD; }
        """)
        save_btn.clicked.connect(self.save_settings)

        main_layout.addSpacing(10)
        main_layout.addWidget(appearance_card)
        main_layout.addWidget(sound_card)
        main_layout.addWidget(info_card)
        main_layout.addStretch()
        main_layout.addWidget(save_btn)
        self.setLayout(main_layout)

    def update_volume(self):
        self.volume_value.setText(f"{self.volume_slider.value()}%")

    def toggle_theme_switch(self, event):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.switch_frame.setStyleSheet(
                "QFrame{ background-color:#00C2FF; border-radius:18px; }"
            )
            self.theme_icon.setText("☾")
            self.switch_frame.layout().setAlignment(self.theme_icon, Qt.AlignLeft)
            self.main_window.apply_theme(True)
        else:
            self.switch_frame.setStyleSheet(
                "QFrame{ background-color:#FFD43B; border-radius:18px; }"
            )
            self.theme_icon.setText("☀")
            self.switch_frame.layout().setAlignment(self.theme_icon, Qt.AlignRight)
            self.main_window.apply_theme(False)

    def save_settings(self):
        QMessageBox.information(
            self, "Settings Saved", "System settings updated successfully."
        )


# ==========================================
# USER MANAGEMENT PAGE
# ==========================================

class UserManagementPage(QWidget):

    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(20)

        # ---- HEADER ----
        header_layout = QHBoxLayout()

        title = QLabel("USER MANAGEMENT")
        title.setStyleSheet("font-size:30px; font-weight:bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        create_btn = QPushButton("Create Account")
        create_btn.clicked.connect(self.create_account)

        delete_btn = QPushButton("Delete Account")
        delete_btn.clicked.connect(self.delete_account)

        for btn in [create_btn, delete_btn]:
            btn.setFixedHeight(42)
            btn.setStyleSheet("""
                QPushButton{
                    background-color:#00C2FF; border:none; border-radius:10px;
                    font-size:14px; font-weight:bold;
                    padding-left:18px; padding-right:18px;
                }
                QPushButton:hover{ background-color:#00A8DD; }
            """)
            header_layout.addWidget(btn)

        # ---- INPUT CARD ----
        input_card = QFrame()
        input_card.setObjectName("card")
        input_card.setStyleSheet("QFrame{ border-radius:18px; }")

        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(20, 20, 20, 20)
        input_layout.setSpacing(15)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["Admin", "User"])

        self.show_password = QCheckBox("Show Password")
        self.show_password.stateChanged.connect(self.toggle_password)
        self.show_password.setStyleSheet("font-size:13px;")

        for widget in [self.username_input, self.password_input, self.role_combo]:
            widget.setFixedHeight(42)
            widget.setStyleSheet("""
                background-color:#2B2B2B; border:none; border-radius:10px;
                padding-left:12px; font-size:14px;
            """)
            input_layout.addWidget(widget)

        input_layout.addWidget(self.show_password)
        input_card.setLayout(input_layout)

        # ---- SEARCH BAR ----
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Username...")
        self.search_input.setFixedHeight(42)
        self.search_input.textChanged.connect(self.search_user)
        self.search_input.setStyleSheet("""
            border:none; border-radius:12px;
            padding-left:15px; font-size:14px;
        """)

        # ---- TABLE TITLE ----
        table_title = QLabel("REGISTERED ACCOUNTS")
        table_title.setStyleSheet("font-size:22px; font-weight:bold;")

        # ---- ACCOUNTS TABLE ----
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(6)
        self.accounts_table.setHorizontalHeaderLabels(
            ["ID", "Username", "Role", "Password", "Status", "Last Login"]
        )
        self.accounts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.accounts_table.verticalHeader().setVisible(False)
        self.accounts_table.setAlternatingRowColors(True)
        self.accounts_table.setStyleSheet("""
            QTableWidget{
                alternate-background-color:#202020; border:none;
                border-radius:18px; font-size:14px; gridline-color:#2B2B2B;
            }
            QHeaderView::section{
                background-color:#252525; border:none;
                padding:12px; font-size:14px; font-weight:bold;
            }
        """)

        main_layout.addLayout(header_layout)
        main_layout.addWidget(input_card)
        main_layout.addWidget(self.search_input)
        main_layout.addWidget(table_title)
        main_layout.addWidget(self.accounts_table)
        self.setLayout(main_layout)

        self.load_users()

    def load_users(self):
        self.accounts_table.setRowCount(0)
        conn   = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users  = cursor.fetchall()
        conn.close()

        for row_data in users:
            row = self.accounts_table.rowCount()
            self.accounts_table.insertRow(row)
            for col, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                if value == "Admin":   item.setForeground(QColor("#FF9500"))
                elif value == "User":  item.setForeground(QColor("#00C2FF"))
                elif value == "Active":  item.setForeground(QColor("#00FF66"))
                elif value == "Offline": item.setForeground(QColor("#FF3B30"))
                self.accounts_table.setItem(row, col, item)

    def create_account(self):
        username = self.username_input.text()
        password = self.password_input.text()
        role     = self.role_combo.currentText()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Enter username and password.")
            return

        conn   = sqlite3.connect("users.db")
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users(username,password,role,status,last_login) VALUES(?,?,?,?,?)",
                (username, password, role, "Offline", "-")
            )
            conn.commit()
            QMessageBox.information(
                self, "Success", f"{role} account created successfully."
            )
        except Exception:
            QMessageBox.warning(self, "Duplicate User", "Username already exists.")
        finally:
            conn.close()

        self.username_input.clear()
        self.password_input.clear()
        self.load_users()

    def delete_account(self):
        selected_row = self.accounts_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Error", "Select account to delete.")
            return

        username = self.accounts_table.item(selected_row, 1).text()
        if username == "admin":
            QMessageBox.warning(self, "Protected", "Default admin cannot be deleted.")
            return

        conn   = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username=?", (username,))
        conn.commit()
        conn.close()
        self.load_users()

    def toggle_password(self):
        self.password_input.setEchoMode(
            QLineEdit.Normal if self.show_password.isChecked()
            else QLineEdit.Password
        )

    def search_user(self):
        search_text = self.search_input.text().lower()
        for row in range(self.accounts_table.rowCount()):
            item = self.accounts_table.item(row, 1)
            if item:
                self.accounts_table.setRowHidden(
                    row, search_text not in item.text().lower()
                )


# ==========================================
# ABOUT PAGE
# ==========================================

class AboutPage(QWidget):

    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)

        title = QLabel("ABOUT SYSTEM")
        title.setStyleSheet("font-size:32px; font-weight:bold;")

        subtitle = QLabel("Smart Environment Monitoring System")
        subtitle.setStyleSheet("font-size:16px; color:#A0A0A0;")

        about_card = QFrame()
        about_card.setObjectName("card")
        about_card.setStyleSheet("QFrame{ border-radius:22px; }")

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(35, 35, 35, 35)
        card_layout.setSpacing(25)

        logo = QLabel("🌍")
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("font-size:70px;")

        project_name = QLabel("SMART ENVIRONMENT\nMONITORING SYSTEM")
        project_name.setAlignment(Qt.AlignCenter)
        project_name.setStyleSheet("font-size:28px; font-weight:bold;")

        description = QLabel(
            "This system is designed to monitor temperature, humidity, alarms and "
            "environmental conditions using STM32 and PyQt5 GUI.\n\n"
            "The dashboard provides real-time monitoring, report generation, "
            "alerts management and user control."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("font-size:15px; color:#CFCFCF; line-height:24px;")

        info_frame = QFrame()
        info_frame.setStyleSheet(
            "QFrame{ background-color:#252525; border-radius:16px; }"
        )

        info_layout = QGridLayout()
        info_layout.setContentsMargins(25, 25, 25, 25)
        info_layout.setHorizontalSpacing(40)
        info_layout.setVerticalSpacing(20)

        info = [
            ("Version",         "1.0.0"),
            ("Microcontroller", "STM32"),
            ("Framework",       "PyQt5"),
            ("Communication",   "UART / Serial"),
            ("Developer",       "Aarushi"),
            ("Status",          "ACTIVE"),
        ]

        for r, (left, right) in enumerate(info):
            left_lbl = QLabel(left)
            left_lbl.setStyleSheet("font-size:14px; font-weight:bold; color:#00C2FF;")
            right_lbl = QLabel(right)
            right_lbl.setStyleSheet("font-size:14px;")
            info_layout.addWidget(left_lbl,  r, 0)
            info_layout.addWidget(right_lbl, r, 1)

        info_frame.setLayout(info_layout)

        footer = QLabel("© 2026 Smart Monitoring System")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("font-size:13px; color:#808080;")

        card_layout.addWidget(logo)
        card_layout.addWidget(project_name)
        card_layout.addWidget(description)
        card_layout.addWidget(info_frame)
        card_layout.addStretch()
        card_layout.addWidget(footer)
        about_card.setLayout(card_layout)

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)
        main_layout.addWidget(about_card)
        self.setLayout(main_layout)


# ==========================================
# DATABASE SETUP
# ==========================================

def create_database():
    conn   = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT UNIQUE,
            password   TEXT,
            role       TEXT,
            status     TEXT,
            last_login TEXT
        )
    """)

    cursor.execute("SELECT * FROM users WHERE username=?", ("admin",))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users(username,password,role,status,last_login) VALUES(?,?,?,?,?)",
            ("admin", "admin123", "Admin", "Offline", "-")
        )

    conn.commit()
    conn.close()


# ==========================================
# LOGIN PAGE
# ==========================================

class LoginPage(QWidget):

    def __init__(self):
        super().__init__()
        self._login_in_progress = False   # guard against double-login

        self.setWindowTitle("LOGIN")
        self.resize(450, 500)
        self.setStyleSheet("""
            QWidget{ background-color:#181818; font-family:Segoe UI; }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        title = QLabel("SMART MONITOR")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:32px; font-weight:bold; color:#00C2FF;")

        subtitle = QLabel("Login to continue")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size:15px; color:#BDBDBD;")

        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet("QFrame{ border-radius:20px; }")

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(20)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        login_input_style = """
            QLineEdit{
                background-color:rgba(255,255,255,0.12);
                color:white;
                border:2px solid rgba(255,255,255,0.18);
                border-radius:14px;
                padding-left:15px;
                font-size:15px;
            }
            QLineEdit:focus{ border:2px solid #00C2FF; }
        """

        for widget in [self.username_input, self.password_input]:
            widget.setFixedHeight(45)
            widget.setStyleSheet(login_input_style)
            card_layout.addWidget(widget)

        self.username_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self.login)

        login_btn = QPushButton("LOGIN")
        login_btn.setFixedHeight(48)
        login_btn.setStyleSheet("""
            QPushButton{
                background-color:#00C2FF; border:none; border-radius:12px;
                font-size:15px; font-weight:bold;
            }
            QPushButton:hover{ background-color:#00A8DD; }
        """)
        login_btn.clicked.connect(self.login)

        card_layout.addWidget(login_btn)
        card.setLayout(card_layout)

        main_layout.addStretch()
        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)
        main_layout.addSpacing(20)
        main_layout.addWidget(card)
        main_layout.addStretch()
        self.setLayout(main_layout)

    def login(self):
        if self._login_in_progress:   # block double-fire
            return
        self._login_in_progress = True

        username = self.username_input.text()
        password = self.password_input.text()

        conn   = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role FROM users WHERE username=? AND password=?",
            (username, password)
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            role         = result[0]
            current_time = QDateTime.currentDateTime().toString("dd-MM-yyyy hh:mm:ss")

            conn   = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET status=?, last_login=? WHERE username=?",
                ("Active", current_time, username)
            )
            conn.commit()
            conn.close()

            self.main_window = MainWindow(username, role)
            self.main_window.show()
            self.close()

        else:
            self._login_in_progress = False   # reset so user can try again
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Login Failed")
            msg.setText("Invalid username or password.")
            msg.setStyleSheet("""
                QMessageBox{ background-color:#171B22; }
                QLabel{ color:white; font-size:14px; }
                QPushButton{
                    background-color:#00C2FF; color:white; border:none;
                    border-radius:8px; min-width:90px; min-height:32px;
                    font-size:13px; font-weight:bold;
                }
                QPushButton:hover{ background-color:#00A8DD; }
            """)
            msg.exec_()

# ==========================================
# MAIN WINDOW
# ==========================================

class MainWindow(QMainWindow):

    def __init__(self, username, role):
        super().__init__()
        self.current_user = username
        self.current_role = role

        self.setWindowTitle("SMART ENVIRONMENT MONITOR")
        self.resize(1500, 850)
        self.sidebar_expanded = False

        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ---- SIDEBAR ----
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(70)
        self.sidebar.setStyleSheet("background-color:#111111;")

        sidebar_layout = QVBoxLayout()

        self.toggle_btn = QPushButton("☰")
        self.toggle_btn.setFixedHeight(50)
        self.toggle_btn.clicked.connect(self.toggle_sidebar)

        self.logo = QLabel("SMART MONITOR")
        self.logo.setStyleSheet(
            "font-size:22px; font-weight:bold; padding:15px;"
        )

        sidebar_layout.addWidget(self.toggle_btn)
        sidebar_layout.addWidget(self.logo)
        self.logo.hide()

        self.menu_buttons = []

        # MENU ITEMS BASED ON ROLE
        if self.current_role == "Admin":
            self.menu_items = [
                ("fa5s.home",                 "Dashboard"),
                ("fa5s.chart-bar",            "Reports"),
                ("fa5s.exclamation-triangle", "Alerts & Logs"),
                ("fa5s.users",                "User Management"),
                ("fa5s.cog",                  "Settings"),
                ("fa5s.info-circle",          "About"),
            ]
        else:
            self.menu_items = [
                ("fa5s.home",                 "Dashboard"),
                ("fa5s.chart-bar",            "Reports"),
                ("fa5s.exclamation-triangle", "Alerts & Logs"),
                ("fa5s.cog",                  "Settings"),
                ("fa5s.info-circle",          "About"),
            ]

        for icon_name, text in self.menu_items:
            btn = QPushButton()
            btn.setIcon(qta.icon(icon_name, color="#EAEAEA"))
            btn.setIconSize(QSize(22, 22))
            btn.setText("")
            btn.setFixedHeight(55)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton{
                    border:none; background-color:transparent;
                    border-radius:10px; text-align:center; padding-left:0px;
                }
                QPushButton:hover{ background-color:#242424; }
            """)
            sidebar_layout.addWidget(btn)
            self.menu_buttons.append(btn)

        sidebar_layout.addStretch()

        # LOGOUT BUTTON
        self.logout_btn = QPushButton()
        self.logout_btn.setIcon(qta.icon("fa5s.sign-out-alt", color="#FF4D4D"))
        self.logout_btn.setIconSize(QSize(22, 22))
        self.logout_btn.setText("")
        self.logout_btn.setFixedHeight(55)
        self.logout_btn.clicked.connect(self.logout)
        self.logout_btn.setStyleSheet("""
            QPushButton{
                text-align:left; padding-left:18px; border:none;
                font-size:15px; font-weight:600; color:#FF4D4D;
                background-color:transparent; border-radius:12px;
            }
            QPushButton:hover{ background-color:#242424; }
        """)
        sidebar_layout.addWidget(self.logout_btn)
        self.sidebar.setLayout(sidebar_layout)

        # ==========================================
        # STACKED PAGES — CORRECT BUILD ORDER
        # ==========================================

        self.pages = QStackedWidget()

        # 1. Build pages
        self.dashboard_page = DashboardPage(self.current_user)
        self.reports_page   = ReportsPage()
        self.alerts_page    = AlertsPage()

        # 2. Link dashboard to reports & alerts BEFORE serial starts firing
        self.dashboard_page.reports_page = self.reports_page
        self.dashboard_page.alerts_page  = self.alerts_page

        # 3. Add to stack in menu order
        self.pages.addWidget(self.dashboard_page)   # index 0
        self.pages.addWidget(self.reports_page)     # index 1
        self.pages.addWidget(self.alerts_page)      # index 2

        if self.current_role == "Admin":
            self.pages.addWidget(UserManagementPage())  # index 3
            self.pages.addWidget(SettingsPage(self))    # index 4
            self.pages.addWidget(AboutPage())           # index 5
        else:
            self.pages.addWidget(SettingsPage(self))    # index 3
            self.pages.addWidget(AboutPage())           # index 4

        # ---- MENU CONNECTIONS ----
        for index, btn in enumerate(self.menu_buttons):
            btn.clicked.connect(
                lambda checked, i=index: (
                    self.pages.setCurrentIndex(i),
                    self.highlight_button(i)
                )
            )

        self.highlight_button(0)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.pages)
        main_widget.setLayout(main_layout)

        self.apply_theme(True)

    # ==========================================
    # TOGGLE SIDEBAR
    # ==========================================

    def toggle_sidebar(self):
        if self.sidebar_expanded:
            self.sidebar.setFixedWidth(70)
            self.logo.hide()
            for btn in self.menu_buttons:
                btn.setText("")
                btn.setStyleSheet("""
                    QPushButton{
                        border:none; background-color:transparent;
                        border-radius:10px; text-align:center; padding-left:0px;
                    }
                    QPushButton:hover{ background-color:#242424; }
                """)
            self.logout_btn.setText("")
            self.sidebar_expanded = False
        else:
            self.sidebar.setFixedWidth(230)
            self.logo.show()
            for btn, (icon_name, text) in zip(self.menu_buttons, self.menu_items):
                btn.setText(f"  {text}")
                btn.setStyleSheet("""
                    QPushButton{
                        text-align:left; padding-left:18px; border:none;
                        font-size:15px; font-weight:600; color:#DADADA;
                        background-color:transparent; border-radius:12px;
                    }
                    QPushButton:hover{ background-color:#242424; }
                """)
            self.logout_btn.setText("  Logout")
            self.sidebar_expanded = True

    # ==========================================
    # HIGHLIGHT ACTIVE MENU BUTTON
    # ==========================================

    def highlight_button(self, index):
        for i, btn in enumerate(self.menu_buttons):
            if i == index:
                btn.setStyleSheet("""
                    QPushButton{
                        border:none; background-color:#1E1E1E;
                        border-left:4px solid #00C2FF; border-radius:10px;
                        text-align:center; padding-left:0px;
                    }
                    QPushButton:hover{ background-color:#2A2A2A; }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton{
                        text-align:left; padding-left:20px; border:none;
                        font-size:16px; color:#BDBDBD;
                        background-color:transparent; border-radius:10px;
                    }
                    QPushButton:hover{ background-color:#2A2A2A; color:white; }
                """)

    # ==========================================
    # APPLY THEME
    # ==========================================

    def apply_theme(self, dark=True):
        if dark:
            self.setStyleSheet("""
                QMainWindow{ background-color:#0F1115; }
                QWidget{ background-color:#0F1115; color:#FFFFFF; font-family:Segoe UI; }
                QFrame#sidebar{ background-color:#0B0D12; border-right:1px solid #1E232B; }
                QFrame#card{ background-color:#171B22; border-radius:18px; border:1px solid #222831; }
                QLabel{ background:transparent; color:#FFFFFF; }
                QPushButton{ border:none; }
                QPushButton:hover{ background-color:#242A33; }
                QLineEdit, QComboBox, QDateTimeEdit{
                    background-color:#222831; border:none;
                    border-radius:10px; padding-left:10px; min-height:38px;
                }
                QTableWidget{
                    background-color:#171B22; border:none;
                    border-radius:15px; gridline-color:#2B2B2B;
                }
                QHeaderView::section{
                    background-color:#222831; border:none;
                    padding:10px; font-weight:bold;
                }
                QScrollBar:vertical{ background:#171B22; width:10px; border:none; }
                QScrollBar::handle:vertical{ background:#00C2FF; border-radius:5px; }
            """)
            for btn, (icon_name, _) in zip(self.menu_buttons, self.menu_items):
                btn.setIcon(qta.icon(icon_name, color="white"))
            self.logout_btn.setIcon(qta.icon("fa5s.sign-out-alt", color="#FF4D4D"))

        else:
            self.setStyleSheet("""
                QMainWindow{ background-color:#F4F7FB; }
                QWidget{ background-color:#F4F7FB; color:#111827; font-family:Segoe UI; }
                QFrame#sidebar{ background-color:#FFFFFF; border-right:1px solid #DDE3EA; }
                QFrame#card{ background-color:#FFFFFF; border-radius:18px; border:1px solid #E5E7EB; }
                QLabel{ background:transparent; color:#111827; }
                QPushButton{ color:#111827; border:none; }
                QPushButton:hover{ background-color:#E8EEF5; }
                QLineEdit, QComboBox, QDateTimeEdit{
                    background-color:white; color:#111827;
                    border:1px solid #D1D5DB; border-radius:10px;
                    padding-left:10px; min-height:38px;
                }
                QTableWidget{
                    background-color:white; color:#111827;
                    border:none; border-radius:15px; gridline-color:#E5E7EB;
                }
                QHeaderView::section{
                    background-color:#EEF2F7; color:#111827;
                    border:none; padding:10px; font-weight:bold;
                }
                QScrollBar:vertical{ background:#F4F7FB; width:10px; border:none; }
                QScrollBar::handle:vertical{ background:#00C2FF; border-radius:5px; }
            """)
            for btn, (icon_name, _) in zip(self.menu_buttons, self.menu_items):
                btn.setIcon(qta.icon(icon_name, color="#111827"))
            self.logout_btn.setIcon(qta.icon("fa5s.sign-out-alt", color="#FF4D4D"))

    # # ==========================================
    # # SET USER OFFLINE ON CLOSE
    # # ==========================================

    # def closeEvent(self, event):
    #     conn   = sqlite3.connect("users.db")
    #     cursor = conn.cursor()
    #     cursor.execute(
    #         "UPDATE users SET status=? WHERE username=?",
    #         ("Offline", self.current_user)
    #     )
    #     conn.commit()
    #     conn.close()
    #     event.accept()

    # # ==========================================
    # # LOGOUT
    # # ==========================================

    # def logout(self):
    #     conn   = sqlite3.connect("users.db")
    #     cursor = conn.cursor()
    #     cursor.execute(
    #         "UPDATE users SET status=? WHERE username=?",
    #         ("Offline", self.current_user)
    #     )
    #     conn.commit()
    #     conn.close()

    #     self.login_page = LoginPage()
    #     self.login_page.show()
    #     self.close()

    def closeEvent(self, event):
        self.close_serial()   # release COM6 before closing
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET status=? WHERE username=?",
            ("Offline", self.current_user)
        )
        conn.commit()
        conn.close()
        event.accept()

    def logout(self):
        self.close_serial()   # release COM6 before logout
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET status=? WHERE username=?",
            ("Offline", self.current_user)
        )
        conn.commit()
        conn.close()

        self.login_page = LoginPage()
        self.login_page.show()
        self.close()
# ==========================================
# RUN APP
# ==========================================

QApplication.setAttribute(Qt.AA_DisableWindowContextHelpButton)

app = QApplication(sys.argv)
app.setStyle("Fusion")

create_database()

login = LoginPage()
login.show()

sys.exit(app.exec_())