document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    const popularGames = document.getElementById('popularGames');
    const personalizedGames = document.getElementById('personalizedGames');
    
    const searchParams = new URLSearchParams(window.location.search);
    const lang = searchParams.get('lang') || 'zh';

    // 获取热门游戏
    async function fetchPopularGames() {
        try {
            const response = await fetch('/api/popular_games', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ lang })
            });

            if (!response.ok) throw new Error('Failed to fetch popular games');

            const data = await response.json();
            displayGames(popularGames, data.games);
        } catch (error) {
            console.error('Error fetching popular games:', error);
            popularGames.innerHTML = `<div class="error-message">${
                lang === 'zh' ? '加载热门游戏失败' : 'Failed to load popular games'
            }</div>`;
        }
    }

    // 获取个性化推荐
    async function fetchPersonalizedGames() {
        try {
            const response = await fetch('/api/personalized_games', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ lang })
            });

            if (!response.ok) throw new Error('Failed to fetch personalized games');

            const data = await response.json();
            displayGames(personalizedGames, data.games);
        } catch (error) {
            console.error('Error fetching personalized games:', error);
            personalizedGames.innerHTML = `<div class="error-message">${
                lang === 'zh' ? '加载个性化推荐失败' : 'Failed to load personalized recommendations'
            }</div>`;
        }
    }

    // 显示游戏列表
    function displayGames(container, games) {
        if (!games || games.length === 0) {
            container.innerHTML = `<div class="no-games">${
                lang === 'zh' ? '暂无游戏' : 'No games available'
            }</div>`;
            return;
        }

        container.innerHTML = games.map(game => `
            <div class="game-card" onclick="window.location.href='/game/${game.appId}?lang=${lang}'">
                <img src="${game.headerImage || '/static/images/placeholder.jpg'}" alt="${escapeHtml(game.name)}">
                <div class="game-info">
                    <h3>${escapeHtml(game.name)}</h3>
                    <div class="game-meta">
                        <span class="price">${formatPrice(game.price)}</span>
                        <span class="rating">${formatRating(game.posRatio)}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }    // 处理搜索
    function handleSearch() {
        const query = searchInput.value.trim();
        if (!query) return;
        
        // 检查是否是高级搜索表达式
        let searchExpression = query;
        if (!query.startsWith('(#')) {
            // 如果不是高级搜索表达式，则使用名称搜索
            searchExpression = `(#名称)=${query}`;
        }
        
        window.location.href = `/search?q=${encodeURIComponent(searchExpression)}&lang=${lang}`;
    }

    // 格式化价格
    function formatPrice(price) {
        if (price === 0) return lang === 'zh' ? '免费' : 'Free';
        return lang === 'zh' ? `¥${price.toFixed(2)}` : `$${price.toFixed(2)}`;
    }

    // 格式化评分
    function formatRating(ratio) {
        const percentage = (ratio * 100).toFixed(1);
        return `${percentage}% ${lang === 'zh' ? '好评' : 'Positive'}`;
    }

    // HTML转义
    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // 事件监听器
    searchButton.addEventListener('click', handleSearch);
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleSearch();
        }
    });

    // 初始化页面
    fetchPopularGames();
    fetchPersonalizedGames();
});
