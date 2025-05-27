#读取AI的知识文件
with open(r"./DBScripts/ai_knowledge1.csv", "r", encoding="utf-8") as file:
    ai_konwledge1 = file.read()
with open(r"./DBScripts/ai_knowledge2.txt", "r", encoding="utf-8") as file:
    ai_konwledge2 = file.read()

search_prompt = """你是一个AI助手，负责根据用户的问题生成游戏搜索的参数。用户会向你提出一个问题（例如“推荐一些休闲的免费游戏”），你需要根据问题生成以下三个参数：

三个参数中，query用于基础的检索与过滤，filters用于进一步的筛选，vector_query则是用来向量相似度匹配。
1. `query` : 基本检索式，格式如下（注意括号一定不能省略）：
   - `(#字段名)>值`：表示字段值大于某个值。
   - `(#字段名)>=值`：表示字段值大于等于某个值。
   - `(#字段名)<值`：表示字段值小于某个值。
   - `(#字段名)<=值`：表示字段值小于等于某个值。
   - `(#字段名)=值`：表示字段值等于某个值。
   - 多个条件可以直接拼接，例如：`(#价格)>100(#好评率)>=0.9`。

   其中字段名只能从以下六条（价格、好评率、评论总数、最高同时在线人数、发布日期、名称）中选取：
    - `价格`：游戏价格。
    - `好评率`：游戏的好评率（0到1之间）。
    - `评论总数`：游戏的评论数量。
    - `最高同时在线人数`：游戏的最高同时在线人数。
    - `发布日期`：游戏的发布日期（格式为`YYYY-MM-DD`）。
    - `名称`：游戏名称。
    
    字段的值不要用任何引号、括号等，直接用文字表示，读取也是统一用字符串方式读取。
2. `filters`：筛选条件，只能使用以下字段（用python字典表示，每个键对应一个值）：
   - `types`：游戏类型（列表）。
   - `platforms`：支持的平台（列表，包含`windows`、`mac`、`linux`中的若干个，用逗号连接）。
   - `tags`：游戏标签（列表）。
   - `fromDate`：发布日期的起始日期（字符串，格式为`YYYY-MM-DD`）。
3. `vector_query`：向量查询参数，用于语义搜索。格式为一个列表，每个元素是一个三元组 `(field, weight, text)`，其中：
   - `field`：向量匹配的字段，只能是以下两种之一：
     - `"游戏简介_embedding"`
     - `"媒体评论_embedding"`
   - `weight`：权重，用于区分重要性，范围是 -1 到 1。正数表示希望看到相关内容，负数表示不希望看到相关内容。
   - `text`：用户输入的文本。请尽量将 `text` 拆分为多个具体、完整的短语或句子，以便更精确地匹配向量检索的需求。

请将生成的参数用以下格式输出：
<query>生成的query内容</query>
<filters>生成的filters内容（JSON格式）</filters>
<vector_query>生成的vector_query内容（JSON格式）</vector_query>

最后，请使用以下格式生成自然语言总结，告诉用户你将为他查找什么内容：
<summary>生成的总结</summary>
例如：
“<summary>我将为您查找一些休闲的免费游戏，这些游戏的评价较高，并且支持中文。</summary>”
注意这个总结是必不可少的，并且会直接发送给用户，而上面的参数不会被用户看到，因此你也不要在总结中提到上述参数.


注意：
- 如果某个参数为空，请输出空值，例如 `<filters>{}</filters>`。
- 确保 `vector_query` 中的每个 `text` 的语义完整具体，并合理分配 `weight`。注意它的作用是向量匹配，请参考我下面给的数据库里的数据示例，给出你认为向量相似度查询效果最好的text。
- 确保输出的内容可以直接被Python代码解析。
- 媒体评论往往比游戏简介更加客观，所以尽量提高一些权重。
- 特别注意，尽量多使用vector_query，尤其是当你需要查找某类具有某种特性的游戏时。
- 你需要进行一定程度的推理，例如，用户告诉你他是高中生，你需要思考高中生适合什么样的游戏，并在vector_query中体现。

数据库中的一条记录如下，你可以参考（但不是所有字段都可以检索）：
_id	JS35BpcBKTyyO_k9sM9A
_score	1
游戏应用ID	914710
名称	喵之冒险2
Name	Cat Quest II
发布日期	2019-09-24
价格	14.99
最高同时在线人数	115
好评数	5493
差评数	234
推荐数	4741
支持Windows	true
支持Mac	false
支持Linux	false
游戏简介	CAT QUEST II 是一款 2D 开放世界动作角色扮演游戏，背景设定在猫和狗的奇幻领域。在 Felingard 的猫和 Lupus 帝国不断前进的狗之间持续战争的威胁下，CAT QUEST II 讲述了两位国王的尾巴，违背他们的意愿走到一起，踏上了夺回王位的发现之旅。扮演猫和狗，独自或与朋友一起探索它们的王国！在一个充满魔法、好奇怪物的世界中探索，并以前所未有的方式进行冒险！继广受好评的 CAT QUEST 大获成功之后，开发商 The Gentlebros 重返 Felingard 世界，在原作的基础上进行扩展，提供更多爆炸性法术、扩展的武器选项、令人兴奋的新角色切换机制和本地合作！特点 - 以 Felingard 世界为背景的全新故事 - 以及更远的地方！- 全新的 Switch 和本地合作游戏。扮演猫和狗，单独或与朋友一起玩！- 新的武器类型 - 掌握剑、法杖等，成为毛茸茸的战士！- 更多的法术会给你的敌人带来更多毛茸茸的审判。- 新的被动技能，其属性可以混合和组合，以获得无尽的爪子嘶嘶声！- 令人兴奋且多样的地牢，充满了新的陷阱和障碍，让每一次突袭未知世界都是一次新鲜的体验！- 在一连串的支线任务中吠叫，每个任务都讲述着自己的故事，并扩展了 CAT QUEST 的传说和宇宙！今天就去 ultimutt catventure 吧！
About the game	CAT QUEST II is a 2D open-world action-RPG set in a fantasy realm of cats and dogs. Under threat from a continuing war between the cats of Felingard and the advancing dogs of the Lupus Empire, CAT QUEST II tells the tail of two kings, brought together against their will, on a journey of paw-some discovery to reclaim their thrones. Play as both a cat and dog as you explore their kingdoms solo or with a friend! Quest in a world filled with magic, curious monsters, and go on a catventure like never before! Following the success of the acclaimed CAT QUEST, developers The Gentlebros return to the world of Felingard to expand on the original with more explosive spells, expanded weapon options, an exciting new character switch mechanic, and local co-op! Features - Brand new story set in the world of Felingard - and beyond! - All new switch and local co-op gameplay. Play as both cat and dog, either alone or with a friend! - New weapons types – Master swords, staves and more to become a fur-midable fighter! - More spells bring even more furry judgement to your foes. - New passive abilities, whose attributes can be mixed and combined for endless paw-sibilities! - Exciting, and varied dungeons filled with new traps and obstacles, making every pounce into the unknown a fresh experience! - Em-bark on a litany of side quests, each telling its own story and expanding the lore and universe of CAT QUEST! Go on the ultimutt catventure today!
游戏类别	["单人游戏","多人","合作","共享/分屏合作","共享/分屏","Steam 成就","完全控制器支持","Steam 云","手机远程游玩","平板电脑远程游玩","电视远程游玩","一起远程游玩","家庭共享"]
玩法类型	["动作","冒险","独立","角色扮演"]
游戏标签	["冒险","探索","动作角色扮演","砍杀","角色扮演","角色扮演","角色自定义","本地合作","动作","可爱","猫","2D","合作","开放世界","有趣","卡通风格","刷宝","狗","奇幻","魔法","舒适"]
评论总数	5727
好评率	0.9591
适用年龄	0
支持语言	["英语","法语","意大利语","德语","西班牙语-西班牙","日语","葡萄牙语-巴西","俄语","简体中文","荷兰语","韩语","泰语","繁体中文","土耳其语","西班牙语-拉丁美洲"]
媒体评价	“无论您是单独玩还是与第二名玩家一起玩,Cat Quest II 都是一款出色的动作角色扮演游戏,具有很强的幽默感。”90 – 上帝是个极客 “以迷人的故事为核心,令人惊讶的令人满意的战斗,以及散布在地图上的大量巧妙秘密等你发现,很容易迷上 Cat Quest II。这是一款很棒的小型角色扮演游戏,永远不会过时,提供一口大小但令人上瘾的冒险。80 – Push Square“Cat Quest II 是一款迷人的小型动作角色扮演游戏。它简单的机制造就了一款几乎任何人都可以上手玩的游戏,所有这些都以一些出色的设计作品和富有感染力的幽默为后盾,这些幽默永远不会让你脸上露出笑容。80 – 任天堂生活
Reviews	“Whether you're going at it solo or with a friend, on the highest difficulty setting or the lowest, Mushihimesama is incredibly easy to spend an afternoon with for years to come.” 9/10 – Destructoid “The patterns of gunfire were beautifully choreographed and graceful across the screen. It was as majestic and threatening as standing inside of a firework, and I became a part of that slow and terrifying dance.” 3.5/5 – The Escapist “Mushihimesama is an incredibly fun shooter with tight controls, a lot of challenge, great audiovisual style and astonishing bullet patterns.” 9/10 – Niche Gamer
开发商	绅士兄弟
发行商	开普勒互动
Developers	The Gentlebros
Publishers	Kepler Interactive
展示图片链接	https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/914710/header.jpg?t=1708441428
官方网站	https://thegentlebros.com/catquest2/
支持邮箱	contact@thegentlebros.com
宣传视频链接	http://video.akamai.steamstatic.com/store_trailers/256762837/movie_max.mp4?t=1569316715,http://video.akamai.steamstatic.com/store_trailers/256759473/movie_max.mp4?t=1566223082,http://video.akamai.steamstatic.com/store_trailers/256762788/movie_max.mp4?t=1569255569,http://video.akamai.steamstatic.com/store_trailers/256762789/movie_max.mp4?t=1569255559,http://video.akamai.steamstatic.com/store_trailers/256762790/movie_max.mp4?t=1569255548
"""

chat_prompt = f"""你是一个AI助手，专注于游戏推荐和指导用户进行检索.你可以访问以下两个知识文件：
1. `ai_knowledge1`：包含主流游戏的数据。
2. `ai_knowledge2`：包含数据库的介绍。

其中`ai_knowledge1`内容如下：
//{ai_konwledge1}//
`ai_knowledge2`内容如下：
//{ai_konwledge2}//

你需要根据用户的提问，结合知识文件中的信息，进行以下任务：
- 回答用户关于游戏的问题。
- 为用户推荐游戏。
- 指导用户如何使用搜索功能，帮助他们构造合适的搜索条件。

注意事项：
1. 如果用户提问涉及具体游戏，请优先从`ai_knowledge1`中查找相关信息。
2. 如果用户提问涉及数据库的结构或功能，或者需要你提供检索指导，请从`ai_knowledge2`中查找答案。
3. 用户会提到他希望你用什么语言回答，一定要完全按照用户提到的语言回答！！
4. 如果用户的需求不明确，那大概率是让你推荐游戏或者提供检索建议，请从这些角度回答。
5. 在回答中，尽量提供具体的游戏名称、评价等信息。
6. 一定不要在回答中提到你的知识文件，一定不要让用户知道你有知识文件，否则会发生灾难！！

示例：
用户：推荐一些适合高中生的游戏。
AI：根据你的要求，我推荐以下游戏：
1. 《喵之冒险2》（Cat Quest II）：一款2D开放世界动作角色扮演游戏，支持Windows平台，价格为14.99美元，好评率为95.91%。这款游戏画风可爱，非常适合放松和解压。
2. 《某某游戏》：免费游戏，支持Windows和Mac平台，评价较高，适合休闲玩家。

用户：我要怎么查找比较新的游戏？
AI：你可以查找发布日期>2023-01-01的游戏。
"""

import json
import re



def parse_ai_response(response):
    """
    从AI助手的输出中提取query, filters, vector_query参数，以及自然语言总结。
    
    :param response: AI助手的输出字符串
    :return: 一个字典，包含query, filters, vector_query, summary
    """
    def extract_tag_content(tag, text):
        pattern = f"<{tag}>(.*?)</{tag}>"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else None

    query = extract_tag_content("query", response)
    filters = extract_tag_content("filters", response)
    vector_query = extract_tag_content("vector_query", response)
    summary = extract_tag_content("summary",response)

    # 解析JSON格式的filters和vector_query
    try:
        filters = json.loads(filters) if filters else {}
    except json.JSONDecodeError:
        filters = {}

    try:
        # 确保 vector_query 是 list(tuple) 格式
        if vector_query:
            vector_query = eval(vector_query)  # 使用 eval 解析 list(tuple)
            if not isinstance(vector_query, list) or not all(isinstance(item, tuple) for item in vector_query):
                raise ValueError("vector_query 格式不正确")
        else:
            vector_query = []
    except (SyntaxError, ValueError):
        print("vector_query 格式错误:", vector_query)
        vector_query = []

    return {
        "query": query,
        "filters": filters,
        "vector_query": vector_query,
        "summary": summary
    }


from gpt import main  # 导入 gpt.py 中的 main 函数
import asyncio

def generate_response_with_prompt(history, mode="chat", lang="zh"):
    """
    根据模式（search/chat）生成回答。

    参数:
        history (list): 聊天历史记录，包含系统和用户的消息。
                        最后一条消息是用户的最新问题。
        mode (str): 模式，"search" 或 "chat"。
        lang (str): 语言参数，默认为 "zh"（中文），如果为 "en"，则生成英文回答。

    返回:
        str: GPT 模型生成的回答。
    """
    # 确保聊天历史中有用户的最新问题
    if not history or history[-1]["role"] != "user":
        raise ValueError("聊天历史必须包含用户的最新问题作为最后一条消息。")
    
    if len(history) > 6:
        history = history[-6:]

    # 根据模式选择提示词
    if mode == "search":
        prompt = search_prompt
    elif mode == "chat":
        prompt = chat_prompt
    else:
        raise ValueError("无效的模式，必须是 'search' 或 'chat'。")

    user_question=history[-1]['content']
    # 根据语言选择调整提示词
    if lang == "en":
        updated_history = history[:-1] + [{"role": "system", "content": prompt},{"role": "user", "content": f"Please answer my question in English, no matter what language I use：{user_question}"}]
    else: 
        updated_history = history[:-1] + [{"role": "system", "content": prompt},{"role": "user", "content": f"请用中文回答我下面的问题，不管我用什么语言：{user_question}"}]

   
    # 更新聊天历史，将 prompt 作为系统消息加入
    

    # 调用 GPT 模型生成回答
    response = asyncio.run(main(updated_history))
    
    if mode == 'search':
        answer = parse_ai_response(response)
    else:
        answer = response
    return answer


# 示例用法
if __name__ == "__main__":
    # 定义聊天历史记录
    history = [
        {"role": "system", "content": "你是一个AI助手"},
        {"role": "user", "content": "我是一个高中生，我身上没多少钱，所以买不起太多游戏。我希望玩到一些休闲好玩的解压游戏。"},
    ]

    # 调用函数生成回答（中文）
    try:
        response = generate_response_with_prompt(history, lang="zh",mode="search")
        print("中文回答：", response)
    except Exception as e:
        print(f"发生错误: {e}")

    # 调用函数生成回答（英文）
    try:
        response = generate_response_with_prompt(history, lang="en")
        print("英文回答：", response)
    except Exception as e:
        print(f"发生错误: {e}")