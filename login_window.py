import json
from encryption_utils import decrypt_file
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QLabel,
    QPushButton, QMessageBox
)
from PyQt6.QtCore import pyqtSignal

# Zmieniamy sygnał:
class LoginWindow(QWidget):
    login_successful = pyqtSignal(str)  # <- emitujemy login


    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logowanie")
        self.setFixedSize(300, 150)

        layout = QVBoxLayout()

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Login")
        layout.addWidget(QLabel("Login:"))
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Hasło")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel("Hasło:"))
        layout.addWidget(self.password_input)

        login_button = QPushButton("Zaloguj")
        login_button.clicked.connect(self.verify_credentials)
        layout.addWidget(login_button)

        self.setLayout(layout)

    def verify_credentials(self):
        try:
            username = self.username_input.text().strip()
            password = self.password_input.text().strip()

            # 👉 Zamiast: with open("users.json", "r") ...
            users = decrypt_file("haslo123")  # ← to hasło, które podałeś przy szyfrowaniu

            user_data = users.get(username)

            if user_data and user_data.get("password") == password:
                self.login_successful.emit(username)
                self.close()
            else:
                QMessageBox.warning(self, "Błąd logowania", "Niepoprawny login lub hasło.")

        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się zalogować:\n{e}")
