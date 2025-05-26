import sys
from PyQt6.QtWidgets import QApplication
from login_window import LoginWindow
from live_plot_window import LiveDynamicPlot
from mqtt_handler import init_mqtt, mqtt_signal, set_user_topic, change_topic
from encryption_utils import decrypt_file  

if __name__ == "__main__":
    app = QApplication(sys.argv)

    login_window = LoginWindow()

    def show_main(username):
        set_user_topic(username)

        users = decrypt_file("haslo123", filename="users.json.encrypted")
        user_role = users[username].get("role", "operator")

        print(f">>> Zalogowano jako {username}, rola: {user_role}")

        global main_window
        main_window = LiveDynamicPlot(user_role=user_role)

        mqtt_signal.new_data.connect(main_window.handle_new_data)
        main_window.show()
        init_mqtt()

    login_window.login_successful.connect(show_main)
    login_window.show()

    sys.exit(app.exec())
