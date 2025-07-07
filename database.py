# Database setup and ORM
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
import bcrypt
import datetime # Using standard datetime for now, will integrate Jalali later

# TODO: Consider PostgreSQL for larger scale
DATABASE_URL = "sqlite:///fleet_management.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- User Model and Authentication ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # "admin", "operator"
    is_active = Column(Boolean, default=True)

    def set_password(self, password):
        self.hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.hashed_password.encode('utf-8'))

# --- Import actual models from their modules ---
# These imports are crucial for SQLAlchemy to recognize the tables.
from vehicle_management.models import Vehicle
from driver_management.models import Driver
from shift_planning.models import Shift, ShiftAssignment # Ensure all relevant models are imported
from mission_management.models import Mission

# (User model is already defined above)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully.")

    # Example: Create a default admin user
    db_session = SessionLocal()
    admin_user = db_session.query(User).filter(User.username == "admin").first()
    if not admin_user:
        admin_user = User(username="admin", role="admin")
        admin_user.set_password("admin123") # Default password, change in production
        db_session.add(admin_user)
        db_session.commit()
        print("Default admin user created.")
    db_session.close()
