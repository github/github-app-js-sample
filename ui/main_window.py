# Main window UI components and layout
from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QMenuBar, QStatusBar, QMessageBox
from PyQt6.QtGui import QAction

class MainWindowUI(QMainWindow):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.setWindowTitle(f"سامانه مدیریت ناوگان (کاربر: {current_user.username} - نقش: {current_user.role})")
        self.setGeometry(100, 100, 1200, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.welcome_label = QLabel(f"کاربر {self.current_user.username} خوش آمدید!", self)
        self.layout.addWidget(self.welcome_label)

        self._create_menu_bar()
        self._create_status_bar()
        # self._create_tool_bar() # Optional

        # Placeholder for module widgets
        self.module_area = QWidget()
        self.layout.addWidget(self.module_area)


    def _create_menu_bar(self):
        self.menu_bar = self.menuBar()

        # File Menu
        file_menu = self.menu_bar.addMenu("فایل")
        exit_action = QAction("خروج", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Management Menu (Dynamically populated based on role)
        management_menu = self.menu_bar.addMenu("مدیریت")

        if self.current_user.role == "admin" or self.current_user.role == "operator":
            vehicle_action = QAction("مدیریت خودروها", self)
            vehicle_action.triggered.connect(self.open_vehicle_module)
            management_menu.addAction(vehicle_action)

            driver_action = QAction("مدیریت رانندگان", self)
            driver_action.triggered.connect(self.open_driver_module)
            management_menu.addAction(driver_action)

            shift_action = QAction("برنامه ریزی شیفت ها", self)
            shift_action.triggered.connect(self.open_shift_module)
            management_menu.addAction(shift_action)

            mission_action = QAction("مدیریت ماموریت ها", self)
            mission_action.triggered.connect(self.open_mission_module)
            management_menu.addAction(mission_action)

        if self.current_user.role == "admin":
            reporting_action = QAction("گزارش گیری", self)
            reporting_action.triggered.connect(self.open_reporting_module)
            management_menu.addAction(reporting_action)

            dashboard_action = QAction("داشبورد مدیریتی", self)
            dashboard_action.triggered.connect(self.open_dashboard_module)
            management_menu.addAction(dashboard_action)

            # user_management_action = QAction("مدیریت کاربران", self) # For admin to manage other users
            # user_management_action.triggered.connect(self.open_user_management_module)
            # management_menu.addAction(user_management_action)


        # Help Menu
        help_menu = self.menu_bar.addMenu("راهنما")
        about_action = QAction("درباره", self)
        # about_action.triggered.connect(self.show_about_dialog) # Connect later
        help_menu.addAction(about_action)

    def _create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("آماده")

    def _clear_module_area(self):
        """Clears the central module area."""
        # Ensure module_area has a layout
        if not self.module_area.layout():
            self.module_area.setLayout(QVBoxLayout()) # Assign a new layout if none exists

        # Now, safely clear existing widgets from the layout
        while self.module_area.layout().count():
            child = self.module_area.layout().takeAt(0)
            if child.widget():
                child.widget().deleteLater()


    def open_vehicle_module(self):
        self._clear_module_area()
        from vehicle_management.ui import VehicleManagementWidget # Lazy import
        vehicle_widget = VehicleManagementWidget(self) # Pass main window as parent
        self.module_area.layout().addWidget(vehicle_widget)
        self.status_bar.showMessage("ماژول مدیریت خودروها بارگذاری شد.")

    def open_driver_module(self):
        self._clear_module_area()
        from driver_management.ui import DriverManagementWidget # Lazy import
        driver_widget = DriverManagementWidget(self)
        self.module_area.layout().addWidget(driver_widget)
        self.status_bar.showMessage("ماژول مدیریت رانندگان بارگذاری شد.")

    def open_shift_module(self):
        self._clear_module_area()
        from shift_planning.ui import ShiftPlanningWidget # Lazy import
        shift_widget = ShiftPlanningWidget(self)
        self.module_area.layout().addWidget(shift_widget)
        self.status_bar.showMessage("ماژول برنامه ریزی شیفت ها بارگذاری شد.")

    def open_mission_module(self):
        self._clear_module_area()
        from mission_management.ui import MissionManagementWidget # Lazy import
        mission_widget = MissionManagementWidget(self)
        self.module_area.layout().addWidget(mission_widget)
        self.status_bar.showMessage("ماژول مدیریت ماموریت ها بارگذاری شد.")

    def open_reporting_module(self):
        if self.current_user.role != "admin":
            QMessageBox.warning(self, "دسترسی ممنوع", "شما اجازه دسترسی به این ماژول را ندارید.")
            return
        self._clear_module_area()
        from reporting.ui import ReportingWidget # Lazy import
        reporting_widget = ReportingWidget(self)
        self.module_area.layout().addWidget(reporting_widget)
        self.status_bar.showMessage("ماژول گزارش گیری بارگذاری شد.")

    def open_dashboard_module(self):
        if self.current_user.role != "admin":
            QMessageBox.warning(self, "دسترسی ممنوع", "شما اجازه دسترسی به این ماژول را ندارید.")
            return
        self._clear_module_area()
        from dashboard.ui import DashboardWidget # Lazy import
        dashboard_widget = DashboardWidget(self)
        self.module_area.layout().addWidget(dashboard_widget)
        self.status_bar.showMessage("داشبورد مدیریتی بارگذاری شد.")


    # def show_about_dialog(self):
    #     QMessageBox.about(self, "درباره سامانه", "سامانه جامع مدیریت ناوگان حمل و نقل\nنسخه 1.0")


if __name__ == '__main__':
    # This part is for testing the MainWindowUI independently
    import sys
    from PyQt6.QtWidgets import QApplication
    # Mock user for testing
    class MockUser:
        def __init__(self, username, role):
            self.username = username
            self.role = role

    app = QApplication(sys.argv)
    # Test with admin user
    admin_user = MockUser("test_admin", "admin")
    main_window_admin = MainWindowUI(admin_user)
    main_window_admin.show()

    # Test with operator user
    # operator_user = MockUser("test_operator", "operator")
    # main_window_operator = MainWindowUI(operator_user)
    # main_window_operator.show()

    sys.exit(app.exec())
