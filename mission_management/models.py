# Mission Management database models
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLAlchemyEnum, Text
from sqlalchemy.orm import relationship
from database import Base
import enum

class MissionType(enum.Enum):
    URBAN = "شهری"
    INTERCITY = "برون شهری"

class MissionStatus(enum.Enum):
    REQUESTED = "درخواست شده"
    EVALUATING = "در حال ارزیابی"
    APPROVED = "تایید شده" # Approved but not yet started/assigned
    ASSIGNED = "تخصیص داده شده" # Driver/Vehicle assigned, scheduled
    IN_PROGRESS = "در حال انجام"
    COMPLETED = "تکمیل شده"
    REJECTED = "رد شده"
    CANCELLED = "لغو شده"


class Mission(Base):
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True, index=True)
    mission_type = Column(SQLAlchemyEnum(MissionType), nullable=False)
    status = Column(SQLAlchemyEnum(MissionStatus), nullable=False, default=MissionStatus.REQUESTED)

    requester_name = Column(String, nullable=False) # نام درخواست کننده
    requester_contact = Column(String) # شماره تماس یا اطلاعات دیگر درخواست کننده

    # Store Jalali dates after conversion to UTC for consistency
    requested_datetime_utc = Column(DateTime) # زمان درخواست ماموریت
    scheduled_start_datetime_utc = Column(DateTime) # زمانبندی شروع
    scheduled_end_datetime_utc = Column(DateTime)   # زمانبندی پایان
    actual_start_datetime_utc = Column(DateTime)    # زمان واقعی شروع
    actual_end_datetime_utc = Column(DateTime)      # زمان واقعی پایان

    origin = Column(String, nullable=False) # مبدا
    destination = Column(String, nullable=False) # مقصد
    route_details = Column(Text) # جزئیات مسیر، نقاط میانی و ...
    purpose = Column(Text) # هدف ماموریت

    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)

    notes = Column(Text) # یادداشت های اضافی، توضیحات رد یا تکمیل
    evaluation_notes = Column(Text) # یادداشت های مربوط به ارزیابی

    driver = relationship("Driver", back_populates="missions")
    vehicle = relationship("Vehicle", back_populates="missions")

    # Relationship to ShiftAssignment (optional, if missions are tied to specific shifts)
    # shift_assignment_id = Column(Integer, ForeignKey("shift_assignments.id"))
    # shift_assignment = relationship("ShiftAssignment")


    def __repr__(self):
        return f"<Mission ID: {self.id} Type: {self.mission_type.value} Status: {self.status.value}>"
