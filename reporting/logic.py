# reporting/logic.py
import pandas as pd
from sqlalchemy import func # For database functions like SUM, COUNT, AVG
from database import SessionLocal
from mission_management.models import Mission, MissionStatus
from driver_management.models import Driver
from vehicle_management.models import Vehicle
import datetime

def generate_driver_performance_data(filters: dict) -> pd.DataFrame:
    """
    Generates data for the driver performance report.
    Filters include: start_date, end_date, selected_driver_ids
    """
    db = SessionLocal()
    try:
        start_date = datetime.datetime.combine(filters["start_date"], datetime.time.min)
        end_date = datetime.datetime.combine(filters["end_date"], datetime.time.max)

        query = db.query(
            Driver.id.label("driver_id"),
            Driver.name.label("نام راننده"),
            func.count(Mission.id).label("تعداد کل ماموریت ها"),
            func.sum(
                case(
                    (Mission.status == MissionStatus.COMPLETED, 1),
                    else_=0
                )
            ).label("تعداد ماموریت های تکمیل شده"),
            func.sum(
                case(
                    (Mission.status == MissionStatus.COMPLETED,
                     func.strftime('%s', Mission.actual_end_datetime_utc) - func.strftime('%s', Mission.actual_start_datetime_utc)),
                    else_=0
                )
            ).label("مجموع مدت زمان ماموریت (ثانیه)")
        ).select_from(Driver).outerjoin(Mission, Driver.id == Mission.driver_id)

        # Apply filters
        if filters.get("selected_driver_ids"):
            query = query.filter(Driver.id.in_(filters["selected_driver_ids"]))

        # Date filter on missions (only count missions within the date range)
        # This condition applies to missions that have a start or end time within the range,
        # or span the entire range.
        query = query.filter(
            (Mission.id == None) | # Include drivers with no missions
            (
                (Mission.actual_start_datetime_utc <= end_date) &
                (Mission.actual_end_datetime_utc >= start_date) &
                (Mission.status == MissionStatus.COMPLETED) # Consider only completed for duration/count
            )
        )

        query = query.group_by(Driver.id, Driver.name).order_by(Driver.name)

        results = query.all()

        if not results:
            return pd.DataFrame()

        df = pd.DataFrame(results)

        if not df.empty:
            # Convert seconds to a more readable format (HH:MM:SS or hours)
            df["مجموع مدت زمان ماموریت (ساعت)"] = df["مجموع مدت زمان ماموریت (ثانیه)"].apply(
                lambda x: round(x / 3600, 2) if pd.notnull(x) and x > 0 else 0
            )
            df.drop(columns=["مجموع مدت زمان ماموریت (ثانیه)"], inplace=True)
            df.fillna({"تعداد کل ماموریت ها": 0, "تعداد ماموریت های تکمیل شده": 0, "مجموع مدت زمان ماموریت (ساعت)":0}, inplace=True)
            df = df[["نام راننده", "تعداد ماموریت های تکمیل شده", "مجموع مدت زمان ماموریت (ساعت)"]]


        return df

    finally:
        db.close()


def generate_vehicle_utilization_data(filters: dict) -> pd.DataFrame:
    """
    Generates data for the vehicle utilization report.
    Filters include: start_date, end_date, selected_vehicle_ids
    """
    db = SessionLocal()
    try:
        from sqlalchemy import case # Import case here if not already global
        start_date = datetime.datetime.combine(filters["start_date"], datetime.time.min)
        end_date = datetime.datetime.combine(filters["end_date"], datetime.time.max)

        query = db.query(
            Vehicle.id.label("vehicle_id"),
            Vehicle.plate_number.label("شماره پلاک"),
            Vehicle.model.label("مدل خودرو"),
            func.count(Mission.id).label("تعداد کل ماموریت ها (در بازه)"),
             func.sum(
                case(
                    (Mission.status == MissionStatus.COMPLETED, 1),
                    else_=0
                )
            ).label("تعداد ماموریت های تکمیل شده (در بازه)"),
            func.sum(
                case(
                    (Mission.status == MissionStatus.COMPLETED,
                     func.strftime('%s', Mission.actual_end_datetime_utc) - func.strftime('%s', Mission.actual_start_datetime_utc)),
                    else_=0 # seconds
                )
            ).label("مجموع زمان استفاده در ماموریت (ثانیه)")
        ).select_from(Vehicle).outerjoin(Mission, Vehicle.id == Mission.vehicle_id)

        if filters.get("selected_vehicle_ids"):
            query = query.filter(Vehicle.id.in_(filters["selected_vehicle_ids"]))

        query = query.filter(
            (Mission.id == None) |
            (
                (Mission.actual_start_datetime_utc <= end_date) &
                (Mission.actual_end_datetime_utc >= start_date) &
                (Mission.status == MissionStatus.COMPLETED)
            )
        )

        query = query.group_by(Vehicle.id, Vehicle.plate_number, Vehicle.model).order_by(Vehicle.plate_number)
        results = query.all()

        if not results:
            return pd.DataFrame()

        df = pd.DataFrame(results)

        if not df.empty:
            df["مجموع زمان استفاده (ساعت)"] = df["مجموع زمان استفاده در ماموریت (ثانیه)"].apply(
                lambda x: round(x / 3600, 2) if pd.notnull(x) and x > 0 else 0
            )
            df.drop(columns=["مجموع زمان استفاده در ماموریت (ثانیه)"], inplace=True)
            df.fillna({"تعداد کل ماموریت ها (در بازه)": 0, "تعداد ماموریت های تکمیل شده (در بازه)": 0, "مجموع زمان استفاده (ساعت)":0}, inplace=True)
            df = df[["شماره پلاک", "مدل خودرو", "تعداد ماموریت های تکمیل شده (در بازه)", "مجموع زمان استفاده (ساعت)"]]

        return df

    finally:
        db.close()

if __name__ == '__main__':
    # Example Usage (for testing)
    print("Testing Driver Performance Report Logic:")
    # Create dummy filters
    # Ensure you have some data in your DB for this to work, or mock it.
    # For a real test, you'd need to setup a test DB or ensure data exists.

    # This is a basic test. For thorough testing, use a test database with known data.
    # For now, we assume the DB might be empty or have some data.

    # Test with all drivers for the last month
    today = datetime.date.today()
    last_month_start = today.replace(day=1) - datetime.timedelta(days=1)
    last_month_start = last_month_start.replace(day=1)

    all_drivers_filters = {
        "start_date": last_month_start,
        "end_date": today,
        "selected_driver_ids": [] # Empty means all
    }
    # driver_df = generate_driver_performance_data(all_drivers_filters)
    # print(driver_df.to_string())

    print("\nTesting Vehicle Utilization Report Logic:")
    all_vehicles_filters = {
        "start_date": last_month_start,
        "end_date": today,
        "selected_vehicle_ids": [] # Empty means all
    }
    # vehicle_df = generate_vehicle_utilization_data(all_vehicles_filters)
    # print(vehicle_df.to_string())

    print("\nNOTE: For meaningful test output, ensure your database (fleet_management.db) contains relevant mission data.")
    print("The queries attempt to sum durations of COMPLETED missions within the date range.")
