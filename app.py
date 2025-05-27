from flask import Flask, render_template, jsonify, request
from datetime import datetime
import json
import jieba
from mock_data import DEMO_GAMES
from elasticsearch import Elasticsearch
import logging
from prompts import generate_response_with_prompt
from embeddings import get_embeddings

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)



# 设置默认支持的语言
SUPPORTED_LANGUAGES = ['zh', 'en']

# 定义有效的筛选选项
VALID_GAME_TYPES = set()
VALID_PLATFORMS = {'windows', 'mac', 'linux'}
VALID_TAGS = set()

# 初始化有效的游戏类型和标签
def initialize_valid_options():
    global VALID_GAME_TYPES, VALID_TAGS
    for game in DEMO_GAMES:
        VALID_GAME_TYPES.update(game['游戏类别'])
        VALID_TAGS.update(game['游戏标签'])
    logger.info(f"Initialized valid game types: {VALID_GAME_TYPES}")
    logger.info(f"Initialized valid tags: {VALID_TAGS}")

# 在应用启动时初始化
initialize_valid_options()

# 初始化Elasticsearch客户端
es = Elasticsearch(['http://10.129.83.200:9200'])

def validate_filters(filters):
    """验证并清理筛选条件"""
    validated_filters = filters.copy() if filters else {}
    
    # 验证游戏类型
    if 'types' in validated_filters:
        original_types = validated_filters['types']
        validated_filters['types'] = [t for t in original_types if t in VALID_GAME_TYPES]
        if len(validated_filters['types']) != len(original_types):
            logger.warning(f"Filtered out invalid game types: {set(original_types) - set(validated_filters['types'])}")
    
    # 验证平台
    if 'platforms' in validated_filters:
        original_platforms = validated_filters['platforms']
        validated_filters['platforms'] = [p.lower() for p in original_platforms if p.lower() in VALID_PLATFORMS]
        if len(validated_filters['platforms']) != len(original_platforms):
            logger.warning(f"Filtered out invalid platforms: {set(original_platforms) - set(validated_filters['platforms'])}")
    
    # 验证标签
    if 'tags' in validated_filters:
        original_tags = validated_filters['tags']
        validated_filters['tags'] = [t for t in original_tags if t in VALID_TAGS]
        if len(validated_filters['tags']) != len(original_tags):
            logger.warning(f"Filtered out invalid tags: {set(original_tags) - set(validated_filters['tags'])}")
    
    # 验证数值范围
    numeric_fields = {
        'minPrice': float,
        'maxPrice': float,
        'minRating': float,
        'minReviews': int,
        'minPeakCCU': int
    }
    
    for field, type_func in numeric_fields.items():
        if field in validated_filters:
            try:
                validated_filters[field] = type_func(validated_filters[field])
            except (ValueError, TypeError):
                logger.warning(f"Invalid {field} value: {validated_filters[field]}")
                del validated_filters[field]
    
    # 验证日期范围
    date_fields = ['fromDate', 'toDate']
    for field in date_fields:
        if field in validated_filters:
            try:
                datetime.strptime(validated_filters[field], '%Y-%m-%d')
            except ValueError:
                logger.warning(f"Invalid {field} value: {validated_filters[field]}")
                del validated_filters[field]
    
    return validated_filters

def search_games(query='', filters=None, sort='relevance', page=1, page_size=20, mode='advanced', lang='zh',vector_query=None):
    """使用Elasticsearch搜索游戏"""
    try:
        # 构建基础查询
        body = {
            'query': {
                'bool': {
                    'must': [],
                    'filter': []
                }
            },
            'from': (page - 1) * page_size,
            'size': page_size,
            '_source': [
                '游戏应用ID', 
                '名称', 'Name',
                '价格', 
                'Header image', '展示图片链接',
                '好评率', '评论总数',
                '最高同时在线人数',
                '发布日期',
                '游戏类别', 
                '玩法类型',
                '游戏标签',
                '游戏简介', 'About the game',
                '媒体评价', 'Reviews',
                '开发商', 'Developers',
                '发行商', 'Publishers',
                '支持Windows', '支持Mac', '支持Linux'
            ]
        }
         # 添加向量查询逻辑
        if vector_query:
            script_score_query = {
                    'query': {
                         'bool':{
                             'must':[],
                             'filter':[]},
                    },
                    'script': {
                        'source': "double totalScore = 0; for (int i = 0; i < params.vector_queries.size(); i++) { def vector_query = params.vector_queries[i]; String field = vector_query.get(\"field\"); double weight = vector_query.get(\"weight\"); def query_vector = vector_query.get(\"vector\"); double cosine_similarity = Math.abs(cosineSimilarity( query_vector,field)); totalScore += weight * cosine_similarity; } return totalScore;",
                        'params': {
                            'vector_queries': []
                        }
                    }}
                
         # 计算嵌入向量并填充参数
            # vector_query: List of (field, weight, text)
            texts = [text for _, _, text in vector_query]
            embeddings = get_embeddings(texts=texts)
            for (field, weight, _), embedding in zip(vector_query, embeddings):
                script_score_query['script']['params']['vector_queries'].append({
                    'field': field,
                    'weight': weight,
                    'vector': embedding["embedding"][0]
                })
            # 将 script_score_query 嵌入到 body['query'] 中，而不是覆盖
            body['query']['script_score'] = script_score_query
            # 清除 bool 字段，避免与 script_score 冲突
            if 'bool' in body['query']:
                del body['query']['bool']
        def append_condition(field,value):
                if not vector_query:
                    body['query']['bool'][field].append(value)
                else:
                    body['query']['script_score']['query']['bool'][field].append(value)
                return
        def handle_advanced_query(query, lang):
            conditions = []
            current_pos = 0
            # 字段映射
            if lang == 'en':
                field_mapping = {
                    'Name': 'Name',
                    'name': 'Name',
                    'About': 'About the game',
                    'about': 'About the game',
                    'Reviews': 'Reviews',
                    'reviews': 'Reviews',
                    'Developers': 'Developers',
                    'developers': 'Developers',
                    'Publishers': 'Publishers',
                    'publishers': 'Publishers',
                    '价格': '价格',
                    'price': '价格',
                    '好评率': '好评率',
                    'rating': '好评率',
                    '评论总数': '评论总数',
                    'reviews_count': '评论总数',
                    '最高同时在线人数': '最高同时在线人数',
                    'peak_ccu': '最高同时在线人数',
                    '发布日期': '发布日期',
                    'release_date': '发布日期'
                }
            else:
                field_mapping = {
                    '名称': '名称',
                    'name': '名称',
                    '简介': '游戏简介',
                    'about': '游戏简介',
                    '评价': '媒体评价',
                    'reviews': '媒体评价',
                    '开发商': '开发商',
                    'developers': '开发商',
                    '发行商': '发行商',
                    'publishers': '发行商',
                    '价格': '价格',
                    'price': '价格',
                    '好评率': '好评率',
                    'rating': '好评率',
                    '评论总数': '评论总数',
                    'reviews_count': '评论总数',
                    '最高同时在线人数': '最高同时在线人数',
                    'peak_ccu': '最高同时在线人数',
                    '发布日期': '发布日期',
                    'release_date': '发布日期'
                }
            while current_pos < len(query):
                if query[current_pos:].startswith('(#'):
                    next_condition = query.find('(#', current_pos + 2)
                    if next_condition == -1:
                        condition = query[current_pos:]
                    else:
                        condition = query[current_pos:next_condition]
                    
                    if ')=' in condition:
                        field = condition[2:condition.find(')=')]
                        value = condition[condition.find(')=')+2:].strip()
                        search_field = field_mapping.get(field, field)
                        if search_field in ['价格', '好评率', '评论总数', '最高同时在线人数','发布日期']:
                            try:
                                if search_field == '好评率':
                                    numeric_value = float(value)
                                    if numeric_value > 1:
                                        numeric_value = numeric_value / 100
                                elif search_field == '发布日期':
                                    numeric_value = value
                                else:
                                    numeric_value = float(value)
                                append_condition('must',{
                                    'match': {search_field: str(numeric_value)}
                                })
                            except ValueError:
                                logger.warning(f"Invalid numeric value for {search_field}: {value}")
                                pass
                        else:
                            append_condition('must',{
                                'match': {search_field: value}
                            })
                    elif ')>=' in condition:
                        field = condition[2:condition.find(')>=')]
                        value = condition[condition.find(')>=')+3:].strip()
                        search_field = field_mapping.get(field, field)
                        try:
                            if search_field == '好评率':
                                numeric_value = float(value)
                                if numeric_value > 1:
                                    numeric_value = numeric_value / 100
                            elif search_field == '发布日期':
                                    numeric_value = value
                            else:
                                numeric_value = float(value)
                            append_condition('filter',{
                                'range': {search_field: {'gte': numeric_value}}
                            })
                        except ValueError:
                            logger.warning(f"Invalid numeric value for {search_field}: {value}")
                            pass
                    elif ')<=' in condition:
                        field = condition[2:condition.find(')<=')]
                        value = condition[condition.find(')<=')+3:].strip()
                        search_field = field_mapping.get(field, field)
                        try:
                            if search_field == '好评率':
                                numeric_value = float(value)
                                if numeric_value > 1:
                                    numeric_value = numeric_value / 100
                            elif search_field == '发布日期':
                                    numeric_value = value
                            else:
                                numeric_value = float(value)
                            append_condition('filter',{
                                'range': {search_field: {'lte': numeric_value}}
                            })
                        except ValueError:
                            logger.warning(f"Invalid numeric value for {search_field}: {value}")
                            pass
                    elif ')>' in condition:
                        field = condition[2:condition.find(')>')]
                        value = condition[condition.find(')>')+2:].strip()
                        search_field = field_mapping.get(field, field)
                        try:
                            if search_field == '好评率':
                                numeric_value = float(value)
                                if numeric_value > 1:
                                    numeric_value = numeric_value / 100
                            elif search_field == '发布日期':
                                    numeric_value = value
                            else:
                                numeric_value = float(value)
                            append_condition('filter',{
                                'range': {search_field: {'gt': numeric_value}}
                            })
                        except ValueError:
                            logger.warning(f"Invalid numeric value for {search_field}: {value}")
                            pass
                    elif ')<' in condition:
                        field = condition[2:condition.find(')<')]
                        value = condition[condition.find(')<')+2:].strip()
                        search_field = field_mapping.get(field, field)
                        try:
                            if search_field == '好评率':
                                numeric_value = float(value)
                                if numeric_value > 1:
                                    numeric_value = numeric_value / 100
                            elif search_field == '发布日期':
                                    numeric_value = value
                            else:
                                numeric_value = float(value)
                            append_condition('filter',{
                                'range': {search_field: {'lt': numeric_value}}
                            })
                        except ValueError:
                            logger.warning(f"Invalid numeric value for {search_field}: {value}")
                            pass
                    current_pos = next_condition if next_condition != -1 else len(query)
                else:
                    current_pos += 1

        # 添加搜索条件
        if query:
            # 判断是否为复杂检索式
            is_advanced_expr = query.strip().startswith('(#')
            if is_advanced_expr:
                # 按复杂检索式处理
                handle_advanced_query(query, lang)
            else:
                # 简单检索式
                if any('\u4e00' <= char <= '\u9fff' for char in query):
                    keywords = jieba.lcut(query.lower())
                    query_string = ' '.join(keywords)
                else:
                    query_string = query.lower()
                search_fields = [
                    '名称^3',
                    'Name^3',
                    '游戏简介^2',
                    'About the game^2',
                    '游戏类别^2',
                    '玩法类型^2',
                    '游戏标签^2',
                    '开发商',
                    'Developers',
                    '发行商',
                    'Publishers',
                    '媒体评价',
                    'Reviews'
                ]
                append_condition('must',{
                    'multi_match': {
                        'query': query_string,
                        'fields': search_fields,
                        'type': 'best_fields',
                        'operator': 'or'
                    }
                })

        # 处理筛选条件
        if filters:
            # 价格范围筛选
            price_range = {}
            if 'minPrice' in filters:
                price_range['gte'] = filters['minPrice']
            if 'maxPrice' in filters:
                price_range['lte'] = filters['maxPrice']
            if price_range:
                append_condition('filter',{
                    'range': {'价格': price_range}
                })

            # 日期范围筛选
            date_range = {}
            if 'fromDate' in filters:
                date_range['gte'] = filters['fromDate']
            if 'toDate' in filters:
                date_range['lte'] = filters['toDate']
            if date_range:
                append_condition('filter',{
                    'range': {'发布日期': date_range}
                })

            # 游戏类型筛选
            if 'types' in filters and filters['types']:
                append_condition('must',{
                    'bool': {
                        'must': [{'term': {'游戏类别': game_type}} for game_type in filters['types']]
                    }
                })

            # 平台筛选
            if 'platforms' in filters and filters['platforms']:
                platform_conditions = []
                for platform in filters['platforms']:
                    if platform.lower() == 'windows':
                        platform_conditions.append({'term': {'支持Windows': True}})
                    elif platform.lower() == 'mac':
                        platform_conditions.append({'term': {'支持Mac': True}})
                    elif platform.lower() == 'linux':
                        platform_conditions.append({'term': {'支持Linux': True}})
                if platform_conditions:
                    append_condition('filter',{
                        'bool': {'should': platform_conditions, 'minimum_should_match': 1}
                    })

            # 语言筛选
            if 'languages' in filters and filters['languages']:
                append_condition('must',{
                    'bool': {
                        'must': [{'term': {'支持语言': language}} for language in filters['languages']]
                    }
                })

            # 标签筛选
            if 'tags' in filters and filters['tags']:
                append_condition('must',{
                    'bool': {
                        'must': [{'term': {'游戏标签': tag}} for tag in filters['tags']]
                    }
                })

            # 好评率筛选
            if 'minRating' in filters:
                append_condition('must',{
                    'range': {'好评率': {'gte': filters['minRating']}}
                })

            # 评论数筛选
            if 'minReviews' in filters:
                append_condition('must',{
                    'range': {'评论总数': {'gte': filters['minReviews']}}
                })

            # 同时在线人数筛选
            if 'minPeakCCU' in filters:
                append_condition('must',{
                    'range': {'最高同时在线人数': {'gte': filters['minPeakCCU']}}
                })

        # 添加排序
        if sort == 'price_asc':
            body['sort'] = [{'价格': 'asc'}]
        elif sort == 'price_desc':
            body['sort'] = [{'价格': 'desc'}]
        elif sort == 'date_asc':
            body['sort'] = [{'发布日期': 'asc'}]
        elif sort == 'date_desc':
            body['sort'] = [{'发布日期': 'desc'}]
        elif sort == 'rating':
            body['sort'] = [{'好评率': 'desc'}]
        elif sort == 'popularity':
            body['sort'] = [{'最高同时在线人数': 'desc'}]

        # 执行搜索
        logger.info(f"Elasticsearch query: {body}")
        response = es.search(index='steam_games', body=body)
        
        # 处理结果
        hits = response['hits']['hits']
        total = response['hits']['total']['value']
        
        # 处理结果，确保每个游戏都有header_image字段，并根据语言选择合适的字段
        games = []
        for hit in hits:
            game = hit['_source']
            # 根据语言选择名称
            if lang == 'en' and 'Name' in game:
                game['名称'] = game['Name']
            
            # 根据语言选择游戏简介
            if lang == 'en' and 'About the game' in game:
                game['游戏简介'] = game['About the game']
            
            # 根据语言选择媒体评价
            if lang == 'en' and 'Reviews' in game:
                game['媒体评价'] = game['Reviews']
            
            # 根据语言选择开发商
            if lang == 'en' and 'Developers' in game:
                game['开发商'] = game['Developers']
            
            # 根据语言选择发行商
            if lang == 'en' and 'Publishers' in game:
                game['发行商'] = game['Publishers']
            
            # 确保header_image字段存在
            if 'Header image' in game:
                game['header_image'] = game['Header image']
            elif '展示图片链接' in game:
                game['header_image'] = game['展示图片链接']
            
            games.append(game)
        return {
            'games': games,
            'total': total
        }
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise e


@app.route('/')
def home():
    lang = request.args.get('lang', 'zh')  # 默认使用中文
    return render_template('index.html', lang=lang)

@app.route('/category')
def category():
    lang = request.args.get('lang', 'zh')
    return render_template('category.html', lang=lang)

@app.route('/guide')
def guide():
    lang = request.args.get('lang', 'zh')
    return render_template('guide.html', lang=lang)

@app.route('/ai_recommend')
@app.route('/<lang>/ai_recommend')
def ai_recommend(lang='zh'):
    return render_template('ai_recommend.html', lang=lang)

@app.route('/search')
def search():
    lang = request.args.get('lang', 'zh')
    query = request.args.get('q', '')
    mode = request.args.get('mode', 'advanced')
    
    # 从 URL 参数中获取筛选条件
    filters = {}
    selected_filters = {}  # 用于存储已选择的筛选条件
    
    # 处理游戏类型筛选
    types = request.args.getlist('types')
    if types:
        filters['types'] = types
        selected_filters['types'] = types  # 记录已选择的类型
    
    # 处理平台筛选
    platforms = request.args.getlist('platforms')
    if platforms:
        filters['platforms'] = [p.lower() for p in platforms]
        selected_filters['platforms'] = platforms  # 记录已选择的平台
    
    # 处理语言筛选
    languages = request.args.getlist('languages')
    if languages:
        filters['languages'] = languages
        selected_filters['languages'] = languages  # 记录已选择的语言
    
    # 处理游戏标签筛选
    tags = request.args.getlist('tags')
    if tags:
        filters['tags'] = tags
        selected_filters['tags'] = tags  # 记录已选择的标签
    
    # 处理价格范围筛选
    min_price = request.args.get('minPrice')
    if min_price:
        try:
            filters['minPrice'] = float(min_price)
            selected_filters['minPrice'] = float(min_price)
        except ValueError:
            pass
    
    max_price = request.args.get('maxPrice')
    if max_price:
        try:
            filters['maxPrice'] = float(max_price)
            selected_filters['maxPrice'] = float(max_price)
        except ValueError:
            pass
    
    # 处理日期范围筛选
    from_date = request.args.get('fromDate')
    if from_date:
        filters['fromDate'] = from_date
        selected_filters['fromDate'] = from_date
    
    to_date = request.args.get('toDate')
    if to_date:
        filters['toDate'] = to_date
        selected_filters['toDate'] = to_date
    
    # 处理好评率筛选
    min_rating = request.args.get('minRating')
    if min_rating:
        try:
            filters['minRating'] = float(min_rating)
            selected_filters['minRating'] = float(min_rating)
        except ValueError:
            pass
    
    # 处理评论数筛选
    min_reviews = request.args.get('minReviews')
    if min_reviews:
        try:
            filters['minReviews'] = int(min_reviews)
            selected_filters['minReviews'] = int(min_reviews)
        except ValueError:
            pass
    
    # 处理同时在线人数筛选
    min_peak_ccu = request.args.get('minPeakCCU')
    if min_peak_ccu:
        try:
            filters['minPeakCCU'] = int(min_peak_ccu)
            selected_filters['minPeakCCU'] = int(min_peak_ccu)
        except ValueError:
            pass
    # 处理 vector_query 参数
    vector_query = request.args.get('vector_query')
    if vector_query:
        try:
            vector_query = json.loads(vector_query)  # 将 JSON 字符串解析为 Python 对象
            if isinstance(vector_query, dict):
                vector_query = [(vector_query['field'], vector_query['weight'], vector_query['text'])]
            elif isinstance(vector_query, list):
                vector_query = [(item['field'], item['weight'], item['text']) for item in vector_query]
            else:
                vector_query = None
        except (json.JSONDecodeError, KeyError, TypeError):
            vector_query = None
    # 获取排序方式
    sort = request.args.get('sort', 'relevance')
    
    # 获取分页参数
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    # 执行搜索
    results = search_games(query, filters, sort, page, page_size, mode, lang,vector_query)
    return render_template('search.html', 
                         lang=lang, 
                         query=query, 
                         mode=mode,
                         filters=filters,
                         selected_filters=selected_filters,  # 添加已选择的筛选条件
                         sort=sort,
                         results=results['games'],
                         total=results['total'],
                         page=page,
                         page_size=page_size,
                         vector_query=vector_query)

@app.route('/api/search', methods=['POST'])
def api_search():
    try:
        data = request.get_json()
        query = data.get('query', '')
        filters = data.get('filters', {})
        sort = data.get('sort', 'relevance')
        page = int(data.get('page', 1))
        page_size = int(data.get('page_size', 20))
        mode = data.get('mode', 'advanced')
        lang = data.get('lang', 'zh')
        vector_query=data.get('vector_query','')
        try:
            # vector_query 可能是嵌套列表形式: [["field", weight, "text"], ...]
            if isinstance(vector_query, str):
                vector_query = json.loads(vector_query)
            if isinstance(vector_query, list) and all(isinstance(item, list) and len(item) == 3 for item in vector_query):
                vector_query = [(item[0], item[1], item[2]) for item in vector_query]
            elif isinstance(vector_query, dict):
                vector_query = [(vector_query['field'], vector_query['weight'], vector_query['text'])]
            else:
                vector_query = None
        except (json.JSONDecodeError, KeyError, TypeError):
            print('-'*50)
            vector_query = None
        # 使用统一的search_games函数
        results = search_games(
            query=query,
            filters=filters,
            sort=sort,
            page=page,
            page_size=page_size,
            mode=mode,
            lang=lang,
            vector_query=vector_query
        )
        
        return jsonify({
            'status': 'success',
            'data': results['games'],
            'total': results['total']
        })
        
    except Exception as e:
        print('xxxx')
        logger.error(f"Search error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/popular_games', methods=['POST'])
def popular_games():
    try:
        # 定义查询条件：好评率高且评论数量足够多
        lang = request.args.get('lang', 'zh')
        body = {
            'query': {
                'bool': {
                    'must': [
                        {'range': {'评论总数': {'gte': 50000}}},  # 评论数大于等于 50000
                        {'range': {'好评率': {'gte': 0.7}}}      # 好评率大于等于 0.7
                    ]
                }
            },
            'sort': [
                {'好评率': 'desc'},  # 按好评率降序
                {'最高同时在线人数': 'desc'}  # 按最高同时在线人数降序
            ],
            'size': 10,  # 只获取前 10 个结果
            '_source': [
                '游戏应用ID', '名称', '价格', '展示图片链接', '好评率'
            ]
        }

        # 从 Elasticsearch 获取数据
        response = es.search(index='steam_games', body=body)
        hits = response['hits']['hits']

        # 格式化返回数据
        games = [{
            'appId': hit['_source']['游戏应用ID'],
            'name': hit['_source']['Name'] if lang == 'en' else hit['_source']['名称'],
            'price': hit['_source']['价格'],
            'headerImage': hit['_source']['展示图片链接'],
            'posRatio': hit['_source']['好评率'],
        } for hit in hits]

        return jsonify({
            'status': 'success',
            'games': games
        })

    except Exception as e:
        logger.error(f"Error fetching popular games: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
@app.route('/api/personalized_games', methods=['POST'])
def personalized_games():
    try:
        # 定义查询条件：最近发布且好评率高
        lang = request.args.get('lang', 'zh')
        body = {
            'query': {
                'bool': {
                    'must': [
                        {'range': {'好评率': {'gte': 0.7}}},  # 好评率大于等于 0.7
                    ]
                }
            },
            'sort': [
                {'发布日期': 'desc'}  # 按发布日期降序
            ],
            'size': 10,  # 只获取前 10 个结果
            '_source': [
                '游戏应用ID', '名称', '价格', '展示图片链接', '好评率'
            ]
        }

        # 从 Elasticsearch 获取数据
        response = es.search(index='steam_games', body=body)
        hits = response['hits']['hits']

        # 格式化返回数据
        games = [{
            'appId': hit['_source']['游戏应用ID'],
            'name': hit['_source']['Name'] if lang == 'en' else hit['_source']['名称'],
            'price': hit['_source']['价格'],
            'headerImage': hit['_source']['展示图片链接'],
            'posRatio': hit['_source']['好评率'],
        } for hit in hits]

        return jsonify({
            'status': 'success',
            'games': games
        })

    except Exception as e:
        logger.error(f"Error fetching personalized games: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/categories', methods=['POST'])
def get_categories():
    try:
        # 收集所有类别、标签和发布年份
        genres = {}  # 使用字典来统计数量
        tags = {}
        years = {}
        price_ranges = {
            'free': 0,
            'under_10': 0,
            '10_to_30': 0,
            '30_to_60': 0,
            'above_60': 0
        }
        
        for game in DEMO_GAMES:
            # 统计游戏类型
            for genre in game['玩法类型']:
                genres[genre] = genres.get(genre, 0) + 1
            
            # 统计标签
            for tag in game['游戏标签']:
                tags[tag] = tags.get(tag, 0) + 1
            
            # 统计发布年份
            year = datetime.strptime(game['发布日期'], '%Y-%m-%d').year
            years[year] = years.get(year, 0) + 1
            
            # 统计价格区间
            price = game['价格']
            if price == 0:
                price_ranges['free'] += 1
            elif price < 10:
                price_ranges['under_10'] += 1
            elif price < 30:
                price_ranges['10_to_30'] += 1
            elif price < 60:
                price_ranges['30_to_60'] += 1
            else:
                price_ranges['above_60'] += 1

        # 返回分类数据，按数量从高到低排序
        return jsonify({
            'status': 'success',
            'gameTypes': sorted([{'id': genre, 'name': genre, 'count': count} 
                        for genre, count in genres.items()],
                        key=lambda x: x['count'], reverse=True),
            'tags': sorted([{'id': tag, 'name': tag, 'count': count} 
                    for tag, count in tags.items()],
                    key=lambda x: x['count'], reverse=True),
            'years': [{'year': year, 'count': count} 
                    for year, count in sorted(years.items())],
            'priceRanges': [
                {'id': 'free', 'name': '免费游戏', 'count': price_ranges['free']},
                {'id': 'under_10', 'name': '¥10以下', 'count': price_ranges['under_10']},
                {'id': '10_to_30', 'name': '¥10-30', 'count': price_ranges['10_to_30']},
                {'id': '30_to_60', 'name': '¥30-60', 'count': price_ranges['30_to_60']},
                {'id': 'above_60', 'name': '¥60以上', 'count': price_ranges['above_60']}
            ]
        })
        
    except Exception as e:
        print(f"Error fetching categories: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/ai_chat', methods=['POST'])
@app.route('/api/ai_chat', methods=['POST'])
def ai_chat():
    data = request.json
    history = data.get('history', [])  # 接收完整的对话历史
    mode = data.get('mode', 'chat')
    lang = data.get('lang', 'zh')
    
    try:
        if mode == 'chat':
            reply = generate_response_with_prompt(history=history,lang=lang,mode=mode)
            return jsonify({
                'status': 'success',
                'reply': reply,
            })
        else:
            # 生成搜索表达式
            reply = generate_response_with_prompt(history=history,lang=lang,mode=mode)
            return jsonify({
                'status': 'success',
                'summary': reply['summary'],
                'query': reply['query'],
                'filters': reply['filters'],
                'vector_query': reply['vector_query']
            })
            
    except Exception as e:
        print(f"Error in AI chat: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
@app.route('/game/<app_id>')
def game_detail(app_id):
    lang = request.args.get('lang', 'zh')
    
    # 查找游戏
    game = next((g for g in DEMO_GAMES if g['游戏应用ID'] == app_id), None)
    
    if not game:
        return render_template('404.html', lang=lang), 404
    
    return render_template('game_detail.html', game=game, lang=lang)

@app.route('/api/search_stats', methods=['POST'])
def get_search_stats():
    try:
        data = request.get_json()
        query = data.get('query', '')
        filters = data.get('filters', {})
        
        # 使用现有的搜索函数获取过滤后的游戏列表
        results = search_games(query, filters)
        filtered_games = results['games']
        
        # 统计游戏类型
        type_count = {}
        for game in filtered_games:
            for type_name in game['游戏类别']:
                type_count[type_name] = type_count.get(type_name, 0) + 1
        
        # 统计游戏标签
        tag_count = {}
        for game in filtered_games:
            for tag in game['游戏标签']:
                tag_count[tag] = tag_count.get(tag, 0) + 1
        
        # 返回统计数据，按数量从高到低排序
        return jsonify({
            'status': 'success',
            'gameTypes': sorted([{'id': type_name, 'name': type_name, 'count': count} 
                        for type_name, count in type_count.items()],
                        key=lambda x: x['count'], reverse=True),
            'tags': sorted([{'id': tag, 'name': tag, 'count': count} 
                    for tag, count in tag_count.items()],
                    key=lambda x: x['count'], reverse=True)
        })
        
    except Exception as e:
        print(f"Error getting search stats: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/advanced_search')
def advanced_search():
    lang = request.args.get('lang', 'zh')
    return render_template('advanced_search.html', lang=lang)

if __name__ == '__main__':
    app.run(debug=True)
