# 小鹅通API调用实现

## 项目简介
这个项目提供了小鹅通开放API的Python实现，可以方便地对接小鹅通平台，实现订单数据同步等功能。

## 文件结构
- `xiaoe_config.py` - API配置和常量定义
- `xiaoe_client.py` - API客户端实现类
- `xiaoe_transformers.py` - 数据转换工具
- `sync_orders.py` - 订单数据同步示例
- `retry_decorator.py` - 重试机制装饰器
- `db_schema.sql` - 数据库表结构

## 使用说明
1. 修改 `xiaoe_config.py` 中的配置，填入你的API凭证
2. 安装依赖包：`pip install requests loguru pymysql`
3. 导入数据库表结构：`mysql -u用户名 -p密码 数据库名 < db_schema.sql`
4. 运行同步示例：`python sync_orders.py`

## 关键功能
- OAuth2.0认证流程
- 订单数据获取和同步
- 用户信息获取
- 商品信息获取
- 直播间列表获取

## 扩展和定制
可以参照现有接口实现，根据小鹅通开放API文档，添加更多接口的调用。

## 注意事项
- 妥善保管API凭证和token文件
- 控制API调用频率，避免触发限流
- 建议实现增量同步机制，避免重复数据 