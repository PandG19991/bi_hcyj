# 小鹅通 API 文档：获取订单列表 2.0

**接口名称:** 获取订单列表 2.0

**接口地址:** `/xe.ecommerce.order.list/1.0.0`

**请求方式:** `POST`

**请求头:** `Content-Type:application/json`

**频率限制:** `1秒20次`


**来源:** [https://api-doc.xiaoe-tech.com/api_list/order/get_order_list_1.0.2.html]

---

## 接口说明

根据指定时间范围和筛选条件，获取订单列表信息。

---

## 请求参数

| 参数名               | 必选 | 类型     | 说明                                                                                                                                   |
| -------------------- | ---- | -------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `access_token`       | 是   | string   | 专属 token                                                                                                                             |
| `page`               | 否   | int      | 页码，默认为 1                                                                                                                         |
| `page_size`          | 否   | int      | 每页数量，默认为 10，最大值为 50                                                                                                       |
| `search_type`        | 是   | int      | 搜索时间类型：1-按订单创建时间搜索，2-按订单支付时间搜索，3-按订单更新时间搜索（更新订单状态/物流/售后状态等），4-按售后状态更新时间搜索 |
| `start_time`         | 是   | string   | 开始时间，格式：`YYYY-MM-DD HH:mm:ss`                                                                                                    |
| `end_time`           | 是   | string   | 结束时间，格式：`YYYY-MM-DD HH:mm:ss`                                                                                                    |
| `order_id`           | 否   | string   | 订单ID，支持单个查询                                                                                                                   |
| `pay_state`          | 否   | int      | 支付状态：0-未支付，1-已支付                                                                                                           |
| `order_state`        | 否   | int      | 订单状态：0-待付款，1-待成交(或支付成功)，2-待发货，3-已发货，4-已完成，5-已关闭                                                            |
| `aftersale_show_state`| 否   | int      | 售后状态：0-无，1-处理中，2-部分退款，3-全部退款                                                                                       |
| `resource_type`      | 否   | int      | 商品类型 (具体值参考小鹅通文档)                                                                                                         |
| `user_id`            | 否   | string   | 用户 ID                                                                                                                                |
| `phone_number`       | 否   | string   | 用户手机号                                                                                                                             |
| `search_key`         | 否   | string   | 搜索关键词（订单ID、商品名称、用户ID、手机号）                                                                                           |
| `pay_type`           | 否   | int      | 支付方式 (具体值参考小鹅通文档)                                                                                                         |
| `order_type`         | 否   | int      | 订单类型：1-普通订单，2-导入订单，3-渠道订单                                                                                           |
| `source`             | 否   | int      | 下单终端类型                                                                                                                           |
| `has_refund_order`   | 否   | boolean  | 是否查询售后列表                                                                                                                       |
| `channel_type`       | 否   | int      | 渠道类型：0-商详页，1-直播间，2-广告渠道                                                                                               |
| `order_spu_sub_type` | 否   | string   | 商品二级类型                                                                                                                           |
| `goods_spu_type`     | 否   | int      | 商品一级类型：0-知识商品，1-实物商品，2-服务类商品，3-打赏，4-红包                                                                     |
| `check_state`        | 否   | int      | 核销状态：0-无，1-待核销，2-已核销，3-已失效，4-部分核销                                                                                 |
| `ship_state`         | 否   | int      | 发货状态                                                                                                                               |
| `is_deleted`         | 否   | boolean  | 是否删除：0-否，1-是                                                                                                                   |
| `settle_state`       | 否   | int      | 结算状态：0-待结算，1-结算中，2-已结算                                                                                                   |
| `relation_order_type`| 否   | int      | 关联订单类型 (具体值参考小鹅通文档)                                                                                                     |
| `distribute_type`    | 否   | int      | 分销类型 (具体值参考小鹅通文档)                                                                                                         |
| `activity_type`      | 否   | int      | 活动类型 (具体值参考小鹅通文档)                                                                                                         |
| `fields`             | 否   | string[] | 指定返回字段列表 (可选，不传默认返回所有字段)                                                                                          |

**注意:**
*   `start_time` 和 `end_time` 跨度不能超过 7 天。
*   使用 `search_key` 时，其他筛选条件（除分页和时间外）会被忽略。

---

## 请求示例

```json
{
    "access_token": "xe_xxxxxx",
    "page": 1,
    "page_size": 10,
    "search_type": 1,
    "start_time": "2022-11-14 00:00:00",
    "end_time": "2022-11-15 23:59:59",
    "order_state": 4
}
```

---

## 响应参数

### 顶层结构

| 参数名      | 类型   | 说明                               |
| ----------- | ------ | ---------------------------------- |
| `code`      | int    | 请求结果码 (0表示成功)             |
| `msg`       | string | 描述信息                           |
| `data`      | object | 数据主体 (详见下文)                |

### `data` 对象详解

| 参数名      | 类型     | 说明                                  |
| ----------- | -------- | ------------------------------------- |
| `list`      | array    | 订单列表 (每个元素结构见下文)         |
| `page`      | int      | 当前页码                            |
| `page_size` | int      | 每页数量                            |
| `total`     | int      | 总订单数                            |

### `data.list[]` 订单对象结构

每个订单对象包含以下子对象：

*   `buyer_info`: 买家信息 (结构见下)
*   `goods_info`: 商品信息 (结构见下)
*   `order_info`: 订单核心信息 (结构见下)
*   `payment_info`: 支付信息 (结构见下)
*   `price_info`: 价格信息 (结构见下)
*   `ship_info`: 物流信息 (结构见下)

#### `list[].buyer_info`

| 参数名                | 类型   | 说明           |
| --------------------- | ------ | -------------- |
| `user_comment`        | string | 用户留言       |
| `user_id`             | string | 用户 ID        |
| `user_nickname`       | string | 用户昵称       |
| `user_phone`          | string | 用户手机号     |
| `user_profile_avatar` | string | 用户头像 URL   |

#### `list[].goods_info`

| 参数名       | 类型     | 说明                       |
| ------------ | -------- | -------------------------- |
| `goods_list` | array    | 商品列表 (结构见下文)      |

##### `goods_info.goods_list[]` 结构

| 参数名                     | 类型   | 说明                                      |
| -------------------------- | ------ | ----------------------------------------- |
| `actual_fee`               | int    | 商品实付金额，单位：分                    |
| `app_id`                   | string | 店铺 ID                                   |
| `check_state`              | int    | 核销状态 (具体值参考小鹅通文档)           |
| `check_state_desc`         | string | 核销状态描述                              |
| `discount_amount`          | int    | 商品优惠金额，单位：分                    |
| `discount_detail`          | array  | 优惠详情列表 (结构见下文)                 |
| `expire_desc`              | string | 有效期描述                                |
| `expire_end`               | string | 有效期结束时间                            |
| `expire_start`             | string | 有效期开始时间                            |
| `goods_desc`               | string | 商品描述                                  |
| `goods_image`              | string | 商品图片 URL                              |
| `goods_name`               | string | 商品名称                                  |
| `goods_sn`                 | string | 商品编码                                  |
| `goods_spec_desc`          | string | 商品规格描述                              |
| `period_type`              | int    | 有效期类型 (具体值参考小鹅通文档)         |
| `refund_state`             | int    | 退款状态 (具体值参考小鹅通文档)           |
| `refund_state_desc`        | string | 退款状态描述                              |
| `relation_goods_id`        | string | 关联商品 ID                               |
| `relation_goods_type`      | int    | 关联商品类型 (具体值参考小鹅通文档)       |
| `relation_goods_type_desc` | string | 关联商品类型描述                          |
| `resource_id`              | string | 资源 ID                                   |
| `resource_type`            | int    | 资源类型 (具体值参考小鹅通文档)           |
| `ship_state`               | int    | 发货状态 (-1: 已发货, 其他值参考文档)     |
| `ship_state_desc`          | string | 发货状态描述                              |
| `sku_id`                   | string | SKU ID                                    |
| `sku_spec_code`            | string | SKU 规格编码                              |
| `spu_id`                   | string | SPU ID (商品 ID)                          |
| `spu_type`                 | string | SPU 类型 (e.g., "CMN", "ITX", "VDO"等)    |
| `total_price`              | int    | 商品总价（单价 * 数量），单位：分         |
| `unit_price`               | int    | 商品单价，单位：分                        |

###### `goods_list[].discount_detail[]` 结构

| 参数名          | 类型   | 说明           |
| --------------- | ------ | -------------- |
| `discount_desc` | string | 优惠描述       |
| `discount_id`   | string | 优惠 ID        |
| `discount_name` | string | 优惠名称       |
| `discount_price`| int    | 优惠金额，单位：分 |
| `discount_type` | string | 优惠类型       |

#### `list[].order_info`

| 参数名                      | 类型     | 说明                                              |
| --------------------------- | -------- | ------------------------------------------------- |
| `actual_fee`                | int      | 订单实付金额，单位：分                            |
| `aftersale_show_state`      | int      | 售后状态 (具体值参考小鹅通文档)                   |
| `aftersale_show_state_time` | string   | 售后状态更新时间                                  |
| `app_id`                    | string   | 店铺 ID                                           |
| `channel_bus_id`            | string   | 渠道业务 ID                                       |
| `channel_type`              | int      | 渠道类型 (具体值参考小鹅通文档)                   |
| `check_state`               | int      | 核销状态 (具体值参考小鹅通文档)                   |
| `deduct_amount`             | int      | 抵扣金额，单位：分                                |
| `discount_amount`           | int      | 订单优惠金额，单位：分                            |
| `freight_actual_price`      | int      | 运费实付金额，单位：分                            |
| `freight_original_price`    | int      | 运费原始金额，单位：分                            |
| `goods_buy_num`             | int      | 商品购买数量                                      |
| `goods_name`                | string   | 商品名称 (可能包含多个商品)                       |
| `goods_original_total_price`| int      | 商品原始总价，单位：分                            |
| `goods_spu_sub_type`        | string   | 商品二级类型                                      |
| `goods_spu_type`            | int      | 商品一级类型 (具体值参考小鹅通文档)               |
| `modified_amount`           | int      | 改价金额，单位：分                                |
| `order_close_type`          | int      | 订单关闭类型 (具体值参考小鹅通文档)               |
| `order_id`                  | string   | 订单 ID                                           |
| `order_state`               | int      | 订单状态 (具体值参考小鹅通文档)                   |
| `order_state_time`          | string   | 订单状态更新时间                                  |
| `order_type`                | int      | 订单类型 (具体值参考小鹅通文档)                   |
| `pay_state`                 | int      | 支付状态 (具体值参考小鹅通文档)                   |
| `pay_state_time`            | string   | 支付状态更新时间 (支付时间)                       |
| `pay_type`                  | int      | 支付方式 (具体值参考小鹅通文档)                   |
| `distribute_type_bitmap`    | array[int]| 分销类型位图                                      |
| `activity_type_bitmap`      | array[int]| 活动类型位图                                      |
| `relation_order_type`       | int      | 关联订单类型 (具体值参考小鹅通文档)               |
| `relation_order_id`         | string   | 关联订单 ID                                       |
| `relation_order_appid`      | string   | 关联订单店铺 ID                                   |
| `refund_fee`                | int      | 退款金额，单位：分                                |
| `refund_time`               | string   | 退款时间                                          |
| `settle_state`              | int      | 结算状态 (具体值参考小鹅通文档)                   |
| `settle_state_time`         | string   | 结算状态更新时间                                  |
| `share_type`                | int      | 分享类型 (具体值参考小鹅通文档)                   |
| `share_user_id`             | string   | 分享者用户 ID                                     |
| `ship_way_choose_type`      | int      | 配送方式选择类型 (具体值参考小鹅通文档)           |
| `sub_order_type`            | int      | 子订单类型 (具体值参考小鹅通文档)                 |
| `trade_id`                  | string   | 交易 ID (通常与 order_id 相同)                    |
| `update_time`               | string   | 订单更新时间                                      |
| `use_collection`            | int      | 是否使用信息采集 (-1: 未知, 其他值参考文档)       |
| `user_id`                   | string   | 用户 ID                                           |
| `wx_app_type`               | int      | 微信应用类型 (具体值参考小鹅通文档)               |

#### `list[].payment_info`

| 参数名         | 类型   | 说明           |
| -------------- | ------ | -------------- |
| `out_order_id` | string | 商户订单号     |
| `third_order_id`| string | 第三方支付订单号 |

#### `list[].price_info`

| 参数名                  | 类型   | 说明                         |
| ----------------------- | ------ | ---------------------------- |
| `actual_price`          | int    | 订单实付总额，单位：分       |
| `freight_modified_price`| int    | 运费改价金额，单位：分       |
| `freight_price`         | int    | 运费金额，单位：分           |
| `origin_price`          | int    | 订单原始总额，单位：分       |
| `total_modified_amount` | int    | 订单总改价金额，单位：分     |
| `total_price`           | int    | 商品总价（含运费），单位：分 |

#### `list[].ship_info`

| 参数名       | 类型   | 说明               |
| ------------ | ------ | ------------------ |
| `city`       | string | 城市               |
| `company`    | string | 物流公司           |
| `confirm_time`| string | 确认收货时间       |
| `county`     | string | 区/县              |
| `detail`     | string | 详细地址           |
| `express_id` | string | 物流单号           |
| `invalid_time`| string | 失效时间 (?)       |
| `phone`      | string | 收货人手机号 (脱敏) |
| `province`   | string | 省份               |
| `receiver`   | string | 收货人姓名 (脱敏) |
| `remark`     | string | 备注               |
| `ship_time`  | string | 发货时间           |
| `user_id`    | string | 收货信息关联用户ID |

---

## 返回示例

```json
{
    "code": 0,
    "msg": "Success",
    "data": {
        "list": [
            {
                "buyer_info": {
                    "user_comment": "",
                    "user_id": "u_60eea4e553c5a_7B28NjQ8Nq",
                    "user_nickname": "用户昵称",
                    "user_phone": "156****1234",
                    "user_profile_avatar": ""
                },
                "goods_info": {
                    "goods_list": [
                        {
                            "actual_fee": 0,
                            "app_id": "appAKLWLitn7978",
                            "check_state": 0,
                            "check_state_desc": "--",
                            "discount_amount": 1,
                            "discount_detail": [
                                {
                                    "discount_desc": "满减",
                                    "discount_id": "cu_63713825c0492_89IFD4WJ",
                                    "discount_name": "0.01优惠券",
                                    "discount_price": 1,
                                    "discount_type": "店铺优惠券"
                                }
                            ],
                            "expire_desc": "--",
                            "expire_end": "--",
                            "expire_start": "--",
                            "goods_desc": "",
                            "goods_image": "https://wechatapppro-12525xxxxxx.file.myqcloud.com/appAKLWLitnxxxx/image/158813b5eb7802e5b155530cc9977470.png",
                            "goods_name": "超级付费2333",
                            "goods_sn": "--",
                            "goods_spec_desc": "规格:111天",
                            "period_type": 0,
                            "refund_state": 0,
                            "refund_state_desc": "--",
                            "relation_goods_id": "",
                            "relation_goods_type": 0,
                            "relation_goods_type_desc": "",
                            "resource_id": "c_6369fed39f345_iNuZIC4B3467",
                            "resource_type": 7,
                            "ship_state": -1,
                            "ship_state_desc": "已发货",
                            "sku_id": "SKU_CMN_66789089929556KUQJ11",
                            "sku_spec_code": "",
                            "spu_id": "c_6369fed39f345_iNuZIC4B3467",
                            "spu_type": "CMN",
                            "total_price": 2,
                            "unit_price": 2
                        }
                    ]
                },
                "order_info": {
                    "actual_fee": 0,
                    "aftersale_show_state": 0,
                    "aftersale_show_state_time": "0000-00-00 00:00:00",
                    "app_id": "appAKLWLitn7978",
                    "channel_bus_id": "",
                    "channel_type": 0,
                    "check_state": 0,
                    "deduct_amount": 0,
                    "discount_amount": 2, // 注意：示例中商品优惠金额与订单优惠金额可能不一致
                    "freight_actual_price": 0,
                    "freight_original_price": 0,
                    "goods_buy_num": 1,
                    "goods_name": "超级付费2333",
                    "goods_original_total_price": 2,
                    "goods_spu_sub_type": "CMN",
                    "goods_spu_type": 0,
                    "modified_amount": 0,
                    "order_close_type": 0,
                    "order_id": "o_1668364330_6371382a9cba9_33409596",
                    "order_state": 4,
                    "order_state_time": "2022-11-15 02:34:02",
                    "order_type": 1,
                    "pay_state": 1,
                    "pay_state_time": "2022-11-14 02:32:11", // 支付时间
                    "pay_type": -1, // -1 可能表示未知或非标准支付方式
                    "distribute_type_bitmap":null,
                    "activity_type_bitmap":[1,5],
                    "relation_order_type":0,
                    "relation_order_id":"",
                    "relation_order_appid":"",
                    "refund_fee": 0,
                    "refund_time": "0000-00-00 00:00:00",
                    "settle_state": 2,
                    "settle_state_time": "2022-11-14 02:32:11",
                    "share_type": 5,
                    "share_user_id": "u_60eea4e553c5a_7B28NjQ8Nq",
                    "ship_way_choose_type": 0,
                    "sub_order_type": 0,
                    "trade_id": "o_1668364330_6371382a9cba9_33409596",
                    "update_time": "2022-11-15 02:34:02", // 订单更新时间
                    "use_collection": -1,
                    "user_id": "u_60eea4e553c5a_7B28NjQ8Nq",
                    "wx_app_type": 5
                },
                "payment_info": {
                    "out_order_id": "",
                    "third_order_id": ""
                },
                "price_info": {
                    "actual_price": 0,
                    "freight_modified_price": 0,
                    "freight_price": 0,
                    "origin_price": 2,
                    "total_modified_amount": 0,
                    "total_price": 2 // 商品总价（含运费）
                },
                "ship_info": {
                    "city": "深圳市",
                    "company": "",
                    "confirm_time": "0000-00-00 00:00:00",
                    "county": "南山区",
                    "detail": "科兴科学园A2栋9楼",
                    "express_id": "",
                    "invalid_time": "0000-00-00 00:00:00",
                    "phone": "1565791****",
                    "province": "广东省",
                    "receiver": "朱*农",
                    "remark": "",
                    "ship_time": "0000-00-00 00:00:00", // 发货时间
                    "user_id": "u_6139c8c051bb9_pU4WzQFuyR"
                }
            }
        ],
        "page": 1,
        "page_size": 1,
        "total": 17
    }
}
``` 