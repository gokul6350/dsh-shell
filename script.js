document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chatMessages');
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const terminalOutput = document.getElementById('terminalOutput');
    const terminalForm = document.getElementById('terminalForm');
    const terminalInput = document.getElementById('terminalInput');
    const resetButton = document.getElementById('resetButton');

    // Chat functionality
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const message = chatInput.value.trim();
        if (message) {
            addChatMessage(message, 'user');
            chatInput.value = '';
            // Simulate AI response
            setTimeout(() => {
                addChatMessage("I've received your message. How else can I help?", 'ai');
            }, 1000);
        }
    });

    function addChatMessage(text, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message', sender);
        messageElement.textContent = text;
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Terminal functionality
    terminalForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const command = terminalInput.value.trim();
        if (command) {
            addTerminalOutput(`$ ${command}`);
            window.terminal.send_command(command);
            terminalInput.value = '';
        }
    });

    // Reset terminal
    resetButton.addEventListener('click', () => {
        // Clear the input field
        terminalInput.value = '';
        
        // Reset the terminal process
        window.terminal.reset_terminal();
    });

    // Initial terminal message
    addTerminalOutput('Welcome to the Ai terminal!');

    // Initial chat message
    addChatMessage("Hello! How can I assist you with the terminal today?", 'ai');
});

