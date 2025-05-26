import requests
import json

es_url = "http://10.129.83.200:9200/steam_games"  # 修改为你的ES地址
headers = {"Content-Type": "application/json"}

data = {
  "settings": {
    "analysis": {
      "analyzer": {
        "ik_chinese": {
          "type": "custom",
          "tokenizer": "ik_max_word",
          "filter": ["lowercase"]
        },
        "english_analyzer": {
          "type": "standard",
          "stopwords": "_english_"
        }
      }
    },
    "number_of_shards": 1
  },
  "mappings": {
    "properties": {
      "游戏应用ID": { "type": "keyword" },
      "名称": {
        "type": "text",
        "analyzer": "ik_chinese",
        "fields": { "keyword": { "type": "keyword" } }
      },
      "发布日期": { "type": "date", "format": "yyyy-MM-dd" },
      "价格": { "type": "float" },
      "最高同时在线人数": { "type": "integer" },
      "好评数": { "type": "integer" },
      "差评数": { "type": "integer" },
      "推荐数": { "type": "integer" },
      "支持Windows": { "type": "boolean" },
      "支持Mac": { "type": "boolean" },
      "支持Linux": { "type": "boolean" },
      "游戏简介": {
        "type": "text",
        "analyzer": "ik_chinese",
        "fields": { "keyword": { "type": "keyword" } }},
      "About the game": {
        "type": "text",
        "analyzer": "english_analyzer",
        "fields": { "keyword": { "type": "keyword" } }},
      "游戏类别": { 
        "type": "keyword",
        "ignore_above": 256, 
        "null_value": "N/A"
      },
      "玩法类型": { "type": "keyword" },
      "游戏标签": {
        "type": "text",
        "analyzer": "ik_chinese",
        "fields": { "keyword": { "type": "keyword" } }
      },
      "评论总数": { "type": "integer" },
      "好评率": { "type": "float" },
      "适用年龄": { "type": "integer" },
      "支持语言": { "type": "keyword" },
      "媒体评价": { "type": "text" },
      "开发商": { "type": "keyword" },
      "发行商": { "type": "keyword","null_value": "N/A" },
      "展示图片链接": { "type": "keyword" },
      "官方网站": { "type": "keyword" ,"null_value": "N/A"},
      "支持邮箱": { "type": "keyword" ,"null_value": "N/A"},
      "宣传视频链接": { "type": "keyword","null_value": "N/A"}
    }
  }
}

response = requests.put(es_url, headers=headers, data=json.dumps(data))
print(response.status_code)
print(response.text)