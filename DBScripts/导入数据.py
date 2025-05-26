from elasticsearch import Elasticsearch, helpers
import pandas as pd
import json  
es = Elasticsearch("http://10.129.83.200:9200")

def clean_multi_value(value):
    if pd.isna(value):
        return []
    return [v.strip() for v in str(value).split(",")]
def convert_embedding(value):
    if pd.isna(value):
        return []
    # 如果是字符串，尝试解析为列表
    if isinstance(value, str):
        try:
            return json.loads(value)
        except:
            return []
    # 如果是 NumPy 数组，转换为列表
    elif hasattr(value, 'tolist'):
        return value.tolist()
    # 其他情况直接返回（假设已经是列表）
    else:
        return value
def load_data():
    df = pd.read_excel("./DBScripts/steam_games_translated_final.xlsx")
    df = df.where(pd.notnull(df), None)
    
    actions = []
    for _, row in df.iterrows():
        action = {
            "_index": "steam_games",
            "_source": {
                "游戏应用ID": str(row["游戏应用ID"]),
                "名称": str(row["名称"]),
                "Name": str(row["Name"]),
                "发布日期": row["发布日期"].strftime("%Y-%m-%d") ,
                "价格": float(row["价格"]) if row["价格"] else 0.0,
                "最高同时在线人数": int(row["最高同时在线人数"]) if row["最高同时在线人数"] else 0,
                "好评数": int(row["好评数"]) if row["好评数"] else 0,
                "差评数": int(row["差评数"]) if row["差评数"] else 0,
                "推荐数": int(row["推荐数"]) if row["推荐数"] else 0,
                "支持Windows": bool(row["支持Windows"]),
                "支持Mac": bool(row["支持Mac"]),
                "支持Linux": bool(row["支持Linux"]),
                "游戏简介": str(row["游戏简介"]) ,
                "About the game": str(row["About the game"]) ,
                "游戏类别": clean_multi_value(row["游戏类别"]),
                "玩法类型": clean_multi_value(row["玩法类型"]),
                "游戏标签": clean_multi_value(row["游戏标签"]),
                "评论总数": int(row["评论总数"]) if row["评论总数"] else 0,
                "好评率": float(row["好评率"]) if row["好评率"] else 0.0,
                "适用年龄": int(row["适用年龄"]),
                "支持语言": clean_multi_value(row["支持语言"]),
                "媒体评价":  str(row["媒体评价"]),
                "Reviews": str(row.get("Reviews", "N/A")),
                "开发商": row["开发商"],
                "发行商": row["发行商"],
                "Developers": row["Developers"],  
                "Publishers": row["Publishers"],
                "展示图片链接": row["展示图片链接"],
                "官方网站": row["官方网站"],
                "支持邮箱": row["支持邮箱"],
                "宣传视频链接": row["宣传视频链接"],
                "游戏简介_embedding": convert_embedding(row['游戏简介_embedding']),
                "媒体评价_embedding": convert_embedding(row['媒体评价_embedding'])
            }
        }
        actions.append(action)
    helpers.bulk(es, actions)
    print(f"导入完成！共处理 {len(actions)} 条数据")

if __name__ == "__main__":
    load_data()