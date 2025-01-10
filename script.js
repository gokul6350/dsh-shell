document.addEventListener('DOMContentLoaded', () => {
    const messagesContainer = document.querySelector('.messages-container');
    const messageInput = document.querySelector('#chatInput');
    const sendButton = document.querySelector('.send-button');

    // Initialize Qt web channel
    new QWebChannel(qt.webChannelTransport, function(channel) {
        window.terminal = channel.objects.terminal;
    });

    // Store the current connection to disconnect it later
    let currentConnection = null;

    function addChatMessage(text, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender);
        messageElement.textContent = text;
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function addExecutionLog(command) {
        const logElement = document.createElement('div');
        logElement.classList.add('message', 'execution-log');
        logElement.innerHTML = `
            <div class="log-header">
                <div class="terminal-icon">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="2" y="4" width="20" height="16" rx="2" />
                        <path d="M6 8l4 4-4 4"/>
                        <line x1="12" y1="16" x2="18" y2="16"/>
                    </svg>
                </div>
                <span class="terminal-name">Terminal AI</span>
            </div>
            <div class="log-content">
                <div class="timeline">
                    <div class="timeline-item">
                        <div class="timeline-icon active">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10"/>
                                <path d="M12 8v4l3 3"/>
                            </svg>
                        </div>
                        <div class="timeline-content">
                            <div class="timeline-title">Received Command</div>
                            <code>${command}</code>
                        </div>
                    </div>
                    <div class="timeline-item">
                        <div class="timeline-icon active">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M5 12h14"/>
                                <path d="M12 5l7 7-7 7"/>
                            </svg>
                        </div>
                        <div class="timeline-content">
                            <div class="timeline-title">Executing</div>
                            <div class="timeline-text">Processing command in terminal</div>
                        </div>
                    </div>
                    <div class="timeline-item">
                        <div class="timeline-icon success">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M20 6L9 17l-5-5"/>
                            </svg>
                        </div>
                        <div class="timeline-content">
                            <div class="timeline-title success">Completed</div>
                            <div class="timeline-text">Command executed successfully</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        messagesContainer.appendChild(logElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    async function handleChatSubmit(e) {
        e.preventDefault();
        const message = messageInput.value.trim();
        if (message) {
            addChatMessage(message, 'user');
            messageInput.value = '';
            
            messageInput.disabled = true;
            addChatMessage("Processing...", 'assistant');

            await new Promise(resolve => {
                // Disconnect previous connection if exists
                if (currentConnection) {
                    window.terminal.response_ready.disconnect(currentConnection);
                }

                // Create new connection handler
                currentConnection = (command, speech) => {
                    // Find and remove the "Processing..." message
                    const processingMessage = Array.from(messagesContainer.getElementsByClassName('message')).find(
                        el => el.textContent === "Processing..."
                    );
                    if (processingMessage) {
                        messagesContainer.removeChild(processingMessage);
                    }
                    
                    addChatMessage(speech, 'assistant');
                    
                    if (command) {
                        addExecutionLog(command);
                        window.terminal.send_command(command);
                    }
                    
                    resolve();
                };

                // Connect new handler
                window.terminal.response_ready.connect(currentConnection);
                
                // Process message
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

    // Add reset button functionality
    const resetButton = document.querySelector('.reset-button');
    resetButton.addEventListener('click', () => {
        if (window.terminal) {
            window.terminal.reset_terminal();
        }
    });
});

