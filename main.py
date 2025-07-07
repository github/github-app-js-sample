# Main application file
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from auth import authenticate_user
from database import create_tables, SessionLocal, User # For initial admin creation
from ui.main_window import MainWindowUI # Import the new UI class

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # --- Database and Initial User Setup ---
    try:
        create_tables() # Ensure tables are created
        db_s = SessionLocal()
        # Create a default admin if none exists
        if not db_s.query(User).filter(User.username == "admin").first():
            admin = User(username="admin", role="admin")
            admin.set_password("admin123") # Change this in a real application!
            db_s.add(admin)
            db_s.commit()
            print("Default admin user 'admin' with password 'admin123' created.")

        # Create a default operator if none exists (for testing)
        if not db_s.query(User).filter(User.username == "operator").first():
            op_user = User(username="operator", role="operator")
            op_user.set_password("op123") # Change this!
            db_s.add(op_user)
            db_s.commit()
            print("Default operator user 'operator' with password 'op123' created.")
        db_s.close()
    except Exception as e:
        QMessageBox.critical(None, "خطای پایگاه داده", f"امکان اتصال یا ایجاد جداول پایگاه داده وجود ندارد: {e}")
        sys.exit(1)


    # --- Authentication ---
    authenticated_user = authenticate_user()

    if authenticated_user:
        # Pass the authenticated_user to the MainWindowUI
        window = MainWindowUI(authenticated_user)
        window.show()
        sys.exit(app.exec())
    else:
        print("Authentication failed by user or dialog was closed. Application will exit.")
        # No need for QMessageBox here as the auth dialog handles user feedback
        sys.exit(0) # Exit gracefully if user cancels login
