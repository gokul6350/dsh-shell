from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTextEdit
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import sys
import ctypes
import os

# Load the C library
terminal_lib = ctypes.CDLL('./terminal_backend.dll')

class TerminalHandle(ctypes.Structure):
    _fields_ = [
        ("hPC", ctypes.c_void_p),
        ("hPipeIn", ctypes.c_void_p),
        ("hPipeOut", ctypes.c_void_p)
    ]

# Set function signatures
terminal_lib.create_terminal.restype = ctypes.POINTER(TerminalHandle)
terminal_lib.write_terminal.argtypes = [ctypes.POINTER(TerminalHandle), ctypes.c_char_p, ctypes.c_int]
terminal_lib.read_terminal.argtypes = [ctypes.POINTER(TerminalHandle), ctypes.c_char_p, ctypes.c_int]

class TerminalReader(QThread):
    dataReceived = pyqtSignal(str)

    def __init__(self, terminal_handle):
        super().__init__()
        self.terminal_handle = terminal_handle
        self.running = True

    def run(self):
        buffer = ctypes.create_string_buffer(1024)
        while self.running:
            bytes_read = terminal_lib.read_terminal(self.terminal_handle, buffer, 1024)
            if bytes_read > 0:
                text = buffer.value[:bytes_read].decode('utf-8', errors='replace')
                self.dataReceived.emit(text)

class TerminalWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        # Create terminal display
        self.terminal_display = QTextEdit()
        self.terminal_display.setReadOnly(True)
        self.terminal_display.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #FFFFFF;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
            }
        """)
        layout.addWidget(self.terminal_display)

        # Initialize terminal
        self.terminal_handle = terminal_lib.create_terminal()
        
        # Start reader thread
        self.reader = TerminalReader(self.terminal_handle)
        self.reader.dataReceived.connect(self._append_text)
        self.reader.start()

    def _append_text(self, text):
        self.terminal_display.insertPlainText(text)
        self.terminal_display.moveCursor(self.terminal_display.textCursor().End)

    def write(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        terminal_lib.write_terminal(self.terminal_handle, data, len(data))

    def closeEvent(self, event):
        self.reader.running = False
        self.reader.wait()
        terminal_lib.close_terminal(self.terminal_handle)
        super().closeEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Windows Terminal Emulator")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.terminal = TerminalWidget()
        layout.addWidget(self.terminal)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
