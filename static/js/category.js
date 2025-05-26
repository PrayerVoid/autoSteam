document.addEventListener('DOMContentLoaded', function() {
    const lang = new URLSearchParams(window.location.search).get('lang') || 'zh';
    const gameTypes = document.getElementById('gameTypes');
    const tagCloud = document.getElementById('tagCloud');
    const yearTimeline = document.getElementById('yearTimeline');
    const priceRanges = document.getElementById('priceRanges');

    // 获取分类数据
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
                renderGameTypes(data.gameTypes);
                renderTags(data.tags);
                renderYears(data.years);
                renderPriceRanges(data.priceRanges);
            } else {
                throw new Error(data.message || 'Unknown error');
            }
        } catch (error) {
            console.error('Error fetching categories:', error);
            showError(error.message);
        }
    }

    // 渲染游戏类型
    function renderGameTypes(types) {
        if (!types || types.length === 0) return;

        const sortedTypes = types.sort((a, b) => b.count - a.count); // 按数量排序
        gameTypes.innerHTML = sortedTypes.map(type => `
            <div class="category-card" data-type="${type.id}">
                <div class="name">${type.name}</div>
                <div class="count">${type.count} ${lang === 'zh' ? '款游戏' : 'games'}</div>
            </div>
        `).join('');

        // 添加点击事件
        gameTypes.querySelectorAll('.category-card').forEach(card => {
            card.addEventListener('click', () => {
                const type = card.dataset.type;
                window.location.href = `/search?q=${encodeURIComponent(`(#游戏类别)=${type}`)}&lang=${lang}`;
            });
        });
    }

    // 渲染标签云
    function renderTags(tags) {
        if (!tags || tags.length === 0) return;

        const sortedTags = tags.sort((a, b) => b.count - a.count); // 按数量排序
        const maxCount = Math.max(...sortedTags.map(t => t.count));
        const minCount = Math.min(...sortedTags.map(t => t.count));
        
        tagCloud.innerHTML = sortedTags.map(tag => {
            // 计算字体大小，范围从14px到24px
            const fontSize = 14 + (tag.count - minCount) * (10 / (maxCount - minCount));
            return `
                <span class="tag" data-tag="${tag.id}" style="font-size: ${fontSize}px">
                    ${tag.name} <span class="tag-count">${tag.count}</span>
                </span>
            `;
        }).join('');

        // 添加点击事件
        tagCloud.querySelectorAll('.tag').forEach(tag => {
            tag.addEventListener('click', () => {
                const tagId = tag.dataset.tag;
                window.location.href = `/search?q=${encodeURIComponent(`(#游戏标签)=${tagId}`)}&lang=${lang}`;
            });
        });
    }

    // 渲染年份时间轴
    function renderYears(years) {
        if (!years || years.length === 0) return;

        const sortedYears = years.sort((a, b) => a.year - b.year);
        yearTimeline.innerHTML = sortedYears.map(year => `
            <div class="year-item" data-year="${year.year}">
                <div class="year">${year.year}</div>
                <div class="count">${year.count}</div>
            </div>
        `).join('');

        // 添加点击事件
        yearTimeline.querySelectorAll('.year-item').forEach(item => {
            item.addEventListener('click', () => {
                const year = item.dataset.year;
                const fromDate = `${year}-01-01`;
                const toDate = `${year}-12-31`;
                window.location.href = `/search?q=${encodeURIComponent(`(#发布日期)>${fromDate}(#发布日期)<${toDate}`)}&lang=${lang}`;
            });
        });
    }

    // 渲染价格区间
    function renderPriceRanges(ranges) {
        if (!ranges || ranges.length === 0) return;

        priceRanges.innerHTML = ranges.map(range => `
            <div class="price-range" data-id="${range.id}">
                <div class="range">${range.name}</div>
                <div class="count">${range.count}</div>
            </div>
        `).join('');

        // 添加点击事件
        priceRanges.querySelectorAll('.price-range').forEach(range => {
            range.addEventListener('click', () => {
                const id = range.dataset.id;
                let searchExpression = '';
                
                switch(id) {
                    case 'free':
                        searchExpression = `(#价格)=0`;
                        break;
                    case 'under_10':
                        searchExpression = `(#价格)>0(#价格)<10`;
                        break;
                    case '10_to_30':
                        searchExpression = `(#价格)>10(#价格)<30`;
                        break;
                    case '30_to_60':
                        searchExpression = `(#价格)>30(#价格)<60`;
                        break;
                    case 'above_60':
                        searchExpression = `(#价格)>60`;
                        break;
                }
                window.location.href = `/search?q=${encodeURIComponent(searchExpression)}&lang=${lang}`;
            });
        });
    }

    // 格式化价格区间
    function formatPriceRange(range, lang) {
        if (lang === 'zh') {
            if (range.min === 0 && range.max === 0) return '免费';
            if (range.max === Infinity) return `¥${range.min}+`;
            return `¥${range.min} - ¥${range.max}`;
        } else {
            if (range.min === 0 && range.max === 0) return 'Free';
            if (range.max === Infinity) return `$${range.min}+`;
            return `$${range.min} - $${range.max}`;
        }
    }

    // 显示错误信息
    function showError() {
        const errorMessage = lang === 'zh' ? 
            '加载分类数据时出错，请稍后重试' : 
            'Error loading categories, please try again later';

        document.querySelector('.category-grid').innerHTML = `
            <div class="error-message" style="grid-column: 1/-1; text-align: center; color: #ff4444;">
                ${errorMessage}
            </div>
        `;
    }

    // 初始化页面
    fetchCategories();
});
