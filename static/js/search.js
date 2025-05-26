document.addEventListener('DOMContentLoaded', function() {
    const searchResults = document.getElementById('searchResults');
    const resultCount = document.getElementById('resultCount');
    const applyFilters = document.getElementById('applyFilters');
    const sortBy = document.getElementById('sortBy');
    const pagination = document.getElementById('pagination');
    const pageSize = 10; // 每页显示的游戏数量

    // 获取URL参数
    const urlParams = new URLSearchParams(window.location.search);
    const query = urlParams.get('q') || '';
    const lang = urlParams.get('lang') || 'zh';
    const currentPage = parseInt(urlParams.get('page') || '1');
    
    // 获取所有游戏类别和标签
    async function fetchCategories() {
        try {
            const response = await fetch('/api/categories', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ lang })
            });

            if (!response.ok) throw new Error('Failed to fetch categories');

            const data = await response.json();
            if (data.status === 'success') {
                // 渲染游戏类型
                renderGameTypes(data.gameTypes);
                // 渲染游戏标签
                renderGameTags(data.tags);
            }
        } catch (error) {
            console.error('Error fetching categories:', error);
        }
    }

    // 渲染游戏类型
    function renderGameTypes(types) {
        const gameTypesContainer = document.getElementById('gameTypes');
        if (!gameTypesContainer) return;
        
        const visibleCategories = gameTypesContainer.querySelector('.visible-categories');
        const moreCategories = gameTypesContainer.querySelector('.more-categories');
        
        if (!visibleCategories || !moreCategories) return;
        
        // 按数量排序
        const sortedTypes = types.sort((a, b) => b.count - a.count);
        
        // 获取当前选中的类型
        const selectedTypes = Array.from(document.querySelectorAll('#gameTypes input:checked'))
            .map(input => input.value);
        
        // 渲染前5个类型
        visibleCategories.innerHTML = sortedTypes.slice(0, 5).map(type => `
            <label class="filter-option">
                <input type="checkbox" value="${escapeHtml(type.name)}" 
                       ${selectedTypes.includes(type.name) ? 'checked' : ''}
                       onchange="performSearch()">
                <span>${escapeHtml(type.name)}</span>
                <span class="count">(${type.count})</span>
            </label>
        `).join('');
        
        // 渲染其余类型
        moreCategories.innerHTML = sortedTypes.slice(5).map(type => `
            <label class="filter-option">
                <input type="checkbox" value="${escapeHtml(type.name)}"
                       ${selectedTypes.includes(type.name) ? 'checked' : ''}
                       onchange="performSearch()">
                <span>${escapeHtml(type.name)}</span>
                <span class="count">(${type.count})</span>
            </label>
        `).join('');

        // 显示/隐藏"显示更多"按钮
        const showMoreBtn = document.querySelector('.show-more-btn');
        if (showMoreBtn) {
            showMoreBtn.style.display = sortedTypes.length > 5 ? 'block' : 'none';
        }
    }

    // 渲染游戏标签
    function renderGameTags(tags) {
        const tagsContainer = document.getElementById('gameTags');
        if (!tagsContainer) return;
        
        // 按数量排序
        const sortedTags = tags.sort((a, b) => b.count - a.count);
        
        // 获取当前选中的标签
        const selectedTags = Array.from(document.querySelectorAll('#gameTags input:checked'))
            .map(input => input.value);
        
        // 渲染所有标签
        tagsContainer.innerHTML = sortedTags.map(tag => `
            <label class="filter-option">
                <input type="checkbox" value="${escapeHtml(tag.name)}"
                       ${selectedTags.includes(tag.name) ? 'checked' : ''}
                       onchange="performSearch()">
                <span>${escapeHtml(tag.name)}</span>
                <span class="count">(${tag.count})</span>
            </label>
        `).join('');
    }

    // 切换显示更多类别
    window.toggleMoreCategories = function() {
        const moreCategories = document.querySelector('.more-categories');
        const showMoreBtn = document.querySelector('.show-more-btn');
        const isHidden = moreCategories.style.display === 'none';
        
        moreCategories.style.display = isHidden ? 'block' : 'none';
        showMoreBtn.textContent = isHidden ? 
            (lang === 'zh' ? '收起' : 'Show Less') : 
            (lang === 'zh' ? '显示更多' : 'Show More');
    };

    // 修改执行搜索函数
    window.performSearch = async function() {
        try {
            const query = document.getElementById('searchInput').value.trim();
            const filters = getFilters();
            const sort = document.getElementById('sortBy').value;
            
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    filters: filters,
                    sort: sort,
                    page: currentPage,
                    page_size: pageSize
                })
            });

            if (!response.ok) throw new Error('Search failed');

            const data = await response.json();
            if (data.status === 'success') {
                displayResults(data.data);
                updateGameTypeFilters(data.data); // 更新游戏类型筛选项
                resultCount.textContent = data.total || 0;
                updatePagination(data.total);
                
                // 更新URL，但不刷新页面
                const newUrl = new URL(window.location.href);
                newUrl.searchParams.set('q', query);
                window.history.pushState({}, '', newUrl);
            }
        } catch (error) {
            console.error('Search error:', error);
            document.getElementById('searchResults').innerHTML = `
                <div class="error-message">
                    ${lang === 'zh' ? '搜索出错，请稍后重试' : 'Search error, please try again later'}
                </div>
            `;
        }
    };

    // 更新游戏类型筛选项
    function updateGameTypeFilters(games) {
        // 统计游戏类型
        const typeCount = {};
        games.forEach(game => {
            if (game.游戏类别) {
                game.游戏类别.forEach(type => {
                    typeCount[type] = (typeCount[type] || 0) + 1;
                });
            }
        });

        // 转换为数组并排序
        const sortedTypes = Object.entries(typeCount)
            .map(([name, count]) => ({ name, count }))
            .sort((a, b) => b.count - a.count);

        // 获取当前选中的类型
        const selectedTypes = Array.from(document.querySelectorAll('#gameTypes input:checked'))
            .map(input => input.value);

        // 更新游戏类型显示
        renderGameTypes(sortedTypes.map(type => ({
            id: type.name,
            name: type.name,
            count: type.count
        })));
    }

    // 获取所有筛选条件
    function getFilters() {
        const filters = {};
        
        // 获取价格范围
        const minPrice = document.getElementById('minPrice').value;
        const maxPrice = document.getElementById('maxPrice').value;
        if (minPrice) filters.minPrice = parseFloat(minPrice);
        if (maxPrice) filters.maxPrice = parseFloat(maxPrice);
        
        // 获取日期范围
        const fromDate = document.getElementById('fromDate').value;
        const toDate = document.getElementById('toDate').value;
        if (fromDate) filters.fromDate = fromDate;
        if (toDate) filters.toDate = toDate;
        
        // 获取选中的平台
        const platforms = Array.from(document.querySelectorAll('input[name="platform"]:checked'))
            .map(input => input.value);
        if (platforms.length > 0) filters.platforms = platforms;
        
        // 获取选中的游戏类型
        const types = Array.from(document.querySelectorAll('#gameTypes input:checked'))
            .map(input => input.value);
        if (types.length > 0) filters.types = types;
        
        return filters;
    }

    // 重置所有筛选条件
    window.resetFilters = function() {
        // 重置价格
        document.getElementById('minPrice').value = '';
        document.getElementById('maxPrice').value = '';
        
        // 重置日期
        document.getElementById('fromDate').value = '';
        document.getElementById('toDate').value = '';
        
        // 重置平台选择
        document.querySelectorAll('input[name="platform"]').forEach(input => {
            input.checked = false;
        });
        
        // 重置游戏类型
        document.querySelectorAll('#gameTypes input').forEach(input => {
            input.checked = false;
        });
        
        // 重置游戏标签
        document.querySelectorAll('#gameTags input').forEach(input => {
            input.checked = false;
        });
        
        // 重新执行搜索
        performSearch();
    };

    // 重置特定筛选条件
    window.resetPriceFilter = function() {
        document.getElementById('minPrice').value = '';
        document.getElementById('maxPrice').value = '';
        performSearch();
    };

    window.resetDateFilter = function() {
        document.getElementById('fromDate').value = '';
        document.getElementById('toDate').value = '';
        performSearch();
    };

    // 重置游戏类型筛选
    window.resetTypeFilter = function() {
        document.querySelectorAll('#gameTypes input').forEach(input => {
            input.checked = false;
        });
        performSearch();
    };

    window.resetTagFilter = function() {
        document.querySelectorAll('#gameTags input').forEach(input => {
            input.checked = false;
        });
        performSearch();
    };

    // 显示搜索结果
    function displayResults(games) {
        if (!games || games.length === 0) {
            searchResults.innerHTML = `<div class="no-results">${
                lang === 'zh' ? '没有找到相关游戏' : 'No games found'
            }</div>`;
            return;
        }
        
        searchResults.innerHTML = games.map(game => `
            <a href="/game/${game.游戏应用ID}?lang=${lang}" class="game-card" style="text-decoration: none; display: block;">
                <img src="${game.header_image || '/static/images/placeholder.jpg'}" 
                     alt="${escapeHtml(game.名称)}"
                     onerror="this.src='/static/images/placeholder.jpg'">
                <div class="game-info">
                    <h3>${escapeHtml(game.名称)}</h3>
                    <div class="game-meta">
                        <div class="game-date">${formatDate(game.发布日期)}</div>
                        <div class="game-price">${formatPrice(game.价格, lang)}</div>
                    </div>
                    <div class="game-stats">
                        <span class="rating" title="${lang === 'zh' ? '评分' : 'Rating'}">
                            ${formatRating(game.好评率)}
                            ${game.评论总数 ? 
                              `(${formatNumber(game.评论总数)} ${lang === 'zh' ? '条评价' : 'reviews'})` : 
                              ''}
                        </span>
                        ${game.最高同时在线人数 ? 
                          `<span class="peak-ccu" title="${lang === 'zh' ? '最高同时在线' : 'Peak CCU'}">
                            👥 ${formatNumber(game.最高同时在线人数)}
                           </span>` : 
                          ''}
                    </div>
                    <div class="game-tags">
                        ${(game.游戏类别 || []).map(category => 
                            `<span class="category-tag" onclick="event.preventDefault(); event.stopPropagation(); searchByCategory('${escapeHtml(category)}')">${escapeHtml(category)}</span>`
                        ).join('')}
                        ${(game.玩法类型 || []).slice(0, 3).map(genre => 
                            `<span class="genre-tag" onclick="event.preventDefault(); event.stopPropagation(); searchByGenre('${escapeHtml(genre)}')">${escapeHtml(genre)}</span>`
                        ).join('')}
                    </div>
                    <div class="game-platforms">
                        ${game.支持Windows ? '<span title="Windows">🪟</span>' : ''}
                        ${game.支持Mac ? '<span title="Mac">🍎</span>' : ''}
                        ${game.支持Linux ? '<span title="Linux">🐧</span>' : ''}
                    </div>
                </div>
            </a>
        `).join('');
    }

    // 格式化价格
    function formatPrice(price, lang) {
        if (price === 0) return lang === 'zh' ? '免费' : 'Free';
        return lang === 'zh' ? `¥${price.toFixed(2)}` : `$${price.toFixed(2)}`;
    }    // 格式化评分
    function formatRating(ratio) {
        if (!ratio && ratio !== 0) return lang === 'zh' ? '暂无评分' : 'No rating';
        const percentage = (ratio * 100).toFixed(1);
        return `${percentage}% ${lang === 'zh' ? '好评' : 'Positive'}`;
    }

    // 格式化日期
    function formatDate(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleDateString(lang === 'zh' ? 'zh-CN' : 'en-US');
    }

    // 格式化数字（添加千位分隔符）
    function formatNumber(num) {
        return new Intl.NumberFormat(lang === 'zh' ? 'zh-CN' : 'en-US').format(num);
    }

    // HTML转义
    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // 按分类搜索
    window.searchByCategory = function(category) {
        const searchExpression = `(#游戏类别)=${category}`;
        window.location.href = `/search?q=${encodeURIComponent(searchExpression)}&lang=${lang}`;
    };

    // 按游戏类型搜索
    window.searchByGenre = function(genre) {
        const searchExpression = `(#玩法类型)=${genre}`;
        window.location.href = `/search?q=${encodeURIComponent(searchExpression)}&lang=${lang}`;
    };

    // 添加事件监听器
    document.addEventListener('DOMContentLoaded', function() {
        // 为所有筛选输入添加事件监听
        const filterInputs = document.querySelectorAll(
            '#minPrice, #maxPrice, #fromDate, #toDate, ' +
            'input[name="platform"], #gameTypes input, #gameTags input'
        );
        
        filterInputs.forEach(input => {
            input.addEventListener('change', performSearch);
        });

        // 为排序选择添加事件监听
        sortBy.addEventListener('change', performSearch);

        // 如果有初始查询，执行搜索
        if (query) {
            performSearch();
        }
    });

    // 初始化
    fetchCategories();
});
