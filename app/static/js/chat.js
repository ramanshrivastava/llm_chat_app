// LLM Chat App JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const chatMessages = document.getElementById('chatMessages');
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    const modelSelect = document.getElementById('modelSelect');
    const temperatureRange = document.getElementById('temperatureRange');
    const temperatureValue = document.getElementById('temperatureValue');
    const maxTokensInput = document.getElementById('maxTokensInput');
    
    // Chat history
    let chatHistory = [];
    
    // Update temperature value display
    temperatureRange.addEventListener('input', function() {
        temperatureValue.textContent = this.value;
    });
    
    // Handle sending messages
    function sendMessage() {
        const message = userInput.value.trim();
        if (message === '') return;
        
        // Add user message to chat
        addMessage('user', message);
        userInput.value = '';
        
        // Show loading indicator
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading';
        loadingDiv.textContent = 'Thinking...';
        chatMessages.appendChild(loadingDiv);
        
        // Scroll to bottom
        scrollToBottom();
        
        // Get settings
        const model = modelSelect.value;
        const temperature = parseFloat(temperatureRange.value);
        const maxTokens = maxTokensInput.value ? parseInt(maxTokensInput.value) : null;
        
        // Add to chat history
        chatHistory.push({
            role: 'user',
            content: message
        });
        
        // Prepare request
        const requestBody = {
            messages: chatHistory,
            model: model || null,
            temperature: temperature,
            max_tokens: maxTokens,
            stream: true
        };

        // Send request to API with streaming response
        fetch('/api/chat/stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        })
        .then(response => {
            if (!response.ok || !response.body) {
                throw new Error('API request failed');
            }

            // Create assistant message container
            const assistantDiv = document.createElement('div');
            assistantDiv.className = 'message assistant-message';
            chatMessages.appendChild(assistantDiv);

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let assistantMessage = '';
            let buffer = '';

            function processBuffer() {
                const parts = buffer.split('\n\n');
                buffer = parts.pop();
                for (const part of parts) {
                    const line = part.trim();
                    if (!line.startsWith('data:')) continue;
                    const dataStr = line.slice(5).trim();
                    if (dataStr === '[DONE]') {
                        chatMessages.removeChild(loadingDiv);
                        chatHistory.push({ role: 'assistant', content: assistantMessage });
                        reader.cancel();
                        return;
                    }
                    try {
                        const json = JSON.parse(dataStr);
                        const delta = json.choices?.[0]?.delta?.content;
                        if (delta) {
                            assistantMessage += delta;
                            assistantDiv.textContent = assistantMessage;
                            scrollToBottom();
                        }
                    } catch (err) {
                        console.error('Invalid SSE data', err, dataStr);
                    }
                }
            }

            function read() {
                reader.read().then(({ done, value }) => {
                    if (done) {
                        chatMessages.removeChild(loadingDiv);
                        if (assistantMessage) {
                            chatHistory.push({ role: 'assistant', content: assistantMessage });
                        }
                        return;
                    }
                    buffer += decoder.decode(value, { stream: true });
                    processBuffer();
                    read();
                });
            }

            read();
        })
        .catch(error => {
            console.error('Error:', error);

            // Remove loading indicator
            chatMessages.removeChild(loadingDiv);

            // Add error message
            const errorDiv = document.createElement('div');
            errorDiv.className = 'message system-message';
            errorDiv.textContent = 'An error occurred while processing your request. Please try again.';
            chatMessages.appendChild(errorDiv);

            // Scroll to bottom
            scrollToBottom();
        });
    }
    
    // Add message to chat
    function addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;
        
        // Check if content contains code blocks
        if (content.includes('```')) {
            // Process code blocks
            let parts = content.split('```');
            for (let i = 0; i < parts.length; i++) {
                if (i % 2 === 0) {
                    // Regular text
                    if (parts[i].trim()) {
                        const textSpan = document.createElement('div');
                        textSpan.textContent = parts[i];
                        messageDiv.appendChild(textSpan);
                    }
                } else {
                    // Code block
                    const codeBlock = document.createElement('pre');
                    codeBlock.className = 'code-block';
                    codeBlock.textContent = parts[i];
                    messageDiv.appendChild(codeBlock);
                }
            }
        } else {
            // Regular text
            messageDiv.textContent = content;
        }
        
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        scrollToBottom();
    }
    
    // Scroll chat to bottom
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Clear chat
    function clearChat() {
        // Keep only the welcome message
        while (chatMessages.children.length > 1) {
            chatMessages.removeChild(chatMessages.lastChild);
        }
        chatHistory = [];
    }
    
    // Toggle dark mode
    function toggleDarkMode() {
        document.body.classList.toggle('dark-mode');
        localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
    }
    
    // Check for saved dark mode preference
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
    }
    
    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });
    
    // Add theme toggle button
    const themeToggle = document.createElement('button');
    themeToggle.className = 'theme-toggle';
    themeToggle.innerHTML = '🌓';
    themeToggle.title = 'Toggle Dark Mode';
    themeToggle.addEventListener('click', toggleDarkMode);
    document.body.appendChild(themeToggle);
    
    // Add clear chat button to settings panel
    const settingsPanel = document.querySelector('.settings-panel');
    const clearButton = document.createElement('button');
    clearButton.className = 'btn btn-outline-danger mt-3';
    clearButton.textContent = 'Clear Chat';
    clearButton.addEventListener('click', clearChat);
    settingsPanel.appendChild(clearButton);
}); 