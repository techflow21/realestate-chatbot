//
document.addEventListener('DOMContentLoaded', () => {
    const botBtn = document.getElementById('botBtn');
    const chatModal = document.getElementById('chatModal');
    const closeChat = document.getElementById('closeChat');
    const sendBtn = document.getElementById('sendBtn');
    const userInput = document.getElementById('userInput');
    const chatMessages = document.getElementById('chatMessages');

    botBtn.addEventListener('click', () => {
        chatModal.classList.remove('hidden');
        userInput.focus();
    });

    closeChat.addEventListener('click', () => {
        chatModal.classList.add('hidden');
    });

    window.addEventListener('click', (e) => {
        if (e.target === chatModal) chatModal.classList.add('hidden');
    });

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    function addMessage(text, isUser = false) {
        const div = document.createElement('div');
        div.className = `mb-3 ${isUser ? 'text-right' : ''}`;
        div.innerHTML = `<small class="inline-block px-2 py-1 rounded text-xs font-semibold ${isUser ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-800'}">${isUser ? 'You' : 'Bot'}:</small> <span class="text-sm">${text}</span>`;
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function sendMessage() {
        const msg = userInput.value.trim();
        if (!msg) return;

        addMessage(msg, true);
        userInput.value = '';
        addMessage("⏳ Searching...", false);

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: msg })
            });
            const data = await res.json();

            chatMessages.lastChild.remove(); // remove "⏳"
            addMessage(data.reply);

            data.properties.forEach(p => {
                const card = `
                    <div class="bg-white rounded-lg shadow-md mb-2 overflow-hidden">
                        <img src="${p.image_url}" class="w-full h-24 object-cover">
                        <div class="p-3">
                            <h6 class="font-semibold text-sm mb-1">${p.title}</h6>
                            <p class="text-sm mb-1"><strong class="text-green-600">₦${p.price.toLocaleString()}</strong> • ${p.location}</p>
                            <small class="text-gray-600 text-xs">🛏️ ${p.bedrooms} • 🛁 ${p.bathrooms} • 📏 ${p.area_sqm}m²</small>
                        </div>
                    </div>
                `;
                addMessage(card);
            });
        } catch (err) {
            chatMessages.lastChild.remove();
            addMessage("❌ Error: Could not reach server.");
        }
    }
});
