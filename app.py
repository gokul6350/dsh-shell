import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, 
                            QHBoxLayout, QPlainTextEdit, QVBoxLayout, QLineEdit)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt, QProcess
import os
import winpty

class TerminalWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # Create terminal output display
        self.terminal_output = QPlainTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setStyleSheet("""
            QPlainTextEdit {
                background-color: #282a36;
                color: #f8f8f2;
                font-family: Consolas, monospace;
                font-size: 14px;
                border: none;
            }
        """)
        
        # Create terminal input line
        self.terminal_input = QLineEdit()
        self.terminal_input.setStyleSheet("""
            QLineEdit {
                background-color: #282a36;
                color: #f8f8f2;
                font-family: Consolas, monospace;
                font-size: 14px;
                border: none;
                padding: 5px;
            }
        """)
        self.terminal_input.returnPressed.connect(self.send_command)
        
        self.layout.addWidget(self.terminal_output)
        self.layout.addWidget(self.terminal_input)
        
        # Initialize terminal process
        self.process = QProcess()
        self.process.setProgram("cmd.exe")
        self.process.readyReadStandardOutput.connect(self.handle_output)
        self.process.readyReadStandardError.connect(self.handle_error)
        self.process.start()
        
    def handle_output(self):
        data = self.process.readAllStandardOutput().data().decode()
        self.terminal_output.appendPlainText(data.strip())
        self.terminal_output.verticalScrollBar().setValue(
            self.terminal_output.verticalScrollBar().maximum()
        )
        
    def handle_error(self):
        data = self.process.readAllStandardError().data().decode()
        self.terminal_output.appendPlainText(data.strip())
        self.terminal_output.verticalScrollBar().setValue(
            self.terminal_output.verticalScrollBar().maximum()
        )
    
    def send_command(self):
        command = self.terminal_input.text() + '\n'
        self.process.write(command.encode())
        self.terminal_input.clear()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Terminal Chat App")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Create web view widget for chat
        self.web_view = QWebEngineView()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        index_path = os.path.join(current_dir, 'index.html')
        self.web_view.setUrl(QUrl.fromLocalFile(index_path))
        
        # Create terminal widget
        self.terminal = TerminalWidget()
        
        # Set size policies
        self.web_view.setMinimumWidth(400)
        self.terminal.setMinimumWidth(600)
        
        # Add widgets to layout
        layout.addWidget(self.web_view, 1)
        layout.addWidget(self.terminal, 2)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 