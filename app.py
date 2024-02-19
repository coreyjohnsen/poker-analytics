import sys
import os
import json
from PyQt6.QtWidgets import QApplication, QGridLayout, QHeaderView, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QFileDialog, QTabWidget, QTableWidget, QSizePolicy, QTableWidgetItem
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QObject, QTimer, QThread
from PyQt6 import QtGui
import pyqtgraph as pg
from reader import get_hand_list, get_text_files, get_player_stats
import ctypes
from utils import format_card_string, get_sorted_hands, format_profit_value, format_date_string

myappid = 'ace_analytics' # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

HAND_TEXT = []
HANDS = []
PLAYER_STATS = {
        "vpip": 0.,
        "best_hand": "",
        "bb/100": 0.,
        "af": 100.,
        "cprofit": 0.,
        "earliest_hand": "",
        "pfr": 0.
    }
USER = ""
DIRPATHS = []
DATA_UPDATE_RATE = 5000 # how many ms between data updates

def update_config_data():
    global USER, DIRPATHS
    with open('./config/config.json', 'r') as file:
        config = json.load(file)
        DIRPATHS = config['handHistoryDirs']
        USER = config['user']

class Worker(QObject):
    finished = pyqtSignal()

    def run(self):
        """Long-running task."""
        global HAND_TEXT, HANDS, PLAYER_STATS
        update_config_data()
        HAND_TEXT = get_text_files(DIRPATHS)
        HANDS = get_hand_list(HAND_TEXT, USER)
        PLAYER_STATS = get_player_stats(HANDS)
        self.finished.emit()

class Config(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.configPath = './config/config.json'
        self.parent = parent
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
            self.close()
            self.parent.onTimerTimeout()

class Main(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setupWorkerAndThread()
        self.setupTimer()

        # Manually trigger the first data update
        self.onTimerTimeout()

    def setupWorkerAndThread(self):
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.updateTabs)

    def setupTimer(self):
        self.timer = QTimer(self)
        self.timer.setInterval(DATA_UPDATE_RATE)
        self.timer.timeout.connect(self.onTimerTimeout)
        self.timer.start()

    def onTimerTimeout(self):
        if not self.thread.isRunning():
            self.thread.start()

    def initUI(self):
        self.setWindowTitle('Ace Analytics')
        self.setGeometry(100, 100, 1000, 800)

        mainLayout = QHBoxLayout(self)
        
        self.dashboard = Dashboard()
        self.basic = BasicStats()
        self.hands = HandHist()

        tabWidget = QTabWidget()
        sections = [
            (self.dashboard, "Dashboard"),
            (self.basic, "Basic Statistics"),
            (QLabel("Advanced Statistics"), "Advanced Statistics"),
            (self.hands, "Hands"),
            (QLabel("Players"), "Players"),
            (QLabel("Charts"), "Charts"),
            (QLabel("Settings"), "Settings"),
        ]
        
        for section, title in sections:
            tabWidget.addTab(section, title)
        
        mainLayout.addWidget(tabWidget)

    def updateTabs(self):
        self.dashboard.updateData()
        self.basic.updateData()
        self.hands.updateData()

    def customShow(self):
        self.show()
        if not isConfigValid():
            self.c = Config(self)
            self.c.show()
             
class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.init_dashboard()

    def init_dashboard(self):
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.addStretch()

        self.user = USER
        welcomeStr = f"<h1 style=\"font-weight: normal;\">Welcome, <b>{self.user}</b></h1>" if self.user else "<h1 style=\"font-weight: normal;\">Welcome!</h1>"
        self.welcomeLabel = QLabel(welcomeStr)
        self.welcomeLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.welcomeLabel)

        if not HANDS:
            self.warningLabel = QLabel(f"<h2 style=\"color: rgb(200, 0, 0); font-weight: normal;\">Warning: No hand data was found in <b>{DIRPATHS}</b></h2>")
            self.warningLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.warningLabel)

        self.numHands = len(HANDS)
        self.handsPlayedLabel = QLabel(f"<h2 style=\"font-weight: normal;\">You've played <b>{len(HANDS)}</b> hands so far</h2>")
        self.handsPlayedLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.handsPlayedLabel)

        profit = PLAYER_STATS["cprofit"]

        if profit >= 0:
            self.profitLabel = QLabel(f"<h2 style=\"font-weight: normal;\">You've made <b>${profit}</b> so far</h2>")
        else:
            self.profitLabel = QLabel(f"<h2 style=\"font-weight: normal;\">You've lost <b style=\"color: rgb(200, 0, 0);\">-${abs(profit)}</b> so far</h2>")
        self.profitLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.profitLabel)

        self.dateLabel = QLabel(f"<h2 style=\"font-weight: normal;\">Playing since <b>{str(PLAYER_STATS['earliest_hand']).split(' ')[0]}</b></h2>")
        self.dateLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.dateLabel)

        graphLayout = QHBoxLayout()
        self.graphWidget = pg.PlotWidget()
        self.graphWidget.setBackground("w")

        self.graphWidget.setMinimumWidth(600)
        self.graphWidget.setMaximumWidth(800)

        graphLayout.addStretch()
        graphLayout.addWidget(self.graphWidget)
        graphLayout.addStretch()

        x = list(range(1, len(HANDS) + 1))
        y = [0]
        for i, hand in enumerate(HANDS, start=1):
            y.append(y[-1] + hand.profit)

        self.graphStyles = {"color": "black", "font-size": "18px"}
        self.graphWidget.setLabel("left", "Cumulative Profit ($)", **self.graphStyles)
        self.graphWidget.setLabel("bottom", "Hands", **self.graphStyles)
        self.graphWidget.plot(x, y[1:], pen='r', name="Cumulative Profit")
        self.ref_pen = pg.mkPen(color=(0, 0, 0), width=1, style=Qt.PenStyle.DotLine)
        self.graphWidget.plot(x, [0 for i in range(len(y[1:]))], pen=self.ref_pen)

        layout.addLayout(graphLayout)

        layout.addStretch()
        self.setLayout(layout)

    def updateData(self):
        if USER != self.user:
            self.user = USER
            welcomeStr = f"<h1 style=\"font-weight: normal;\">Welcome, <b>{self.user}</b></h1>" if self.user else "<h1 style=\"font-weight: normal;\">Welcome!</h1>"
            self.welcomeLabel.setText(welcomeStr)

        if len(HANDS) != self.numHands:
            prevHands = self.numHands
            self.numHands = len(HANDS)
            if prevHands == 0:
                self.warningLabel.deleteLater()
                self.warningLabel = None
                self.handsPlayedLabel.setText(f"<h2 style=\"font-weight: normal;\">You've played <b>{len(HANDS)}</b> hands so far</h2>")
            
            self.handsPlayedLabel.setText(f"<h2 style=\"font-weight: normal;\">You've played <b>{len(HANDS)}</b> hands so far</h2>")
            profit = PLAYER_STATS["cprofit"]
            if profit >= 0: self.profitLabel.setText(f"<h2 style=\"font-weight: normal;\">You've made <b>${profit}</b> so far</h2>")
            else: self.profitLabel.setText(f"<h2 style=\"font-weight: normal;\">You've lost <b style=\"color: rgb(200, 0, 0);\">-${abs(profit)}</b> so far</h2>")
            self.graphWidget.clear()
            x = list(range(1, len(HANDS) + 1))
            y = [0]
            for i, hand in enumerate(HANDS, start=1):
                y.append(y[-1] + hand.profit)
            self.graphWidget.setLabel("left", "Cumulative Profit ($)", **self.graphStyles)
            self.graphWidget.setLabel("bottom", "Hands", **self.graphStyles)
            self.graphWidget.plot(x, y[1:], pen='r', name="Cumulative Profit")
            self.graphWidget.plot(x, [0 for i in range(len(y[1:]))], pen=self.ref_pen)

class BasicStats(QWidget):
    def __init__(self):
        super().__init__()
        self.value_labels = {}
        self.init_dashboard()

    def init_dashboard(self):
        grid_layout = QGridLayout()
        grid_layout.setSpacing(0)
        
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 5)

        def create_title_label(text):
            label = QLabel(f'<h3><b>{text}</b></h3>')
            label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            return label

        def create_value_label(name, text):
            label = QLabel(f'<h3 style="font-weight: normal;">{text}</h3>')
            label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            self.value_labels[name] = label
            return label

        labels = [
            ("VPIP", "vpip"),
            ("PFR", "pfr"),
            ("AF", "af"),
            ("BB/100", "bb/100"),
            ("$/100 Hands", "dollar_per_100_hands"),
            ("Cumulative Profit", "cprofit"),
            ("Best Hand", "best_hand"),
        ]

        for i, (title, name) in enumerate(labels):
            grid_layout.addWidget(create_title_label(title), i, 0)
            grid_layout.addWidget(create_value_label(name, ""), i, 1)

        grid_layout.setRowStretch(len(labels), 1)
        self.setLayout(grid_layout)
        self.updateData()

    def calculate_dollar_per_100_hands(self):
        if len(HANDS) > 0:
            return round(PLAYER_STATS['cprofit'] / len(HANDS) * 100, 2)
        return 0.0

    def updateData(self):
        self.value_labels['vpip'].setText(f'{PLAYER_STATS["vpip"] * 100}%')
        self.value_labels['pfr'].setText(f'{PLAYER_STATS["pfr"] * 100}%')
        self.value_labels['af'].setText(str(PLAYER_STATS['af']))
        self.value_labels['bb/100'].setText(str(PLAYER_STATS['bb/100']))
        self.value_labels['dollar_per_100_hands'].setText(f"${self.calculate_dollar_per_100_hands()}")
        self.value_labels['cprofit'].setText(f"${PLAYER_STATS['cprofit']}" if PLAYER_STATS['cprofit'] >= 0 else f"-${abs(PLAYER_STATS['cprofit'])}")
        self.value_labels['best_hand'].setText(PLAYER_STATS['best_hand'])

class HandHist(QWidget):
    def __init__(self):
        super().__init__()
        self.init()

    def init(self):
        layout = QVBoxLayout()
        self.table = QTableWidget()

        self.table.setRowCount(len(HANDS))
        self.table.setColumnCount(6) # Date, hole cards, community cards, win, profit, position
        self.table.setHorizontalHeaderLabels(["Date", "Hole Cards", "Community Cards", "Win?", "Profit", "Position"])

        self.numHands = len(HANDS)

        for i, hand in enumerate(get_sorted_hands(HANDS)):
            date = QTableWidgetItem(format_date_string(str(hand.date)))
            hole = self.get_card_label(format_card_string(hand.hand))
            community = self.get_card_label(format_card_string(hand.community))
            win = QTableWidgetItem("Yes" if hand.won else "No")
            profit_str = format_profit_value(hand.profit)
            profit_str = f'<p style="color: red">{profit_str}</p>' if hand.profit < 0 else f'<p style="color: green">{profit_str}</p>' if hand.profit > 0 else profit_str
            profit = QLabel(profit_str)
            position = QTableWidgetItem(hand.position)

            self.table.setItem(i, 0, date)
            self.table.setCellWidget(i, 1, hole)
            self.table.setCellWidget(i, 2, community)
            self.table.setItem(i, 3, win)
            self.table.setCellWidget(i, 4, profit)
            self.table.setItem(i, 5, position)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)

        layout.addWidget(self.table)
        self.setLayout(layout)

    def get_card_label(self, card_str):
        card_str = card_str.replace("♦", "<span style=\"color: red\">♦</span>")
        card_str = card_str.replace("♥", "<span style=\"color: red\">♥</span>")
        return QLabel(f'<p>{card_str}</p>')
    
    def updateData(self):
        if self.numHands != len(HANDS):
            self.numHands = len(HANDS)
            self.table.clear()
            self.table.setRowCount(len(HANDS))
            for i, hand in enumerate(get_sorted_hands(HANDS)):
                date = QTableWidgetItem(format_date_string(str(hand.date)))
                hole = self.get_card_label(format_card_string(hand.hand))
                community = self.get_card_label(format_card_string(hand.community))
                win = QTableWidgetItem("Yes" if hand.won else "No")
                profit_str = format_profit_value(hand.profit)
                profit_str = f'<p style="color: red">{profit_str}</p>' if hand.profit < 0 else f'<p style="color: green">{profit_str}</p>' if hand.profit > 0 else profit_str
                profit = QLabel(profit_str)
                position = QTableWidgetItem(hand.position)

                self.table.setItem(i, 0, date)
                self.table.setCellWidget(i, 1, hole)
                self.table.setCellWidget(i, 2, community)
                self.table.setItem(i, 3, win)
                self.table.setCellWidget(i, 4, profit)
                self.table.setItem(i, 5, position)

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
    main.customShow()
    sys.exit(app.exec())