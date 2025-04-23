# 小鹅通 API 文档：批量查询用户信息

**接口名称:** 批量查询用户信息

**接口地址:** `/xe.user.info.batch.get/1.0.0`

**请求方式:** `POST`

**请求头:** `Content-Type: application/json`

**频率限制:** `1秒20次`

**来源:** [https://api-doc.xiaoe-tech.com/api_list/user/get_user_info_batch_2.html](https://api-doc.xiaoe-tech.com/api_list/user/get_user_info_batch_2.html)

---

## 接口说明

根据用户ID列表批量查询用户信息。

---

## 请求参数

| 参数名         | 必选 | 类型         | 说明                                       |
| -------------- | ---- | ------------ | ------------------------------------------ |
| `access_token` | 是   | string       | 专属 token                                 |
| `user_ids`     | 是   | array[string]| 用户 ID 列表，单次请求最多支持 100 个 user_id |

---

## 请求示例

```json
{
    "access_token": "xe_xxxxxx",
    "user_ids": [
        "u_xxxxxx1",
        "u_xxxxxx2"
    ]
}
```

---

## 响应参数

### 顶层结构

| 参数名 | 类型   | 说明                 |
| ------ | ------ | -------------------- |
| `code` | int    | 请求结果码 (0表示成功) |
| `msg`  | string | 描述信息             |
| `data` | object | 数据主体 (详见下文)  |

### `data` 对象详解

| 参数名   | 类型   | 说明         |
| -------- | ------ | ------------ |
| `users`  | array  | 用户信息列表 |

### `data.users[]` 用户信息结构

| 参数名         | 类型     | 说明                                                           |
| -------------- | -------- | -------------------------------------------------------------- |
| `user_id`      | string   | 用户 ID                                                        |
| `nickname`     | string   | 用户昵称                                                       |
| `avatar`       | string   | 用户头像 URL                                                   |
| `phone`        | string   | 用户手机号                                                     |
| `gender`       | int      | 性别：0-未知，1-男，2-女                                         |
| `birthday`     | string   | 生日，格式：`YYYY-MM-DD`                                        |
| `province`     | string   | 省份                                                           |
| `city`         | string   | 城市                                                           |
| `register_time`| string   | 注册时间，格式：`YYYY-MM-DD HH:mm:ss`                            |
| `user_type`    | int      | 用户类型：0-普通用户，1-讲师用户，2-助教用户，3-管理员用户，4-超级管理员 |
| `vip_info`     | object   | 会员信息对象 (结构未详细说明)                                  |
| `unionid`      | string   | 微信 UnionID                                                  |
| `openid`       | string   | 微信公众号 OpenID                                             |
| `app_openid`   | string   | 微信小程序 OpenID                                             |

---

## 响应示例

```json
{
    "code": 0,
    "msg": "success",
    "data": {
        "users": [
            {
                "user_id": "u_xxxxxx1",
                "nickname": "用户昵称1",
                "avatar": "http://example.com/avatar1.jpg",
                "phone": "13800138001",
                "gender": 1,
                "birthday": "2000-01-01",
                "province": "广东",
                "city": "深圳",
                "register_time": "2023-01-15 10:00:00",
                "user_type": 0,
                "vip_info": {
                    // 会员相关信息...
                },
                "unionid": "o_unionid_1",
                "openid": "o_openid_1",
                "app_openid": "o_app_openid_1"
            },
            {
                "user_id": "u_xxxxxx2",
                "nickname": "用户昵称2",
                "avatar": "http://example.com/avatar2.jpg",
                "phone": "13900139002",
                "gender": 2,
                "birthday": null,
                "province": "北京",
                "city": "北京",
                "register_time": "2023-02-20 11:30:00",
                "user_type": 0,
                "vip_info": null,
                "unionid": "o_unionid_2",
                "openid": null,
                "app_openid": "o_app_openid_2"
            }
            // ...更多用户信息
        ]
    }
}
``` 