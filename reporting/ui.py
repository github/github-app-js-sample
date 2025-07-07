# UI components for Reporting
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox,
                             QDateEdit, QGridLayout, QGroupBox, QFileDialog, QMessageBox,
                             QCheckBox, QScrollArea) # Added QCheckBox, QScrollArea
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QIcon
from database import SessionLocal
from driver_management.models import Driver
from vehicle_management.models import Vehicle
# from reporting.logic import generate_driver_performance_data, generate_vehicle_utilization_data # To be created
# from reporting.export import export_to_pdf, export_to_excel # To be created
# --- Actual imports ---
from reporting.logic import generate_driver_performance_data, generate_vehicle_utilization_data
from reporting.export import export_to_pdf, export_to_excel
import pandas as pd # For data handling

class ReportingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setWindowTitle("گزارش گیری پیشرفته")

        title_label = QLabel("ماژول گزارش گیری", self)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        self.layout.addWidget(title_label)

        # --- Filters Group ---
        filters_group = QGroupBox("تنظیمات و فیلترهای گزارش")
        filters_layout = QGridLayout(filters_group)

        filters_layout.addWidget(QLabel("نوع گزارش:"), 0, 0)
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItem("عملکرد راننده", "driver_performance")
        self.report_type_combo.addItem("میزان استفاده از خودرو", "vehicle_utilization")
        self.report_type_combo.currentIndexChanged.connect(self.update_specific_filters)
        filters_layout.addWidget(self.report_type_combo, 0, 1, 1, 3)

        filters_layout.addWidget(QLabel("از تاریخ:"), 1, 0)
        self.start_date_edit = QDateEdit(QDate.currentDate().addMonths(-1)) # Default to one month ago
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy/MM/dd") # Placeholder for Jalali
        filters_layout.addWidget(self.start_date_edit, 1, 1)

        filters_layout.addWidget(QLabel("تا تاریخ:"), 1, 2)
        self.end_date_edit = QDateEdit(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("yyyy/MM/dd") # Placeholder for Jalali
        filters_layout.addWidget(self.end_date_edit, 1, 3)

        # --- Specific Filters Placeholder ---
        self.specific_filters_group = QGroupBox("فیلترهای خاص گزارش")
        self.specific_filters_layout = QVBoxLayout(self.specific_filters_group)
        filters_layout.addWidget(self.specific_filters_group, 2, 0, 1, 4)

        self.layout.addWidget(filters_group)
        self.update_specific_filters() # Initial call

        # --- Action Buttons ---
        action_layout = QHBoxLayout()
        self.generate_excel_button = QPushButton(QIcon.fromTheme("document-export"), " تولید گزارش Excel")
        self.generate_excel_button.clicked.connect(lambda: self.generate_report(export_format="excel"))
        action_layout.addWidget(self.generate_excel_button)

        self.generate_pdf_button = QPushButton(QIcon.fromTheme("document-export"), " تولید گزارش PDF")
        self.generate_pdf_button.clicked.connect(lambda: self.generate_report(export_format="pdf"))
        action_layout.addWidget(self.generate_pdf_button)
        self.layout.addLayout(action_layout)

        self.status_label = QLabel("برای تولید گزارش، نوع و فیلترهای مورد نظر را انتخاب کرده و روی دکمه مربوطه کلیک کنید.")
        self.status_label.setWordWrap(True)
        self.layout.addWidget(self.status_label)
        self.layout.addStretch()


    def update_specific_filters(self):
        # Clear previous specific filters
        while self.specific_filters_layout.count():
            child = self.specific_filters_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        report_type = self.report_type_combo.currentData()
        db_session = SessionLocal()

        if report_type == "driver_performance":
            self.specific_filters_layout.addWidget(QLabel("انتخاب رانندگان (یک یا چند مورد):"))
            self.driver_checkboxes = {}
            drivers = db_session.query(Driver).filter(Driver.is_active == True).order_by(Driver.name).all()

            scroll_area = QScrollArea() # Make checkboxes scrollable if many drivers
            scroll_content = QWidget()
            scroll_layout = QVBoxLayout(scroll_content)

            for driver in drivers:
                cb = QCheckBox(f"{driver.name} (کد ملی: {driver.national_id})")
                self.driver_checkboxes[driver.id] = cb
                scroll_layout.addWidget(cb)

            scroll_area.setWidget(scroll_content)
            scroll_area.setWidgetResizable(True)
            scroll_area.setFixedHeight(150) # Adjust height as needed
            self.specific_filters_layout.addWidget(scroll_area)

        elif report_type == "vehicle_utilization":
            self.specific_filters_layout.addWidget(QLabel("انتخاب خودروها (یک یا چند مورد):"))
            self.vehicle_checkboxes = {}
            vehicles = db_session.query(Vehicle).filter(Vehicle.is_active == True).order_by(Vehicle.plate_number).all()

            scroll_area = QScrollArea()
            scroll_content = QWidget()
            scroll_layout = QVBoxLayout(scroll_content)

            for vehicle in vehicles:
                cb = QCheckBox(f"{vehicle.plate_number} ({vehicle.model})")
                self.vehicle_checkboxes[vehicle.id] = cb
                scroll_layout.addWidget(cb)

            scroll_area.setWidget(scroll_content)
            scroll_area.setWidgetResizable(True)
            scroll_area.setFixedHeight(150)
            self.specific_filters_layout.addWidget(scroll_area)

        db_session.close()


    def get_selected_filters(self):
        filters = {
            "report_type": self.report_type_combo.currentData(),
            "start_date": self.start_date_edit.date().toPyDate(),
            "end_date": self.end_date_edit.date().toPyDate(),
            "selected_driver_ids": [],
            "selected_vehicle_ids": [],
        }
        if filters["start_date"] > filters["end_date"]:
            QMessageBox.warning(self, "خطای تاریخ", "تاریخ شروع نمی تواند بعد از تاریخ پایان باشد.")
            return None

        if filters["report_type"] == "driver_performance":
            filters["selected_driver_ids"] = [driver_id for driver_id, cb in self.driver_checkboxes.items() if cb.isChecked()]
            if not filters["selected_driver_ids"]: # If none selected, assume all
                 filters["selected_driver_ids"] = list(self.driver_checkboxes.keys())


        elif filters["report_type"] == "vehicle_utilization":
            filters["selected_vehicle_ids"] = [vehicle_id for vehicle_id, cb in self.vehicle_checkboxes.items() if cb.isChecked()]
            if not filters["selected_vehicle_ids"]: # If none selected, assume all
                 filters["selected_vehicle_ids"] = list(self.vehicle_checkboxes.keys())
        return filters

    def generate_report(self, export_format="excel"):
        filters = self.get_selected_filters()
        if not filters:
            return

        self.status_label.setText(f"در حال تولید گزارش {self.report_type_combo.currentText()}...")
        QApplication.processEvents() # Update UI

        data = pd.DataFrame() # Initialize empty dataframe
        filename_suggestion = "گزارش"
        report_title_for_export = self.report_type_combo.currentText()

        if filters["report_type"] == "driver_performance":
            data = generate_driver_performance_data(filters)
            filename_suggestion = f"گزارش_عملکرد_رانندگان_{filters['start_date']}_تا_{filters['end_date']}"
            report_title_for_export = f"گزارش عملکرد رانندگان از {filters['start_date']} تا {filters['end_date']}"

        elif filters["report_type"] == "vehicle_utilization":
            data = generate_vehicle_utilization_data(filters)
            filename_suggestion = f"گزارش_استفاده_خودروها_{filters['start_date']}_تا_{filters['end_date']}"
            report_title_for_export = f"گزارش استفاده خودروها از {filters['start_date']} تا {filters['end_date']}"
        else:
            self.status_label.setText("نوع گزارش انتخاب نشده یا نامعتبر است.")
            return

        if data is None or data.empty: # Check if data is None as well
            self.status_label.setText("داده ای برای گزارش با فیلترهای انتخابی یافت نشد.")
            QMessageBox.information(self, "نتیجه گزارش", "داده ای برای گزارش با فیلترهای انتخابی یافت نشد.")
            return

        report_info_for_pdf = {
            "title": report_title_for_export,
            "start_date": filters["start_date"],
            "end_date": filters["end_date"],
            # Add any other relevant filter info to display in PDF header if needed
        }

        try:
            if export_format == "excel":
                file_path, _ = QFileDialog.getSaveFileName(self, "ذخیره گزارش Excel", f"{filename_suggestion}.xlsx", "Excel Files (*.xlsx)")
                if file_path:
                    export_to_excel(data, file_path, self.report_type_combo.currentText()) # Pass simple title for sheet name
                    self.status_label.setText(f"گزارش Excel با موفقیت در {file_path} ذخیره شد.")
                    QMessageBox.information(self, "موفقیت", f"گزارش Excel با موفقیت در {file_path} ذخیره شد.")
            elif export_format == "pdf":
                file_path, _ = QFileDialog.getSaveFileName(self, "ذخیره گزارش PDF", f"{filename_suggestion}.pdf", "PDF Files (*.pdf)")
                if file_path:
                    export_to_pdf(data, file_path, report_info_for_pdf)
                    self.status_label.setText(f"گزارش PDF با موفقیت در {file_path} ذخیره شد.")
                    QMessageBox.information(self, "موفقیت", f"گزارش PDF با موفقیت در {file_path} ذخیره شد.")

        except Exception as e:
            self.status_label.setText(f"خطا در تولید یا ذخیره گزارش: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در تولید یا ذخیره گزارش: {e}")


if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    from database import create_tables # For testing

    app = QApplication(sys.argv)
    create_tables() # Ensure DB and tables exist if logic needs them
    main_widget = ReportingWidget()
    main_widget.show()
    sys.exit(app.exec())
