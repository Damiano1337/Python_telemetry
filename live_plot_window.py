import time
import datetime
from mqtt_handler import change_topic
from collections import deque
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton,
    QLabel, QLineEdit, QMessageBox, QGridLayout, QGroupBox,
    QSizePolicy, QSpacerItem, QSizePolicy as QSizePolicyEnum
)
import pyqtgraph as pg
from pyqtgraph import AxisItem
from encryption_utils import decrypt_file
from config import ADMIN_PASSWORD

MAX_PLOTS = 12

class TimeAxisItem(AxisItem):
    def tickStrings(self, values, scale, spacing):
        return [datetime.datetime.fromtimestamp(value).strftime("%H:%M:%S") for value in values]


class LiveDynamicPlot(QWidget):
    def __init__(self, user_role=None):
        super().__init__()
        self.user_role = user_role
        self.selected_topic = None

        self.setWindowTitle("Dynamiczny wykres danych (MQTT)")
        self.resize(1400, 900)

        self.all_variables = [
            "v1", "c1", "v2", "c2", "v3", "c3", "v4", "c4",
            "s", "e_c", "e_s"
        ]

        self.variable_colors = {
            "v1": "yellow", "v2": "yellow", "v3": "yellow", "v4": "yellow",
            "c1": "red", "c2": "red", "c3": "red", "c4": "red",
            "predkosc": "green",
            "nat_silnika": "blue",
            "obr_silnika": "blue"
        }

        self.time_buffer = deque(maxlen=10000)
        self.data_buffer = {var: deque(maxlen=10000) for var in self.all_variables}
        self.plots = []
        self.curves = []
        self.plot_names = []

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.create_controls_panel()
        self.create_plot_grid()

        if self.user_role == "admin":
            self.admin_button = QPushButton("Zarządzaj użytkownikami")
            self.admin_button.clicked.connect(self.open_user_manager)
            self.main_layout.addWidget(self.admin_button)

    def create_controls_panel(self):
        self.controls_group = QGroupBox("Panel sterowania")
        self.controls_group.setFixedHeight(100)
        self.controls_layout = QHBoxLayout()
        self.controls_group.setLayout(self.controls_layout)
        self.main_layout.addWidget(self.controls_group)

        if self.user_role == "admin":
            self.topic_selector = QComboBox()
            self.topic_selector.addItems(self.get_all_topics())
            self.topic_selector.currentTextChanged.connect(self.set_selected_topic)
            self.controls_layout.addWidget(QLabel("Wybierz topik:"))
            self.controls_layout.addWidget(self.topic_selector)

            self.refresh_topics_button = QPushButton("🔄 Odśwież topiki")
            self.refresh_topics_button.clicked.connect(self.refresh_topics)
            self.controls_layout.addWidget(self.refresh_topics_button)

        self.var_selector = QComboBox()
        self.var_selector.addItems(self.all_variables)
        self.controls_layout.addWidget(QLabel("Zmienna:"))
        self.controls_layout.addWidget(self.var_selector)

        self.plot_selector = QComboBox()
        self.controls_layout.addWidget(QLabel("Wykres:"))
        self.controls_layout.addWidget(self.plot_selector)

        self.add_button = QPushButton("Dodaj zmienną")
        self.add_button.clicked.connect(self.add_variable)
        self.controls_layout.addWidget(self.add_button)

        self.remove_button = QPushButton("Usuń zmienną")
        self.remove_button.clicked.connect(self.remove_variable)
        self.controls_layout.addWidget(self.remove_button)

        self.plot_name_input = QLineEdit()
        self.plot_name_input.setPlaceholderText("Nazwa wykresu")
        self.controls_layout.addWidget(self.plot_name_input)

        self.add_plot_button = QPushButton("Dodaj wykres")
        self.add_plot_button.clicked.connect(self.add_plot)
        self.controls_layout.addWidget(self.add_plot_button)

        self.remove_plot_button = QPushButton("Usuń wykres")
        self.remove_plot_button.clicked.connect(self.remove_plot)
        self.controls_layout.addWidget(self.remove_plot_button)

        self.controls_layout.addItem(QSpacerItem(40, 20, QSizePolicyEnum.Policy.Expanding, QSizePolicyEnum.Policy.Minimum))

    def create_plot_grid(self):
        self.grid_layout = QGridLayout()
        self.grid_layout.setHorizontalSpacing(10)
        self.grid_layout.setVerticalSpacing(10)
        self.main_layout.addLayout(self.grid_layout)
        self.main_layout.addStretch(1)

    def refresh_topics(self):
        if hasattr(self, "topic_selector"):
            topics = self.get_all_topics()
            self.topic_selector.clear()
            self.topic_selector.addItems(topics)
            print(">>> Lista topików odświeżona")

    def open_user_manager(self):
        try:
            from user_manager_window import UserManagerWindow
            self.user_manager = UserManagerWindow()
            self.user_manager.add_default_plots_signal.connect(self.add_default_plots)
            self.user_manager.show()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się otworzyć panelu admina:\n{e}")


    def get_all_topics(self):
        try:
            users = decrypt_file(ADMIN_PASSWORD)
            return list(set(u["topic"] for u in users.values()))
        except Exception as e:
            print("Błąd odczytu topików:", e)
            return []

    def set_selected_topic(self, topic):
        self.selected_topic = topic
        print(f">>> Wybrano topik: {topic}")
        change_topic(topic)

    def update_grid_layout(self):
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            self.grid_layout.removeWidget(widget)
            widget.setParent(None)

        for i, plot in enumerate(self.plots):
            row = i // 4
            col = i % 4
            self.grid_layout.addWidget(plot, row, col)

        self.plot_selector.clear()
        self.plot_selector.addItems(self.plot_names)

    def add_plot(self):
        if len(self.plots) >= MAX_PLOTS:
            QMessageBox.warning(self, "Limit", f"Maksymalna liczba wykresów to {MAX_PLOTS}.")
            return

        name = self.plot_name_input.text().strip()
        if not name:
            name = f"Wykres {len(self.plots) + 1}"
        elif name in self.plot_names:
            QMessageBox.warning(self, "Błąd", "Wykres o takiej nazwie już istnieje.")
            return

        pw = pg.PlotWidget(title=name, axisItems={'bottom': TimeAxisItem(orientation='bottom')})
        pw.setLabel("bottom", "Czas", "HH:MM:SS")
        pw.showGrid(x=True, y=True)
        pw.setFixedSize(450, 280)

        self.plots.append(pw)
        self.curves.append({})
        self.plot_names.append(name)

        self.update_grid_layout()
        self.plot_name_input.clear()

    def remove_plot(self):
        index = self.plot_selector.currentIndex()
        if index >= 0 and len(self.plots) > 0:
            self.grid_layout.removeWidget(self.plots[index])
            self.plots[index].deleteLater()
            del self.plots[index]
            del self.curves[index]
            del self.plot_names[index]
            self.update_grid_layout()

    def add_variable(self):
        var = self.var_selector.currentText()
        index = self.plot_selector.currentIndex()
        if index == -1 or var in self.curves[index]:
            return

        pen = pg.mkPen(self.variable_colors.get(var, "gray"), width=2)
        curve = self.plots[index].plot(pen=pen)
        self.curves[index][var] = curve

    def remove_variable(self):
        var = self.var_selector.currentText()
        index = self.plot_selector.currentIndex()
        if index == -1:
            return
        if var in self.curves[index]:
            self.plots[index].removeItem(self.curves[index][var])
            del self.curves[index][var]

    def handle_new_data(self, payload, topic):
        current_time = time.time()

        if self.user_role == "admin" and self.selected_topic:
            if topic != self.selected_topic:
                return

        self.time_buffer.append(current_time)

        for var in self.all_variables:
            try:
                value = float(payload.get(var, 0))
            except (ValueError, TypeError):
                value = 0.0
            self.data_buffer[var].append(value)

        for i, curve_dict in enumerate(self.curves):
            for var, curve in curve_dict.items():
                try:
                    curve.setData(list(self.time_buffer), list(self.data_buffer[var]))
                    self.plots[i].setXRange(current_time - 60, current_time)
                    self.plots[i].enableAutoRange(axis='y')
                except Exception as e:
                    print(f"Błąd w rysowaniu {var}: {e}")
    def add_default_plots(self, variable_names):
        for i, var in enumerate(variable_names):
            if len(self.plots) <= i:
                self.plot_name_input.setText(f"Auto {i+1}")
                self.add_plot()
            self.plot_selector.setCurrentIndex(i)
            self.var_selector.setCurrentText(var)
            self.add_variable()

