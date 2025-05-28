import asyncio
from openai import AsyncOpenAI
import random

apikeys=['595876ef8347467585f50f43af419ad9.2dtMBnRS0swoDBvR', '3b70962e17aa4b229b3e1b95c954f857.yXiX4XwoK2JOuGTn','c90fb13295234851aeee5a44eae6d650.t0CaxOWUg5guSXPz','0be88cb4f9534be3b38b63f9650f2fe7.9fuHB3dGebMrdfcg']
# 定义异步主函数，用于与 OpenAI API 交互
async def main(history):
    """
    调用 OpenAI 的聊天模型生成回复。

    参数:
        history (list): 聊天历史记录，包含系统和用户的消息。

    返回:
        None
    """
    
    api_key = random.choice(apikeys)  # 随机选择一个 API 密钥
    # 初始化 OpenAI 客户端
    client = AsyncOpenAI(
        
        api_key=api_key,  # API 密钥
        base_url="https://open.bigmodel.cn/api/paas/v4",  # API 基础 URL
    )

    # 配置模型参数
    model = "glm-4-flash-250414"  # 使用的模型名称
    max_output_tokens = 8192  # 最大输出 token 数
    temperature = 0.5  # 控制生成文本的随机性

    try:
        # 调用聊天模型生成回复
        completion = await client.chat.completions.create(
            model=model,
            messages=history,
            stream=False,
            max_tokens=int(max_output_tokens),
            temperature=temperature,
        )
        # 打印生成的回复内容
        return completion.choices[0].message.content
    except Exception as e:
        # 捕获并打印异常信息
        print(f"调用 API 时发生错误: {e}")
        return None


# 定义聊天历史记录
history = [
    {"role": "system", "content": "你是一个AI助手"},
    {
        "role": "user",
        "content": "请翻译成英语：“床前明月光，疑是地上霜。举头望明月，低头思故乡。”",
    },
]

# 使用 asyncio.run 执行异步函数
if __name__ == "__main__":
    # 避免多次调用 asyncio.run 导致 RuntimeError
    response = asyncio.run(main(history))
    if response:
        print(response)
