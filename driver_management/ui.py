# UI components for Driver Management
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit,
                             QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
                             QDateEdit, QCheckBox, QMessageBox, QHBoxLayout, QTextEdit)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QIcon
from database import SessionLocal
from driver_management.models import Driver
# from utils.jalali_converter import qdate_to_jalali_str, jalali_str_to_qdate # Uncomment when implemented

class DriverManagementWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setWindowTitle("مدیریت رانندگان")

        title_label = QLabel("ماژول مدیریت رانندگان", self)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        self.layout.addWidget(title_label)

        action_layout = QHBoxLayout()
        self.add_driver_button = QPushButton(QIcon.fromTheme("list-add"), " افزودن راننده جدید")
        self.add_driver_button.clicked.connect(self.open_add_driver_dialog)
        action_layout.addWidget(self.add_driver_button)

        self.edit_driver_button = QPushButton(QIcon.fromTheme("document-edit"), " ویرایش راننده منتخب")
        self.edit_driver_button.clicked.connect(self.open_edit_driver_dialog)
        self.edit_driver_button.setEnabled(False)
        action_layout.addWidget(self.edit_driver_button)

        self.delete_driver_button = QPushButton(QIcon.fromTheme("list-remove"), " حذف راننده منتخب")
        self.delete_driver_button.clicked.connect(self.delete_selected_driver)
        self.delete_driver_button.setEnabled(False)
        action_layout.addWidget(self.delete_driver_button)
        self.layout.addLayout(action_layout)

        self.drivers_table = QTableWidget(self)
        self.drivers_table.setColumnCount(8) # ID, Name, National ID, License No, License Expiry, Contact, Active, Status
        self.drivers_table.setHorizontalHeaderLabels([
            "شناسه", "نام و نام خانوادگی", "کد ملی", "شماره گواهینامه",
            "پایان اعتبار گواهینامه", "شماره تماس", "فعال؟", "وضعیت گواهینامه"
        ])
        self.drivers_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.drivers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.drivers_table.selectionModel().selectionChanged.connect(self.on_table_selection_changed)
        self.drivers_table.doubleClicked.connect(self.open_edit_driver_dialog_on_double_click)
        self.layout.addWidget(self.drivers_table)

        self.refresh_drivers_table()

    def on_table_selection_changed(self):
        selected = self.drivers_table.selectionModel().hasSelection()
        self.edit_driver_button.setEnabled(selected)
        self.delete_driver_button.setEnabled(selected)

    def get_selected_driver_id(self):
        selected_items = self.drivers_table.selectedItems()
        return int(selected_items[0].text()) if selected_items else None

    def open_add_driver_dialog(self):
        dialog = AddEditDriverDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_drivers_table()

    def open_edit_driver_dialog(self):
        driver_id = self.get_selected_driver_id()
        if driver_id is None:
            QMessageBox.information(self, "راهنما", "لطفا ابتدا یک راننده از جدول انتخاب کنید.")
            return

        db_session = SessionLocal()
        driver_to_edit = db_session.query(Driver).get(driver_id)
        db_session.close()

        if not driver_to_edit:
            QMessageBox.critical(self, "خطا", "راننده مورد نظر یافت نشد.")
            self.refresh_drivers_table()
            return

        dialog = AddEditDriverDialog(driver=driver_to_edit, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_drivers_table()

    def open_edit_driver_dialog_on_double_click(self, model_index):
        if model_index.isValid():
            self.open_edit_driver_dialog()

    def delete_selected_driver(self):
        driver_id = self.get_selected_driver_id()
        if driver_id is None:
            QMessageBox.information(self, "راهنما", "لطفا ابتدا یک راننده از جدول انتخاب کنید.")
            return

        reply = QMessageBox.question(self, "تایید حذف",
                                     f"آیا از حذف راننده با شناسه {driver_id} اطمینان دارید؟",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            db_session = SessionLocal()
            try:
                driver_to_delete = db_session.query(Driver).get(driver_id)
                if driver_to_delete:
                    # TODO: Check dependencies (active shifts, missions)
                    db_session.delete(driver_to_delete)
                    db_session.commit()
                    QMessageBox.information(self, "موفقیت", f"راننده با شناسه {driver_id} حذف شد.")
                    self.refresh_drivers_table()
                else:
                    QMessageBox.critical(self, "خطا", "راننده یافت نشد.")
            except Exception as e:
                db_session.rollback()
                QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در حذف راننده: {e}")
            finally:
                db_session.close()

    def refresh_drivers_table(self):
        self.drivers_table.setRowCount(0)
        self.edit_driver_button.setEnabled(False)
        self.delete_driver_button.setEnabled(False)
        db_session = SessionLocal()
        drivers = db_session.query(Driver).order_by(Driver.id).all()
        today = QDate.currentDate().toPyDate()

        for row, driver in enumerate(drivers):
            self.drivers_table.insertRow(row)
            self.drivers_table.setItem(row, 0, QTableWidgetItem(str(driver.id)))
            self.drivers_table.setItem(row, 1, QTableWidgetItem(driver.name))
            self.drivers_table.setItem(row, 2, QTableWidgetItem(driver.national_id))
            self.drivers_table.setItem(row, 3, QTableWidgetItem(driver.license_number or "N/A"))

            # expiry_str = qdate_to_jalali_str(QDate.fromPyDate(driver.license_expiry_date)) if driver.license_expiry_date else "ندارد"
            expiry_str = str(driver.license_expiry_date) if driver.license_expiry_date else "ندارد"
            self.drivers_table.setItem(row, 4, QTableWidgetItem(expiry_str))
            self.drivers_table.setItem(row, 5, QTableWidgetItem(driver.contact_number or "N/A"))
            self.drivers_table.setItem(row, 6, QTableWidgetItem("بله" if driver.is_active else "خیر"))

            status_msg = "OK"
            status_color = Qt.GlobalColor.black
            if driver.license_expiry_date and driver.license_expiry_date < today:
                status_msg = "گواهینامه منقضی شده"
                status_color = Qt.GlobalColor.red

            status_item = QTableWidgetItem(status_msg)
            status_item.setForeground(status_color)
            self.drivers_table.setItem(row, 7, status_item)

        self.drivers_table.resizeColumnsToContents()
        db_session.close()


class AddEditDriverDialog(QDialog):
    def __init__(self, driver: Driver = None, parent=None):
        super().__init__(parent)
        self.driver_instance = driver
        self.db_session = SessionLocal()

        self.setWindowTitle("افزودن/ویرایش اطلاعات راننده" if driver else "افزودن راننده جدید")
        self.setMinimumWidth(450)
        self.layout = QFormLayout(self)

        self.name_input = QLineEdit(self)
        self.national_id_input = QLineEdit(self)
        self.national_id_input.setPlaceholderText("مثال: 0012345678")
        self.license_number_input = QLineEdit(self)
        self.license_expiry_date_input = QDateEdit(self)
        self.license_expiry_date_input.setCalendarPopup(True)
        self.license_expiry_date_input.setDisplayFormat("yyyy/MM/dd") # Placeholder for Jalali
        self.license_expiry_date_input.setDate(QDate.currentDate().addYears(1)) # Default to 1 year from now

        self.contact_number_input = QLineEdit(self)
        self.address_input = QTextEdit(self) # For multi-line address
        self.address_input.setFixedHeight(80)
        self.certifications_input = QTextEdit(self) # For multi-line text
        self.certifications_input.setFixedHeight(80)
        self.certifications_input.setPlaceholderText("هر گواهینامه در یک خط جدید یا با کاما جدا شود")
        self.violations_input = QTextEdit(self) # For multi-line text
        self.violations_input.setFixedHeight(80)
        self.violations_input.setPlaceholderText("هر تخلف در یک خط جدید یا با کاما جدا شود")
        self.is_active_checkbox = QCheckBox("راننده فعال است؟", self)
        self.is_active_checkbox.setChecked(True)

        self.layout.addRow("نام و نام خانوادگی (*):", self.name_input)
        self.layout.addRow("کد ملی (*):", self.national_id_input)
        self.layout.addRow("شماره گواهینامه:", self.license_number_input)
        self.layout.addRow("پایان اعتبار گواهینامه:", self.license_expiry_date_input)
        self.layout.addRow("شماره تماس:", self.contact_number_input)
        self.layout.addRow("آدرس:", self.address_input)
        self.layout.addRow("گواهینامه ها/مجوزها:", self.certifications_input)
        self.layout.addRow("سوابق تخلفات:", self.violations_input)
        self.layout.addRow(self.is_active_checkbox)

        self.button_box = QHBoxLayout()
        self.save_button = QPushButton(QIcon.fromTheme("document-save"), " ذخیره")
        self.save_button.clicked.connect(self.save_driver)
        self.cancel_button = QPushButton(QIcon.fromTheme("dialog-cancel"), " انصراف")
        self.cancel_button.clicked.connect(self.reject)
        self.button_box.addWidget(self.save_button)
        self.button_box.addWidget(self.cancel_button)
        self.layout.addRow(self.button_box)

        if self.driver_instance:
            self.load_driver_data()

    def load_driver_data(self):
        self.name_input.setText(self.driver_instance.name)
        self.national_id_input.setText(self.driver_instance.national_id)
        self.license_number_input.setText(self.driver_instance.license_number or "")
        if self.driver_instance.license_expiry_date:
            self.license_expiry_date_input.setDate(QDate.fromPyDate(self.driver_instance.license_expiry_date))
        self.contact_number_input.setText(self.driver_instance.contact_number or "")
        self.address_input.setText(self.driver_instance.address or "")
        self.certifications_input.setText(self.driver_instance.certifications or "")
        self.violations_input.setText(self.driver_instance.violations_history or "")
        self.is_active_checkbox.setChecked(self.driver_instance.is_active)

    def save_driver(self):
        name = self.name_input.text().strip()
        national_id = self.national_id_input.text().strip()
        license_number = self.license_number_input.text().strip() or None # Allow empty if not mandatory

        if not name or not national_id:
            QMessageBox.warning(self, "خطا در ورودی", "نام و کد ملی راننده نمی‌توانند خالی باشند.")
            return

        # Basic National ID validation (length) - more complex validation can be added
        if not (national_id.isdigit() and len(national_id) == 10):
             QMessageBox.warning(self, "خطای فرمت", "کد ملی باید ۱۰ رقم و فقط شامل اعداد باشد.")
             return

        license_expiry = self.license_expiry_date_input.date().toPyDate()
        contact = self.contact_number_input.text().strip() or None
        address = self.address_input.toPlainText().strip() or None
        certs = self.certifications_input.toPlainText().strip() or None
        violations = self.violations_input.toPlainText().strip() or None
        is_active = self.is_active_checkbox.isChecked()

        try:
            if self.driver_instance is None: # New Driver
                existing_national_id = self.db_session.query(Driver).filter(Driver.national_id == national_id).first()
                if existing_national_id:
                    QMessageBox.warning(self, "خطای تکرار", f"راننده با کد ملی '{national_id}' قبلا ثبت شده است.")
                    return
                if license_number:
                    existing_license = self.db_session.query(Driver).filter(Driver.license_number == license_number).first()
                    if existing_license:
                        QMessageBox.warning(self, "خطای تکرار", f"راننده با شماره گواهینامه '{license_number}' قبلا ثبت شده است.")
                        return

                new_driver = Driver(name=name, national_id=national_id, license_number=license_number,
                                    license_expiry_date=license_expiry, contact_number=contact,
                                    address=address, certifications=certs, violations_history=violations,
                                    is_active=is_active)
                self.db_session.add(new_driver)
                QMessageBox.information(self, "موفقیت", "راننده جدید با موفقیت اضافه شد.")
            else: # Edit Driver
                if self.driver_instance.national_id != national_id:
                    conflicting_nid = self.db_session.query(Driver).filter(Driver.national_id == national_id, Driver.id != self.driver_instance.id).first()
                    if conflicting_nid:
                        QMessageBox.warning(self, "خطای تکرار", f"کد ملی '{national_id}' متعلق به راننده دیگری است.")
                        return
                if license_number and self.driver_instance.license_number != license_number:
                     conflicting_lic = self.db_session.query(Driver).filter(Driver.license_number == license_number, Driver.id != self.driver_instance.id).first()
                     if conflicting_lic:
                        QMessageBox.warning(self, "خطای تکرار", f"شماره گواهینامه '{license_number}' متعلق به راننده دیگری است.")
                        return

                self.driver_instance.name = name
                self.driver_instance.national_id = national_id
                self.driver_instance.license_number = license_number
                self.driver_instance.license_expiry_date = license_expiry
                self.driver_instance.contact_number = contact
                self.driver_instance.address = address
                self.driver_instance.certifications = certs
                self.driver_instance.violations_history = violations
                self.driver_instance.is_active = is_active
                self.db_session.add(self.driver_instance)
                QMessageBox.information(self, "موفقیت", "اطلاعات راننده با موفقیت ویرایش شد.")

            self.db_session.commit()
            self.accept()
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در ذخیره سازی اطلاعات راننده: {e}")

    def done(self, result):
        self.db_session.close()
        super().done(result)


if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    from database import create_tables # For testing standalone

    app = QApplication(sys.argv)
    create_tables() # Ensure tables exist for testing

    # To test AddEditDriverDialog
    # dialog = AddEditDriverDialog()
    # dialog.show()

    # To test DriverManagementWidget
    main_widget = DriverManagementWidget()
    main_widget.show()

    sys.exit(app.exec())
