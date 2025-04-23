# 获取售后订单列表 (xe.aftersale.list/1.0.0)

获取店铺的售后订单列表信息。

**请求方式及 URL**

*   **请求方式:** `POST`
*   **请求头:** `Content-Type: application/json`
*   **接口地址:** `https://api.xiaoe-tech.com/xe.aftersale.list/1.0.0`
*   **频率限制:** `10秒500次`

**请求参数**

| 参数名                  | 必选 | 类型     | 说明                                                                                                                            |
| -------------------- | -- | ------ | ------------------------------------------------------------------------------------------------------------------------------- |
| `access_token`       | 是  | string | [专属token](../get_access_token.html)                                                                                             |
| `data.page_index`    | 是  | int    | 当前页数，从1开始                                                                                                                 |
| `data.page_size`     | 是  | int    | 每页个数，最大支持50                                                                                                              |
| `data.aftersale_id`  | 否  | string | 售后单号                                                                                                                          |
| `data.created_at_start`| 否  | string | 售后单创建开始时间 (格式: YYYY-MM-DD HH:MM:SS)                                                                                    |
| `data.created_at_end`  | 否  | string | 售后单创建结束时间 (格式: YYYY-MM-DD HH:MM:SS)                                                                                    |
| `data.updated_at_start`| 否  | string | 售后单更新开始时间 (格式: YYYY-MM-DD HH:MM:SS)                                                                                    |
| `data.updated_at_end`  | 否  | string | 售后单更新结束时间 (格式: YYYY-MM-DD HH:MM:SS)                                                                                    |
| `data.goods_name`    | 否  | string | 商品名称                                                                                                                          |
| `data.order_id`      | 否  | string | 父订单号                                                                                                                          |
| `data.nick_name`     | 否  | string | 买家昵称                                                                                                                          |
| `data.ship_state`    | 否  | int    | 退货物流状态 (0-无需发货, 1-待买家发货, 2-买家已发货, 3-商家已收货, 4-商家未收货)                                                                       |
| `data.state`         | 否  | int    | 售后状态 (1-待商家处理, 2-待买家处理, 3-待平台处理, 10-售后关闭, 11-售后中, 12-售后取消, 13-售后成功, 14-待买家补充凭证, 15-商家拒绝, 16-仲裁拒绝, 17-仲裁通过) |
| `data.sale_type`     | 否  | int    | 售后方式 (1-仅退款, 2-退款退货)                                                                                                         |

**请求示例**

```json
{
    "access_token": "YOUR_ACCESS_TOKEN",
    "data": {
        "page_index": 1,
        "page_size": 10
    }
}
```

**返回参数**

| 参数名           | 类型     | 说明             |
| ------------- | ------ | ---------------- |
| `code`        | int    | 状态码 (0 表示成功)   |
| `msg`         | string | 返回消息         |
| `data`        | object | 数据对象         |
| `data.list`   | array  | 售后订单列表     |
| `data.row_count`| int    | 符合条件的总记录数 |

**`data.list` 售后订单结构**

| 参数名                  | 类型     | 说明                                                                                                                       |
| ----------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------- |
| `actual_fee`            | int    | 订单实际支付金额 (单位: 分)                                                                                                        |
| `aftersale_id`          | string | 售后单号                                                                                                                     |
| `apply_refund_money`    | int    | 申请退款金额 (单位: 分)                                                                                                        |
| `created_at`            | string | 创建时间 (格式: YYYY-MM-DD HH:MM:SS)                                                                                         |
| `goods_list`            | array  | 商品列表                                                                                                                     |
| `goods_name`            | string | 商品名称 (取 `goods_list` 第一个商品)                                                                                             |
| `img_url`               | string | 商品图片 URL (取 `goods_list` 第一个商品)                                                                                         |
| `invalid_time`          | string | 售后单失效时间 (格式: YYYY-MM-DD HH:MM:SS)                                                                                     |
| `nick_name`             | string | 买家昵称                                                                                                                     |
| `order_id`              | string | 父订单号                                                                                                                     |
| `original_price`        | int    | 订单原价 (单位: 分)                                                                                                          |
| `reason`                | string | 买家申请售后原因                                                                                                                 |
| `refund_money`          | int    | 实际退款金额 (单位: 分)                                                                                                        |
| `resource_type_str`     | string | 资源类型中文名                                                                                                                 |
| `sale_type_name`        | string | 售后方式中文名 (退款/退款退货)                                                                                                       |
| `ship_state_str`        | string | 退货物流状态中文名                                                                                                               |
| `sku_info`              | string | 商品规格信息 (取 `goods_list` 第一个商品)                                                                                         |
| `state`                 | int    | 售后状态 (枚举值见请求参数说明)                                                                                                    |
| `state_invalid_time`    | string | 状态失效时间 (格式: YYYY-MM-DD HH:MM:SS)                                                                                     |
| `state_reason`          | string | 状态原因                                                                                                                     |
| `state_str`             | string | 售后状态中文名                                                                                                                 |
| `updated_at`            | string | 最后更新时间 (格式: YYYY-MM-DD HH:MM:SS)                                                                                     |
| `use_collection`        | int    | 订单渠道 (无需关注)                                                                                                            |
| `wx_avatar`             | string | 微信头像 URL                                                                                                                 |
| `remark`                | string | 买家售后备注 (文档中描述但示例未出现)                                                                                               |
| `merchant_remark`       | string | 商家售后备注 (文档中描述但示例未出现)                                                                                               |
| `sku_id`                | string | 商品规格 ID (文档中描述但示例未出现)                                                                                             |

**`goods_list` 商品结构**

| 参数名            | 类型     | 说明            |
| ---------------- | ------ | --------------- |
| `buy_num`        | int    | 购买数量        |
| `goods_name`     | string | 商品名          |
| `goods_price`    | int    | 商品价格 (单位: 分) |
| `goods_tag`      | string | 商品标签        |
| `img_url`        | string | 商品图片 URL      |
| `resource_type`  | int    | 资源类型 (无需关注) |
| `single_type`    | int    | 无需关注        |
| `sku_info`       | string | 商品规格信息    |

**返回示例**

```json
{
    "code": 0,
    "msg": "操作成功",
    "data": {
        "list": [
            {
                "actual_fee": 0,
                "aftersale_id": "A1676284458_63ea122a379c4_84723683",
                "apply_refund_money": 0,
                "created_at": "2023-02-13 18:34:18",
                "goods_list": [
                    {
                        "buy_num": 1,
                        "goods_name": "HX付费图文关联作业",
                        "goods_price": 20, // 单位：分
                        "goods_tag": "图文",
                        "img_url": "https://commonresource-1252xxxxxxx.cdn.xiaoeknow.com/image/lbyxhhvqxxxx.png",
                        "resource_type": 1, // 示例中无此字段，根据文档补充
                        "single_type": 0,
                        "sku_info": null
                    }
                ],
                "goods_name": "HX付费图文关联作业",
                "img_url": "https://commonresource-1252xxxxxxx.cdn.xiaoeknow.com/image/lbyxhhvqxxxx.png",
                "invalid_time": "2023-02-20 18:34:18",
                "nick_name": "大肉丸xxxx",
                "order_id": "o_1676284286_63ea117e2d99c_5057xxxx",
                "original_price": 20, // 单位：分
                "reason": "",
                "refund_money": 0, // 单位：分
                "resource_type_str": "图文",
                "sale_type_name": "退款",
                "ship_state_str": "无需发货",
                "sku_info": "--", // 对应 goods_list[0].sku_info
                "state": 13,
                "state_invalid_time": "-0001-11-30 00:00:00",
                "state_reason": "商家主动发起售后",
                "state_str": "售后成功",
                "updated_at": "2023-02-13 18:34:18",
                "use_collection": 0,
                "wx_avatar": "http://wechatavator-125252xxxx.file.myqcloud.com/appAKLWLitnxxxx/image/compress/u_609f80e83277a_WXyxi4xxxx.png"
            }
            // ... more aftersale orders
        ],
        "row_count": 37
    }
}
```

**注意:**

*   所有涉及金额的字段（如 `actual_fee`, `apply_refund_money`, `original_price`, `refund_money`, `goods_list.goods_price`）单位均为 **分**。
*   部分在参数说明中列出的字段（如 `remark`, `merchant_remark`, `sku_id`）在返回示例中未出现，已在结构说明中注明。
*   `goods_list` 结构中的 `resource_type` 字段在示例中未出现，但存在于参数说明中。