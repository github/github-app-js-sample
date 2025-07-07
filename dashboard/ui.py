# UI components for Management Dashboard
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGridLayout, QGroupBox,
                             QPushButton, QScrollArea, QApplication) # Added QApplication for main
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon

# Matplotlib imports for charting
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt # For colormaps or specific plot types if needed
import matplotlib.font_manager as fm # For font management

from database import SessionLocal
from vehicle_management.models import Vehicle
from driver_management.models import Driver
from mission_management.models import Mission, MissionStatus
import datetime

# --- Font Setup for Matplotlib (Attempt for Persian) ---
# This should ideally be more robust, perhaps using a config file or better font discovery.
# For now, we assume Vazir.ttf might be available.
# TODO: Ensure Vazir.ttf is in the project and path is correct, or use a system-installed Jalali font.
try:
    # Find a Persian font if possible, otherwise default.
    # This is a simplistic way; a more robust method would be to bundle a font.
    font_path = None
    for font in fm.findSystemFonts(fontpaths=None, fontext='ttf'):
        if 'vazir' in font.lower() or 'sahel' in font.lower() or 'shabnam' in font.lower(): # Common Persian fonts
            font_path = font
            break

    if font_path:
        fm.fontManager.addfont(font_path)
        plt.rcParams['font.family'] = fm.FontProperties(fname=font_path).get_name()
        print(f"Matplotlib using font: {plt.rcParams['font.family']}")
    else:
        print("Matplotlib: Persian font (Vazir, Sahel, Shabnam) not found. Using default.")
        # plt.rcParams['font.family'] = 'DejaVu Sans' # A common fallback that supports many glyphs
except Exception as e:
    print(f"Error setting Matplotlib font: {e}. Using default.")
    # plt.rcParams['font.family'] = 'DejaVu Sans'

plt.rcParams['axes.unicode_minus'] = False # Handle minus sign correctly with non-ASCII fonts


class DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setWindowTitle("داشبورد مدیریتی")

        # --- Main Title ---
        title_label = QLabel("داشبورد مدیریتی - نمای کلی", self)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold; margin-bottom: 10px;")
        self.layout.addWidget(title_label)

        # --- Refresh Button ---
        refresh_button = QPushButton(QIcon.fromTheme("view-refresh"), " بروزرسانی داشبورد")
        refresh_button.clicked.connect(self.load_dashboard_data)
        self.layout.addWidget(refresh_button, 0, Qt.AlignmentFlag.AlignRight)


        # --- Scroll Area for Content ---
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.content_layout = QVBoxLayout(self.scroll_content)
        scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(scroll_area)


        # --- KPIs Group ---
        kpi_group = QGroupBox("شاخص های کلیدی عملکرد (KPIs)")
        kpi_group.setStyleSheet("font-weight: bold;")
        self.kpi_grid = QGridLayout(kpi_group)

        self.kpi_labels = {
            "active_vehicles": QLabel("خودروهای فعال: N/A"),
            "active_drivers": QLabel("رانندگان فعال: N/A"),
            "drivers_on_mission": QLabel("رانندگان در مأموریت: N/A"),
            "vehicles_on_mission": QLabel("خودروها در مأموریت: N/A"),
            "upcoming_insurance": QLabel("هشدار بیمه ها (تا ۳۰ روز آینده): N/A"),
            "upcoming_inspection": QLabel("هشدار معاینه فنی (تا ۳۰ روز آینده): N/A"),
        }
        for i, (key, label) in enumerate(self.kpi_labels.items()):
            label.setStyleSheet("font-size: 11pt; padding: 5px; border: 1px solid #ccc; border-radius: 5px; background-color: #f0f0f0;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.kpi_grid.addWidget(label, i // 2, i % 2) # Arrange in 2 columns
        self.content_layout.addWidget(kpi_group)

        # --- Charts Group ---
        charts_group = QGroupBox("نمودارهای آماری")
        charts_group.setStyleSheet("font-weight: bold;")
        self.charts_layout = QVBoxLayout(charts_group) # Main layout for all charts

        # Placeholder for Mission Status Chart
        self.mission_status_canvas_placeholder = QWidget()
        self.charts_layout.addWidget(QLabel("وضعیت مأموریت ها:"))
        self.charts_layout.addWidget(self.mission_status_canvas_placeholder)

        # Add more chart placeholders if needed
        # self.vehicle_types_canvas_placeholder = QWidget()
        # self.charts_layout.addWidget(QLabel("انواع خودروها:"))
        # self.charts_layout.addWidget(self.vehicle_types_canvas_placeholder)

        self.content_layout.addWidget(charts_group)
        self.content_layout.addStretch()

        # --- Auto-refresh Timer ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.load_dashboard_data)
        self.timer.start(60000 * 5) # Refresh every 5 minutes (300,000 ms)

        self.load_dashboard_data() # Initial load

    def load_dashboard_data(self):
        self.status_label = getattr(self.parent(), 'status_bar', None) # Try to get status bar from parent
        if self.status_label: self.status_label.showMessage("در حال بروزرسانی داشبورد...")

        db = SessionLocal()
        try:
            # KPI: Active Vehicles
            active_vehicles_count = db.query(Vehicle).filter(Vehicle.is_active == True).count()
            self.kpi_labels["active_vehicles"].setText(f"خودروهای فعال: {active_vehicles_count}")

            # KPI: Active Drivers
            active_drivers_count = db.query(Driver).filter(Driver.is_active == True).count()
            self.kpi_labels["active_drivers"].setText(f"رانندگان فعال: {active_drivers_count}")

            # KPI: Drivers on Mission
            drivers_on_mission_count = db.query(Mission).filter(Mission.status == MissionStatus.IN_PROGRESS, Mission.driver_id != None).distinct(Mission.driver_id).count()
            self.kpi_labels["drivers_on_mission"].setText(f"رانندگان در مأموریت: {drivers_on_mission_count}")

            # KPI: Vehicles on Mission
            vehicles_on_mission_count = db.query(Mission).filter(Mission.status == MissionStatus.IN_PROGRESS, Mission.vehicle_id != None).distinct(Mission.vehicle_id).count()
            self.kpi_labels["vehicles_on_mission"].setText(f"خودروها در مأموریت: {vehicles_on_mission_count}")

            # KPI: Upcoming Insurance/Inspections
            today = datetime.date.today()
            in_30_days = today + datetime.timedelta(days=30)

            upcoming_tpi = db.query(Vehicle).filter(Vehicle.is_active == True, Vehicle.third_party_insurance_expiry.between(today, in_30_days)).count()
            upcoming_bi = db.query(Vehicle).filter(Vehicle.is_active == True, Vehicle.body_insurance_expiry.between(today, in_30_days)).count()
            self.kpi_labels["upcoming_insurance"].setText(f"بیمه در شرف انقضا: ثالث ({upcoming_tpi}), بدنه ({upcoming_bi})")

            upcoming_insp = db.query(Vehicle).filter(Vehicle.is_active == True, Vehicle.technical_inspection_expiry.between(today, in_30_days)).count()
            self.kpi_labels["upcoming_inspection"].setText(f"معاینه فنی در شرف انقضا: {upcoming_insp}")

            # --- Chart Data ---
            # Mission Status Distribution
            mission_statuses = db.query(Mission.status, func.count(Mission.id)).group_by(Mission.status).all()
            if mission_statuses:
                labels = [status.value for status, count in mission_statuses] # Use enum value for Persian label
                sizes = [count for status, count in mission_statuses]
                self.setup_mission_status_chart(labels, sizes)
            else: # Clear chart if no data
                 self.clear_chart_placeholder(self.mission_status_canvas_placeholder)


            if self.status_label: self.status_label.showMessage("داشبورد بروزرسانی شد.", 3000)

        except Exception as e:
            if self.status_label: self.status_label.showMessage(f"خطا در بارگذاری داشبورد: {e}", 5000)
            print(f"Error loading dashboard data: {e}")
        finally:
            db.close()

    def setup_mission_status_chart(self, labels, sizes):
        # Clear previous chart if any
        self.clear_chart_placeholder(self.mission_status_canvas_placeholder)

        fig = Figure(figsize=(5, 3), dpi=100) # Smaller figure size for dashboard
        ax = fig.add_subplot(111)

        # Explode slices slightly if you want (optional)
        # explode = tuple([0.05] * len(labels))

        # Use a good colormap
        # colors = plt.cm.Paired(range(len(labels))) # Using a colormap
        # ax.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%', shadow=False, startangle=90, colors=colors)

        # Simpler pie without explode and specific colors, letting Matplotlib choose
        wedges, texts, autotexts = ax.pie(sizes, autopct='%1.1f%%', startangle=90, textprops={'fontsize': 8}) # Smaller font for pie

        ax.axis('equal') # Equal aspect ratio ensures that pie is drawn as a circle.
        # ax.set_title("پراکندگی وضعیت مأموریت ها", fontproperties=fm.FontProperties(fname=font_path) if font_path else None, fontsize=10)
        # Title is now part of the groupbox label

        # Add legend to the side if many slices, or rely on labels/autopct for fewer slices
        # ax.legend(wedges, labels, title="وضعیت ها", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), prop={'size':7} )

        fig.tight_layout() # Adjust layout to prevent labels from overlapping

        canvas = FigureCanvas(fig)

        # Replace placeholder with new canvas
        old_widget = self.mission_status_canvas_placeholder.layout().itemAt(0).widget() if self.mission_status_canvas_placeholder.layout() else None
        if old_widget:
            old_widget.deleteLater()
        else: # First time, create layout
             self.mission_status_canvas_placeholder.setLayout(QVBoxLayout())

        self.mission_status_canvas_placeholder.layout().addWidget(canvas)
        canvas.draw()


    def clear_chart_placeholder(self, placeholder_widget):
        if placeholder_widget.layout() is not None:
            while placeholder_widget.layout().count():
                item = placeholder_widget.layout().takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
        else: # If no layout, create one (though it should have one after first chart)
            placeholder_widget.setLayout(QVBoxLayout())


if __name__ == '__main__':
    import sys
    # from PyQt6.QtWidgets import QApplication # Already imported above
    from database import create_tables # For testing standalone

    app = QApplication(sys.argv)
    create_tables()

    # To test font loading, you might need to ensure the app path is correct
    # or place Vazir.ttf in the script's directory for this standalone test.
    # For example, if Vazir.ttf is next to ui.py:
    # import os
    # FONT_PATH = os.path.join(os.path.dirname(__file__), "Vazir.ttf")
    # if os.path.exists(FONT_PATH):
    #     fm.fontManager.addfont(FONT_PATH)
    #     plt.rcParams['font.family'] = fm.FontProperties(fname=FONT_PATH).get_name()
    # else:
    #     print("Vazir.ttf not found for standalone test.")


    main_widget = DashboardWidget()
    main_widget.showMaximized()
    sys.exit(app.exec())
