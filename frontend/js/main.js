async function uploadFiles() {
    const fileInput = document.getElementById('fileInput');
    const uploadStatus = document.getElementById('uploadStatus');
    const uploadStatusText = document.getElementById('uploadStatusText');
    const uploadProgressBar = document.getElementById('uploadProgressBar');
    const uploadBtn = document.getElementById('uploadBtn');
    
    if (fileInput.files.length === 0) {
        alert('Please select a file to upload');
        return;
    }

    // show progress
    uploadStatus.classList.remove('d-none');
    uploadStatusText.textContent = 'Uploading file...';
    uploadBtn.disabled = true;
    
    try {
        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);

        // animate progress
        let progress = 0;
        const interval = setInterval(() => {
            progress += 5;
            if (progress > 90) clearInterval(interval);
            uploadProgressBar.style.width = `${progress}%`;
        }, 100);

        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        clearInterval(interval);
        uploadProgressBar.style.width = '100%';

        const data = await response.json();
        
        if (response.ok) {
            uploadStatusText.textContent = 'File uploaded successfully!';
            uploadStatusText.className = 'small text-center text-success mb-0';
            sessionId = data.session_id;
            enableChatInterface(true, file.name);
            
            setTimeout(() => {
                addMessage('Hello! I\'ve analyzed your data. What would you like to know about it?', false);
            }, 500);
        } else {
            uploadStatusText.textContent = data.error || 'Upload failed';
            uploadStatusText.className = 'small text-center text-danger mb-0';
        }
    } catch (error) {
        uploadStatusText.textContent = 'Error uploading file';
        uploadStatusText.className = 'small text-center text-danger mb-0';
        console.error('Upload error:', error);
    } finally {
        uploadBtn.disabled = false;
        
        if (sessionId) {
            setTimeout(() => {
                uploadStatus.classList.add('d-none');
            }, 3000);
        }
    }
}

async function queryDocuments() {
    const queryInput = document.getElementById('queryInput');
    const askBtn = document.getElementById('askBtn');
    
    const question = queryInput.value.trim();
    if (!question) return;
    
    if (!sessionId) {
        addMessage('Please upload a file first', false);
        return;
    }
    
    // show question
    addMessage(question, true);
    queryInput.value = '';
    queryInput.disabled = true;
    askBtn.disabled = true;
    
    try {
        const formData = new FormData();
        formData.append('session_id', sessionId);
        formData.append('question', question);
        
        // show loading
        const chatMessages = document.getElementById('chatMessages');
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'chat-message chat-message-bot typing-indicator fade-in';
        typingIndicator.innerHTML = `
            <div class="d-flex align-items-center gap-2">
                <div class="spinner-border spinner-border-sm text-primary"></div>
                <small>Thinking...</small>
            </div>
        `;
        chatMessages.appendChild(typingIndicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        const response = await fetch('/ask', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        chatMessages.removeChild(typingIndicator);
        
        if (response.ok) {
            addMessage(data.answer, false);
        } else {
            addMessage(`Error: ${data.error || 'Failed to process your question'}`, false);
        }
    } catch (error) {
        console.error('Query error:', error);
        addMessage('Error connecting to server. Please try again.', false);
    } finally {
        queryInput.disabled = false;
        askBtn.disabled = false;
        queryInput.focus();
    }
} 