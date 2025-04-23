# 查询用户订单列表 (xe.get.user.orders)

根据用户 ID 查询其订单列表。

**请求方式及 URL**

*   **请求方式:** `POST`
*   **请求头:** `Content-Type: application/json`
*   **接口地址:** `https://api.xiaoe-tech.com/xe.get.user.orders/1.0.0`
*   **频率限制:** `10秒 3000次`

**请求参数**

| 参数名                 | 必选 | 类型     | 说明                                                                                                                      |
| ------------------- | -- | ------ | ----------------------------------------------------------------------------------------------------------------------- |
| `access_token`      | 是  | string | 专属 token ([获取 access_token](../get_access_token.html))                                                              |
| `user_id`           | 是  | string | 用户 ID                                                                                                                   |
| `data.order_id`     | 否  | string | 订单 ID                                                                                                                   |
| `data.product_id`   | 否  | string | 资源 ID                                                                                                                   |
| `data.begin_time`   | 否  | string | 订单创建开始时间，例如：`2019-08-01 12:00:00`                                                                               |
| `data.end_time`     | 否  | string | 订单创建结束时间，例如：`2019-08-01 12:00:00`                                                                               |
| `data.order_state`  | 否  | int    | 订单状态：0-未支付 1-支付成功 2-支付失败 6-订单过期 10-退款成功                                                                 |
| `data.payment_type` | 否  | int    | 付费类型：2-单笔、3-付费产品包、4-团购、5-单笔的购买赠送、6-产品包的购买赠送、7-问答提问、8-问答偷听、11-付费活动报名、12-打赏类型、13-拼团单个资源、14-拼团产品包、15-超级会员                  |
| `data.resource_type`| 否  | int    | 资源类型：0-无（不通过资源的购买入口）、1-图文、2-音频、3-视频、4-直播、5-活动报名、6-专栏/会员、7-圈子、8-大专栏、20-电子书、21-实物商品、23-超级会员 25-训练营 29-面授课                 |
| `data.client_type`  | 否  | int    | 购买时使用的客户端类型：0-小程序，1-公众号，10-开放api导入，11-PC ，12-APP，13-线下订单，15-APP内嵌SDK，5-手机号，2-QQ，20-抖音，30-管理台导入， 31-积分兑换，32-企业微信，不填查全部类型 |
| `data.page_index`   | 否  | int    | 当前页数，从1开始，默认为1                                                                                                          |
| `data.page_size`    | 否  | int    | 每页个数，最大支持50,默认取10条                                                                                                      |
| `data.order_by`     | 否  | string | 排序方式，默认为 `created_at:desc`                                                                                                |

**请求示例**

```json
{
    "access_token": "xe_xxxxx",
    "user_id": "xxxx",
    "data": {
        "order_id": "o_xxxxxxx",
        "product_id": "i_xxxxxxxx",
        "payment_type": 2,
        "resource_type": 1,
        "begin_time": "2019-07-31 12:00:00",
        "end_time": "2019-08-01 12:00:00",
        "order_state": 1,
        "client_type": 10,
        "page_index": 1, // 注意：文档示例是 0，但说明是 1 开始，这里按说明写 1
        "page_size": 20,
        "order_by": "created_at:desc"
    }
}
```

**返回参数**

| code | msg     | data         |
| ---- | ------- | ------------ |
| 0    | success | 详见返回结构示例 |

**返回示例**

```json
{
    "code": 0,
    "msg": "success",
    "data": {
        "total": 30,
        "list": [
            {
                "app_id": "appxxx",
                "order_id": "o_1xxx157",
                "user_id": "u_xxxxxh",
                "payment_type": 14,
                "resource_type": 6,
                "resource_id": "p_61xxxx4595",
                "product_id": "p_6xxxx6430024595",
                "purchase_name": "专栏拼团123",
                "price": 0,    // 单位：分
                "order_state": 1,
                "out_order_id": null,
                "wx_app_type": 1,
                "period": null, // 有效期
                "pay_time": "2021-08-06 14:18:38",
                "created_at": "2021-08-06 14:18:37",
                "settle_time": "0000-00-00 00:00:00",
                "receiver_name": "",  // 收件人姓名
                "receiver_detail": "", // 收件人地址
                "receiver_phone": "" // 收件人手机号
            }
            // ... more orders
        ]
    }
}
```

**注意:**

*   官方文档示例中的 `page_index` 为 0，但参数说明中写的是从 1 开始，示例中已按说明调整为 1。
*   返回示例中的 `price` 单位是 **分**。