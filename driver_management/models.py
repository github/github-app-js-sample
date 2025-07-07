# Driver database models
from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    national_id = Column(String, unique=True, index=True, nullable=False) # کد ملی
    license_number = Column(String, unique=True) # شماره گواهینامه
    license_expiry_date = Column(Date)
    # Assuming 'گواهی نامه' refers to certifications or additional permits
    certifications = Column(Text) # Store as JSON string or comma-separated, or a separate table for many-to-many
    violations_history = Column(Text) # Store as JSON string or comma-separated, or a separate table
    contact_number = Column(String)
    address = Column(String)
    is_active = Column(Boolean, default=True)

    # Relationship to Vehicle (if a driver is primarily assigned to one or more vehicles)
    # This can be a one-to-many from Driver to Vehicle (if driver has multiple vehicles)
    # or many-to-many through an association table (DriverVehicleAssignment)
    # For simplicity, let's assume a driver can be associated with missions, not directly tied to a vehicle here
    # assigned_vehicles = relationship("Vehicle", back_populates="current_driver")

    # Relationship to Shifts
    shifts = relationship("ShiftAssignment", back_populates="driver")

    # Relationship to Missions
    missions = relationship("Mission", back_populates="driver")


    def __repr__(self):
        return f"<Driver {self.name} ({self.national_id})>"
