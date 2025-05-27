import requests

# 服务器地址
url = "http://10.129.83.80:1234/embed"

# 测试文本列表
def get_embeddings(texts, ids=None, url=url):
    """
    给定文本列表、可选的id列表和API地址，返回每个文本的嵌入向量，结果用id标识。
    :param texts: List[str]，待嵌入的文本列表
    :param ids: Optional[List[str]]，每个文本的唯一标识，若为None则用索引
    :param url: str，API地址
    :return: List[dict]，每个文本的结果字典，包含'id'和'embedding'
    """
    if ids is None:
        ids = list(range(len(texts)))
    results = []
    for id_, text in zip(ids, texts):
        test_data = {"text": text}
        try:
            response = requests.post(url, json=test_data)
            response.raise_for_status()
            result = response.json()
            results.append({
                "id": id_,
                "embedding": result.get("embedding")
            })
        except requests.exceptions.RequestException as e:
            results.append({
                "id": id_,
                "embedding": None,
                "error": str(e)
            })
    return results

if __name__ == "__main__":
    ids=["1", "2", "3", "4", "5"] # 示例ID列表（可以不给）
    sample_texts = [
        "Hello, how are you doing today?",
        "The quick brown fox jumps over the lazy dog.",
        "Artificial intelligence is transforming the world.",
        "This is a longer example sentence to test the embedding API with more complex input.",
        "Natural language processing enables computers to understand human language."
    ]
    results = get_embeddings(texts=sample_texts,ids=ids)
    print(results)