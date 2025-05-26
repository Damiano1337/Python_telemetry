import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget,
    QPushButton, QMessageBox
)
from encryption_utils import decrypt_file, encrypt_file
from config import ADMIN_PASSWORD

class DeleteUserWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Usuń użytkownika")
        self.resize(400, 300)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.user_list = QListWidget()
        self.layout.addWidget(QLabel("Wybierz użytkownika do usunięcia:"))
        self.layout.addWidget(self.user_list)

        self.delete_button = QPushButton("Usuń zaznaczonego użytkownika")
        self.delete_button.clicked.connect(self.delete_selected_user)
        self.layout.addWidget(self.delete_button)

        self.users = {}
        self.load_users()

    def load_users(self):
        try:
            self.users = decrypt_file(ADMIN_PASSWORD)
            self.user_list.addItems([u for u in self.users.keys() if u != "admin"])
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się wczytać użytkowników:\n{e}")

    def delete_selected_user(self):
        selected_items = self.user_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Błąd", "Nie wybrano użytkownika do usunięcia.")
            return

        username = selected_items[0].text()

        confirm = QMessageBox.question(
            self,
            "Potwierdź usunięcie",
            f"Czy na pewno chcesz usunąć użytkownika '{username}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            self.users.pop(username, None)
            try:
                encrypt_file(self.users, ADMIN_PASSWORD)
                QMessageBox.information(self, "Sukces", f"Użytkownik '{username}' został usunięty.")
                self.user_list.clear()
                self.load_users()
            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Nie udało się zapisać zmian:\n{e}")