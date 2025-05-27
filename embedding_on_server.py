from flask import Flask, request, jsonify
from transformers import AutoModel, AutoTokenizer
import os

# 初始化 Flask 应用
app = Flask(__name__)



# 加载模型和分词器
device="cpu"
model_path = "Alibaba-NLP/gte-modernbert-base"
local_model_path = "./模型"  # 替换为本地模型的实际路径（如果有）

if os.path.exists(local_model_path):
    tokenizer = AutoTokenizer.from_pretrained(local_model_path)
    model = AutoModel.from_pretrained(local_model_path).to(device)
else:
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModel.from_pretrained(model_path).to(device)

# 嵌入函数
def embedding(model, tokenizer, input_texts):
    batch_dict = tokenizer(input_texts, max_length=5000, padding=True, truncation=True, return_tensors='pt')
    batch_dict = {k: v.to(device) for k, v in batch_dict.items()}
    outputs = model(**batch_dict)
    embeddings = outputs.last_hidden_state[:, 0]
    return embeddings.cpu().detach().numpy()

# 定义 API 路由
@app.route('/embed', methods=['POST'])
def embed_text():
    try:
        # 获取请求中的 JSON 数据
        data = request.get_json()
        if 'text' not in data:
            return jsonify({'error': 'Missing "text" field in request'}), 400

        # 获取原始文本
        raw_text = data['text']

        # 生成嵌入向量
        embedding_vector = embedding(model, tokenizer, [raw_text])

        # 返回嵌入向量
        return jsonify({'embedding': embedding_vector.tolist()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 启动服务器
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1234,debug=False)