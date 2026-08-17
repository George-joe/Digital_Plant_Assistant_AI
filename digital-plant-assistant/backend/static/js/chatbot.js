document.addEventListener('DOMContentLoaded', () => {
    const chatbotToggle = document.getElementById('chatbotToggle');
    const chatbotWindow = document.getElementById('chatbotWindow');
    const closeChatBtn = document.getElementById('closeChatBtn');
    const chatInput = document.getElementById('chatInput');
    const sendChatBtn = document.getElementById('sendChatBtn');
    const chatBody = document.getElementById('chatBody');

    // Toggle Chatbot Window
    chatbotToggle.addEventListener('click', () => {
        chatbotWindow.classList.toggle('hidden');
        if (!chatbotWindow.classList.contains('hidden')) {
            chatInput.focus();
        }
    });

    closeChatBtn.addEventListener('click', () => {
        chatbotWindow.classList.add('hidden');
    });

    // Append Message Helper
    function appendMessage(text, role) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-msg ${role === 'user' ? 'user-msg' : 'ai-msg'}`;
        msgDiv.innerText = text;
        chatBody.appendChild(msgDiv);
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    // Send Message Logic
    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        appendMessage(text, 'user');
        chatInput.value = '';

        // Determine context if we are on a plant page
        const plantId = localStorage.getItem('selectedPlantId');
        const isPlantPage = window.location.pathname.startsWith('/plant');

        let payload = { message: text };
        if (isPlantPage && plantId) {
            payload.plant_id = parseInt(plantId);
        }

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (data.reply) {
                appendMessage(data.reply, 'ai');
            } else if (data.error) {
                appendMessage("Error: " + data.error, 'ai');
            }
        } catch (err) {
            appendMessage("I'm having trouble connecting right now.", 'ai');
        }
    }

    sendChatBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});
