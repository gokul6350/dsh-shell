import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.process = QProcess(self)
        
        # Create a text edit widget to show output
        self.terminal = QTextEdit(self)
        self.terminal.setReadOnly(True)
        self.terminal.setFont(QFont('Consolas', 10))  # Use a monospace font
        
        # Create an input line
        self.input_line = QLineEdit(self)
        self.input_line.returnPressed.connect(self.send_command)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.terminal)
        layout.addWidget(self.input_line)
        
        # Setup process
        self.process.setProgram('cmd.exe')
        self.process.start()
        
        # Connect signals
        self.process.readyReadStandardOutput.connect(self.handle_output)
        self.process.readyReadStandardError.connect(self.handle_error)

    def send_command(self):
        command = self.input_line.text() + '\n'
        self.process.write(command.encode())
        self.input_line.clear()

    def handle_output(self):
        output = self.process.readAllStandardOutput().data().decode()
        self.terminal.append(output)

    def handle_error(self):
        error = self.process.readAllStandardError().data().decode()
        self.terminal.append(error)

    def closeEvent(self, event):
        self.process.terminate()
        self.process.waitForFinished(1000)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.setGeometry(100, 100, 800, 600)
    window.show()
    sys.exit(app.exec_())