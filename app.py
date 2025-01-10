import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QSplashScreen, QVBoxLayout, QSplitter
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt, QProcess, pyqtSlot, QObject, pyqtSignal
from PyQt5.QtWebChannel import QWebChannel
import os
from PyQt5.QtGui import QIcon, QPixmap
import cmd_agent
import json
import debugpy
from terminal_widget import TerminalWidget



class TerminalBridge(QObject):
    response_ready = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.page = None
        self.terminal = None  # Will store reference to terminal widget
    
    @pyqtSlot(str, str)
    def log_chat_message(self, message, sender):
        # Simple logging, can be removed if not needed
        pass
    
    @pyqtSlot(str)
    def send_command(self, command):
        """Simulate typing and execute command in terminal"""
        if self.terminal and self.terminal.process.state() == QProcess.Running:
            # Write the command to terminal
            self.terminal.process.write(command.encode())
            # Simulate Enter key press
            self.terminal.process.write(b'\r\n')
            
            # Add to terminal's command history
            self.terminal.command_history.append(command)
            self.terminal.history_index = len(self.terminal.command_history)

    def ask_commandline(self, message):
        response = cmd_agent.ask_agent_cmd(message)
        return response

    @pyqtSlot(str)
    def process_chat_message(self, message):
        try:
            response = cmd_agent.ask_agent_cmd(message)
            response = response.replace('\\', '\\\\')
            response_dict = json.loads(response)
            
            print(f"Parsed response: {response_dict}")
            
            self.response_ready.emit(
                response_dict.get("run", ""), 
                response_dict.get("speak", "No response")
            )
        except json.JSONDecodeError as je:
            print(f"JSON parsing error: {je}")
            print(f"Raw response: {response}")
            self.response_ready.emit("", "Sorry, I had trouble understanding the response")
        except Exception as e:
            print(f"Error processing message: {e}")
            self.response_ready.emit("", f"Sorry, I encountered an error: {str(e)}")

    @pyqtSlot()
    def reset_terminal(self):
        """Reset the terminal"""
        if self.terminal:
            self.terminal.clear()  # Clear terminal content
            self.terminal.start_process()  # Restart the process



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Deep Shell 🐚")
        self.showMaximized()
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logo.png')
        self.setWindowIcon(QIcon(icon_path))
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create splitter for web view and terminal
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background: #2c2e33;
                width: 2px;
                margin-top: 0px;
                margin-bottom: 0px;
            }
            QSplitter::handle:hover {
                background: #3c3e43;
            }
            QSplitter::handle:pressed {
                background: #4c4e53;
            }
        """)
        
        # Make the splitter handle more visible
        self.splitter.setHandleWidth(2)
        
        # Create web view widget
        self.web_view = QWebEngineView()
        
        # Set up web channel for JavaScript communication
        self.channel = QWebChannel()
        self.terminal_bridge = TerminalBridge()
        self.channel.registerObject('terminal', self.terminal_bridge)
        self.web_view.page().setWebChannel(self.channel)
        
        # Store page reference for terminal bridge
        self.terminal_bridge.page = self.web_view.page()
        
        # Load the HTML file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        index_path = os.path.join(current_dir, 'index.html')
        self.web_view.setUrl(QUrl.fromLocalFile(index_path))
        
        # Create terminal widget
        self.terminal = TerminalWidget()
        
        # Connect terminal to bridge
        self.terminal_bridge.terminal = self.terminal
        
        # Add widgets to splitter
        self.splitter.addWidget(self.web_view)
        self.splitter.addWidget(self.terminal)
        
        # Set initial sizes (adjust the ratio as needed)
        self.splitter.setSizes([int(self.width() * 0.6), int(self.width() * 0.4)])
        
        # Add splitter to layout
        layout.addWidget(self.splitter)

def main():
    # Enable debugging on port 5678
    try:
        debugpy.listen(5678)
        print("Debugger is listening on port 5678")
    except Exception as e:
        print(f"Debugger failed to start: {e}")
        
    app = QApplication(sys.argv)
    
    # Show splash screen
    splash_pix = QPixmap('logo.png')
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.show()
    app.processEvents()
    
    # Initialize main window
    window = MainWindow()
    
    # Show main window and close splash
    window.show()
    splash.finish(window)
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 