# 获取售后订单列表 (xe.ecommerce.after_sale.list/1.0.0)

用于查询店铺的售后订单列表。

## 基本信息

*   **接口地址:** `https://api.xiaoe-tech.com/xe.ecommerce.after_sale.list/1.0.0`
*   **请求方式:** `POST`
*   **请求头:** `Content-Type: application/json`
*   **频率限制:** 1分钟 300次
*   **权限要求:** 订单管理-查询

## 请求参数

| 参数名            | 必选 | 类型   | 说明                                                                                                                                                                                                                                                           |
| :---------------- | :--- | :----- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `access_token`    | 是   | string | 专属token                                                                                                                                                                                                                                                      |
| `page_size`       | 是   | int    | 每页条数                                                                                                                                                                                                                                                       |
| `page_index`      | 是   | int    | 页码 (从 1 开始?)                                                                                                                                                                                                                                               |
| `created_at`      | 是   | string | **时间筛选字段，与 `date_type` 搭配使用。** 格式为 `YYYY-MM-DD||YYYY-MM-DD`，表示起始日期和结束日期，使用 `||` 分隔。                                                                                                                                                 |
| `phone`           | 否   | string | 买家手机号                                                                                                                                                                                                                                                     |
| `ship_receiver`   | 否   | string | 收货人姓名                                                                                                                                                                                                                                                     |
| `ship_phone`      | 否   | string | 收货人手机号                                                                                                                                                                                                                                                   |
| `purchase_name`   | 否   | string | 商品名称                                                                                                                                                                                                                                                       |
| `nick_name`       | 否   | string | 买家昵称                                                                                                                                                                                                                                                       |
| `order_id`        | 否   | string | 订单号                                                                                                                                                                                                                                                         |
| `transaction_id`  | 否   | string | 交易单号 (支付交易号)                                                                                                                                                                                                                                            |
| `out_order_id`    | 否   | string | 商户单号                                                                                                                                                                                                                                                       |
| `aftersale_id`    | 否   | string | 售后单号                                                                                                                                                                                                                                                       |
| `order_user_id`   | 否   | string | 用户ID                                                                                                                                                                                                                                                         |
| `sales_state`     | 否   | int    | 售后状态: -1:全部, 1:待商家处理, 2:售后成功, 6:售后中, 3:已撤销                                                                                                                                                                                                   |
| `date_type`       | 否   | string | **指定 `created_at` 筛选和排序依据的日期字段。** 可选值: `created_at` (售后单创建时间), `updated_at` (售后单更新时间), `refund_time` (售后单退款时间), `apply_time` (售后单申请时间) - **注意:** 文档描述为 `created_at` 字段，但实际可能是 `apply_time`？需确认 |

## 请求示例

```json
{
    "access_token":"xxxxx",
    "page_size": 10,
    "page_index": 1,
    "created_at": "2023-01-14||2023-02-13", // 筛选 2023-01-14 到 2023-02-13 之间的数据
    "date_type": "updated_at" // 基于更新时间筛选
}
```

## 返回参数

| 参数名        | 类型   | 说明             |
| :------------ | :----- | :--------------- |
| `code`        | int    | 请求结果码 (0 表示成功) |
| `msg`         | string | 描述信息         |
| `data`        | object | 数据对象         |
| `data.list`   | array  | 售后订单列表 (详见下文) |
| `data.row_count`| int   | 售后订单总数     |

### 售后订单列表项 (`data.list[]`)

| 参数名             | 类型   | 说明                                                                                                                                                                                                                                                                                                 |
| :----------------- | :----- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `aftersale_id`     | string | 售后单号                                                                                                                                                                                                                                                                                             |
| `order_id`         | string | 订单号                                                                                                                                                                                                                                                                                               |
| `nick_name`        | string | 用户昵称                                                                                                                                                                                                                                                                                             |
| `wx_avatar`        | string | 微信头像                                                                                                                                                                                                                                                                                             |
| `state`            | int    | 售后状态: `0`:未受理,`1`:用户取消,`2`:商家受理中,`3`:商家逾期未处理,`4`:商家拒绝退款,`5`:商家拒绝退货退款,`6`:待买家退货,`7`:退货退款关闭,`8`:待商家收货,`11`:商家退款中,`12`:商家逾期未退款,`13`:退款完成,`14`:退货退款完成,`15`:换货完成,`16`:待商家发货,`17`:待用户确认收货,`18`:商家拒绝换货,`19`:商家已收到货 |
| `state_str`        | string | 售后状态中文名                                                                                                                                                                                                                                                                                       |
| `sale_type`        | int    | 售后方式: 1-仅退款, 2-退款退货                                                                                                                                                                                                                                                                         |
| `sale_type_name`   | string | 售后类型名称 (例如: "退款")                                                                                                                                                                                                                                                                           |
| `apply_refund_money`| int   | 申请退款金额 (分)                                                                                                                                                                                                                                                                                    |
| `refund_money`     | int    | 商家实际退款金额 (分)                                                                                                                                                                                                                                                                                |
| `reason`           | string | 售后原因                                                                                                                                                                                                                                                                                             |
| `remark`           | string | 买家售后备注                                                                                                                                                                                                                                                                                         |
| `merchant_remark`  | string | 商家售后备注                                                                                                                                                                                                                                                                                         |
| `state_reason`     | string | 状态原因 (例如: "商家主动发起售后")                                                                                                                                                                                                                                                                    |
| `created_at`       | string | 售后单申请时间 (格式: YYYY-MM-DD HH:MM:SS)                                                                                                                                                                                                                                                             |
| `updated_at`       | string | 最后更新时间 (格式: YYYY-MM-DD HH:MM:SS)                                                                                                                                                                                                                                                             |
| `invalid_time`     | string | 申请单失效时间 (格式: YYYY-MM-DD HH:MM:SS)                                                                                                                                                                                                                                                           |
| `state_invalid_time`| string | 当前状态逾期时间 (格式: YYYY-MM-DD HH:MM:SS)                                                                                                                                                                                                                                                         |
| `goods_name`       | string | 商品名 (可能是订单中第一个商品?)                                                                                                                                                                                                                                                                      |
| `img_url`          | string | 商品图片 URL (可能是订单中第一个商品?)                                                                                                                                                                                                                                                               |
| `sku_info`         | string | 规格信息 (可能是订单中第一个商品?)                                                                                                                                                                                                                                                                      |
| `sku_id`           | string | 商品规格 ID (可能是订单中第一个商品?)                                                                                                                                                                                                                                                                 |
| `actual_fee`       | int    | 订单金额 (分)                                                                                                                                                                                                                                                                                        |
| `original_price`   | int    | 商品金额 (分) - **注意:** 这里的 `original_price` 指的是什么？是单个商品的原价还是订单商品总原价？                                                                                                                                                                                                      |
| `goods_list`       | array  | 商品列表 (详见下文)                                                                                                                                                                                                                                                                                    |
| `ship_state_str`   | string | 物流状态 (例如: "无需发货")                                                                                                                                                                                                                                                                            |
| `resource_type_str`| string | 资源类型 (文档说明无需关注)                                                                                                                                                                                                                                                                           |
| `use_collection`   | int    | 订单渠道 (文档说明无需关注)                                                                                                                                                                                                                                                                           |

#### 商品列表项 (`data.list[].goods_list[]`)

| 参数名          | 类型   | 说明         |
| :-------------- | :----- | :----------- |
| `goods_name`    | string | 商品名       |
| `img_url`       | string | 商品图片 URL |
| `buy_num`       | int    | 购买数量     |
| `goods_price`   | int    | 商品价格 (分) |
| `sku_info`      | string | 商品规格信息 |
| `goods_tag`     | string | 商品标签     |
| `resource_type` | int    | 资源类型 (文档说明无需关注) |
| `single_type`   | int    | (文档说明无需关注) |

## 返回示例

```json
{
    "code": 0,
    "msg": "操作成功",
    "data": {
        "list": [
            {
                "actual_fee": 0, // 订单金额
                "aftersale_id": "A1676284458_63ea122a379c4_84723683",
                "apply_refund_money": 0, // 申请退款金额
                "created_at": "2023-02-13 18:34:18", // 售后单申请时间
                "goods_list": [
                    {
                        "buy_num": 1,
                        "goods_name": "HX付费图文关联作业",
                        "goods_price": 20, // 商品价格 (分)
                        "goods_tag": "图文",
                        "img_url": "https://commonresource-1252xxxxxxx.cdn.xiaoeknow.com/image/lbyxhhvqxxxx.png",
                        "single_type": 0,
                        "sku_info": null // 商品规格信息
                    }
                ],
                "goods_name": "HX付费图文关联作业", // 第一个商品名?
                "img_url": "https://commonresource-1252xxxxxxx.cdn.xiaoeknow.com/image/lbyxhhvqxxxx.png", // 第一个商品图片?
                "invalid_time": "2023-02-20 18:34:18", // 申请单失效时间
                "nick_name": "大肉丸xxxx", // 用户昵称
                "order_id": "o_1676284286_63ea117e2d99c_5057xxxx",
                "original_price": 20, // 商品金额?
                "reason": "", // 售后原因
                "refund_money": 0, // 商家退款金额
                "resource_type_str": "图文", // 资源类型描述
                "sale_type_name": "退款", // 售后类型名称
                "ship_state_str": "无需发货", // 物流状态
                "sku_info": "--", // 第一个商品规格?
                "state": 13, // 售后状态: 退款完成
                "state_invalid_time": "-0001-11-30 00:00:00", // 当前状态逾期时间
                "state_reason": "商家主动发起售后", // 状态原因
                "state_str": "售后成功", // 售后状态中文名
                "updated_at": "2023-02-13 18:34:18", // 最后更新时间
                "use_collection": 0, // 订单渠道
                "wx_avatar": "http://wechatavator-125252xxxx.file.myqcloud.com/appAKLWLitnxxxx/image/compress/u_609f80e83277a_WXyxi4xxxx.png"
                // "remark": "", // 买家备注, 示例中未包含
                // "merchant_remark": "" // 商家备注, 示例中未包含
                // "sku_id": "" // 第一个商品sku_id, 示例中未包含
            }
        ],
        "row_count": 37 // 总数
    }
}