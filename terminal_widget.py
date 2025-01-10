from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtCore import Qt, QProcess, pyqtSignal, QProcessEnvironment
from PyQt5.QtGui import QFont, QTextCursor, QKeyEvent, QPalette, QColor
import sys
import os

class TerminalWidget(QPlainTextEdit):
    commandExecuted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_appearance()
        
        # Initialize terminal process
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.handle_finished)
        
        self.command_buffer = ""
        self.command_history = []
        self.history_index = 0
        
        # Start the shell
        self.start_process()

    def setup_appearance(self):
        # Set font
        self.setFont(QFont('Courier New', 10))
        
        # Create and configure palette with the theme colors
        palette = self.palette()
        
        # Background (Dark theme matching the web terminal)
        palette.setColor(QPalette.Base, QColor("#1a1b1e"))
        
        # Text color (White)
        palette.setColor(QPalette.Text, QColor("#FFFFFF"))
        
        # Selection color
        palette.setColor(QPalette.Highlight, QColor("#2c2e33"))
        palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
        
        # Apply the palette
        self.setPalette(palette)
        
        # Set margins and padding to match web terminal
        document = self.document()
        document.setDocumentMargin(10)
        
        # Other appearance settings
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        
        # Style the scrollbar to match web terminal
        self.setStyleSheet("""
            QPlainTextEdit {
                border: none;
                padding: 20px;
                background-color: #1a1b1e;
            }
            QScrollBar:vertical {
                width: 6px;
                background: #1a1b1e;
            }
            QScrollBar::handle:vertical {
                background: #2c2e33;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #3c3e43;
            }
            QScrollBar:horizontal {
                height: 6px;
                background: #1a1b1e;
            }
            QScrollBar::handle:horizontal {
                background: #2c2e33;
                border-radius: 3px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #3c3e43;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                height: 0px;
                width: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
            QScrollBar::corner {
                background: #1a1b1e;
            }
        """)

    def start_process(self):
        if sys.platform == 'win32':
            program = 'powershell.exe'
            args = ['-NoLogo']  # Prevent PowerShell from showing its logo
            
            # Create proper QProcessEnvironment
            env = QProcessEnvironment.systemEnvironment()
            env.insert("PYTHONIOENCODING", "utf-8")
            self.process.setProcessEnvironment(env)
        else:
            program = os.environ.get('SHELL', '/bin/bash')
            args = []

        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.setWorkingDirectory(os.getcwd())
        self.process.start(program, args)

    def handle_stdout(self):
        data = self.process.readAllStandardOutput()
        text = bytes(data).decode('utf-8', errors='replace')
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def handle_stderr(self):
        data = self.process.readAllStandardError()
        text = bytes(data).decode('utf-8', errors='replace')
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.handle_return()
        elif event.key() == Qt.Key_Up:
            self.handle_up()
        elif event.key() == Qt.Key_Down:
            self.handle_down()
        elif event.key() == Qt.Key_C and event.modifiers() & Qt.ControlModifier:
            self.handle_ctrl_c()
        elif event.key() == Qt.Key_V and event.modifiers() & Qt.ControlModifier:
            self.paste()
        else:
            if self.process.state() == QProcess.Running:
                if event.text():
                    self.process.write(event.text().encode())
                    return  # Don't call the parent class handler
        super().keyPressEvent(event)

    def handle_return(self):
        if self.process.state() == QProcess.Running:
            self.process.write(b'\r\n')
            command = self.textCursor().block().text().strip()
            if command:
                self.command_history.append(command)
                self.history_index = len(self.command_history)

    def handle_ctrl_c(self):
        if self.process.state() == QProcess.Running:
            self.process.write(b'\x03')

    def handle_up(self):
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            self.process.write(self.command_history[self.history_index].encode() + b'\r')

    def handle_down(self):
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.process.write(self.command_history[self.history_index].encode() + b'\r')

    def handle_finished(self):
        self.insertPlainText("\nProcess finished. Restarting...\n")
        self.start_process() 