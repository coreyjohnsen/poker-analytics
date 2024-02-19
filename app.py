import sys
import os
import json
from PyQt6.QtWidgets import QApplication, QGridLayout, QHeaderView, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QFileDialog, QTabWidget, QTableWidget, QSizePolicy, QTableWidgetItem
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6 import QtGui
import pyqtgraph as pg
from reader import get_hand_list, get_text_files, get_player_stats
import ctypes
from utils import format_card_string, get_sorted_hands, format_profit_value, format_date_string

myappid = 'ace_analytics' # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

HAND_TEXT = []
HANDS = []
PLAYER_STATS = {}
USER = ""
DIRPATHS = []

def update_config_data():
    global USER, DIRPATHS
    with open('./config/config.json', 'r') as file:
        config = json.load(file)
        DIRPATHS = config['handHistoryDirs']
        USER = config['user']

def update_hand_details():
    global HAND_TEXT, HANDS, PLAYER_STATS
    HAND_TEXT = get_text_files(DIRPATHS)
    HANDS = get_hand_list(HAND_TEXT, USER)
    PLAYER_STATS = get_player_stats(HANDS)

class Config(QWidget):
    configurationCompleted = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.configPath = './config/config.json'
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('Ace Analytics Configuration')
        self.setMinimumWidth(400)
        # self.setGeometry(100, 100, 400, 400)  # Updated window size

        self.showDirectorySelection()

    def showDirectorySelection(self):
        """UI for directory selection."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Directory selection
        self.userLabel = QLabel('Enter your username:', self)
        layout.addWidget(self.userLabel)

        # Directory path line edit
        self.userLineEdit = QLineEdit(self)
        self.userLineEdit.setPlaceholderText("Enter the same username as your poker software")
        layout.addWidget(self.userLineEdit)
        
        # Directory selection
        self.dirLabel = QLabel('Select hand directory:', self)
        layout.addWidget(self.dirLabel)

        # Directory path line edit
        self.dirLineEdit = QLineEdit(self)
        self.dirLineEdit.setPlaceholderText("Choose the directory containing your poker hands")
        layout.addWidget(self.dirLineEdit)
        
        # Browse button
        self.browseButton = QPushButton('Browse Files', self)
        self.browseButton.clicked.connect(self.browseDirectory)
        layout.addWidget(self.browseButton)
        
        # Submit button
        self.submitButton = QPushButton('Submit', self)
        self.submitButton.clicked.connect(self.saveDetailsAndContinue)
        layout.addWidget(self.submitButton)
    
    def browseDirectory(self):
        dirPath = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dirPath:
            self.dirLineEdit.setText(dirPath)
    
    def saveDetailsAndContinue(self):
        dirPath = self.dirLineEdit.text()
        user = self.userLineEdit.text()
        if os.path.isdir(dirPath) and user != "":
            config = {'handHistoryDirs': [dirPath], "user": user}
            with open(self.configPath, 'w') as file:
                json.dump(config, file)
            self.configurationCompleted.emit()  # Emit signal after saving configuration
            self.close()

class Main(QWidget):
    def __init__(self):
        super().__init__()

    def updateAndShow(self):
        update_config_data()
        update_hand_details()
        self.initUI()
        self.show()

    def initUI(self):
        self.setWindowTitle('Ace Analytics')
        self.setGeometry(100, 100, 1000, 800)  # Updated window size

        # Main layout is horizontal: tabs on the left, content on the right
        mainLayout = QHBoxLayout()
        self.setLayout(mainLayout)
        
        # Tabs for different sections
        tabWidget = QTabWidget()
        tabWidget.addTab(Dashboard(), "Dashboard")
        tabWidget.addTab(BasicStats(), "Basic Statistics")
        tabWidget.addTab(QLabel("Advanced Statistics"), "Advanced Statistics")
        tabWidget.addTab(HandHist(), "Hands")
        tabWidget.addTab(QLabel("Players"), "Players")
        tabWidget.addTab(QLabel("Charts"), "Charts")
        tabWidget.addTab(QLabel("Settings"), "Settings")
        
        # Add the tab widget to the main layout
        mainLayout.addWidget(tabWidget)

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        update_config_data()
        update_hand_details()
        self.init_dashboard()

    def init_dashboard(self):
        layout = QVBoxLayout()
        layout.setSpacing(0)

        layout.addStretch()

        welcomeLabel = QLabel(f"<h1 style=\"font-weight: normal;\">Welcome, <b>{USER}</b></h1>")
        welcomeLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcomeLabel)

        if len(HANDS) == 0:
            warningLabel = QLabel(f"<h2 style=\"color: rgb(200, 0, 0); font-weight: normal;\">Warning: No hand data was found in <b>{DIRPATHS}</b></h2>")
            warningLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(warningLabel)
        else:
            handsPlayedLabel = QLabel(f"<h2 style=\"font-weight: normal;\">You've played <b>{len(HANDS)}</b> hands so far</h2>")
            handsPlayedLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(handsPlayedLabel)

            profit = PLAYER_STATS["cprofit"]

            if profit >= 0:
                profitLabel = QLabel(f"<h2 style=\"font-weight: normal;\">You've made <b>${profit}</b> so far</h2>")
            else:
                profitLabel = QLabel(f"<h2 style=\"font-weight: normal;\">You've lost <b style=\"color: rgb(200, 0, 0);\">-${abs(profit)}</b> so far</h2>")
            profitLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(profitLabel)

            dateLabel = QLabel(f"<h2 style=\"font-weight: normal;\">Playing since <b>{str(PLAYER_STATS['earliest_hand']).split(' ')[0]}</b></h2>")
            dateLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(dateLabel)

            if HANDS:
                graphLayout = QHBoxLayout()
                graphWidget = pg.PlotWidget()
                graphWidget.setBackground("w")

                graphWidget.setMinimumWidth(600)
                graphWidget.setMaximumWidth(800)

                graphLayout.addStretch()
                graphLayout.addWidget(graphWidget)
                graphLayout.addStretch()

                x = list(range(1, len(HANDS) + 1))
                y = [0]
                for i, hand in enumerate(HANDS, start=1):
                    y.append(y[-1] + hand.profit)

                styles = {"color": "black", "font-size": "18px"}
                graphWidget.setLabel("left", "Cumulative Profit ($)", **styles)
                graphWidget.setLabel("bottom", "Hands", **styles)
                graphWidget.plot(x, y[1:], pen='r', name="Cumulative Profit")
                ref_pen = pg.mkPen(color=(0, 0, 0), width=1, style=Qt.PenStyle.DotLine)
                graphWidget.plot(x, [0 for i in range(len(y[1:]))], pen=ref_pen)

                layout.addLayout(graphLayout)

        self.setLayout(layout)
        layout.addStretch()
        self.setLayout(layout)

class BasicStats(QWidget):
    def __init__(self):
        super().__init__()
        update_config_data()
        update_hand_details()
        self.init_dashboard()

    def init_dashboard(self):
        grid_layout = QGridLayout()
        grid_layout.setSpacing(0)
        
        grid_layout.setColumnStretch(0, 1)  # First column stretch factor set to 2
        grid_layout.setColumnStretch(1, 5)

        # Helper function to create a title label
        def create_title_label(text):
            label = QLabel(f'<h3><b>{text}</b></h3>')
            label.setObjectName("title")
            label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            return label

        # Helper function to create a value label
        def create_value_label(text):
            label = QLabel(f'<h3 style="font-weight: normal;">{text}</h3>')
            label.setObjectName("value")
            label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            return label

        # Add widgets to the grid layout
        labels = [
            ("VPIP:", f'{PLAYER_STATS["vpip"] * 100}%'),
            ("PFR:", f'{PLAYER_STATS["pfr"] * 100}%'),
            ("AF:", PLAYER_STATS['af']),
            ("BB/100:", PLAYER_STATS['bb/100']),
            ("$/100 Hands:", format_profit_value(self.calculate_dollar_per_100_hands())),
            ("Cumulative Profit:", f"${PLAYER_STATS['cprofit']}" if PLAYER_STATS['cprofit'] >= 0 else f"-${abs(PLAYER_STATS['cprofit'])}"),
            ("Best Hand:", PLAYER_STATS['best_hand']),
        ]

        for i, (title, value) in enumerate(labels):
            grid_layout.addWidget(create_title_label(title), i, 0)
            grid_layout.addWidget(create_value_label(str(value)), i, 1)

        # This line will push all the content to the top and left.
        grid_layout.setRowStretch(len(labels), 1)

        # Set the layout to the grid layout
        self.setLayout(grid_layout)

    def calculate_dollar_per_100_hands(self):
        if len(HANDS) > 0:
            return round(PLAYER_STATS['cprofit'] / len(HANDS) * 100, 2)
        return 0.0

class HandHist(QWidget):
    def __init__(self):
        super().__init__()
        update_config_data()
        update_hand_details()
        self.init()

    def init(self):
        layout = QVBoxLayout()
        table = QTableWidget()

        table.setRowCount(len(HANDS))
        table.setColumnCount(6) # Date, hole cards, community cards, win, profit, position
        table.setHorizontalHeaderLabels(["Date", "Hole Cards", "Community Cards", "Win?", "Profit", "Position"])

        for i, hand in enumerate(get_sorted_hands(HANDS)):
            date = QTableWidgetItem(format_date_string(str(hand.date)))
            hole = self.get_card_label(format_card_string(hand.hand))
            community = self.get_card_label(format_card_string(hand.community))
            win = QTableWidgetItem("Yes" if hand.won else "No")
            profit_str = format_profit_value(hand.profit)
            profit_str = f'<p style="color: red">{profit_str}</p>' if hand.profit < 0 else f'<p style="color: green">{profit_str}</p>' if hand.profit > 0 else profit_str
            profit = QLabel(profit_str)
            position = QTableWidgetItem(hand.position)

            table.setItem(i, 0, date)
            table.setCellWidget(i, 1, hole)
            table.setCellWidget(i, 2, community)
            table.setItem(i, 3, win)
            table.setCellWidget(i, 4, profit)
            table.setItem(i, 5, position)

        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setSortingEnabled(True)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)

        layout.addWidget(table)
        self.setLayout(layout)

    def get_card_label(self, card_str):
        card_str = card_str.replace("♦", "<span style=\"color: red\">♦</span>")
        card_str = card_str.replace("♥", "<span style=\"color: red\">♥</span>")
        return QLabel(f'<p>{card_str}</p>')

def isConfigValid():
    try:
        with open('./config/config.json', 'r') as file:
            config = json.load(file)
            dirs = config.get('handHistoryDirs', '')
            user = config.get('user', '')
            for dir in dirs:
                if not os.path.isdir(dir): return False
            return user != ''
    except FileNotFoundError:
        return False
    except json.JSONDecodeError:
        return False

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon('resources/logo.png'))
    main = Main()
    if not isConfigValid():
        configWindow = Config()
        configWindow.configurationCompleted.connect(main.updateAndShow)
        configWindow.show()
    else:
        main_window = Main()
        main_window.updateAndShow()
    
    sys.exit(app.exec())