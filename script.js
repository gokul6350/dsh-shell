document.addEventListener('DOMContentLoaded', () => {
    const chatPanel = document.querySelector('.chat-panel');
    const messageInput = document.querySelector('#chatInput');
    const sendButton = document.querySelector('.send-button');

    // Initialize Qt web channel
    new QWebChannel(qt.webChannelTransport, function(channel) {
        window.terminal = channel.objects.terminal;
    });

    // Chat functionality
    function addChatMessage(text, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender);
        messageElement.textContent = text;
        messageInput.parentElement.insertBefore(messageElement, messageInput.parentElement);
        chatPanel.scrollTop = chatPanel.scrollHeight;
    }

    async function handleChatSubmit(e) {
        e.preventDefault();
        const message = messageInput.value.trim();
        if (message) {
            addChatMessage(message, 'user');
            window.terminal.log_chat_message(message, 'user');
            messageInput.value = '';
            
            messageInput.disabled = true;
            addChatMessage("Processing...", 'assistant');

            await new Promise(resolve => {
                window.terminal.response_ready.connect((command, speech) => {
                    // Remove "Processing..." message
                    chatPanel.removeChild(chatPanel.lastChild);
                    
                    addChatMessage(speech, 'assistant');
                    
                    if (command) {
                        // Send command directly to the embedded terminal
                        window.terminal.send_command(command);
                    }
                    
                    resolve();
                });
                
                window.terminal.process_chat_message(message);
            });
            
            messageInput.disabled = false;
        }
    }

    // Event listeners
    sendButton.addEventListener('click', handleChatSubmit);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleChatSubmit(e);
    });
});

