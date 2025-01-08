from PyQt5.QtWidgets import QApplication
from a2 import Terminal
import sys

def main():
    app = QApplication(sys.argv)
    
    # Create the terminal widget
    # The first parameter is the parent widget (None in this case)
    # The second parameter determines if the window is movable
    terminal = Terminal(parent=None, movable=True)
    
    # Add the terminal components
    terminal.add()
    
    # Show the terminal
    terminal.show()
    
    # Center the terminal on screen (optional)
    terminal.center()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 