# 获取售后订单详情 (xe.aftersale.detail/1.0.0)

根据售后单号获取售后订单的详细信息。

**请求方式及 URL**

*   **请求方式:** `POST`
*   **请求头:** `Content-Type: application/json`
*   **接口地址:** `https://api.xiaoe-tech.com/xe.aftersale.detail/1.0.0`
*   **频率限制:** `10秒500次`

**请求参数**

| 参数名           | 必选 | 类型     | 说明                                      |
| ------------- | -- | ------ | ----------------------------------------- |
| `access_token` | 是  | string | [专属token](../get_access_token.html)       |
| `aftersale_id` | 是  | string | 售后单号                                  |
| `user_id`      | 否  | string | 用户 ID (如果需要根据用户 ID 校验权限)        |
| `order_id`     | 否  | string | 父订单号 (如果需要根据父订单号校验权限) |

**请求示例**

```json
{
    "access_token": "YOUR_ACCESS_TOKEN",
    "aftersale_id": "A1676256272_63e9a41000b74_73803812"
}
```

**返回参数**

| 参数名                 | 类型     | 说明                                                                                                                            |
| ----------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------- |
| `code`                  | int    | 状态码 (0 表示成功)                                                                                                               |
| `msg`                   | string | 返回消息                                                                                                                      |
| `data`                  | object | 售后详情数据                                                                                                                    |
| `data.actual_fee`       | int    | 订单实际支付金额 (单位: 分)                                                                                                       |
| `data.after_sale_count` | int    | 售后次数                                                                                                                      |
| `data.aftersale_id`     | string | 售后单号                                                                                                                      |
| `data.apply_channel`    | string | 申请渠道 (无需关注)                                                                                                             |
| `data.apply_refund_money`| int    | 申请退款金额 (单位: 分)                                                                                                       |
| `data.certificate`      | array  | 凭证图片 URL 列表                                                                                                             |
| `data.created_at`       | string | 售后单创建时间 (格式: YYYY-MM-DD HH:MM:SS)                                                                                      |
| `data.distribution_amount`| int    | 分销金额 (单位: 分)                                                                                                           |
| `data.freight`          | int    | 运费 (单位: 分)                                                                                                               |
| `data.goods_list`       | array  | 商品列表                                                                                                                      |
| `data.goods_name`       | string | 商品名称 (取 `goods_list` 第一个商品)                                                                                             |
| `data.img_url`          | string | 商品图片 URL (取 `goods_list` 第一个商品)                                                                                         |
| `data.invalid_time`     | string | 售后单失效时间 (格式: YYYY-MM-DD HH:MM:SS)                                                                                      |
| `data.merchant_remark`  | string | 商家售后备注                                                                                                                  |
| `data.order_id`         | string | 父订单号                                                                                                                      |
| `data.original_price`   | int    | 订单原价 (单位: 分)                                                                                                           |
| `data.payment_amount`   | int    | 支付金额 (单位: 分) - *注意：此字段含义与 `actual_fee` 可能重复或有细微差别，需结合业务确认*                                                              |
| `data.phone`            | string | 用户手机号                                                                                                                    |
| `data.prompt_state`     | int    | 无需关注                                                                                                                      |
| `data.reason`           | string | 买家申请售后原因                                                                                                                |
| `data.refund_money`     | int    | 实际退款金额 (单位: 分)                                                                                                         |
| `data.remark`           | string | 买家售后备注                                                                                                                  |
| `data.resource_type`    | int    | 资源类型 (枚举值参考订单或商品相关文档)                                                                                             |
| `data.sale_type`        | int    | 售后方式 (1-仅退款, 2-退款退货)                                                                                                     |
| `data.ship_state`       | int    | 退货物流状态 (0-无需发货, 1-待买家发货, 2-买家已发货, 3-商家已收货, 4-商家未收货)                                                                    |
| `data.ship_state_str`   | string | 退货物流状态中文名                                                                                                              |
| `data.sku_id`           | string | 商品规格 ID (取 `goods_list` 第一个商品)                                                                                         |
| `data.sku_info`         | string | 商品规格信息 (取 `goods_list` 第一个商品)                                                                                         |
| `data.state`            | int    | 售后状态 (枚举值见 `获取售后订单列表` API 文档)                                                                                      |
| `data.state_invalid_time`| string | 状态失效时间 (格式: YYYY-MM-DD HH:MM:SS)                                                                                      |
| `data.state_reason`     | string | 状态原因                                                                                                                      |
| `data.state_str`        | int/string | 售后状态中文名或代码 (示例中为数字 4，但通常应为字符串)                                                                               |
| `data.study_time`       | string/null | 学习时长 (格式或单位未知，示例为 null)                                                                                            |
| `data.submit_type`      | int    | 提交类型 (1-买家提交, 2-商家提交)                                                                                                   |
| `data.use_collection`   | int/string | 订单渠道 (无需关注，示例中为数字 2)                                                                                             |
| `data.user_id`          | string | 用户 ID                                                                                                                       |
| `data.user_name`        | string | 用户昵称                                                                                                                      |
| `data.updated_at`       | string | 最后更新时间 (格式: YYYY-MM-DD HH:MM:SS)                                                                                      |

**`goods_list` 商品结构**

| 参数名            | 类型     | 说明            |
| ---------------- | ------ | --------------- |
| `buy_num`        | int    | 购买数量        |
| `goods_name`     | string | 商品名          |
| `goods_price`    | int    | 商品价格 (单位: 分) |
| `goods_tag`      | string | 商品标签        |
| `img_url`        | string | 商品图片 URL      |
| `resource_type`  | int    | 资源类型        |
| `single_type`    | string | 无需关注        |
| `sku_info`       | string | 商品规格信息    |

**返回示例**

```json
{
    "code": 0,
    "msg": "操作成功",
    "data": {
        "actual_fee": 10, // 单位：分
        "after_sale_count": 1,
        "aftersale_id": "A1676256272_63e9a41000b74_73803812",
        "apply_channel": "xiaoe",
        "apply_refund_money": 10, // 单位：分
        "certificate": [],
        "created_at": "2023-02-13 10:44:32",
        "distribution_amount": 0, // 单位：分
        "freight": 0, // 单位：分
        "goods_list": [
            {
                "buy_num": 1,
                "goods_name": "专栏1",
                "goods_price": 10, // 单位：分
                "goods_tag": "专栏",
                "img_url": "https://commonresource-125xxxxxxx.cdn.xiaoeknow.com/image/lbyxhhvyxxxx.png",
                "resource_type": 6,
                "single_type": "0",
                "sku_info": "--"
            },
            {
                "buy_num": 1,
                "goods_name": "测试图文重复采集210",
                "goods_price": 2, // 单位：分
                "goods_tag": "图文",
                "img_url": "https://commonresource-125xxxxxxx.cdn.xiaoeknow.com/image/lbyxhhvyxxxx.png",
                "resource_type": 1,
                "single_type": "1",
                "sku_info": "--"
            },
            {
                "buy_num": 1,
                "goods_name": "测试图文重复采集210永久有效)",
                "goods_price": 2, // 单位：分
                "goods_tag": "图文",
                "img_url": "https://commonresource-125xxxxxxx.cdn.xiaoeknow.com/image/lbyxhhvyxxxx.png",
                "resource_type": 1,
                "single_type": "1",
                "sku_info": "--"
            }
        ],
        "goods_name": "专栏1", // 取 goods_list[0]
        "img_url": "https://commonresource-125xxxxxxx.cdn.xiaoeknow.com/image/lbyxhhvyxxxx.png", // 取 goods_list[0]
        "invalid_time": "2023-02-20 10:44:32",
        "merchant_remark": "测试",
        "order_id": "o_1676256216_63e9a3d8f402e_31056719",
        "original_price": 10, // 单位：分
        "payment_amount": 0, // 单位：分
        "phone": "18566321640",
        "prompt_state": 0,
        "reason": "",
        "refund_money": 0, // 单位：分
        "remark": "测试",
        "resource_type": 6, // 取 goods_list[0]
        "sale_type": 1,
        "ship_state": 0,
        "ship_state_str": "无需发货",
        "sku_id": "SKU_SPC_6760233267270JdBCs10", // 取 goods_list[0]
        "sku_info": "--", // 取 goods_list[0]
        "state": 4,
        "state_invalid_time": "-0001-11-30 00:00:00",
        "state_reason": "商家已拒绝售后申请",
        "state_str": 4, // 注意：示例中为数字，文档通常应为字符串
        "study_time": null,
        "submit_type": 1,
        "use_collection": 2,
        "user_id": "u_5dae9dd91d9b4_Vw2uqLs5w0",
        "user_name": "更新资料",
        "updated_at": "2023-02-13 10:44:32" // 文档中描述但示例未出现，根据结构补充
    }
}
```

**注意:**

*   所有涉及金额的字段单位均为 **分**。
*   返回参数 `data.state_str` 在示例中是数字 `4`，但根据字段名推断，通常应为对应的状态中文名，如 "售后关闭" 或 "商家拒绝"。这可能是示例数据的问题。
*   `data.goods_name`, `data.img_url`, `data.resource_type`, `data.sku_id`, `data.sku_info` 这些字段的值通常取自 `data.goods_list` 中的第一个商品信息。
*   返回参数 `data.updated_at` 在参数说明中有，但在返回示例中缺失，已在结构说明中补充。
*   `payment_amount` 字段的含义需要结合业务场景与 `actual_fee` 进行区分。