import json
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit
from PyQt5.QtCore import Qt

class ResultAgent:
    def __init__(self):
        self.last_command = None
        self.last_result = None

    async def process_command_result(self, command, result):
        """Process the command output and provide analysis"""
        self.last_command = command
        self.last_result = result
        
        # TODO: Implement result analysis using LLM
        analysis = {
            'success': True,
            'summary': f'Command {command} executed successfully',
            'details': result,
            'suggestions': []
        }
        return analysis

class ConfirmationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Command Confirmation')
        layout = QVBoxLayout()

        # Command preview
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        layout.addWidget(QLabel('Proposed Command:'))
        layout.addWidget(self.preview)

        # Explanation
        self.explanation = QTextEdit()
        self.explanation.setReadOnly(True)
        layout.addWidget(QLabel('Explanation:'))
        layout.addWidget(self.explanation)

        # Buttons
        btn_layout = QVBoxLayout()
        self.confirm_btn = QPushButton('Confirm')
        self.confirm_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton('Cancel')
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.confirm_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def set_command(self, command, explanation):
        self.preview.setText(command)
        self.explanation.setText(explanation)

def show_confirmation_dialog(parent, command, explanation):
    dialog = ConfirmationDialog(parent)
    dialog.set_command(command, explanation)
    result = dialog.exec_()
    return result == QDialog.Accepted