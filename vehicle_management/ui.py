# UI components for Vehicle Management
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit,
                             QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
                             QDateEdit, QCheckBox, QMessageBox, QHBoxLayout, QSpinBox)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QIcon # For icons in buttons
from database import SessionLocal
from vehicle_management.models import Vehicle
# from utils.jalali_converter import to_jalali, to_gregorian, qdate_to_jalali_str, jalali_str_to_qdate # Uncomment when implemented

class VehicleManagementWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setWindowTitle("مدیریت خودروها")

        # Title Label
        title_label = QLabel("ماژول مدیریت خودروها", self)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        self.layout.addWidget(title_label)

        # Action Buttons Layout
        action_layout = QHBoxLayout()
        self.add_vehicle_button = QPushButton(QIcon.fromTheme("list-add"), " افزودن خودرو جدید") # Example icon
        self.add_vehicle_button.clicked.connect(self.open_add_vehicle_dialog)
        action_layout.addWidget(self.add_vehicle_button)

        self.edit_vehicle_button = QPushButton(QIcon.fromTheme("document-edit"), " ویرایش خودرو منتخب")
        self.edit_vehicle_button.clicked.connect(self.open_edit_vehicle_dialog)
        self.edit_vehicle_button.setEnabled(False) # Disabled until a row is selected
        action_layout.addWidget(self.edit_vehicle_button)

        self.delete_vehicle_button = QPushButton(QIcon.fromTheme("list-remove"), " حذف خودرو منتخب")
        self.delete_vehicle_button.clicked.connect(self.delete_selected_vehicle)
        self.delete_vehicle_button.setEnabled(False) # Disabled until a row is selected
        action_layout.addWidget(self.delete_vehicle_button)
        self.layout.addLayout(action_layout)


        # Vehicles Table
        self.vehicles_table = QTableWidget(self)
        self.vehicles_table.setColumnCount(9) # ID, پلاک, مدل, سال, بیمه ثالث, بیمه بدنه, معاینه فنی, فعال, وضعیت بیمه ها
        self.vehicles_table.setHorizontalHeaderLabels([
            "شناسه", "شماره پلاک", "مدل", "سال ساخت",
            "پایان بیمه ثالث", "پایان بیمه بدنه", "پایان معاینه فنی",
            "فعال؟", "وضعیت بیمه/معاینه"
        ])
        self.vehicles_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # Make table read-only by default
        self.vehicles_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows) # Select whole row
        self.vehicles_table.selectionModel().selectionChanged.connect(self.on_table_selection_changed)
        self.vehicles_table.doubleClicked.connect(self.open_edit_vehicle_dialog_on_double_click)

        self.layout.addWidget(self.vehicles_table)
        self.refresh_vehicles_table()

    def on_table_selection_changed(self):
        selected_rows = self.vehicles_table.selectionModel().hasSelection()
        self.edit_vehicle_button.setEnabled(selected_rows)
        self.delete_vehicle_button.setEnabled(selected_rows)

    def get_selected_vehicle_id(self):
        selected_items = self.vehicles_table.selectedItems()
        if not selected_items:
            return None
        # Assuming ID is in the first column
        return int(selected_items[0].text())

    def open_add_vehicle_dialog(self):
        dialog = AddEditVehicleDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_vehicles_table()

    def open_edit_vehicle_dialog(self):
        vehicle_id = self.get_selected_vehicle_id()
        if vehicle_id is None:
            QMessageBox.information(self, "راهنما", "لطفا ابتدا یک خودرو از جدول انتخاب کنید.")
            return

        db_session = SessionLocal()
        vehicle_to_edit = db_session.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        db_session.close()

        if not vehicle_to_edit:
            QMessageBox.critical(self, "خطا", "خودرو مورد نظر یافت نشد.")
            self.refresh_vehicles_table() # In case it was deleted by another process
            return

        dialog = AddEditVehicleDialog(vehicle=vehicle_to_edit, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_vehicles_table()

    def open_edit_vehicle_dialog_on_double_click(self, model_index):
        if model_index.isValid():
            self.open_edit_vehicle_dialog()


    def delete_selected_vehicle(self):
        vehicle_id = self.get_selected_vehicle_id()
        if vehicle_id is None:
            QMessageBox.information(self, "راهنما", "لطفا ابتدا یک خودرو از جدول انتخاب کنید.")
            return

        reply = QMessageBox.question(self, "تایید حذف",
                                     f"آیا از حذف خودرو با شناسه {vehicle_id} اطمینان دارید؟ این عمل قابل بازگشت نیست.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            db_session = SessionLocal()
            try:
                vehicle_to_delete = db_session.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
                if vehicle_to_delete:
                    # TODO: Check for dependencies (e.g., active missions, shifts) before deleting
                    # if db_session.query(Mission).filter(Mission.vehicle_id == vehicle_id, Mission.status not in ['COMPLETED', 'CANCELLED']).count() > 0:
                    #     QMessageBox.warning(self, "خطا در حذف", "این خودرو در ماموریت های فعال استفاده شده و قابل حذف نیست.")
                    #     return

                    db_session.delete(vehicle_to_delete)
                    db_session.commit()
                    QMessageBox.information(self, "موفقیت", f"خودرو با شناسه {vehicle_id} با موفقیت حذف شد.")
                    self.refresh_vehicles_table()
                else:
                    QMessageBox.critical(self, "خطا", "خودرو مورد نظر برای حذف یافت نشد.")
            except Exception as e:
                db_session.rollback()
                QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در حذف خودرو: {e}")
            finally:
                db_session.close()

    def refresh_vehicles_table(self):
        self.vehicles_table.setRowCount(0)
        self.edit_vehicle_button.setEnabled(False)
        self.delete_vehicle_button.setEnabled(False)
        db_session = SessionLocal()
        vehicles = db_session.query(Vehicle).order_by(Vehicle.id).all()
        today = QDate.currentDate().toPyDate()

        for row, vehicle in enumerate(vehicles):
            self.vehicles_table.insertRow(row)
            self.vehicles_table.setItem(row, 0, QTableWidgetItem(str(vehicle.id)))
            self.vehicles_table.setItem(row, 1, QTableWidgetItem(vehicle.plate_number))
            self.vehicles_table.setItem(row, 2, QTableWidgetItem(vehicle.model))
            self.vehicles_table.setItem(row, 3, QTableWidgetItem(str(vehicle.year)))

            # Date display (using Jalali stubs for now)
            # tp_expiry_str = qdate_to_jalali_str(QDate.fromPyDate(vehicle.third_party_insurance_expiry)) if vehicle.third_party_insurance_expiry else "ندارد"
            # body_expiry_str = qdate_to_jalali_str(QDate.fromPyDate(vehicle.body_insurance_expiry)) if vehicle.body_insurance_expiry else "ندارد"
            # tech_expiry_str = qdate_to_jalali_str(QDate.fromPyDate(vehicle.technical_inspection_expiry)) if vehicle.technical_inspection_expiry else "ندارد"
            tp_expiry_str = str(vehicle.third_party_insurance_expiry) if vehicle.third_party_insurance_expiry else "ندارد"
            body_expiry_str = str(vehicle.body_insurance_expiry) if vehicle.body_insurance_expiry else "ندارد"
            tech_expiry_str = str(vehicle.technical_inspection_expiry) if vehicle.technical_inspection_expiry else "ندارد"

            self.vehicles_table.setItem(row, 4, QTableWidgetItem(tp_expiry_str))
            self.vehicles_table.setItem(row, 5, QTableWidgetItem(body_expiry_str))
            self.vehicles_table.setItem(row, 6, QTableWidgetItem(tech_expiry_str))
            self.vehicles_table.setItem(row, 7, QTableWidgetItem("بله" if vehicle.is_active else "خیر"))

            # Status warnings
            warnings = []
            if vehicle.third_party_insurance_expiry and vehicle.third_party_insurance_expiry < today:
                warnings.append("بیمه ثالث منقضی شده")
            if vehicle.body_insurance_expiry and vehicle.body_insurance_expiry < today:
                warnings.append("بیمه بدنه منقضی شده")
            if vehicle.technical_inspection_expiry and vehicle.technical_inspection_expiry < today:
                warnings.append("معاینه فنی منقضی شده")

            status_item = QTableWidgetItem(", ".join(warnings) if warnings else "OK")
            if warnings:
                status_item.setForeground(Qt.GlobalColor.red)
            self.vehicles_table.setItem(row, 8, status_item)

        self.vehicles_table.resizeColumnsToContents()
        db_session.close()


class AddEditVehicleDialog(QDialog):
    def __init__(self, vehicle: Vehicle = None, parent=None):
        super().__init__(parent)
        self.vehicle_instance = vehicle # Renamed to avoid conflict with module name
        self.db_session = SessionLocal() # Keep one session for the dialog lifetime

        if self.vehicle_instance:
            self.setWindowTitle("ویرایش اطلاعات خودرو")
        else:
            self.setWindowTitle("افزودن خودرو جدید")

        self.layout = QFormLayout(self)
        self.setMinimumWidth(400) # Set a minimum width for the dialog

        self.plate_input = QLineEdit(self)
        self.plate_input.setPlaceholderText("مثال: 12الف345 ایران 67")
        self.model_input = QLineEdit(self)
        self.year_input = QSpinBox(self)
        self.year_input.setRange(1370, 1450) # Assuming Shamsi years, adjust if Gregorian
        self.year_input.setValue(QDate.currentDate().year() - 621 if QDate.currentDate().month() > 3 else QDate.currentDate().year() - 622) # Approximate Shamsi year

        # Date inputs - will use JalaliCalendar when integrated
        self.third_party_expiry_input = QDateEdit(self)
        self.third_party_expiry_input.setCalendarPopup(True)
        self.third_party_expiry_input.setDisplayFormat("yyyy/MM/dd") # Placeholder, use Jalali format later
        # self.third_party_expiry_input.setCalendarWidget(JalaliCalendarWidget()) # Example
        self.third_party_expiry_input.setDate(QDate.currentDate())

        self.body_expiry_input = QDateEdit(self)
        self.body_expiry_input.setCalendarPopup(True)
        self.body_expiry_input.setDisplayFormat("yyyy/MM/dd")
        self.body_expiry_input.setDate(QDate.currentDate())

        self.tech_inspection_expiry_input = QDateEdit(self)
        self.tech_inspection_expiry_input.setCalendarPopup(True)
        self.tech_inspection_expiry_input.setDisplayFormat("yyyy/MM/dd")
        self.tech_inspection_expiry_input.setDate(QDate.currentDate())

        self.is_active_checkbox = QCheckBox("خودرو فعال است؟", self)
        self.is_active_checkbox.setChecked(True)


        self.layout.addRow("شماره پلاک (*):", self.plate_input)
        self.layout.addRow("مدل خودرو (*):", self.model_input)
        self.layout.addRow("سال ساخت (*):", self.year_input)
        self.layout.addRow("پایان اعتبار بیمه ثالث:", self.third_party_expiry_input)
        self.layout.addRow("پایان اعتبار بیمه بدنه:", self.body_expiry_input)
        self.layout.addRow("پایان اعتبار معاینه فنی:", self.tech_inspection_expiry_input)
        self.layout.addRow(self.is_active_checkbox)

        # Buttons
        self.button_box = QHBoxLayout()
        self.save_button = QPushButton(QIcon.fromTheme("document-save"), " ذخیره", self)
        self.save_button.clicked.connect(self.save_vehicle)
        self.cancel_button = QPushButton(QIcon.fromTheme("dialog-cancel"), " انصراف", self)
        self.cancel_button.clicked.connect(self.reject)
        self.button_box.addWidget(self.save_button)
        self.button_box.addWidget(self.cancel_button)
        self.layout.addRow(self.button_box)

        if self.vehicle_instance:
            self.load_vehicle_data()

    def load_vehicle_data(self):
        self.plate_input.setText(self.vehicle_instance.plate_number)
        self.model_input.setText(self.vehicle_instance.model)
        self.year_input.setValue(self.vehicle_instance.year or QDate.currentDate().year() - 621) # Default if None

        # date_format = "yyyy-MM-dd" # Standard Python date format
        # if self.vehicle_instance.third_party_insurance_expiry:
        #     self.third_party_expiry_input.setDate(QDate.fromString(str(self.vehicle_instance.third_party_insurance_expiry), date_format))
        # if self.vehicle_instance.body_insurance_expiry:
        #     self.body_expiry_input.setDate(QDate.fromString(str(self.vehicle_instance.body_insurance_expiry), date_format))
        # if self.vehicle_instance.technical_inspection_expiry:
        #     self.tech_inspection_expiry_input.setDate(QDate.fromString(str(self.vehicle_instance.technical_inspection_expiry), date_format))

        # Using QDate.fromPyDate for direct conversion
        if self.vehicle_instance.third_party_insurance_expiry:
            self.third_party_expiry_input.setDate(QDate.fromPyDate(self.vehicle_instance.third_party_insurance_expiry))
        if self.vehicle_instance.body_insurance_expiry:
            self.body_expiry_input.setDate(QDate.fromPyDate(self.vehicle_instance.body_insurance_expiry))
        if self.vehicle_instance.technical_inspection_expiry:
            self.tech_inspection_expiry_input.setDate(QDate.fromPyDate(self.vehicle_instance.technical_inspection_expiry))

        self.is_active_checkbox.setChecked(self.vehicle_instance.is_active)


    def save_vehicle(self):
        plate_number = self.plate_input.text().strip()
        model = self.model_input.text().strip()
        year = self.year_input.value()

        if not plate_number or not model:
            QMessageBox.warning(self, "خطا در ورودی", "شماره پلاک و مدل خودرو نمی‌توانند خالی باشند.")
            return

        try:
            # Convert QDate to Python date objects
            # For Jalali, this would involve: jalali_str_to_qdate(self.third_party_expiry_input.text()).toPyDate()
            tp_expiry_date = self.third_party_expiry_input.date().toPyDate()
            body_expiry_date = self.body_expiry_input.date().toPyDate()
            tech_expiry_date = self.tech_inspection_expiry_input.date().toPyDate()


            if self.vehicle_instance is None: # Adding new vehicle
                # Check for duplicate plate number
                existing_vehicle = self.db_session.query(Vehicle).filter(Vehicle.plate_number == plate_number).first()
                if existing_vehicle:
                    QMessageBox.warning(self, "خطای تکرار", f"خودرو با شماره پلاک '{plate_number}' قبلا ثبت شده است.")
                    return # Do not close dialog, allow user to correct

                new_vehicle = Vehicle(
                    plate_number=plate_number,
                    model=model,
                    year=year,
                    third_party_insurance_expiry=tp_expiry_date,
                    has_third_party_insurance=tp_expiry_date >= QDate.currentDate().toPyDate(),
                    body_insurance_expiry=body_expiry_date,
                    has_body_insurance=body_expiry_date >= QDate.currentDate().toPyDate(),
                    technical_inspection_expiry=tech_expiry_date,
                    is_active=self.is_active_checkbox.isChecked()
                )
                self.db_session.add(new_vehicle)
                self.db_session.commit()
                QMessageBox.information(self, "موفقیت", "خودرو جدید با موفقیت اضافه شد.")
            else: # Editing existing vehicle
                # Check if plate number is changed and if it conflicts with another vehicle
                if self.vehicle_instance.plate_number != plate_number:
                    conflicting_vehicle = self.db_session.query(Vehicle).filter(Vehicle.plate_number == plate_number, Vehicle.id != self.vehicle_instance.id).first()
                    if conflicting_vehicle:
                        QMessageBox.warning(self, "خطای تکرار", f"خودرو دیگری با شماره پلاک '{plate_number}' وجود دارد.")
                        return

                self.vehicle_instance.plate_number = plate_number
                self.vehicle_instance.model = model
                self.vehicle_instance.year = year
                self.vehicle_instance.third_party_insurance_expiry = tp_expiry_date
                self.vehicle_instance.has_third_party_insurance = tp_expiry_date >= QDate.currentDate().toPyDate()
                self.vehicle_instance.body_insurance_expiry = body_expiry_date
                self.vehicle_instance.has_body_insurance = body_expiry_date >= QDate.currentDate().toPyDate()
                self.vehicle_instance.technical_inspection_expiry = tech_expiry_date
                self.vehicle_instance.is_active = self.is_active_checkbox.isChecked()

                self.db_session.add(self.vehicle_instance) # Add to session to track changes
                self.db_session.commit()
                QMessageBox.information(self, "موفقیت", "اطلاعات خودرو با موفقیت ویرایش شد.")

            self.accept() # Close dialog
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در ذخیره سازی اطلاعات: {e}")
        # finally:
        #     self.db_session.close() # Session is closed when dialog is closed

    def done(self, result):
        """Ensure db_session is closed when dialog finishes."""
        self.db_session.close()
        super().done(result)


if __name__ == '__main__':
    # Example usage (for testing this widget independently)
    import sys
    from PyQt6.QtWidgets import QApplication
    from database import create_tables, SessionLocal, User # For main app context

    # This standalone test needs a QApplication
    app = QApplication(sys.argv)

    # Ensure tables exist
    create_tables()

    # Mock a main window or parent if needed for context, otherwise None is fine for AddEditVehicleDialog
    # test_dialog_parent = QWidget()

    # Test Add/Edit Dialog
    # To test edit, you'd fetch a vehicle first
    # s = SessionLocal()
    # v = s.query(Vehicle).first()
    # s.close()
    # dialog = AddEditVehicleDialog(vehicle=v, parent=test_dialog_parent)

    dialog = AddEditVehicleDialog(parent=None) # Test Add mode
    dialog.show()

    # Or test the main widget
    # main_vehicle_widget = VehicleManagementWidget()
    # main_vehicle_widget.show()

    sys.exit(app.exec())
