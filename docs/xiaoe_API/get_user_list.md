# 获取用户列表 2.0 (xe.user.batch.get/2.0.0)

用于批量获取店铺的用户信息。

## 基本信息

*   **接口地址:** `https://api.xiaoe-tech.com/xe.user.batch.get/2.0.0`
*   **请求方式:** `POST`
*   **请求头:** `Content-Type: application/json`
*   **频率限制:** 10秒 3000次
*   **权限要求:** 用户管理-查询

## 请求参数

| 参数名               | 必选 | 类型   | 说明                                                                                                                                                                                                                                                                                        |
| :------------------- | :--- | :----- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `access_token`       | 是   | string | 专属token                                                                                                                                                                                                                                                                                   |
| `page_size`          | 是   | int    | 每页条数，最大50条                                                                                                                                                                                                                                                                            |
| `es_skip`            | 否   | object | 上一页最后一条数据中的 `es_skip` 字段，不传则为第一页，用于翻页 (详见下文 `es_skip` 字段说明)                                                                                                                                                                                                       |
| `phone`              | 否   | string | 手机号 (与 `nickname` 和 `name` 不同时生效，优先级：高)                                                                                                                                                                                                                                        |
| `nickname`           | 否   | string | 店铺个人中心的昵称 (与 `phone` 和 `name` 不同时生效, 优先级中)                                                                                                                                                                                                                                 |
| `name`               | 否   | string | 姓名 (与 `nickname` 和 `phone` 不同时生效, 优先级低)                                                                                                                                                                                                                                         |
| `tag_id`             | 否   | string | 用户标签id (若多个则用逗号隔开，如：`241151,240333`)                                                                                                                                                                                                                                      |
| `from`               | 否   | int    | 用户来源：-1-全部, 0-微信, 1-sdk, 2-字节跳动, 3-百度, 4-飞书企业内训, 5-小班课app, 6-通用h5, 7-微博, 8-B端导入, 9-手机号注册, 10-QQ                                                                                                                                                            |
| `user_type`          | 否   | int    | 用户身份: 0-全部, 1-黑名单, 2-超级会员                                                                                                                                                                                                                                                        |
| `last_paytime_start` | 否   | string | 查询支付起始时间 (格式: YYYY-MM-DD)                                                                                                                                                                                                                                                         |
| `last_paytime_end`   | 否   | string | 查询支付截至时间 (格式: YYYY-MM-DD)                                                                                                                                                                                                                                                         |
| `min_pay_sum`        | 否   | string | 查询支付最小金额 (单位：分?)                                                                                                                                                                                                                                                              |
| `max_pay_sum`        | 否   | string | 查询支付最大金额 (单位：分?)                                                                                                                                                                                                                                                              |
| `min_punch_count`    | 否   | string | 查询支付最小次数                                                                                                                                                                                                                                                                          |
| `max_punch_count`    | 否   | string | 查询支付最大次数                                                                                                                                                                                                                                                                          |
| `user_created_start` | 否   | string | 查询用户创建起始时间 (格式: YYYY-MM-DD, 起始时间必须小于结束时间)                                                                                                                                                                                                                         |
| `user_created_end`   | 否   | string | 查询用户创建截止时间 (格式: YYYY-MM-DD)                                                                                                                                                                                                                                                         |
| `latest_visited_start`| 否  | string | 最近访问时间起始时间 (格式: YYYY-MM-DD, 起始时间必须小于结束时间)                                                                                                                                                                                                                         |
| `latest_visited_end`  | 否  | string | 最近访问时间结束时间 (格式: YYYY-MM-DD)                                                                                                                                                                                                                                                         |
| `need_column`        | 否   | array  | 需要额外返回的字段列表，可选值: `latest_visited_at` (用户最后一次访问店铺的时间)                                                                                                                                                                                                                 |

### `es_skip` 字段说明 (用于翻页)

| 参数名            | 类型   | 说明              |
| :---------------- | :----- | :---------------- |
| `id`              | string | 上一页最后用户的 ID |
| `user_created_at` | int    | 上一页最后用户的创建时间戳 (毫秒) |

## 请求示例

```json
{
    "access_token": "xxxxxxxx",
    "es_skip": {
        "id": "u_61a86592cf48a_7O4smLS1YV",
        "user_created_at": 1638426002000
    },
    "page_size": 1,
    "phone": "",
    "nickname": "",
    "name": "",
    "tag_id": "",
    "from": -1,
    "user_type": 0,
    "last_paytime_start": "",
    "last_paytime_end": "",
    "user_created_start": "2019-01-01",
    "user_created_end": "2019-05-05",
    "min_pay_sum": "",
    "max_pay_sum": "",
    "min_punch_count": "",
    "max_punch_count": "",
    "need_column": [
        "latest_visited_at"
    ]
}
```

## 返回参数

| 参数名     | 类型   | 说明                   |
| :--------- | :----- | :--------------------- |
| `code`     | int    | 状态码 (0 表示成功)      |
| `msg`      | string | 对返回码的文本描述内容 |
| `data`     | object | 数据对象               |
| `data.list`| array  | 用户列表 (详见下文)      |
| `data.total`| int   | 查询结果记录数         |

### 用户列表项 (`data.list[]`)

| 参数名             | 类型   | 说明                                                                                                                                                 |
| :----------------- | :----- | :--------------------------------------------------------------------------------------------------------------------------------------------------- |
| `user_id`          | string | 用户 ID                                                                                                                                              |
| `user_nickname`    | string | 用户昵称                                                                                                                                             |
| `bind_phone`       | string | 绑定手机号                                                                                                                                           |
| `collect_phone`    | string | 采集手机号                                                                                                                                           |
| `avatar`           | string | 头像 URL                                                                                                                                             |
| `from`             | string | 用户来源 (0-微信, 1-sdk, 2-字节跳动, 3-百度, 4-飞书企业内训, 5-小班课app, 6-通用h5, 7-微博, 8-B端导入, 9-手机号注册, 10-QQ) - **注意: 返回的是字符串描述** |
| `latest_visited_at`| int    | 用户最后一次访问店铺的时间 (毫秒时间戳, 为0表示没有访问过店铺) - **仅当请求参数 `need_column` 包含 `latest_visited_at` 时返回**                             |
| `pay_sum`          | float  | 消费总额 (分)                                                                                                                                        |
| `punch_count`      | int    | 购买次数                                                                                                                                             |
| `wx_union_id`      | string | 微信 union_id                                                                                                                                        |
| `wx_app_open_id`   | string | 小程序 open_id                                                                                                                                       |
| `wx_open_id`       | string | 微信 open_id                                                                                                                                         |
| `user_created_at`  | string | 用户创建时间 (格式: YYYY-MM-DD HH:MM:SS)                                                                                                               |
| `es_skip`          | object | 用于下一页请求的翻页信息 (结构同请求参数 `es_skip`)                                                                                                    |

## 返回示例

```json
{
    "code": 0,
    "msg": "ok",
    "data": {
        "list": [
            {
                "avatar": "http://xxx.png",
                "bind_phone": "",
                "collect_phone": "",
                "es_skip": {
                    "id": "u_5cc8101835ebf_XkqYQDe5Wy",
                    "user_created_at": 1556615192000 // 注意这是时间戳
                },
                "from": "微信", // 注意这里是描述
                "pay_sum": 0,
                "punch_count": 1,
                "user_created_at": "2019-04-30 17:06:32", // 注意这里是格式化时间
                "user_id": "u_5cc8101835ebf_XkqYQDe5Wy",
                "user_nickname": "小琪",
                "wx_app_open_id": "",
                "wx_open_id": "",
                "wx_union_id": ""
                // 如果请求了 "latest_visited_at", 这里会包含该字段
            }
        ],
        "total": 163
    }
}
``` 