document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chatMessages');
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const terminalOutput = document.getElementById('terminalOutput');
    const terminalForm = document.getElementById('terminalForm');
    const terminalInput = document.getElementById('terminalInput');
    const resetButton = document.getElementById('resetButton');

    // Chat functionality
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = chatInput.value.trim();
        if (message) {
            addChatMessage(message, 'user');
            // Log user message to Python console
            window.terminal.log_chat_message(message, 'user');
            chatInput.value = '';
            
            // Disable input while processing
            chatInput.disabled = true;
            addChatMessage("Processing...", 'ai');

            // Set up one-time event listener for Python response
            await new Promise(resolve => {
                window.terminal.response_ready.connect((command, speech) => {
                    // Remove "Processing..." message
                    chatMessages.removeChild(chatMessages.lastChild);
                    
                    // Add AI response
                    addChatMessage(speech, 'ai');
                    
                    // If there's a command, execute it in terminal
                    if (command) {
                        addTerminalOutput(`$ ${command}`);
                        window.terminal.send_command(command);
                    }
                    
                    resolve();
                });
                
                // Send message to Python
                window.terminal.process_chat_message(message);
            });
            
            // Re-enable input
            chatInput.disabled = false;
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

