from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QMessageBox, QListWidget
)
from PyQt6.QtCore import pyqtSignal
from encryption_utils import decrypt_file, encrypt_file
from delete_user_window import DeleteUserWindow
from config import ADMIN_PASSWORD


class UserManagerWindow(QWidget):
    add_default_plots_signal = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Zarządzanie użytkownikami")
        self.setFixedSize(300, 250)

        layout = QVBoxLayout()

        self.add_button = QPushButton("➕ Dodaj użytkownika")
        self.edit_button = QPushButton("✏️ Edytuj użytkownika")
        self.delete_button = QPushButton("🗑️ Usuń użytkownika")
        self.default_plots_button = QPushButton("📊 Dodaj 11 domyślnych wykresów")

        self.delete_button.clicked.connect(self.open_delete_window)
        self.add_button.clicked.connect(self.open_add_window)
        self.edit_button.clicked.connect(self.open_edit_window)
        self.default_plots_button.clicked.connect(self.add_default_plots)

        layout.addWidget(self.add_button)
        layout.addWidget(self.edit_button)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.default_plots_button)

        self.setLayout(layout)

    def open_add_window(self):
        self.add_window = AddUserWindow()
        self.add_window.show()

    def open_edit_window(self):
        self.edit_window = EditUserWindow()
        self.edit_window.show()

    def open_delete_window(self):
        self.delete_window = DeleteUserWindow()
        self.delete_window.show()

    def add_default_plots(self):
        plots = ["v1", "v2", "v3", "v4", "c1", "c2", "c3", "c4", "s", "e_c", "e_s"]
        self.add_default_plots_signal.emit(plots)
        QMessageBox.information(self, "Dodano wykresy", "Dodano 11 domyślnych wykresów.")


class AddUserWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dodaj użytkownika")
        self.setFixedSize(400, 300)

        layout = QVBoxLayout()

        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.topic_input = QLineEdit()
        self.role_input = QComboBox()
        self.role_input.addItems(["operator", "admin"])

        layout.addWidget(QLabel("Login użytkownika:"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("Hasło:"))
        layout.addWidget(self.password_input)
        layout.addWidget(QLabel("Topic:"))
        layout.addWidget(self.topic_input)
        layout.addWidget(QLabel("Rola:"))
        layout.addWidget(self.role_input)

        self.save_button = QPushButton("Dodaj")
        self.save_button.clicked.connect(self.add_user)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def add_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        topic = self.topic_input.text().strip()
        role = self.role_input.currentText()

        if not username or not password or not topic:
            QMessageBox.warning(self, "Błąd", "Wszystkie pola muszą być wypełnione.")
            return

        try:
            users = decrypt_file(ADMIN_PASSWORD)
        except Exception:
            users = {}

        if username in users:
            QMessageBox.warning(self, "Błąd", "Taki użytkownik już istnieje.")
            return

        users[username] = {
            "password": password,
            "topic": topic,
            "role": role
        }

        try:
            encrypt_file(users, ADMIN_PASSWORD)
            QMessageBox.information(self, "Sukces", "Użytkownik dodany.")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się zapisać: {e}")


class EditUserWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Edytuj użytkownika")
        self.resize(500, 500)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.user_list = QListWidget()
        self.layout.addWidget(QLabel("Wybierz użytkownika:"))
        self.layout.addWidget(self.user_list)
        self.user_list.setMinimumHeight(200)
        self.user_list.setMaximumHeight(300)
        self.user_list.itemClicked.connect(self.populate_fields_from_item)

        self.password_input = QLineEdit()
        self.topic_input = QLineEdit()
        self.role_input = QComboBox()
        self.role_input.addItems(["operator", "admin"])

        self.layout.addWidget(QLabel("Nowe hasło:"))
        self.layout.addWidget(self.password_input)
        self.layout.addWidget(QLabel("Nowy topic:"))
        self.layout.addWidget(self.topic_input)
        self.layout.addWidget(QLabel("Nowa rola:"))
        self.layout.addWidget(self.role_input)

        self.save_button = QPushButton("Zapisz zmiany")
        self.save_button.clicked.connect(self.save_changes)
        self.layout.addWidget(self.save_button)

        self.users = {}
        self.current_username = None
        self.load_users()

    def load_users(self):
        self.user_list.clear()
        try:
            self.users = decrypt_file(ADMIN_PASSWORD)
            self.user_list.addItems(list(self.users.keys()))

            if self.user_list.count() > 0:
                self.user_list.setCurrentRow(0)
                self.populate_fields_from_item(self.user_list.item(0))

        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się wczytać użytkowników:\n{e}")

    def populate_fields_from_item(self, item):
        username = item.text()
        self.current_username = username
        user = self.users.get(username, {})
        self.password_input.setText(user.get("password", ""))
        self.topic_input.setText(user.get("topic", ""))
        self.role_input.setCurrentText(user.get("role", "operator"))

    def save_changes(self):
        if not self.current_username:
            return

        new_password = self.password_input.text().strip()
        new_topic = self.topic_input.text().strip()
        new_role = self.role_input.currentText()

        if not new_password or not new_topic:
            QMessageBox.warning(self, "Błąd", "Wszystkie pola muszą być wypełnione.")
            return

        self.users[self.current_username] = {
            "password": new_password,
            "topic": new_topic,
            "role": new_role
        }

        try:
            encrypt_file(self.users, ADMIN_PASSWORD)
            QMessageBox.information(self, "Sukces", "Dane zaktualizowane.")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się zapisać:\n{e}")