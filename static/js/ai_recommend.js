document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chatMessages');
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendMessage');
    const recommendationResults = document.getElementById('recommendationResults');
    const modeBtns = document.querySelectorAll('.mode-btn');
    
    let currentMode = 'chat'; // 'chat' or 'search'
    let isProcessing = false;
    let chatHistory = []; // 用于存储完整的对话历史

    // 切换模式
    modeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            if (isProcessing) return;
            
            const mode = btn.dataset.mode;
            if (mode === currentMode) return;

            modeBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentMode = mode;

            // 更新输入框提示文本
            userInput.placeholder = currentMode === 'chat' 
                ? (window.LANG === 'zh' ? '输入你的问题...' : 'Type your question...')
                : (window.LANG === 'zh' ? '描述你想找的游戏...' : 'Describe the game you\'re looking for...');
            
            // 添加模式切换提示消息
            addAIMessage(currentMode === 'chat'
                ? (window.LANG === 'zh' ? '已切换到对话模式，你可以直接与我交流。' : 'Switched to chat mode. You can talk to me directly.')
                : (window.LANG === 'zh' ? '已切换到搜索模式，我会根据你的描述生成搜索表达式。' : 'Switched to search mode. I\'ll generate search expressions based on your description.')
            );
        });
    });

    // 发送消息
    async function sendMessage() {
        if (isProcessing) return;

        const message = userInput.value.trim();
        if (!message) return;

        isProcessing = true;
        userInput.value = '';
        addUserMessage(message);

    // 添加假的 AI 消息框，显示加载动画
const loadingMessageDiv = document.createElement('div');
loadingMessageDiv.className = 'message ai-message loading';
loadingMessageDiv.innerHTML = `
    <div class="message-content">
        <div class="loading-spinner"></div>
    </div>
`;
chatMessages.appendChild(loadingMessageDiv);
chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const response = await fetch('/api/ai_chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    history: chatHistory, // 发送完整的对话历史
                    mode: currentMode,
                    lang: window.LANG
                })
            });

            if (!response.ok) throw new Error('AI response failed');

            const data = await response.json();

            loadingMessageDiv.remove();
            
            if (currentMode === 'chat') {
                // 显示AI回复
                addAIMessage(data.reply);

                
            } else {
                // 搜索模式：显示生成的搜索表达式
                addAIMessage(data.summary
                );

                // 存储后端返回的 query, filters 和 vector_query
    const query = data.query;
    const filters = data.filters;
    const vectorQuery = data.vector_query;

    // 拆解 filters 为 /search 路由支持的格式
    const searchParams = new URLSearchParams();
    if (filters.types) {
        filters.types.forEach(type => searchParams.append('types', type));
    }
    if (filters.platforms) {
        filters.platforms.forEach(platform => searchParams.append('platforms', platform));
    }
    if (filters.languages) {
        filters.languages.forEach(language => searchParams.append('languages', language));
    }
    if (filters.tags) {
        filters.tags.forEach(tag => searchParams.append('tags', tag));
    }
    if (filters.minPrice !== undefined) {
        searchParams.append('minPrice', filters.minPrice);
    }
    if (filters.maxPrice !== undefined) {
        searchParams.append('maxPrice', filters.maxPrice);
    }
    if (filters.fromDate) {
        searchParams.append('fromDate', filters.fromDate);
    }
    if (filters.toDate) {
        searchParams.append('toDate', filters.toDate);
        }
    if (filters.minRating !== undefined) {
        searchParams.append('minRating', filters.minRating);
    }
    if (filters.minReviews !== undefined) {
        searchParams.append('minReviews', filters.minReviews);
    }
    if (filters.minPeakCCU !== undefined) {
        searchParams.append('minPeakCCU', filters.minPeakCCU);
    }

    // 添加"执行搜索"按钮
    const searchButton = document.createElement('button');
    searchButton.textContent = window.LANG === 'zh' ? '执行搜索' : 'Execute Search';
    searchButton.classList.add('execute-search-btn');
    searchButton.onclick = () => {
        // 将 query, filters 和 vector_query 绑定到搜索 URL
        const searchUrl = `/search?q=${encodeURIComponent(query)}&${searchParams.toString()}&vector_query=${encodeURIComponent(JSON.stringify(vectorQuery))}&lang=${window.LANG}`;
        window.location.href = searchUrl;
    };
    chatMessages.appendChild(searchButton);

            }
        } catch (error) {
            console.error('AI chat error:', error);
            addAIMessage(window.LANG === 'zh' 
                ? '抱歉，处理您的请求时出现错误，请稍后重试。'
                : 'Sorry, there was an error processing your request. Please try again later.'
            );
        } finally {
            isProcessing = false;
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    // 添加用户消息
    function addUserMessage(message) {
        chatHistory.push({'role':'user','content':message})
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        messageDiv.innerHTML = `
            <div class="message-content">${escapeHtml(message)}</div>
        `;
        chatMessages.appendChild(messageDiv);
    }

    // 添加AI消息
    function addAIMessage(message) {
        chatHistory.push({'role':'system','content':message})
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message ai-message';
        messageDiv.innerHTML = `
            <div class="message-content">${formatMessage(message)}</div>
        `;
        chatMessages.appendChild(messageDiv);
    }


    // 格式化消息（支持简单的markdown语法）
    function formatMessage(message) {
        return message
            .replace(/\`([^\`]+)\`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }

    // HTML转义
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // 格式化价格
    function formatPrice(price) {
        if (!price || price === 0) {
            return window.LANG === 'zh' ? '免费' : 'Free';
        }
        return window.LANG === 'zh' ? `¥${price.toFixed(2)}` : `$${price.toFixed(2)}`;
    }

    // 事件监听器
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 自动获取输入框焦点
    userInput.focus();
});
