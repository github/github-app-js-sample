# Shift Planning database models
from sqlalchemy import Column, Integer, String, Date, Time, DateTime, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from database import Base
import enum

# Using python enum for shift types
class ShiftType(enum.Enum):
    DAILY = "روزانه"
    WEEKLY = "هفتگی"
    ON_DEMAND = "در اختیار" # or "سفارشی"

class Shift(Base):
    __tablename__ = "shifts_template" # Template for creating shift instances

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True) # e.g., "Morning Shift", "Night Shift"
    type = Column(SQLAlchemyEnum(ShiftType), nullable=False)
    start_time = Column(Time) # Relevant for daily/weekly shifts
    end_time = Column(Time)   # Relevant for daily/weekly shifts
    # For weekly shifts, one might define days of the week it applies to, or create separate templates.
    # For on-demand, start/end time might be less relevant for the template itself.
    description = Column(String)

    assignments = relationship("ShiftAssignment", back_populates="shift_template")

    def __repr__(self):
        return f"<ShiftTemplate {self.name} ({self.type.value})>"


class ShiftAssignment(Base):
    __tablename__ = "shift_assignments" # Actual assigned shifts

    id = Column(Integer, primary_key=True, index=True)
    shift_template_id = Column(Integer, ForeignKey("shifts_template.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True) # Vehicle might be optional or assigned later

    # For specific instances, especially on-demand or overrides of weekly/daily
    # These will store Jalali dates after conversion
    start_datetime_utc = Column(DateTime, nullable=False) # Store as UTC
    end_datetime_utc = Column(DateTime, nullable=False)   # Store as UTC
    # Note: When displaying or taking input, convert these UTC times to local Jalali time.

    notes = Column(String)

    shift_template = relationship("Shift", back_populates="assignments")
    driver = relationship("Driver", back_populates="shifts")
    vehicle = relationship("Vehicle") # Define back_populates in Vehicle model if needed

    def __repr__(self):
        return f"<ShiftAssignment Driver: {self.driver_id} Start: {self.start_datetime_utc}>"
