import os
import json
import requests
from openai import OpenAI


# ========== 工具函数 ==========
def get_weather(city):
    url = "https://wttr.in/" + city + "?format=j1"
    response = requests.get(url)
    data = response.json()

    current = data["current_condition"][0]

    return {
        "city": city,
        "temp": current["temp_C"],
        "weather": current["weatherDesc"][0]["value"],
        "humidity": current["humidity"]
    }


# ========== 工具说明 ==========
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询某个城市的当前天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名，比如 Beijing"
                    }
                },
                "required": ["city"]
            }
        }
    }
]


# ========== 客户端 ==========
client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)


# ========== 主程序 ==========
def main():
    user_input = input("你说：")

    # 第一次请求：让模型决定
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "user", "content": user_input}
        ],
        tools=tools
    )

    message = response.choices[0].message

    if not message.tool_calls:
        print(message.content)
        return

    tool_call = message.tool_calls[0]
    arguments = tool_call.function.arguments
    args = json.loads(arguments)
    city = args["city"]

    # 执行工具
    result = get_weather(city)

    # 第二次请求：把结果发回给模型
    messages = [
        {"role": "user", "content": user_input},
        message,
        {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result, ensure_ascii=False)
        }
    ]

    final_response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=tools
    )

    print(final_response.choices[0].message.content)


if __name__ == "__main__":
    main()