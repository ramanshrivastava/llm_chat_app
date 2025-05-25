// LLM Chat App JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const chatMessages = document.getElementById('chatMessages');
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    // Simplified UI does not include advanced settings
    
    // Chat history
    let chatHistory = [];
    
    
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
        
        // Add to chat history
        chatHistory.push({
            role: 'user',
            content: message
        });

        // Prepare request
        const requestBody = {
            messages: chatHistory,
            stream: false
        };
        
        // Send request to API
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('API request failed');
            }
            return response.json();
        })
        .then(data => {
            // Remove loading indicator
            chatMessages.removeChild(loadingDiv);
            
            // Add assistant message to chat
            addMessage('assistant', data.message.content);
            
            // Add to chat history
            chatHistory.push({
                role: 'assistant',
                content: data.message.content
            });
            
            // Display token usage if available
            if (data.usage) {
                console.log('Token usage:', data.usage);
            }
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
    
    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });
}); 