# Vehicle database models
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String, unique=True, index=True, nullable=False)
    model = Column(String)
    year = Column(Integer)
    # Basic insurance info - can be expanded to a separate table if more detail is needed
    third_party_insurance_expiry = Column(Date)
    body_insurance_expiry = Column(Date)
    has_third_party_insurance = Column(Boolean, default=False)
    has_body_insurance = Column(Boolean, default=False)
    technical_inspection_expiry = Column(Date)
    is_active = Column(Boolean, default=True) # Is the vehicle currently in service?

    # Add more fields like color, VIN, capacity, fuel_type, etc. as needed

    # Relationship to Driver (One-to-Many or Many-to-Many if vehicles can have multiple assigned drivers over time)
    # For simplicity, a current_driver_id can be added if a vehicle has one primary driver at a time.
    # Or a separate association table for history of assignments.
    # current_driver_id = Column(Integer, ForeignKey("drivers.id"))
    # current_driver = relationship("Driver", back_populates="assigned_vehicles")

    # Relationship to Missions
    missions = relationship("Mission", back_populates="vehicle")

    def __repr__(self):
        return f"<Vehicle {self.plate_number} ({self.model})>"
