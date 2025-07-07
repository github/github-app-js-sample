# UI components for Mission Management
import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget,
                             QTableWidgetItem, QDialog, QFormLayout, QLineEdit, QTextEdit,
                             QComboBox, QMessageBox, QHBoxLayout, QDateTimeEdit, QGridLayout)
from PyQt6.QtCore import QDateTime, Qt
from PyQt6.QtGui import QIcon
from database import SessionLocal
from mission_management.models import Mission, MissionType, MissionStatus
from driver_management.models import Driver
from vehicle_management.models import Vehicle
# from utils.jalali_converter import # Import when ready

# --- Dialog for Requesting a New Mission ---
class RequestMissionDialog(QDialog):
    def __init__(self, mission: Mission = None, parent=None, current_user_role="operator"):
        super().__init__(parent)
        self.mission_instance = mission
        self.current_user_role = current_user_role # To control field editability
        self.db_session = SessionLocal()

        self.setWindowTitle("درخواست/ویرایش مأموریت" if mission else "ثبت درخواست مأموریت جدید")
        self.setMinimumWidth(500)
        self.layout = QFormLayout(self)

        self.mission_type_combo = QComboBox(self)
        for mtype in MissionType:
            self.mission_type_combo.addItem(mtype.value, mtype)

        self.requester_name_input = QLineEdit(self)
        self.requester_contact_input = QLineEdit(self)

        self.origin_input = QLineEdit(self)
        self.destination_input = QLineEdit(self)
        self.purpose_input = QTextEdit(self)
        self.purpose_input.setFixedHeight(80)
        self.route_details_input = QTextEdit(self) # New field for route details
        self.route_details_input.setFixedHeight(80)

        # Datetimes - User requests desired schedule, admin confirms/adjusts
        self.requested_datetime_label = QLabel(self) # Will be set programmatically
        self.scheduled_start_input = QDateTimeEdit(self)
        self.scheduled_start_input.setCalendarPopup(True)
        self.scheduled_start_input.setDisplayFormat("yyyy/MM/dd HH:mm") # Placeholder for Jalali
        self.scheduled_start_input.setDateTime(QDateTime.currentDateTime().addDays(1)) # Default to next day

        self.scheduled_end_input = QDateTimeEdit(self)
        self.scheduled_end_input.setCalendarPopup(True)
        self.scheduled_end_input.setDisplayFormat("yyyy/MM/dd HH:mm")
        self.scheduled_end_input.setDateTime(QDateTime.currentDateTime().addDays(1).addSecs(4*3600)) # Default +4 hours

        self.notes_input = QTextEdit(self) # General notes
        self.notes_input.setFixedHeight(60)

        self.layout.addRow("نوع مأموریت (*):", self.mission_type_combo)
        self.layout.addRow("نام درخواست کننده (*):", self.requester_name_input)
        self.layout.addRow("اطلاعات تماس درخواست کننده:", self.requester_contact_input)
        self.layout.addRow("مبدأ (*):", self.origin_input)
        self.layout.addRow("مقصد (*):", self.destination_input)
        self.layout.addRow("جزئیات مسیر پیشنهادی:", self.route_details_input)
        self.layout.addRow("هدف مأموریت (*):", self.purpose_input)
        self.layout.addRow("زمان پیشنهادی شروع (*):", self.scheduled_start_input)
        self.layout.addRow("زمان پیشنهادی پایان (*):", self.scheduled_end_input)
        self.layout.addRow("یادداشت های درخواست:", self.notes_input)
        if self.mission_instance:
             self.layout.addRow("زمان ثبت درخواست:", self.requested_datetime_label)


        self.button_box = QHBoxLayout()
        self.save_button = QPushButton(QIcon.fromTheme("document-save"), " ثبت/ذخیره درخواست")
        self.save_button.clicked.connect(self.save_mission_request)
        self.cancel_button = QPushButton(QIcon.fromTheme("dialog-cancel"), " انصراف")
        self.cancel_button.clicked.connect(self.reject)
        self.button_box.addWidget(self.save_button)
        self.button_box.addWidget(self.cancel_button)
        self.layout.addRow(self.button_box)

        if self.mission_instance:
            self.load_mission_data()

    def load_mission_data(self):
        self.mission_type_combo.setCurrentIndex(self.mission_type_combo.findData(self.mission_instance.mission_type))
        self.requester_name_input.setText(self.mission_instance.requester_name)
        self.requester_contact_input.setText(self.mission_instance.requester_contact or "")
        self.origin_input.setText(self.mission_instance.origin)
        self.destination_input.setText(self.mission_instance.destination)
        self.route_details_input.setText(self.mission_instance.route_details or "")
        self.purpose_input.setText(self.mission_instance.purpose or "")

        if self.mission_instance.requested_datetime_utc:
            # req_dt_local = QDateTime.fromSecsSinceEpoch(int(self.mission_instance.requested_datetime_utc.timestamp()), Qt.TimeSpec.UTC).toLocalTime()
            # self.requested_datetime_label.setText(req_dt_local.toString("yyyy/MM/dd HH:mm:ss") + " (UTC: " + self.mission_instance.requested_datetime_utc.strftime("%Y-%m-%d %H:%M:%S") + ")")
             self.requested_datetime_label.setText(self.mission_instance.requested_datetime_utc.strftime("%Y-%m-%d %H:%M:%S UTC"))


        if self.mission_instance.scheduled_start_datetime_utc:
            self.scheduled_start_input.setDateTime(QDateTime.fromSecsSinceEpoch(int(self.mission_instance.scheduled_start_datetime_utc.timestamp()), Qt.TimeSpec.UTC))
        if self.mission_instance.scheduled_end_datetime_utc:
            self.scheduled_end_input.setDateTime(QDateTime.fromSecsSinceEpoch(int(self.mission_instance.scheduled_end_datetime_utc.timestamp()), Qt.TimeSpec.UTC))

        self.notes_input.setText(self.mission_instance.notes or "")

        # Prevent editing of certain fields if mission is past 'REQUESTED' stage by non-admins
        if self.current_user_role != 'admin' and self.mission_instance.status != MissionStatus.REQUESTED:
            for w in [self.mission_type_combo, self.requester_name_input, self.requester_contact_input,
                      self.origin_input, self.destination_input, self.route_details_input, self.purpose_input,
                      self.scheduled_start_input, self.scheduled_end_input, self.notes_input]:
                w.setEnabled(False)
            self.save_button.setEnabled(False)
            self.setWindowTitle(f"مشاهده جزئیات مأموریت (ID: {self.mission_instance.id})")


    def save_mission_request(self):
        mission_type = self.mission_type_combo.currentData()
        requester_name = self.requester_name_input.text().strip()
        origin = self.origin_input.text().strip()
        destination = self.destination_input.text().strip()
        purpose = self.purpose_input.toPlainText().strip()

        if not all([requester_name, origin, destination, purpose]):
            QMessageBox.warning(self, "خطا", "لطفا تمامی فیلدهای ستاره دار (*) را پر کنید.")
            return

        scheduled_start_utc = self.scheduled_start_input.dateTime().toUTC().toPyDateTime()
        scheduled_end_utc = self.scheduled_end_input.dateTime().toUTC().toPyDateTime()

        if scheduled_start_utc >= scheduled_end_utc:
            QMessageBox.warning(self, "خطای تاریخ", "زمان پیشنهادی پایان باید بعد از زمان شروع باشد.")
            return

        try:
            if self.mission_instance is None: # New request
                new_mission = Mission(
                    mission_type=mission_type,
                    requester_name=requester_name,
                    requester_contact=self.requester_contact_input.text().strip() or None,
                    origin=origin,
                    destination=destination,
                    route_details=self.route_details_input.toPlainText().strip() or None,
                    purpose=purpose,
                    requested_datetime_utc=datetime.datetime.now(datetime.timezone.utc), # Record request time
                    scheduled_start_datetime_utc=scheduled_start_utc,
                    scheduled_end_datetime_utc=scheduled_end_utc,
                    notes=self.notes_input.toPlainText().strip() or None,
                    status=MissionStatus.REQUESTED
                )
                self.db_session.add(new_mission)
                QMessageBox.information(self, "موفقیت", "درخواست مأموریت جدید با موفقیت ثبت شد.")
            else: # Editing existing request (usually only if status is still REQUESTED or by admin)
                self.mission_instance.mission_type = mission_type
                self.mission_instance.requester_name = requester_name
                self.mission_instance.requester_contact = self.requester_contact_input.text().strip() or None
                self.mission_instance.origin = origin
                self.mission_instance.destination = destination
                self.mission_instance.route_details = self.route_details_input.toPlainText().strip() or None
                self.mission_instance.purpose = purpose
                self.mission_instance.scheduled_start_datetime_utc = scheduled_start_utc
                self.mission_instance.scheduled_end_datetime_utc = scheduled_end_utc
                self.mission_instance.notes = self.notes_input.toPlainText().strip() or None
                # Status is not changed here, that's done in evaluation/assignment dialogs
                self.db_session.add(self.mission_instance)
                QMessageBox.information(self, "موفقیت", "اطلاعات درخواست مأموریت با موفقیت ویرایش شد.")

            self.db_session.commit()
            self.accept()
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در ذخیره سازی درخواست مأموریت: {e}")

    def done(self, result):
        self.db_session.close()
        super().done(result)

# --- Dialog for Evaluating a Mission ---
class EvaluateMissionDialog(QDialog):
    def __init__(self, mission: Mission, parent=None):
        super().__init__(parent)
        self.mission_instance = mission
        self.db_session = SessionLocal()

        self.setWindowTitle(f"ارزیابی مأموریت (ID: {mission.id})")
        self.setMinimumWidth(450)
        layout = QFormLayout(self)

        # Display non-editable mission details
        details_group = QGroupBox("جزئیات درخواست مأموریت")
        details_layout = QFormLayout(details_group)
        details_layout.addRow("نوع:", QLabel(mission.mission_type.value))
        details_layout.addRow("درخواست کننده:", QLabel(mission.requester_name))
        details_layout.addRow("تماس:", QLabel(mission.requester_contact or "---"))
        details_layout.addRow("مبدأ:", QLabel(mission.origin))
        details_layout.addRow("مقصد:", QLabel(mission.destination))
        start_sched_str = mission.scheduled_start_datetime_utc.strftime("%Y-%m-%d %H:%M UTC") if mission.scheduled_start_datetime_utc else "N/A"
        end_sched_str = mission.scheduled_end_datetime_utc.strftime("%Y-%m-%d %H:%M UTC") if mission.scheduled_end_datetime_utc else "N/A"
        details_layout.addRow("شروع پیشنهادی:", QLabel(start_sched_str))
        details_layout.addRow("پایان پیشنهادی:", QLabel(end_sched_str))
        details_layout.addRow("هدف:", QLabel(mission.purpose or "---"))
        details_layout.addRow("یادداشت درخواست:", QLabel(mission.notes or "---"))
        layout.addWidget(details_group)

        self.new_status_combo = QComboBox(self)
        # Populate with relevant statuses for evaluation
        self.new_status_combo.addItem(MissionStatus.APPROVED.value, MissionStatus.APPROVED)
        self.new_status_combo.addItem(MissionStatus.REJECTED.value, MissionStatus.REJECTED)
        # Could add an option to revert to REQUESTED if logic allows, or other intermediary statuses

        self.evaluation_notes_input = QTextEdit(self)
        self.evaluation_notes_input.setPlaceholderText("دلایل رد یا توضیحات تکمیلی برای تأیید...")
        self.evaluation_notes_input.setFixedHeight(100)

        layout.addRow("وضعیت جدید مأموریت (*):", self.new_status_combo)
        layout.addRow("یادداشت ارزیابی:", self.evaluation_notes_input)

        # Buttons
        button_box = QHBoxLayout()
        save_button = QPushButton(QIcon.fromTheme("document-save"), " ذخیره ارزیابی")
        save_button.clicked.connect(self.save_evaluation)
        cancel_button = QPushButton(QIcon.fromTheme("dialog-cancel"), " انصراف")
        cancel_button.clicked.connect(self.reject)
        button_box.addWidget(save_button)
        button_box.addWidget(cancel_button)
        layout.addRow(button_box)

        if mission.evaluation_notes: # Load existing evaluation notes if any
            self.evaluation_notes_input.setText(mission.evaluation_notes)
        # Pre-select current status if it's one of the evaluation outcomes, or default
        current_eval_status_idx = self.new_status_combo.findData(mission.status)
        if current_eval_status_idx != -1 :
             self.new_status_combo.setCurrentIndex(current_eval_status_idx)
        elif mission.status == MissionStatus.REQUESTED: # Default to Approved if currently requested
            approve_idx = self.new_status_combo.findData(MissionStatus.APPROVED)
            if approve_idx != -1: self.new_status_combo.setCurrentIndex(approve_idx)


    def save_evaluation(self):
        new_status = self.new_status_combo.currentData()
        evaluation_notes = self.evaluation_notes_input.toPlainText().strip() or None

        if not new_status: # Should not happen with current setup
            QMessageBox.warning(self, "خطا", "لطفا وضعیت جدید را انتخاب کنید.")
            return

        try:
            self.mission_instance.status = new_status
            self.mission_instance.evaluation_notes = evaluation_notes
            # Potentially update other fields, e.g., an 'evaluated_by_user_id' or 'evaluation_datetime'

            self.db_session.add(self.mission_instance)
            self.db_session.commit()
            QMessageBox.information(self, "موفقیت", f"مأموریت به وضعیت '{new_status.value}' تغییر یافت.")
            self.accept()
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در ذخیره ارزیابی: {e}")

    def done(self, result):
        self.db_session.close()
        super().done(result)


# --- Dialog for Assigning Driver/Vehicle to Mission ---
class AssignToMissionDialog(QDialog):
    def __init__(self, mission: Mission, parent=None):
        super().__init__(parent)
        self.mission_instance = mission
        self.db_session = SessionLocal()

        self.setWindowTitle(f"تخصیص راننده/خودرو به مأموریت (ID: {mission.id})")
        self.setMinimumWidth(500)
        layout = QFormLayout(self)

        # Display non-editable mission details (condensed)
        details_group = QGroupBox("خلاصه مأموریت")
        details_layout = QFormLayout(details_group)
        details_layout.addRow("نوع:", QLabel(mission.mission_type.value))
        details_layout.addRow("مبدأ:", QLabel(mission.origin))
        details_layout.addRow("مقصد:", QLabel(mission.destination))
        start_sched_str = mission.scheduled_start_datetime_utc.strftime("%Y-%m-%d %H:%M UTC") if mission.scheduled_start_datetime_utc else "N/A"
        end_sched_str = mission.scheduled_end_datetime_utc.strftime("%Y-%m-%d %H:%M UTC") if mission.scheduled_end_datetime_utc else "N/A"
        details_layout.addRow("زمانبندی:", QLabel(f"{start_sched_str} الی {end_sched_str}"))
        layout.addWidget(details_group)

        self.driver_combo = QComboBox(self)
        self.vehicle_combo = QComboBox(self) # Optional

        # Allow adjustment of scheduled times if necessary
        self.scheduled_start_input = QDateTimeEdit(self)
        self.scheduled_start_input.setCalendarPopup(True)
        self.scheduled_start_input.setDisplayFormat("yyyy/MM/dd HH:mm") # Placeholder for Jalali
        if mission.scheduled_start_datetime_utc:
            self.scheduled_start_input.setDateTime(QDateTime.fromSecsSinceEpoch(int(mission.scheduled_start_datetime_utc.timestamp()), Qt.TimeSpec.UTC))
        else:
            self.scheduled_start_input.setDateTime(QDateTime.currentDateTime())


        self.scheduled_end_input = QDateTimeEdit(self)
        self.scheduled_end_input.setCalendarPopup(True)
        self.scheduled_end_input.setDisplayFormat("yyyy/MM/dd HH:mm")
        if mission.scheduled_end_datetime_utc:
            self.scheduled_end_input.setDateTime(QDateTime.fromSecsSinceEpoch(int(mission.scheduled_end_datetime_utc.timestamp()), Qt.TimeSpec.UTC))
        else:
            self.scheduled_end_input.setDateTime(QDateTime.currentDateTime().addSecs(4*3600))

        self.assignment_notes_input = QTextEdit(self)
        self.assignment_notes_input.setPlaceholderText("یادداشت های مربوط به تخصیص (اختیاری)...")
        self.assignment_notes_input.setFixedHeight(80)


        self.populate_combos() # Populate before adding rows

        layout.addRow("راننده (*):", self.driver_combo)
        layout.addRow("خودرو (اختیاری):", self.vehicle_combo)
        layout.addRow("تنظیم زمان شروع:", self.scheduled_start_input)
        layout.addRow("تنظیم زمان پایان:", self.scheduled_end_input)
        layout.addRow("یادداشت تخصیص:", self.assignment_notes_input)


        button_box = QHBoxLayout()
        save_button = QPushButton(QIcon.fromTheme("document-save"), " ذخیره تخصیص")
        save_button.clicked.connect(self.save_assignment)
        cancel_button = QPushButton(QIcon.fromTheme("dialog-cancel"), " انصراف")
        cancel_button.clicked.connect(self.reject)
        button_box.addWidget(save_button)
        button_box.addWidget(cancel_button)
        layout.addRow(button_box)

        # Load existing assignment if any (though typically this dialog is for new assignments)
        if self.mission_instance.driver_id:
            driver_idx = self.driver_combo.findData(self.mission_instance.driver_id)
            if driver_idx != -1: self.driver_combo.setCurrentIndex(driver_idx)
        if self.mission_instance.vehicle_id:
            vehicle_idx = self.vehicle_combo.findData(self.mission_instance.vehicle_id)
            if vehicle_idx != -1: self.vehicle_combo.setCurrentIndex(vehicle_idx)
        if self.mission_instance.notes : # Append to existing notes or use a dedicated field for assignment notes
             current_notes = self.mission_instance.notes or ""
             # self.assignment_notes_input.setText(current_notes) # Or a new field in model for assignment_notes


    def populate_combos(self):
        # Drivers (active ones)
        # TODO: Filter for drivers available during mission.scheduled_start_datetime_utc and end
        drivers = self.db_session.query(Driver).filter(Driver.is_active == True).order_by(Driver.name).all()
        self.driver_combo.addItem("--- انتخاب راننده ---", None)
        for driver in drivers:
            self.driver_combo.addItem(f"{driver.name} ({driver.national_id})", driver.id)

        # Vehicles (active ones) - Add a "None" option
        # TODO: Filter for vehicles available during mission.scheduled_start_datetime_utc and end
        self.vehicle_combo.addItem("--- بدون خودرو (اختیاری) ---", None)
        vehicles = self.db_session.query(Vehicle).filter(Vehicle.is_active == True).order_by(Vehicle.plate_number).all()
        for vh in vehicles:
            self.vehicle_combo.addItem(f"{vh.plate_number} ({vh.model})", vh.id)

    def save_assignment(self):
        driver_id = self.driver_combo.currentData()
        vehicle_id = self.vehicle_combo.currentData() # Can be None

        if driver_id is None:
            QMessageBox.warning(self, "خطا", "راننده باید انتخاب شود.")
            return

        scheduled_start_utc = self.scheduled_start_input.dateTime().toUTC().toPyDateTime()
        scheduled_end_utc = self.scheduled_end_input.dateTime().toUTC().toPyDateTime()

        if scheduled_start_utc >= scheduled_end_utc:
            QMessageBox.warning(self, "خطای تاریخ", "زمان پایان باید بعد از زمان شروع باشد.")
            return

        assignment_notes = self.assignment_notes_input.toPlainText().strip() or None

        try:
            self.mission_instance.driver_id = driver_id
            self.mission_instance.vehicle_id = vehicle_id
            self.mission_instance.scheduled_start_datetime_utc = scheduled_start_utc # Update if changed
            self.mission_instance.scheduled_end_datetime_utc = scheduled_end_utc     # Update if changed

            # Append assignment notes to general notes or use a specific field if added to model
            if assignment_notes:
                existing_notes = self.mission_instance.notes or ""
                self.mission_instance.notes = f"{existing_notes}\nیادداشت تخصیص: {assignment_notes}".strip()

            self.mission_instance.status = MissionStatus.ASSIGNED

            self.db_session.add(self.mission_instance)
            self.db_session.commit()
            QMessageBox.information(self, "موفقیت", "راننده و خودرو با موفقیت به مأموریت تخصیص داده شدند.")
            self.accept()
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در ذخیره تخصیص: {e}")

    def done(self, result):
        self.db_session.close()
        super().done(result)


# --- Dialog for Completing or Cancelling a Mission ---
class CompleteCancelMissionDialog(QDialog):
    def __init__(self, mission: Mission, action_type: str, parent=None): # action_type: "complete" or "cancel"
        super().__init__(parent)
        self.mission_instance = mission
        self.action_type = action_type
        self.db_session = SessionLocal()

        if self.action_type == "complete":
            self.setWindowTitle(f"تکمیل مأموریت (ID: {mission.id})")
        else: # cancel
            self.setWindowTitle(f"لغو مأموریت (ID: {mission.id})")

        self.setMinimumWidth(400)
        layout = QFormLayout(self)

        details_group = QGroupBox("خلاصه مأموریت")
        details_layout = QFormLayout(details_group)
        # You can add more details if needed
        details_layout.addRow("مبدأ:", QLabel(mission.origin))
        details_layout.addRow("مقصد:", QLabel(mission.destination))
        details_layout.addRow("راننده:", QLabel(mission.driver.name if mission.driver else "---"))
        layout.addWidget(details_group)

        self.notes_label_text = "یادداشت های تکمیلی (اختیاری):"
        if self.action_type == "cancel":
            self.notes_label_text = "دلیل لغو مأموریت (اختیاری):"

        self.action_notes_input = QTextEdit(self)
        self.action_notes_input.setPlaceholderText(self.notes_label_text)

        layout.addRow(self.notes_label_text, self.action_notes_input)

        if self.action_type == "complete":
            self.actual_end_datetime_input = QDateTimeEdit(self)
            self.actual_end_datetime_input.setCalendarPopup(True)
            self.actual_end_datetime_input.setDisplayFormat("yyyy/MM/dd HH:mm")
            self.actual_end_datetime_input.setDateTime(QDateTime.currentDateTime())
            layout.addRow("زمان واقعی پایان مأموریت (*):", self.actual_end_datetime_input)


        button_box = QHBoxLayout()
        action_text = " ثبت تکمیل" if self.action_type == "complete" else " ثبت لغو"
        save_button = QPushButton(QIcon.fromTheme("document-save"), action_text)
        save_button.clicked.connect(self.save_action)
        cancel_button = QPushButton(QIcon.fromTheme("dialog-cancel"), " انصراف")
        cancel_button.clicked.connect(self.reject)
        button_box.addWidget(save_button)
        button_box.addWidget(cancel_button)
        layout.addRow(button_box)

    def save_action(self):
        action_notes = self.action_notes_input.toPlainText().strip() or None

        try:
            if self.action_type == "complete":
                actual_end_utc = self.actual_end_datetime_input.dateTime().toUTC().toPyDateTime()
                if not self.mission_instance.actual_start_datetime_utc: # Should not happen if status is IN_PROGRESS
                     QMessageBox.warning(self, "خطا", "زمان شروع واقعی مأموریت ثبت نشده است!")
                     return
                if actual_end_utc < self.mission_instance.actual_start_datetime_utc:
                    QMessageBox.warning(self, "خطای تاریخ", "زمان واقعی پایان نمی‌تواند قبل از زمان واقعی شروع باشد.")
                    return

                self.mission_instance.status = MissionStatus.COMPLETED
                self.mission_instance.actual_end_datetime_utc = actual_end_utc
                if action_notes: # Append to existing notes
                    self.mission_instance.notes = (self.mission_instance.notes or "") + f"\nیادداشت تکمیل: {action_notes}"

            else: # Cancel action
                self.mission_instance.status = MissionStatus.CANCELLED
                if action_notes: # Append to existing notes
                    self.mission_instance.notes = (self.mission_instance.notes or "") + f"\nدلیل لغو: {action_notes}"

            self.db_session.add(self.mission_instance)
            self.db_session.commit()
            QMessageBox.information(self, "موفقیت", f"مأموریت با موفقیت {self.windowTitle()} شد.")
            self.accept()
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در ثبت عملیات: {e}")

    def done(self, result):
        self.db_session.close()
        super().done(result)


# --- Main Mission Management Widget ---
class MissionManagementWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setWindowTitle("مدیریت مأموریت ها")
        # TODO: Get current user role from parent or auth system to pass to dialogs
        self.current_user_role = getattr(parent.current_user, 'role', 'operator') if hasattr(parent, 'current_user') else 'operator'


        title_label = QLabel("ماژول مدیریت مأموریت ها", self)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        self.layout.addWidget(title_label)

        # Action buttons grid
        actions_grid = QGridLayout()
        self.request_mission_button = QPushButton(QIcon.fromTheme("document-new"), " ثبت مأموریت جدید")
        self.request_mission_button.clicked.connect(self.open_request_mission_dialog)
        actions_grid.addWidget(self.request_mission_button, 0, 0)

        self.view_edit_mission_button = QPushButton(QIcon.fromTheme("document-properties"), " مشاهده/ویرایش جزئیات")
        self.view_edit_mission_button.clicked.connect(self.open_view_edit_mission_dialog)
        self.view_edit_mission_button.setEnabled(False)
        actions_grid.addWidget(self.view_edit_mission_button, 0, 1)

        self.evaluate_mission_button = QPushButton(QIcon.fromTheme("edit-find-replace"), " ارزیابی مأموریت") # Example icon
        self.evaluate_mission_button.clicked.connect(self.open_evaluate_mission_dialog)
        self.evaluate_mission_button.setEnabled(False)
        actions_grid.addWidget(self.evaluate_mission_button, 0, 2)

        self.assign_mission_button = QPushButton(QIcon.fromTheme("system-users"), " تخصیص راننده/خودرو")
        self.assign_mission_button.clicked.connect(self.open_assign_mission_dialog)
        self.assign_mission_button.setEnabled(False)
        actions_grid.addWidget(self.assign_mission_button, 0, 3)

        self.start_mission_button = QPushButton(QIcon.fromTheme("media-playback-start"), " شروع مأموریت")
        self.start_mission_button.clicked.connect(self.start_selected_mission)
        self.start_mission_button.setEnabled(False)
        actions_grid.addWidget(self.start_mission_button, 1, 0)

        self.complete_mission_button = QPushButton(QIcon.fromTheme("media-playback-stop"), " تکمیل مأموریت") # Using stop icon as placeholder
        self.complete_mission_button.clicked.connect(self.open_complete_mission_dialog)
        self.complete_mission_button.setEnabled(False)
        actions_grid.addWidget(self.complete_mission_button, 1, 1)

        self.cancel_mission_button = QPushButton(QIcon.fromTheme("process-stop"), " لغو مأموریت")
        self.cancel_mission_button.clicked.connect(self.open_cancel_mission_dialog)
        self.cancel_mission_button.setEnabled(False)
        actions_grid.addWidget(self.cancel_mission_button, 1, 2)

        self.layout.addLayout(actions_grid)

        # Filters (TODO)
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("فیلترها:"))
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItem("همه وضعیت ها", None)
        for status in MissionStatus:
            self.status_filter_combo.addItem(status.value, status)
        self.status_filter_combo.currentIndexChanged.connect(self.refresh_missions_table)
        filter_layout.addWidget(self.status_filter_combo)
        # Add date range filters, type filters etc.
        self.layout.addLayout(filter_layout)


        self.missions_table = QTableWidget(self)
        self.missions_table.setColumnCount(10) # ID, Type, Requester, Origin, Dest, Sched. Start, Sched. End, Driver, Vehicle, Status
        self.missions_table.setHorizontalHeaderLabels([
            "شناسه", "نوع", "درخواست کننده", "مبدأ", "مقصد",
            "شروع برنامه ریزی شده (UTC)", "پایان برنامه ریزی شده (UTC)",
            "راننده", "خودرو", "وضعیت"
        ])
        self.missions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.missions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.missions_table.selectionModel().selectionChanged.connect(self.on_table_selection_changed)
        self.missions_table.doubleClicked.connect(self.open_view_edit_mission_dialog_on_double_click) # For quick view/edit
        self.layout.addWidget(self.missions_table)

        self.refresh_missions_table()

    def on_table_selection_changed(self):
        selected = self.missions_table.selectionModel().hasSelection()
        self.view_edit_mission_button.setEnabled(selected)

        can_evaluate = False
        can_assign = False
        can_start = False
        can_complete = False
        can_cancel = False # Can cancel most active states by admin

        if selected:
            mission_id = self.get_selected_mission_id()
            if mission_id:
                db = SessionLocal()
                mission = db.query(Mission).filter(Mission.id == mission_id).first()
                db.close()
                if mission:
                    user_is_privileged = self.current_user_role == 'admin' or self.current_user_role == 'operator'

                    if mission.status == MissionStatus.REQUESTED and user_is_privileged:
                        can_evaluate = True
                    if mission.status == MissionStatus.APPROVED and user_is_privileged:
                        can_assign = True
                    if mission.status == MissionStatus.ASSIGNED and user_is_privileged: # Or if current user is the assigned driver
                        can_start = True
                    if mission.status == MissionStatus.IN_PROGRESS and user_is_privileged: # Or if current user is the assigned driver
                        can_complete = True

                    # Admin can cancel most active missions, operator might have more restrictions
                    if mission.status not in [MissionStatus.COMPLETED, MissionStatus.REJECTED, MissionStatus.CANCELLED] and user_is_privileged:
                        can_cancel = True

        self.evaluate_mission_button.setEnabled(can_evaluate)
        self.assign_mission_button.setEnabled(can_assign)
        self.start_mission_button.setEnabled(can_start)
        self.complete_mission_button.setEnabled(can_complete)
        self.cancel_mission_button.setEnabled(can_cancel)

    def get_selected_mission_id(self):
        selected_items = self.missions_table.selectedItems()
        return int(selected_items[0].text()) if selected_items else None

    def open_request_mission_dialog(self):
        # For a new request, no mission instance is passed
        dialog = RequestMissionDialog(parent=self, current_user_role=self.current_user_role)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_missions_table()

    def open_view_edit_mission_dialog(self):
        mission_id = self.get_selected_mission_id()
        if mission_id is None:
            QMessageBox.information(self, "راهنما", "لطفا یک مأموریت از جدول انتخاب کنید.")
            return

        db = SessionLocal()
        mission = db.query(Mission).get(mission_id)
        db.close()

        if not mission:
            QMessageBox.critical(self, "خطا", "مأموریت یافت نشد.")
            self.refresh_missions_table()
            return

        # Pass the mission instance to the dialog for viewing/editing
        dialog = RequestMissionDialog(mission=mission, parent=self, current_user_role=self.current_user_role)
        if dialog.exec() == QDialog.DialogCode.Accepted: # If any changes were made and saved
            self.refresh_missions_table()

    def open_view_edit_mission_dialog_on_double_click(self, model_index):
        if model_index.isValid():
             self.open_view_edit_mission_dialog()

    def open_evaluate_mission_dialog(self):
        mission_id = self.get_selected_mission_id()
        if mission_id is None:
            QMessageBox.information(self, "راهنما", "لطفا یک مأموریت برای ارزیابی انتخاب کنید.")
            return

        db = SessionLocal()
        mission = db.query(Mission).get(mission_id)
        db.close()

        if not mission:
            QMessageBox.critical(self, "خطا", "مأموریت یافت نشد.")
            self.refresh_missions_table()
            return

        if mission.status != MissionStatus.REQUESTED: # Check before opening dialog
            QMessageBox.information(self, "اطلاع", f"این مأموریت در وضعیت '{mission.status.value}' است و در حال حاضر قابل ارزیابی نیست.")
            return

        dialog = EvaluateMissionDialog(mission=mission, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_missions_table()

    def open_assign_mission_dialog(self):
        mission_id = self.get_selected_mission_id()
        if mission_id is None:
            QMessageBox.information(self, "راهنما", "لطفا یک مأموریت برای تخصیص انتخاب کنید.")
            return

        db = SessionLocal()
        mission = db.query(Mission).get(mission_id)
        db.close()

        if not mission:
            QMessageBox.critical(self, "خطا", "مأموریت یافت نشد.")
            self.refresh_missions_table()
            return

        if mission.status != MissionStatus.APPROVED: # Only assign approved missions
            QMessageBox.information(self, "اطلاع", f"این مأموریت در وضعیت '{mission.status.value}' است و قابل تخصیص راننده/خودرو نیست. ابتدا باید تأیید شود.")
            return

        dialog = AssignToMissionDialog(mission=mission, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_missions_table()

    def start_selected_mission(self):
        mission_id = self.get_selected_mission_id()
        if not mission_id: return QMessageBox.information(self, "راهنما", "لطفا مأموریتی را برای شروع انتخاب کنید.")

        db = SessionLocal()
        mission = db.query(Mission).get(mission_id)
        if not mission:
            db.close()
            return QMessageBox.critical(self, "خطا", "مأموریت یافت نشد.")

        if mission.status != MissionStatus.ASSIGNED:
            db.close()
            return QMessageBox.warning(self, "خطا", f"فقط مأموریت های در وضعیت '{MissionStatus.ASSIGNED.value}' قابل شروع هستند.")

        if not mission.driver_id: # Should not happen if status is ASSIGNED
            db.close()
            return QMessageBox.warning(self, "خطا", "راننده ای به این مأموریت تخصیص داده نشده است.")

        reply = QMessageBox.question(self, "تأیید شروع مأموریت",
                                     f"آیا از شروع مأموریت ID: {mission.id} اطمینان دارید؟",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                mission.status = MissionStatus.IN_PROGRESS
                mission.actual_start_datetime_utc = datetime.datetime.now(datetime.timezone.utc)
                db.add(mission)
                db.commit()
                QMessageBox.information(self, "موفقیت", f"مأموریت ID: {mission.id} شروع شد.")
                self.refresh_missions_table()
            except Exception as e:
                db.rollback()
                QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در شروع مأموریت: {e}")
            finally:
                db.close()
        else:
            db.close()


    def open_complete_mission_dialog(self):
        mission_id = self.get_selected_mission_id()
        if not mission_id: return QMessageBox.information(self, "راهنما", "لطفا مأموریتی را برای تکمیل انتخاب کنید.")

        db = SessionLocal()
        mission = db.query(Mission).get(mission_id)
        db.close() # Close session after fetching, dialog will use its own

        if not mission: return QMessageBox.critical(self, "خطا", "مأموریت یافت نشد.")

        if mission.status != MissionStatus.IN_PROGRESS:
            return QMessageBox.warning(self, "خطا", f"فقط مأموریت های در وضعیت '{MissionStatus.IN_PROGRESS.value}' قابل تکمیل هستند.")

        dialog = CompleteCancelMissionDialog(mission=mission, action_type="complete", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_missions_table()

    def open_cancel_mission_dialog(self):
        mission_id = self.get_selected_mission_id()
        if not mission_id: return QMessageBox.information(self, "راهنما", "لطفا مأموریتی را برای لغو انتخاب کنید.")

        db = SessionLocal()
        mission = db.query(Mission).get(mission_id)
        db.close()

        if not mission: return QMessageBox.critical(self, "خطا", "مأموریت یافت نشد.")

        if mission.status in [MissionStatus.COMPLETED, MissionStatus.REJECTED, MissionStatus.CANCELLED]:
             return QMessageBox.warning(self, "خطا", f"مأموریت در وضعیت '{mission.status.value}' قابل لغو نیست.")

        dialog = CompleteCancelMissionDialog(mission=mission, action_type="cancel", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_missions_table()


    def refresh_missions_table(self):
        self.missions_table.setRowCount(0)
        self.view_edit_mission_button.setEnabled(False)
        self.evaluate_mission_button.setEnabled(False)
        self.assign_mission_button.setEnabled(False)
        self.start_mission_button.setEnabled(False)
        self.complete_mission_button.setEnabled(False)
        self.cancel_mission_button.setEnabled(False)

        db = SessionLocal()
        query = db.query(Mission)

        # Apply filters
        selected_status_filter = self.status_filter_combo.currentData()
        if selected_status_filter is not None:
            query = query.filter(Mission.status == selected_status_filter)

        # Add other filters (date range, type) here if implemented

        missions = query.order_by(Mission.requested_datetime_utc.desc()).all()

        for row, m in enumerate(missions):
            self.missions_table.insertRow(row)
            self.missions_table.setItem(row, 0, QTableWidgetItem(str(m.id)))
            self.missions_table.setItem(row, 1, QTableWidgetItem(m.mission_type.value))
            self.missions_table.setItem(row, 2, QTableWidgetItem(m.requester_name))
            self.missions_table.setItem(row, 3, QTableWidgetItem(m.origin))
            self.missions_table.setItem(row, 4, QTableWidgetItem(m.destination))

            start_sched_str = m.scheduled_start_datetime_utc.strftime("%Y-%m-%d %H:%M") if m.scheduled_start_datetime_utc else "N/A"
            end_sched_str = m.scheduled_end_datetime_utc.strftime("%Y-%m-%d %H:%M") if m.scheduled_end_datetime_utc else "N/A"
            self.missions_table.setItem(row, 5, QTableWidgetItem(start_sched_str))
            self.missions_table.setItem(row, 6, QTableWidgetItem(end_sched_str))

            self.missions_table.setItem(row, 7, QTableWidgetItem(m.driver.name if m.driver else "---"))
            self.missions_table.setItem(row, 8, QTableWidgetItem(m.vehicle.plate_number if m.vehicle else "---"))
            self.missions_table.setItem(row, 9, QTableWidgetItem(m.status.value))

            # Optionally color rows based on status
            # if m.status == MissionStatus.REQUESTED:
            #     for col in range(self.missions_table.columnCount()):
            #         self.missions_table.item(row, col).setBackground(Qt.yellow)

        self.missions_table.resizeColumnsToContents()
        db.close()


if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    from database import create_tables

    app = QApplication(sys.argv)
    create_tables() # Ensure tables exist for testing

    # Test RequestMissionDialog
    # dialog = RequestMissionDialog()
    # dialog.show()

    # Test MissionManagementWidget
    main_widget = MissionManagementWidget() # Needs a mock parent with current_user for full testing
    main_widget.showMaximized()

    sys.exit(app.exec())
