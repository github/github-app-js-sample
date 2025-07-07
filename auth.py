# User authentication and authorization
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox
from database import SessionLocal, User

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ورود کاربر")
        self.layout = QVBoxLayout(self)

        self.username_label = QLabel("نام کاربری:", self)
        self.layout.addWidget(self.username_label)
        self.username_input = QLineEdit(self)
        self.layout.addWidget(self.username_input)

        self.password_label = QLabel("رمز عبور:", self)
        self.layout.addWidget(self.password_label)
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.layout.addWidget(self.password_input)

        self.login_button = QPushButton("ورود", self)
        self.login_button.clicked.connect(self.handle_login)
        self.layout.addWidget(self.login_button)

        self.user = None

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        db_session = SessionLocal()
        user = db_session.query(User).filter(User.username == username).first()
        db_session.close()

        if user and user.is_active and user.check_password(password):
            self.user = user
            self.accept()  # Close the dialog and return QDialog.Accepted
        else:
            QMessageBox.warning(self, "خطا در ورود", "نام کاربری یا رمز عبور نامعتبر است.")

def authenticate_user():
    """
    Shows the login dialog and returns the authenticated user object or None.
    """
    dialog = LoginDialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.user
    return None

if __name__ == '__main__':
    # This is for testing the login dialog independently
    # In the main app, it will be integrated into the startup flow
    from PyQt6.QtWidgets import QApplication
    import sys
    from database import create_tables, SessionLocal, User

    # Ensure tables and default admin exist for testing
    create_tables()
    db_s = SessionLocal()
    if not db_s.query(User).filter(User.username == "admin").first():
        admin = User(username="admin", role="admin")
        admin.set_password("admin123")
        db_s.add(admin)
        db_s.commit()
    db_s.close()


    app = QApplication(sys.argv)
    authenticated_user = authenticate_user()

    if authenticated_user:
        print(f"User '{authenticated_user.username}' authenticated with role '{authenticated_user.role}'.")
        # Proceed to main application window
    else:
        print("Authentication failed or dialog cancelled.")
        sys.exit(1) # Exit if authentication fails in a real scenario

    # Example of how to use in main.py (conceptual)
    # main_window = MainWindow(authenticated_user)
    # main_window.show()
    # sys.exit(app.exec())
