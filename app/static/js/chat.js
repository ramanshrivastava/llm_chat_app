// LLM Chat App JavaScript - Enhanced Version

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const chatMessages = document.getElementById('chatMessages');
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    const modelSelect = document.getElementById('modelSelect');
    const temperatureRange = document.getElementById('temperatureRange');
    const temperatureValue = document.getElementById('temperatureValue');
    const maxTokensInput = document.getElementById('maxTokensInput');
    const enableSearchCheck = document.getElementById('enableSearchCheck');
    const searchStatus = document.getElementById('searchStatus');
    
    // Chat state
    let chatHistory = [];
    let isGenerating = false;
    
    // Load chat history from localStorage
    loadChatHistory();
    
    // Update temperature value display
    temperatureRange.addEventListener('input', function() {
        temperatureValue.textContent = this.value;
    });
    
    // Handle model selection changes
    modelSelect.addEventListener('change', function() {
        const selectedModel = this.value;
        // Enable web search for Ollama models that support it
        if (selectedModel && selectedModel.startsWith('ollama:')) {
            const modelName = selectedModel.replace('ollama:', '');
            if (modelName.includes('gpt-oss') || modelName.includes('llama')) {
                enableSearchCheck.disabled = false;
                searchStatus.textContent = enableSearchCheck.checked ? 'Ready' : 'Available';
                searchStatus.className = 'badge bg-success ms-1';
            } else {
                enableSearchCheck.disabled = true;
                enableSearchCheck.checked = false;
                searchStatus.textContent = 'Not Supported';
                searchStatus.className = 'badge bg-warning ms-1';
            }
        } else {
            enableSearchCheck.disabled = true;
            enableSearchCheck.checked = false;
            searchStatus.textContent = 'Off';
            searchStatus.className = 'badge bg-secondary ms-1';
        }
    });
    
    // Handle search toggle
    enableSearchCheck.addEventListener('change', function() {
        if (this.checked) {
            searchStatus.textContent = 'Enabled';
            searchStatus.className = 'badge bg-primary ms-1';
        } else {
            searchStatus.textContent = 'Available';
            searchStatus.className = 'badge bg-success ms-1';
        }
    });
    
    // Auto-resize textarea
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 150) + 'px';
    });
    
    // Handle sending messages
    function sendMessage() {
        if (isGenerating) return;
        
        const message = userInput.value.trim();
        if (message === '') return;
        
        // Disable input while generating
        setGenerating(true);
        
        // Add user message to chat
        addMessage('user', message);
        userInput.value = '';
        userInput.style.height = 'auto';
        
        // Show loading indicator
        const loadingDiv = showLoading();
        
        // Get settings
        let model = modelSelect.value;
        let provider = null;
        
        // Check if it's an Ollama model
        if (model && model.startsWith('ollama:')) {
            provider = 'ollama';
            model = model.replace('ollama:', '');  // Remove prefix
        }
        
        const temperature = parseFloat(temperatureRange.value);
        const maxTokens = maxTokensInput.value ? parseInt(maxTokensInput.value) : null;
        
        // Determine provider and actual model name
        let provider = null;
        let actualModel = model;
        if (model && model.startsWith('ollama:')) {
            provider = 'ollama';
            actualModel = model.replace('ollama:', '');
        }
        
        // Add to chat history
        chatHistory.push({
            role: 'user',
            content: message,
            timestamp: new Date().toISOString()
        });
        
        // Prepare request
        const requestBody = {
            messages: chatHistory.map(msg => ({role: msg.role, content: msg.content})),
            model: actualModel || null,
            provider: provider,
            temperature: temperature,
            max_tokens: maxTokens,
            stream: true,
            enable_search: enableSearchCheck.checked
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
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.detail || 'API request failed');
                });
            }
            
            if (!response.body) {
                throw new Error('No response body');
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
                buffer = parts.pop() || '';
                
                for (const part of parts) {
                    const line = part.trim();
                    if (!line.startsWith('data:')) continue;
                    
                    const dataStr = line.slice(5).trim();
                    if (dataStr === '[DONE]') {
                        hideLoading(loadingDiv);
                        setGenerating(false);
                        
                        if (assistantMessage) {
                            chatHistory.push({ 
                                role: 'assistant', 
                                content: assistantMessage,
                                timestamp: new Date().toISOString()
                            });
                            saveChatHistory();
                        }
                        reader.cancel();
                        return;
                    }
                    
                    try {
                        const json = JSON.parse(dataStr);
                        
                        // Handle error in stream
                        if (json.error) {
                            throw new Error(json.error.message || 'Stream error');
                        }
                        
                        const delta = json.choices?.[0]?.delta?.content;
                        if (delta) {
                            assistantMessage += delta;
                            renderMessage(assistantDiv, assistantMessage);
                            scrollToBottom();
                        }
                    } catch (err) {
                        console.error('Invalid SSE data', err, dataStr);
                        if (dataStr.includes('error')) {
                            showError('Stream was interrupted. Please try again.');
                            hideLoading(loadingDiv);
                            setGenerating(false);
                            return;
                        }
                    }
                }
            }

            function read() {
                reader.read().then(({ done, value }) => {
                    if (done) {
                        hideLoading(loadingDiv);
                        setGenerating(false);
                        
                        if (assistantMessage) {
                            chatHistory.push({ 
                                role: 'assistant', 
                                content: assistantMessage,
                                timestamp: new Date().toISOString()
                            });
                            saveChatHistory();
                        }
                        return;
                    }
                    
                    buffer += decoder.decode(value, { stream: true });
                    processBuffer();
                    read();
                }).catch(err => {
                    console.error('Stream read error:', err);
                    showError('Connection lost. Please try again.');
                    hideLoading(loadingDiv);
                    setGenerating(false);
                });
            }

            read();
        })
        .catch(error => {
            console.error('Error:', error);
            hideLoading(loadingDiv);
            setGenerating(false);
            showError(error.message || 'An error occurred while processing your request. Please try again.');
        });
    }
    
    // Add message to chat with enhanced rendering
    function addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;
        
        renderMessage(messageDiv, content);
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }
    
    // Render message content with code highlighting
    function renderMessage(container, content) {
        container.innerHTML = '';
        
        if (content.includes('```')) {
            // Process code blocks with syntax highlighting
            const parts = content.split('```');
            
            for (let i = 0; i < parts.length; i++) {
                if (i % 2 === 0) {
                    // Regular text
                    if (parts[i].trim()) {
                        const textDiv = document.createElement('div');
                        textDiv.innerHTML = formatText(parts[i]);
                        container.appendChild(textDiv);
                    }
                } else {
                    // Code block
                    const codeContainer = document.createElement('div');
                    codeContainer.className = 'code-container';
                    
                    const codeBlock = document.createElement('pre');
                    codeBlock.className = 'code-block';
                    
                    // Extract language from first line if present
                    const lines = parts[i].split('\n');
                    const firstLine = lines[0].trim();
                    const language = firstLine.length < 20 && !firstLine.includes(' ') ? firstLine : '';
                    const codeContent = language ? lines.slice(1).join('\n') : parts[i];
                    
                    codeBlock.textContent = codeContent;
                    
                    // Add copy button
                    const copyButton = document.createElement('button');
                    copyButton.className = 'copy-button';
                    copyButton.textContent = 'Copy';
                    copyButton.addEventListener('click', () => copyToClipboard(codeContent, copyButton));
                    
                    codeContainer.appendChild(codeBlock);
                    codeContainer.appendChild(copyButton);
                    container.appendChild(codeContainer);
                }
            }
        } else {
            // Regular text with basic formatting
            container.innerHTML = formatText(content);
        }
    }
    
    // Format text with basic markdown-like features
    function formatText(text) {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }
    
    // Copy to clipboard with feedback
    function copyToClipboard(text, button) {
        navigator.clipboard.writeText(text).then(() => {
            const originalText = button.textContent;
            button.textContent = 'Copied!';
            button.style.background = '#28a745';
            
            setTimeout(() => {
                button.textContent = originalText;
                button.style.background = '';
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy:', err);
            button.textContent = 'Failed';
            setTimeout(() => {
                button.textContent = 'Copy';
            }, 2000);
        });
    }
    
    // Show loading indicator
    function showLoading() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading';
        loadingDiv.innerHTML = 'Thinking<span class="dots">...</span>';
        chatMessages.appendChild(loadingDiv);
        scrollToBottom();
        return loadingDiv;
    }
    
    // Hide loading indicator
    function hideLoading(loadingDiv) {
        if (loadingDiv && loadingDiv.parentNode) {
            loadingDiv.parentNode.removeChild(loadingDiv);
        }
    }
    
    // Show error message
    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'message system-message error-message';
        errorDiv.textContent = message;
        chatMessages.appendChild(errorDiv);
        scrollToBottom();
    }
    
    // Set generating state
    function setGenerating(generating) {
        isGenerating = generating;
        sendButton.disabled = generating;
        userInput.disabled = generating;
        sendButton.textContent = generating ? 'Sending...' : 'Send';
        
        if (generating) {
            sendButton.classList.add('generating');
        } else {
            sendButton.classList.remove('generating');
        }
    }
    
    // Scroll chat to bottom
    function scrollToBottom() {
        requestAnimationFrame(() => {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        });
    }
    
    // Save chat history to localStorage
    function saveChatHistory() {
        try {
            localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
        } catch (error) {
            console.warn('Failed to save chat history:', error);
        }
    }
    
    // Load chat history from localStorage
    function loadChatHistory() {
        try {
            const saved = localStorage.getItem('chatHistory');
            if (saved) {
                chatHistory = JSON.parse(saved);
                
                // Restore messages to UI
                chatHistory.forEach(msg => {
                    if (msg.role !== 'system') {
                        addMessage(msg.role, msg.content);
                    }
                });
            }
        } catch (error) {
            console.warn('Failed to load chat history:', error);
            chatHistory = [];
        }
    }
    
    // Clear chat
    function clearChat() {
        // Keep only the welcome message
        while (chatMessages.children.length > 1) {
            chatMessages.removeChild(chatMessages.lastChild);
        }
        chatHistory = [];
        saveChatHistory();
    }
    
    // Toggle dark mode
    function toggleDarkMode() {
        document.body.classList.toggle('dark-mode');
        const isDark = document.body.classList.contains('dark-mode');
        localStorage.setItem('darkMode', isDark);
        
        // Update theme toggle button
        const themeToggle = document.querySelector('.theme-toggle');
        if (themeToggle) {
            themeToggle.innerHTML = isDark ? '☀️' : '🌙';
        }
    }
    
    // Check for saved dark mode preference
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(event) {
        // Ctrl/Cmd + Enter to send message
        if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
            event.preventDefault();
            sendMessage();
        }
        
        // Escape to stop generation
        if (event.key === 'Escape' && isGenerating) {
            setGenerating(false);
        }
    });
    
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
    themeToggle.innerHTML = document.body.classList.contains('dark-mode') ? '☀️' : '🌙';
    themeToggle.title = 'Toggle Dark Mode (🌙/☀️)';
    themeToggle.addEventListener('click', toggleDarkMode);
    document.body.appendChild(themeToggle);
    
    // Add clear chat button to settings panel
    const settingsPanel = document.querySelector('.settings-panel');
    if (settingsPanel) {
        const clearButton = document.createElement('button');
        clearButton.className = 'btn btn-outline-danger mt-3';
        clearButton.textContent = 'Clear Chat';
        clearButton.title = 'Clear chat history';
        clearButton.addEventListener('click', () => {
            if (confirm('Are you sure you want to clear the chat history?')) {
                clearChat();
            }
        });
        
        const exportButton = document.createElement('button');
        exportButton.className = 'btn btn-outline-primary mt-3 ms-2';
        exportButton.textContent = 'Export Chat';
        exportButton.title = 'Export chat as text file';
        exportButton.addEventListener('click', exportChat);
        
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'd-flex gap-2';
        buttonContainer.appendChild(clearButton);
        buttonContainer.appendChild(exportButton);
        settingsPanel.appendChild(buttonContainer);
    }
    
    // Export chat function
    function exportChat() {
        if (chatHistory.length === 0) {
            alert('No chat history to export');
            return;
        }
        
        const chatText = chatHistory
            .map(msg => `[${msg.role.toUpperCase()}]: ${msg.content}`)
            .join('\n\n');
        
        const blob = new Blob([chatText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat-export-${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    // Add styles for new elements
    const style = document.createElement('style');
    style.textContent = `
        .code-container {
            position: relative;
            margin: 0.5rem 0;
        }
        
        .copy-button {
            position: absolute;
            top: 0.5rem;
            right: 0.5rem;
            background: var(--bg-accent);
            color: white;
            border: none;
            border-radius: 4px;
            padding: 0.25rem 0.5rem;
            font-size: 0.75rem;
            cursor: pointer;
            opacity: 0.8;
            transition: opacity 0.3s ease;
        }
        
        .copy-button:hover {
            opacity: 1;
        }
        
        .generating {
            opacity: 0.7;
            cursor: wait;
        }
        
        .error-message {
            background-color: #dc3545 !important;
            color: white !important;
        }
        
        .dots {
            animation: blink 1.5s infinite;
        }
        
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0.3; }
        }
        
        code {
            background-color: var(--code-bg);
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: monospace;
            font-size: 0.9em;
        }
    `;
    document.head.appendChild(style);
}); 