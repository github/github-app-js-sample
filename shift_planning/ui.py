# UI components for Shift Planning
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget,
                             QTableWidgetItem, QDialog, QFormLayout, QLineEdit,
                             QTimeEdit, QComboBox, QMessageBox, QHBoxLayout, QTabWidget,
                             QGroupBox, QDateTimeEdit)
from PyQt6.QtCore import QTime, Qt, QDateTime
from PyQt6.QtGui import QIcon
from database import SessionLocal
from shift_planning.models import Shift, ShiftAssignment, ShiftType
from driver_management.models import Driver
from vehicle_management.models import Vehicle
# from utils.jalali_converter import # Import specific functions when ready

# --- Dialog for Shift Templates ---
class AddEditShiftTemplateDialog(QDialog):
    def __init__(self, template: Shift = None, parent=None):
        super().__init__(parent)
        self.template_instance = template
        self.db_session = SessionLocal()

        self.setWindowTitle("افزودن/ویرایش قالب شیفت" if template else "افزودن قالب شیفت جدید")
        self.setMinimumWidth(400)
        self.layout = QFormLayout(self)

        self.name_input = QLineEdit(self)
        self.type_combo = QComboBox(self)
        for shift_type in ShiftType:
            self.type_combo.addItem(shift_type.value, shift_type) # Store enum member as data

        self.start_time_input = QTimeEdit(self)
        self.start_time_input.setDisplayFormat("HH:mm")
        self.end_time_input = QTimeEdit(self)
        self.end_time_input.setDisplayFormat("HH:mm")
        self.description_input = QLineEdit(self)

        self.type_combo.currentIndexChanged.connect(self.toggle_time_inputs)

        self.layout.addRow("نام قالب (*):", self.name_input)
        self.layout.addRow("نوع شیفت (*):", self.type_combo)
        self.layout.addRow("زمان شروع:", self.start_time_input)
        self.layout.addRow("زمان پایان:", self.end_time_input)
        self.layout.addRow("توضیحات:", self.description_input)

        self.button_box = QHBoxLayout()
        self.save_button = QPushButton(QIcon.fromTheme("document-save"), " ذخیره")
        self.save_button.clicked.connect(self.save_template)
        self.cancel_button = QPushButton(QIcon.fromTheme("dialog-cancel"), " انصراف")
        self.cancel_button.clicked.connect(self.reject)
        self.button_box.addWidget(self.save_button)
        self.button_box.addWidget(self.cancel_button)
        self.layout.addRow(self.button_box)

        if self.template_instance:
            self.load_template_data()
        self.toggle_time_inputs() # Initial state based on type

    def toggle_time_inputs(self):
        selected_type = self.type_combo.currentData()
        enable_time = selected_type in [ShiftType.DAILY, ShiftType.WEEKLY]
        self.start_time_input.setEnabled(enable_time)
        self.end_time_input.setEnabled(enable_time)
        if not enable_time:
            self.start_time_input.setTime(QTime(0,0))
            self.end_time_input.setTime(QTime(0,0))


    def load_template_data(self):
        self.name_input.setText(self.template_instance.name)
        self.type_combo.setCurrentIndex(self.type_combo.findData(self.template_instance.type))
        if self.template_instance.start_time:
            self.start_time_input.setTime(QTime.fromPyTime(self.template_instance.start_time))
        if self.template_instance.end_time:
            self.end_time_input.setTime(QTime.fromPyTime(self.template_instance.end_time))
        self.description_input.setText(self.template_instance.description or "")

    def save_template(self):
        name = self.name_input.text().strip()
        shift_type_enum = self.type_combo.currentData() # Get the enum member

        if not name:
            QMessageBox.warning(self, "خطا", "نام قالب شیفت نمی‌تواند خالی باشد.")
            return

        start_time_val = self.start_time_input.time().toPyTime() if self.start_time_input.isEnabled() else None
        end_time_val = self.end_time_input.time().toPyTime() if self.end_time_input.isEnabled() else None
        description = self.description_input.text().strip() or None

        try:
            if self.template_instance is None: # New template
                existing = self.db_session.query(Shift).filter(Shift.name == name).first()
                if existing:
                    QMessageBox.warning(self, "خطای تکرار", f"قالب شیفتی با نام '{name}' قبلا ثبت شده است.")
                    return

                new_template = Shift(name=name, type=shift_type_enum, start_time=start_time_val,
                                     end_time=end_time_val, description=description)
                self.db_session.add(new_template)
                QMessageBox.information(self, "موفقیت", "قالب شیفت جدید با موفقیت اضافه شد.")
            else: # Edit template
                if self.template_instance.name != name:
                    conflicting = self.db_session.query(Shift).filter(Shift.name == name, Shift.id != self.template_instance.id).first()
                    if conflicting:
                        QMessageBox.warning(self, "خطای تکرار", f"قالب شیفت دیگری با نام '{name}' وجود دارد.")
                        return
                self.template_instance.name = name
                self.template_instance.type = shift_type_enum
                self.template_instance.start_time = start_time_val
                self.template_instance.end_time = end_time_val
                self.template_instance.description = description
                self.db_session.add(self.template_instance)
                QMessageBox.information(self, "موفقیت", "اطلاعات قالب شیفت با موفقیت ویرایش شد.")

            self.db_session.commit()
            self.accept()
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در ذخیره سازی قالب شیفت: {e}")

    def done(self, result):
        self.db_session.close()
        super().done(result)


# --- Main Shift Planning Widget ---
class ShiftPlanningWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setWindowTitle("برنامه ریزی شیفت ها")

        title_label = QLabel("ماژول برنامه ریزی شیفت ها", self)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        self.layout.addWidget(title_label)

        self.tabs = QTabWidget(self)
        self.templates_tab = QWidget()
        self.assignments_tab = QWidget()

        self.tabs.addTab(self.templates_tab, "مدیریت قالب های شیفت")
        self.tabs.addTab(self.assignments_tab, "مدیریت تخصیص شیفت ها")

        self.setup_templates_tab()
        self.setup_assignments_tab() # Placeholder for now

        self.layout.addWidget(self.tabs)

    def setup_templates_tab(self):
        layout = QVBoxLayout(self.templates_tab)

        action_layout = QHBoxLayout()
        self.add_template_button = QPushButton(QIcon.fromTheme("list-add"), " افزودن قالب جدید")
        self.add_template_button.clicked.connect(self.open_add_template_dialog)
        action_layout.addWidget(self.add_template_button)

        self.edit_template_button = QPushButton(QIcon.fromTheme("document-edit"), " ویرایش قالب منتخب")
        self.edit_template_button.clicked.connect(self.open_edit_template_dialog)
        self.edit_template_button.setEnabled(False)
        action_layout.addWidget(self.edit_template_button)

        self.delete_template_button = QPushButton(QIcon.fromTheme("list-remove"), " حذف قالب منتخب")
        self.delete_template_button.clicked.connect(self.delete_selected_template)
        self.delete_template_button.setEnabled(False)
        action_layout.addWidget(self.delete_template_button)
        layout.addLayout(action_layout)

        self.templates_table = QTableWidget()
        self.templates_table.setColumnCount(5) # ID, Name, Type, Start, End
        self.templates_table.setHorizontalHeaderLabels(["شناسه", "نام قالب", "نوع", "زمان شروع", "زمان پایان"])
        self.templates_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.templates_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.templates_table.selectionModel().selectionChanged.connect(self.on_template_table_selection_changed)
        self.templates_table.doubleClicked.connect(self.open_edit_template_dialog_on_double_click)
        layout.addWidget(self.templates_table)
        self.refresh_templates_table()

    def on_template_table_selection_changed(self):
        selected = self.templates_table.selectionModel().hasSelection()
        self.edit_template_button.setEnabled(selected)
        self.delete_template_button.setEnabled(selected)

    def get_selected_template_id(self):
        selected_items = self.templates_table.selectedItems()
        return int(selected_items[0].text()) if selected_items else None

    def open_add_template_dialog(self):
        dialog = AddEditShiftTemplateDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_templates_table()

    def open_edit_template_dialog(self):
        template_id = self.get_selected_template_id()
        if template_id is None:
            QMessageBox.information(self, "راهنما", "لطفا یک قالب از جدول انتخاب کنید.")
            return
        db = SessionLocal()
        template = db.query(Shift).get(template_id)
        db.close()
        if not template:
            QMessageBox.critical(self, "خطا", "قالب شیفت یافت نشد.")
            self.refresh_templates_table()
            return
        dialog = AddEditShiftTemplateDialog(template=template, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_templates_table()

    def open_edit_template_dialog_on_double_click(self, model_index):
        if model_index.isValid():
            self.open_edit_template_dialog()

    def delete_selected_template(self):
        template_id = self.get_selected_template_id()
        if template_id is None: return QMessageBox.information(self, "راهنما", "لطفا یک قالب از جدول انتخاب کنید.")

        # Check if template is used in any assignments
        db = SessionLocal()
        assignment_count = db.query(ShiftAssignment).filter(ShiftAssignment.shift_template_id == template_id).count()
        db.close()

        if assignment_count > 0:
            QMessageBox.warning(self, "خطا در حذف", f"این قالب شیفت در {assignment_count} تخصیص استفاده شده و قابل حذف نیست. ابتدا تخصیص های مرتبط را حذف یا ویرایش کنید.")
            return

        reply = QMessageBox.question(self, "تایید حذف", f"آیا از حذف قالب شیفت با شناسه {template_id} اطمینان دارید؟",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            db = SessionLocal()
            try:
                template = db.query(Shift).get(template_id)
                if template:
                    db.delete(template)
                    db.commit()
                    QMessageBox.information(self, "موفقیت", "قالب شیفت حذف شد.")
                    self.refresh_templates_table()
                else: QMessageBox.critical(self, "خطا", "قالب شیفت یافت نشد.")
            except Exception as e:
                db.rollback()
                QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در حذف: {e}")
            finally: db.close()

    def refresh_templates_table(self):
        self.templates_table.setRowCount(0)
        self.edit_template_button.setEnabled(False)
        self.delete_template_button.setEnabled(False)
        db = SessionLocal()
        templates = db.query(Shift).order_by(Shift.id).all()
        for row, tpl in enumerate(templates):
            self.templates_table.insertRow(row)
            self.templates_table.setItem(row, 0, QTableWidgetItem(str(tpl.id)))
            self.templates_table.setItem(row, 1, QTableWidgetItem(tpl.name))
            self.templates_table.setItem(row, 2, QTableWidgetItem(tpl.type.value)) # Display enum value
            self.templates_table.setItem(row, 3, QTableWidgetItem(tpl.start_time.strftime("%H:%M") if tpl.start_time else "N/A"))
            self.templates_table.setItem(row, 4, QTableWidgetItem(tpl.end_time.strftime("%H:%M") if tpl.end_time else "N/A"))
        self.templates_table.resizeColumnsToContents()
        db.close()

    def setup_assignments_tab(self):
        # Placeholder - to be implemented next
        layout = QVBoxLayout(self.assignments_tab)

        action_layout = QHBoxLayout()
        self.add_assignment_button = QPushButton(QIcon.fromTheme("list-add"), " تخصیص شیفت جدید")
        self.add_assignment_button.clicked.connect(self.open_add_assignment_dialog)
        action_layout.addWidget(self.add_assignment_button)

        self.edit_assignment_button = QPushButton(QIcon.fromTheme("document-edit"), " ویرایش تخصیص منتخب")
        self.edit_assignment_button.clicked.connect(self.open_edit_assignment_dialog)
        self.edit_assignment_button.setEnabled(False)
        action_layout.addWidget(self.edit_assignment_button)

        self.delete_assignment_button = QPushButton(QIcon.fromTheme("list-remove"), " حذف تخصیص منتخب")
        self.delete_assignment_button.clicked.connect(self.delete_selected_assignment)
        self.delete_assignment_button.setEnabled(False)
        action_layout.addWidget(self.delete_assignment_button)
        layout.addLayout(action_layout)

        # TODO: Add date filter for assignments
        # filter_layout = QHBoxLayout()
        # self.assignment_date_filter = QDateEdit(QDate.currentDate())
        # self.assignment_date_filter.setCalendarPopup(True)
        # self.assignment_date_filter.setDisplayFormat("yyyy/MM/dd") # For Jalali later
        # self.assignment_date_filter.dateChanged.connect(self.refresh_assignments_table)
        # filter_layout.addWidget(QLabel("نمایش تخصیص ها برای تاریخ:"))
        # filter_layout.addWidget(self.assignment_date_filter)
        # layout.addLayout(filter_layout)


        self.assignments_table = QTableWidget()
        self.assignments_table.setColumnCount(7) # ID, Template, Driver, Vehicle, Start, End, Notes
        self.assignments_table.setHorizontalHeaderLabels([
            "شناسه", "قالب شیفت", "راننده", "خودرو",
            "زمان شروع (UTC)", "زمان پایان (UTC)", "یادداشت"
        ])
        self.assignments_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.assignments_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.assignments_table.selectionModel().selectionChanged.connect(self.on_assignment_table_selection_changed)
        self.assignments_table.doubleClicked.connect(self.open_edit_assignment_dialog_on_double_click)
        layout.addWidget(self.assignments_table)
        self.refresh_assignments_table()


    def on_assignment_table_selection_changed(self):
        selected = self.assignments_table.selectionModel().hasSelection()
        self.edit_assignment_button.setEnabled(selected)
        self.delete_assignment_button.setEnabled(selected)

    def get_selected_assignment_id(self):
        selected_items = self.assignments_table.selectedItems()
        return int(selected_items[0].text()) if selected_items else None

    def open_add_assignment_dialog(self):
        dialog = AddEditShiftAssignmentDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_assignments_table()

    def open_edit_assignment_dialog(self):
        assignment_id = self.get_selected_assignment_id()
        if assignment_id is None:
            QMessageBox.information(self, "راهنما", "لطفا یک تخصیص از جدول انتخاب کنید.")
            return

        db = SessionLocal()
        assignment = db.query(ShiftAssignment).get(assignment_id)
        # Eager load related objects if needed for the dialog, or pass IDs
        # Example: assignment = db.query(ShiftAssignment).options(joinedload(ShiftAssignment.driver), joinedload(ShiftAssignment.vehicle), joinedload(ShiftAssignment.shift_template)).get(assignment_id)
        db.close()

        if not assignment:
            QMessageBox.critical(self, "خطا", "تخصیص شیفت یافت نشد.")
            self.refresh_assignments_table()
            return

        dialog = AddEditShiftAssignmentDialog(assignment=assignment, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_assignments_table()

    def open_edit_assignment_dialog_on_double_click(self, model_index):
        if model_index.isValid():
            self.open_edit_assignment_dialog()

    def delete_selected_assignment(self):
        assignment_id = self.get_selected_assignment_id()
        if assignment_id is None:
            return QMessageBox.information(self, "راهنما", "لطفا یک تخصیص از جدول انتخاب کنید.")

        reply = QMessageBox.question(self, "تایید حذف",
                                     f"آیا از حذف تخصیص شیفت با شناسه {assignment_id} اطمینان دارید؟",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            db = SessionLocal()
            try:
                assignment = db.query(ShiftAssignment).get(assignment_id)
                if assignment:
                    db.delete(assignment)
                    db.commit()
                    QMessageBox.information(self, "موفقیت", "تخصیص شیفت حذف شد.")
                    self.refresh_assignments_table()
                else:
                    QMessageBox.critical(self, "خطا", "تخصیص شیفت یافت نشد.")
            except Exception as e:
                db.rollback()
                QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در حذف تخصیص: {e}")
            finally:
                db.close()

    def refresh_assignments_table(self):
        self.assignments_table.setRowCount(0)
        self.edit_assignment_button.setEnabled(False)
        self.delete_assignment_button.setEnabled(False)
        db = SessionLocal()
        # TODO: Add date filtering based on self.assignment_date_filter
        # selected_date = self.assignment_date_filter.date().toPyDate()
        # assignments = db.query(ShiftAssignment).filter(func.date(ShiftAssignment.start_datetime_utc) == selected_date).order_by(ShiftAssignment.start_datetime_utc).all()
        assignments = db.query(ShiftAssignment).order_by(ShiftAssignment.start_datetime_utc).all()

        for row, assign in enumerate(assignments):
            self.assignments_table.insertRow(row)
            self.assignments_table.setItem(row, 0, QTableWidgetItem(str(assign.id)))
            self.assignments_table.setItem(row, 1, QTableWidgetItem(assign.shift_template.name if assign.shift_template else "N/A"))
            self.assignments_table.setItem(row, 2, QTableWidgetItem(assign.driver.name if assign.driver else "N/A"))
            self.assignments_table.setItem(row, 3, QTableWidgetItem(assign.vehicle.plate_number if assign.vehicle else "اختیاری"))

            # For Jalali, these would be converted
            start_dt_str = assign.start_datetime_utc.strftime("%Y-%m-%d %H:%M") # format for UTC display
            end_dt_str = assign.end_datetime_utc.strftime("%Y-%m-%d %H:%M")
            self.assignments_table.setItem(row, 4, QTableWidgetItem(start_dt_str))
            self.assignments_table.setItem(row, 5, QTableWidgetItem(end_dt_str))
            self.assignments_table.setItem(row, 6, QTableWidgetItem(assign.notes or ""))

        self.assignments_table.resizeColumnsToContents()
        db.close()


# --- Dialog for Shift Assignments ---
class AddEditShiftAssignmentDialog(QDialog):
    def __init__(self, assignment: ShiftAssignment = None, parent=None):
        super().__init__(parent)
        self.assignment_instance = assignment
        self.db_session = SessionLocal()

        self.setWindowTitle("افزودن/ویرایش تخصیص شیفت" if assignment else "تخصیص شیفت جدید")
        self.setMinimumWidth(500)
        self.layout = QFormLayout(self)

        self.shift_template_combo = QComboBox(self)
        self.driver_combo = QComboBox(self)
        self.vehicle_combo = QComboBox(self) # Optional

        self.start_datetime_input = QDateTimeEdit(self)
        self.start_datetime_input.setCalendarPopup(True)
        self.start_datetime_input.setDisplayFormat("yyyy/MM/dd HH:mm") # Placeholder for Jalali
        self.start_datetime_input.setDateTime(QDateTime.currentDateTime())

        self.end_datetime_input = QDateTimeEdit(self)
        self.end_datetime_input.setCalendarPopup(True)
        self.end_datetime_input.setDisplayFormat("yyyy/MM/dd HH:mm") # Placeholder for Jalali
        self.end_datetime_input.setDateTime(QDateTime.currentDateTime().addSecs(8 * 3600)) # Default 8 hours later

        self.notes_input = QLineEdit(self)

        self.populate_combos()

        self.layout.addRow("قالب شیفت (*):", self.shift_template_combo)
        self.layout.addRow("راننده (*):", self.driver_combo)
        self.layout.addRow("خودرو (اختیاری):", self.vehicle_combo)
        self.layout.addRow("زمان و تاریخ شروع (*):", self.start_datetime_input)
        self.layout.addRow("زمان و تاریخ پایان (*):", self.end_datetime_input)
        self.layout.addRow("یادداشت:", self.notes_input)

        self.button_box = QHBoxLayout()
        self.save_button = QPushButton(QIcon.fromTheme("document-save"), " ذخیره")
        self.save_button.clicked.connect(self.save_assignment)
        self.cancel_button = QPushButton(QIcon.fromTheme("dialog-cancel"), " انصراف")
        self.cancel_button.clicked.connect(self.reject)
        self.button_box.addWidget(self.save_button)
        self.button_box.addWidget(self.cancel_button)
        self.layout.addRow(self.button_box)

        if self.assignment_instance:
            self.load_assignment_data()

    def populate_combos(self):
        # Shift Templates
        templates = self.db_session.query(Shift).order_by(Shift.name).all()
        for tpl in templates:
            self.shift_template_combo.addItem(f"{tpl.name} ({tpl.type.value})", tpl.id)

        # Drivers (active ones)
        drivers = self.db_session.query(Driver).filter(Driver.is_active == True).order_by(Driver.name).all()
        for driver in drivers:
            self.driver_combo.addItem(f"{driver.name} ({driver.national_id})", driver.id)

        # Vehicles (active ones) - Add a "None" option
        self.vehicle_combo.addItem("بدون خودرو (اختیاری)", None) # UserData is None
        vehicles = self.db_session.query(Vehicle).filter(Vehicle.is_active == True).order_by(Vehicle.plate_number).all()
        for vh in vehicles:
            self.vehicle_combo.addItem(f"{vh.plate_number} ({vh.model})", vh.id)

    def load_assignment_data(self):
        # Select template
        template_idx = self.shift_template_combo.findData(self.assignment_instance.shift_template_id)
        if template_idx != -1: self.shift_template_combo.setCurrentIndex(template_idx)

        # Select driver
        driver_idx = self.driver_combo.findData(self.assignment_instance.driver_id)
        if driver_idx != -1: self.driver_combo.setCurrentIndex(driver_idx)

        # Select vehicle
        vehicle_idx = self.vehicle_combo.findData(self.assignment_instance.vehicle_id) # Handles None if vehicle_id is None
        if vehicle_idx != -1: self.vehicle_combo.setCurrentIndex(vehicle_idx)
        else: self.vehicle_combo.setCurrentIndex(0) # Select "بدون خودرو" if not found or None

        # Set QDateTime from python datetime (UTC)
        # For Jalali, this would involve conversion before setting
        self.start_datetime_input.setDateTime(QDateTime.fromSecsSinceEpoch(int(self.assignment_instance.start_datetime_utc.timestamp()), Qt.TimeSpec.UTC))
        self.end_datetime_input.setDateTime(QDateTime.fromSecsSinceEpoch(int(self.assignment_instance.end_datetime_utc.timestamp()), Qt.TimeSpec.UTC))

        self.notes_input.setText(self.assignment_instance.notes or "")

    def save_assignment(self):
        template_id = self.shift_template_combo.currentData()
        driver_id = self.driver_combo.currentData()
        vehicle_id = self.vehicle_combo.currentData() # This will be None if "بدون خودرو" is selected

        if template_id is None or driver_id is None:
            QMessageBox.warning(self, "خطا", "قالب شیفت و راننده باید انتخاب شوند.")
            return

        # Get QDateTime, then convert to Python datetime (UTC)
        # For Jalali, input would be Jalali, then converted to UTC for storage
        start_dt_utc = self.start_datetime_input.dateTime().toUTC().toPyDateTime()
        end_dt_utc = self.end_datetime_input.dateTime().toUTC().toPyDateTime()

        if start_dt_utc >= end_dt_utc:
            QMessageBox.warning(self, "خطای تاریخ", "زمان پایان باید بعد از زمان شروع باشد.")
            return

        notes = self.notes_input.text().strip() or None

        # TODO: Check for overlapping shifts for the selected driver/vehicle
        # This is a more complex check and might involve querying existing assignments

        try:
            if self.assignment_instance is None: # New assignment
                new_assignment = ShiftAssignment(
                    shift_template_id=template_id,
                    driver_id=driver_id,
                    vehicle_id=vehicle_id,
                    start_datetime_utc=start_dt_utc,
                    end_datetime_utc=end_dt_utc,
                    notes=notes
                )
                self.db_session.add(new_assignment)
                QMessageBox.information(self, "موفقیت", "تخصیص شیفت جدید با موفقیت انجام شد.")
            else: # Edit assignment
                self.assignment_instance.shift_template_id = template_id
                self.assignment_instance.driver_id = driver_id
                self.assignment_instance.vehicle_id = vehicle_id
                self.assignment_instance.start_datetime_utc = start_dt_utc
                self.assignment_instance.end_datetime_utc = end_dt_utc
                self.assignment_instance.notes = notes
                self.db_session.add(self.assignment_instance)
                QMessageBox.information(self, "موفقیت", "اطلاعات تخصیص شیفت با موفقیت ویرایش شد.")

            self.db_session.commit()
            self.accept()
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در ذخیره سازی تخصیص شیفت: {e}")

    def done(self, result):
        self.db_session.close()
        super().done(result)


if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    from database import create_tables

    app = QApplication(sys.argv)
    create_tables()
    main_widget = ShiftPlanningWidget()
    main_widget.showMaximized() # Show maximized for better view of tabs
    sys.exit(app.exec())
