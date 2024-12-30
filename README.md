# Deep Shell 🐚

Deep Shell is an intelligent terminal application that combines a chat interface with a command-line interface, powered by Google's Gemini AI. It helps users execute terminal commands through natural language conversations.

## Preview

![Deep Shell Preview](./assets/screenshot.png)

## Features

- Interactive chat interface with AI assistant
- Integrated terminal emulator 
- Command explanations
- Support for various development operations:
  - Python environment management
  - Git operations
  - Docker commands
  - Database operations (MySQL, PostgreSQL)
  - Package management (pip, npm)
  - File system operations
  - System information queries

## TODO

- [ ] Fix terminal direct input handling
- [ ] Add Agent B for command result processing
- [ ] Add settings button and configuration panel
- [ ] Implement transparent and blur window features
- [ ] Add support for additional LLMs:
  - [ ] Integration with LiteLLM
  - [ ] Support for local models via Ollama
  - [ ] Model switching capability

## Prerequisites

- Python 3.x
- Qt framework
- Google Gemini API key



## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd deep-shell
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure the API key:
   - Copy `config.template.py` to `config.py`
   ```bash
   cp config.template.py config.py
   ```
   - Edit `config.py` and add your Gemini API key:
   ```python
   GEMINI_API_KEY = "your-api-key-here"
   ```

## Usage

1. Start the application:
   ```bash
   python app.py
   ```

2. The interface consists of two main sections:
   - Left: Chat interface for natural language interactions
   - Right: Terminal emulator for command execution

3. Type your query in the chat input to get command suggestions and explanations

4. Use the terminal directly for command execution

5. Click the reset button (↻) to clear and restart the terminal session

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Add your license here] 