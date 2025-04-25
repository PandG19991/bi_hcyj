# %%
from token_manager import TokenManager
import json
import requests

print("--- xiaoe_client.py: 模块加载 ---")

APP_ID = "app0vuxiwxw3082"
CLIENT_ID = "xopgsoZOmum5341"
SECRET_KEY = "rYfj7uxWhjN7Bk9rw326lCJyNP6kFLws"
GRANT_TYPE = "client_credential" # 固定值 硬编码即可
print(f"--- xiaoe_client.py: 硬编码凭证 APP_ID={APP_ID}")

# %%

print("--- xiaoe_client.py: 准备创建 TokenManager 实例 ---")
MANAGER = TokenManager(APP_ID, CLIENT_ID, SECRET_KEY, GRANT_TYPE)
print("--- xiaoe_client.py: TokenManager 实例已创建 ---")

# 调用小鹅client实现接口操作
class XiaoeClient:
    # user_params 需要传dict
    def request(self, method, url, user_params={}):
        print("--- XiaoeClient.request: 开始执行 ---")
        print("--- XiaoeClient.request: 准备调用 MANAGER.token() ---")
        access_token = MANAGER.token()
        print(f"--- XiaoeClient.request: 获取到 access_token={access_token[:5]}...{access_token[-5:]}") # 打印部分token以确认
        user_params["access_token"] = access_token
        payload = json.dumps(user_params)
        print(f"--- XiaoeClient.request: 请求 payload={payload}")
        headers = {
            'Content-Type': 'application/json'
        }
        print(f"--- XiaoeClient.request: 发送 {method.upper()} 请求到 {url}")
        response = requests.request(method, url, headers=headers, data=payload)
        print(f"--- XiaoeClient.request: 收到响应 status_code={response.status_code}")
        print(f"--- XiaoeClient.request: 响应内容 response.text={response.text}")
        print("--- XiaoeClient.request: 结束执行 ---")
        return response.text
