from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QSlider, QComboBox, QCheckBox,
                             QGroupBox, QSpinBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import config
from llm_manager import LLMManager

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        self.setWindowTitle('Settings')
        self.setMinimumWidth(400)
        layout = QVBoxLayout()

        # Window Effects
        effects_group = QGroupBox('Window Effects')
        effects_layout = QVBoxLayout()

        # Transparency
        transparency_layout = QHBoxLayout()
        self.transparency_slider = QSlider(Qt.Horizontal)
        self.transparency_slider.setRange(50, 100)
        self.transparency_slider.setValue(95)
        transparency_layout.addWidget(QLabel('Window Transparency:'))
        transparency_layout.addWidget(self.transparency_slider)
        effects_layout.addLayout(transparency_layout)

        # Blur Effect
        self.blur_checkbox = QCheckBox('Enable Window Blur')
        effects_layout.addWidget(self.blur_checkbox)
        effects_group.setLayout(effects_layout)
        layout.addWidget(effects_group)

        # LLM Settings
        llm_group = QGroupBox('LLM Settings')
        llm_layout = QVBoxLayout()

        # Initialize LLM Manager to get available models
        self.llm_manager = LLMManager()

        # Provider Selection
        provider_layout = QHBoxLayout()
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(self.llm_manager.get_available_providers())
        self.provider_combo.currentTextChanged.connect(self.update_model_list)
        provider_layout.addWidget(QLabel('LLM Provider:'))
        provider_layout.addWidget(self.provider_combo)
        llm_layout.addLayout(provider_layout)
        
        # Model Selection
        model_layout = QHBoxLayout()
        self.model_combo = QComboBox()
        model_layout.addWidget(QLabel('Model:'))
        model_layout.addWidget(self.model_combo)
        llm_layout.addLayout(model_layout)

        # Context Length
        context_layout = QHBoxLayout()
        self.context_length_spin = QSpinBox()
        self.context_length_spin.setRange(1000, 32000)
        self.context_length_spin.setSingleStep(1000)
        self.context_length_spin.setValue(4000)
        context_layout.addWidget(QLabel('Context Length:'))
        context_layout.addWidget(self.context_length_spin)
        llm_layout.addLayout(context_layout)

        # Token Length
        token_layout = QHBoxLayout()
        self.token_length_spin = QSpinBox()
        self.token_length_spin.setRange(100, 4000)
        self.token_length_spin.setSingleStep(100)
        self.token_length_spin.setValue(1000)
        token_layout.addWidget(QLabel('Max Token Length:'))
        token_layout.addWidget(self.token_length_spin)
        llm_layout.addLayout(token_layout)

        # Model Settings
        self.temperature_spin = QSpinBox()
        self.temperature_spin.setRange(0, 100)
        self.temperature_spin.setValue(70)
        self.temperature_spin.setSingleStep(10)
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel('Temperature:'))
        temp_layout.addWidget(self.temperature_spin)
        llm_layout.addLayout(temp_layout)

        # Image Support for Ollama
        self.image_support_checkbox = QCheckBox('Enable Image Support (Ollama Vision Models)')
        self.image_support_checkbox.setEnabled(False)
        self.provider_combo.currentTextChanged.connect(self.update_image_support)
        llm_layout.addWidget(self.image_support_checkbox)

        llm_group.setLayout(llm_layout)
        layout.addWidget(llm_group)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton('Save')
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_settings(self):
        # Load current settings
        self.provider_combo.setCurrentText(config.DEFAULT_LLM_PROVIDER)
        self.update_model_list(config.DEFAULT_LLM_PROVIDER)
        current_model = config.MODEL_SETTINGS[config.DEFAULT_LLM_PROVIDER]['model_name']
        index = self.model_combo.findText(current_model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
        self.temperature_spin.setValue(int(config.MODEL_SETTINGS[config.DEFAULT_LLM_PROVIDER]['temperature'] * 100))
        
        # Load context and token length settings
        self.context_length_spin.setValue(config.MODEL_SETTINGS[config.DEFAULT_LLM_PROVIDER].get('context_length', 4000))
        self.token_length_spin.setValue(config.MODEL_SETTINGS[config.DEFAULT_LLM_PROVIDER].get('max_tokens', 1000))
        
        # Load image support setting
        self.update_image_support(config.DEFAULT_LLM_PROVIDER)
        self.image_support_checkbox.setChecked(config.MODEL_SETTINGS[config.DEFAULT_LLM_PROVIDER].get('image_support', False))
        
    def update_model_list(self, provider):
        """Update the model list when provider changes"""
        self.model_combo.clear()
        models = self.llm_manager.get_available_models(provider)
        if models:
            self.model_combo.addItems(models)

    def update_image_support(self, provider):
        """Enable/disable image support checkbox based on provider"""
        self.image_support_checkbox.setEnabled(provider.lower() == 'ollama')
        if provider.lower() != 'ollama':
            self.image_support_checkbox.setChecked(False)

    def save_settings(self):
        # Save window effects settings
        opacity = self.transparency_slider.value() / 100
        blur_enabled = self.blur_checkbox.isChecked()
        
        # Save LLM settings
        provider = self.provider_combo.currentText()
        model = self.model_combo.currentText()
        temperature = self.temperature_spin.value() / 100

        # Update config
        config.DEFAULT_LLM_PROVIDER = provider
        if model:
            config.MODEL_SETTINGS[provider]['model_name'] = model
        config.MODEL_SETTINGS[provider]['temperature'] = temperature
        config.MODEL_SETTINGS[provider]['context_length'] = self.context_length_spin.value()
        config.MODEL_SETTINGS[provider]['max_tokens'] = self.token_length_spin.value()
        config.MODEL_SETTINGS[provider]['image_support'] = self.image_support_checkbox.isChecked()

        # Apply window effects
        if self.parent():
            self.parent().setWindowOpacity(opacity)
            # TODO: Implement blur effect when supported

        self.accept()