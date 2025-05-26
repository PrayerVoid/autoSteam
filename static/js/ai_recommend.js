document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chatMessages');
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendMessage');
    const recommendationResults = document.getElementById('recommendationResults');
    const modeBtns = document.querySelectorAll('.mode-btn');
    
    let currentMode = 'chat'; // 'chat' or 'search'
    let isProcessing = false;

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

        try {
            const response = await fetch('/api/ai_chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message,
                    mode: currentMode,
                    lang: window.LANG
                })
            });

            if (!response.ok) throw new Error('AI response failed');

            const data = await response.json();
            
            if (currentMode === 'chat') {
                // 显示AI回复
                addAIMessage(data.reply);
                
                // 如果有推荐游戏，显示在右侧
                if (data.recommendations?.length > 0) {
                    showRecommendations(data.recommendations);
                }
            } else {
                // 搜索模式：显示生成的搜索表达式
                addAIMessage(window.LANG === 'zh' 
                    ? `我已根据你的描述生成以下搜索表达式：\n\`${data.searchExpression}\``
                    : `I've generated the following search expression based on your description:\n\`${data.searchExpression}\``
                );

                // 添加"执行搜索"按钮
                const searchButton = document.createElement('button');
                searchButton.textContent = window.LANG === 'zh' ? '执行搜索' : 'Execute Search';
                searchButton.classList.add('execute-search-btn');
                searchButton.onclick = () => {
                    window.location.href = `/search?q=${encodeURIComponent(data.searchExpression)}&lang=${window.LANG}`;
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
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        messageDiv.innerHTML = `
            <div class="message-content">${escapeHtml(message)}</div>
        `;
        chatMessages.appendChild(messageDiv);
    }

    // 添加AI消息
    function addAIMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message ai-message';
        messageDiv.innerHTML = `
            <div class="message-content">${formatMessage(message)}</div>
        `;
        chatMessages.appendChild(messageDiv);
    }

    // 显示推荐游戏
    function showRecommendations(games) {
        recommendationResults.innerHTML = '';
        games.forEach(game => {
            const gameCard = document.createElement('div');
            gameCard.className = 'game-card';
            gameCard.innerHTML = `
                <h3>${escapeHtml(game.name)}</h3>
                <div class="game-info">
                    <p class="release-date">${game.release_date}</p>
                    <p class="price">${formatPrice(game.price)}</p>
                    <p class="rating">⭐ ${game.rating.toFixed(1)}</p>
                </div>
                <p class="description">${escapeHtml(game.description || '')}</p>
                <a href="https://store.steampowered.com/app/${game.appid}" target="_blank" class="view-on-steam">
                    ${window.LANG === 'zh' ? '在Steam上查看' : 'View on Steam'}
                </a>
            `;
            recommendationResults.appendChild(gameCard);
        });
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
