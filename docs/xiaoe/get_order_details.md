# 小鹅通 API 文档：获取订单详情 2.0

**接口名称:** 获取订单详情 2.0

**接口地址:** `/xe.ecommerce.order.detail/1.0.0`

**请求方式:** `POST`

**请求头:** `Content-Type: application/json`

**频率限制:** 1秒 20次

**权限要求:** 订单管理-查询

**来源:** [https://api-doc.xiaoe-tech.com/api_list/order/get_order_details_2.html](https://api-doc.xiaoe-tech.com/api_list/order/get_order_details_2.html) (仅供参考，实际内容来自用户提供)

---

## 请求参数

| 参数名         | 必选 | 类型   | 说明       |
| -------------- | ---- | ------ | ---------- |
| `access_token` | 是   | string | 专属 token |
| `order_id`     | 是   | string | 订单 ID    |

---

## 请求示例

```json
{
    "access_token": "xe_xxxxx",
    "order_id": "o_xxxxxx_xxxxxxx"
}
```

---

## 响应参数

### 顶层结构

| 参数名 | 类型   | 说明                |
| ------ | ------ | ------------------- |
| `code` | int    | 请求结果码 (0表示成功) |
| `msg`  | string | 描述信息            |
| `data` | object | 数据主体 (详见下文)   |

### `data` 对象详解

`data` 对象包含多个子对象，详细结构如下：

#### `data.buyer_info` (买家信息)

| 参数名                     | 类型    | 说明                         |
| -------------------------- | ------- | ---------------------------- |
| `avatar_url`               | string  | 买家头像                     |
| `comment`                  | string  | 买家留言                     |
| `has_result`               | boolean | 是否存在内容                 |
| `info_collect_phone_number`| string  | 买家信息采集手机号           |
| `nickname`                 | string  | 买家昵称                     |
| `phone_number`             | string  | 买家手机号                   |
| `user_id`                  | string  | 买家 用户ID                  |

#### `data.goods_info` (商品信息)

| 参数名                   | 类型    | 说明                   |
| ------------------------ | ------- | ---------------------- |
| `goods_list`             | array   | 商品列表 (详见下文)    |
| `has_result`             | boolean | 是否存在商品信息内容   |

##### `data.goods_info.goods_list[]` (商品列表项)

每个列表项包含以下字段：

| 参数名                             | 类型   | 说明                                                                                     |
| ---------------------------------- | ------ | ---------------------------------------------------------------------------------------- |
| `actual_fee`                       | int    | 商品实收金额，单位：分                                                                     |
| `app_id`                           | string | 店铺 ID                                                                                  |
| `check_state`                      | int    | 核销状态 (0-无 1-待核销 2-已核销 3-已失效 4-部分核销)                                     |
| `check_state_description`          | string | 核销状态描述                                                                             |
| `discounts_info`                   | object | 商品优惠信息 (详见下文)                                                                     |
| `expire_desc`                      | string | 商品有效期描述                                                                           |
| `expire_display`                   | boolean| 是否显示过期时间                                                                           |
| `expire_end`                       | string | 商品有效期结束时间                                                                         |
| `expire_start`                     | string | 商品有效期开始时间                                                                         |
| `goods_description`                | string | 商品描述                                                                                 |
| `goods_image`                      | string | 商品图片                                                                                 |
| `goods_name`                       | string | 商品名称                                                                                 |
| `goods_sn`                         | string | 商品编码                                                                                 |
| `goods_spec_description`           | string | 商品规格描述                                                                             |
| `modified_amount`                  | int    | 商品改价金额，单位：分                                                                     |
| `paid_coupon_info`                 | array  | 有价优惠券信息 (详见下文)                                                                  |
| `period_type`                      | int    | 商品有效期类型 (0-长期有效；1-具体时间前有效；2-有效期时间范围（秒）)                        |
| `quantity`                         | int    | 商品数量                                                                                 |
| `refund_amount`                    | int    | 商品退款金额，单位：分                                                                     |
| `refund_state`                     | int    | 退款状态 (0-无 1-售后中 2-部分退款 3-全额退款)                                             |
| `refund_state_description`         | string | 退款状态描述                                                                             |
| `refundable_amount`                | int    | 商品可退金额，单位：分                                                                     |
| `relation_goods_id`                | string | 关联商品 ID (order goods id)                                                             |
| `relation_goods_type`              | int    | 关联商品类型 (0-无 1-虚拟带货主商品 2-实物带货主商品 3-内容分销市场主商品 4-总分店总店商品) |
| `relation_goods_type_description`  | string | 关联商品类型描述 ("套餐商品" 或空)                                                       |
| `remain_count`                     | int    | 剩余核销次数                                                                             |
| `ship_state`                       | int    | 发货状态                                                                                 |
| `ship_state_description`           | string | 发货状态描述                                                                             |
| `sku_id`                           | string | 规格 ID                                                                                  |
| `sku_spec_code`                    | string | 规格编码                                                                                 |
| `spec_value`                       | string | 商品规格附加值 (暂时只有 OLC 线下课需要返回值)                                               |
| `spu_id`                           | string | 商品 ID                                                                                  |
| `spu_type`                         | string | 商品一级类型 (0-知识商品 1-实物商品 2-服务类商品 3-打赏 4-红包 5-知识/实物商品)              |
| `spu_type_description`             | string | 商品类型描述                                                                             |
| `sub_total`                        | int    | 商品小计（实付金额 - 改价金额），单位：分                                                     |
| `tag_description`                  | string | 商品标签描述                                                                             |
| `unit_price`                       | int    | 商品单价，单位：分                                                                         |
| `vs_commission`                    | int    | 视频号小店主播佣金，单位：分                                                               |
| `vs_nick_name`                     | string | 视频号小店主播昵称                                                                         |
| `vs_platform_fee`                  | int    | 视频号小店平台服务费，单位：分                                                             |

###### `goods_list[].discounts_info` 结构

| 参数名                           | 类型    | 说明                       |
| -------------------------------- | ------- | -------------------------- |
| `coupons_list`                   | array   | 优惠券列表 (结构见下)      |
| `discounts_list`                 | array   | 优惠列表 (结构见下)        |
| `multi_coupons_usage`            | boolean | 是否多张优惠券叠加使用     |
| `no_coupon_list`                 | array   | 不包含优惠券的优惠列表 (结构见下) |
| `total_coupons_discount_amount`  | int     | 优惠券总金额，单位：分     |

*   `coupons_list[]`, `discounts_list[]`, `no_coupon_list[]` 列表项结构：

    | 参数名                         | 类型   | 说明             |
    | ------------------------------ | ------ | ---------------- |
    | `discount_amount`              | int    | 优惠金额，单位：分 |
    | `discount_name`                | string | 优惠名称         |
    | `discount_sub_type`            | int    | 二级优惠类型     |
    | `discount_sub_type_description`| string | 二级优惠类型描述 |

###### `goods_list[].paid_coupon_info[]` 结构

| 参数名          | 类型   | 说明                                      |
| --------------- | ------ | ----------------------------------------- |
| `app_id`        | array  | 店铺id (文档写array? 疑为string)           |
| `coupon_code`   | string | 有价优惠券code                            |
| `coupon_password`| string | 有价优惠券卡密                            |
| `goods_id`      | string | 商品id                                    |
| `order_id`      | string | 订单id                                    |
| `receive_at`    | string | 领取时间                                  |
| `stat`          | int    | 状态 (2表示领取)                          |
| `user_id`       | string | 领取用户                                  |

#### `data.internal_extra_info` (内部额外信息)

包含多个子对象，例如：

*   `after_sale_info`: 售后信息
*   `consignee_info`: 收货信息
*   `content_distribution_info`: 内容分销信息
*   `indentor_info`: 订货商信息
*   `logistics_info`: 物流信息
*   `refund_info`: 退款信息
*   `student_info`: 学生信息
*   `talent_douyin_info`: 达人抖音号信息
*   `veri_code_info`: 核销信息

*(详细字段请参考原始文档或示例)*

#### `data.invoice_info` (发票信息)

| 参数名               | 类型    | 说明         |
| -------------------- | ------- | ------------ |
| `bank`               | string  | 开户银行     |
| `bank_account`       | string  | 银行账户     |
| `content`            | string  | 发票内容     |
| `email`              | string  | 收票邮箱     |
| `has_result`         | boolean | 是否存在内容 |
| `phone_number`       | string  | 收票手机号   |
| `registered_address` | string  | 注册地址     |
| `registered_contact` | string  | 注册电话     |
| `tax_id`             | string  | 企业税号     |
| `title`              | string  | 发票抬头     |

#### `data.order_info` (订单核心信息)

| 参数名                          | 类型    | 说明                                                                                                   |
| ------------------------------- | ------- | ------------------------------------------------------------------------------------------------------ |
| `activity_description`          | string  | 营销活动描述                                                                                           |
| `after_sale_show_state`         | int     | 售后状态 (0-无 1-售后中 2-部分退款 3-全额退款)                                                           |
| `app_id`                        | string  | 商铺 ID                                                                                                |
| `app_type`                      | int     | 商铺类型                                                                                               |
| `app_type_description`          | string  | 商铺类型描述                                                                                           |
| `can_modify_price`              | boolean | 是否可以修改价格                                                                                       |
| `cant_modify_price_reason`      | string  | 无法修改价格原因                                                                                       |
| `channel_source_description`    | string  | 渠道来源描述                                                                                           |
| `channel_type`                  | int     | 渠道类型 (0-商详页 1-直播间 2-广告渠道)                                                                |
| `channel_alive_id`              | string  | 渠道直播ID                                                                                             |
| `collection_type`               | int     | 收款类型                                                                                               |
| `collection_type_description`   | string  | 收款类型描述                                                                                           |
| `community_name`                | string  | 圈子名称                                                                                               |
| `discount_description`          | string  | 优惠描述（不算营销活动）                                                                               |
| `discount_jump_url`             | string  | 兑换码/邀请码跳转链接                                                                                  |
| `redeem_batch_id`               | string  | 兑换码批次id                                                                                           |
| `redeem_activity_id`            | string  | 兑换码活动id                                                                                           |
| `redeem_code`                   | string  | 兑换码码号                                                                                             |
| `distribution_description`      | string  | 分销描述                                                                                               |
| `estimate_settle_time`          | string  | 订单预估结算时间 (视频号小店(小鹅通小店)使用字段 t(订单完成时间) + 22天)                               |
| `estimate_settle_time_description`| string  | 订单预估结算时间描述                                                                                   |
| `finder_nickname`               | string  | 视频号分销主播名                                                                                       |
| `gift_available_count`          | int     | 买赠订单赠品可用数量                                                                                   |
| `gift_batch_id`                 | string  | 买赠订单批次 ID                                                                                        |
| `gift_claimed_count`            | int     | 买赠订单赠品已使用数量                                                                                 |
| `gift_invalid_count`            | int     | 买赠订单赠品已失效数量                                                                                 |
| `gift_total_count`              | int     | 买赠订单赠品总数量                                                                                     |
| `goods_spu_type`                | int     | 商品一级类型 (0-知识商品 1-实物商品 2-服务类商品 3-打赏 4-红包)                                          |
| `has_result`                    | boolean | 是否存在订单信息内容                                                                                   |
| `ks_author_id`                  | string  | 快手ID                                                                                                 |
| `order_close_info`              | string  | 订单关闭信息                                                                                           |
| `order_close_reason`            | string  | 订单关闭原因                                                                                           |
| `order_close_type`              | int     | 订单关闭类型 (0-未关闭 1-自动取消 2-用户手动取消 3-商家取消 4-全额退款 5-拼团失败 6-系统取消)          |
| `order_close_type_description`  | string  | 订单关闭类型描述                                                                                       |
| `order_create_time`             | string  | 订单创建时间                                                                                           |
| `order_id`                      | string  | 订单 ID                                                                                                |
| `order_pay_time`                | string  | 订单支付状态变更时间                                                                                   |
| `order_settle_time`             | string  | 订单结算状态变更时间                                                                                   |
| `order_spu_type`                | string  | 订单商品类型 (用`|`分隔, e.g., "ITX|VDO")                                                           |
| `order_state`                   | int     | 订单状态 (0-待付款 1-待成交 2-待发货 3-已发货 4-已完成 5-已关闭)                                         |
| `order_state_description`       | string  | 订单状态描述                                                                                           |
| `order_type`                    | int     | 订单类型 (1-交易订单 2-导入订单 3-渠道采购订单（内容市场）4-兑换订单)                                  |
| `order_type_description`        | string  | 订单类型描述                                                                                           |
| `payment_type`                  | int     | 支付类型 (1-微信支付 2-支付宝支付 3-线下支付 4-百度支付 8-虚拟币 9-支付宝花呗)                         |
| `payment_type_description`      | string  | 支付类型描述                                                                                           |
| `plan_auto_cancel_time`         | string  | 订单计划自动取消时间                                                                                   |
| `plan_auto_confirm_time`        | string  | 订单计划自动确认时间                                                                                   |
| `plan_auto_confirm_timestamp`   | int     | 订单计划自动确认时间戳                                                                                 |
| `promoter_type`                 | int     | 推广员订单类型 (0 非推广员订单, 1 推广员订单)                                                          |
| `relation_app_id`               | string  | 关联商铺 ID                                                                                            |
| `relation_order_id`             | string  | 关联订单 ID                                                                                            |
| `relation_order_type`           | int     | 关联订单类型 (1 带货主订单, 2 带货副订单, 3 买赠主订单, 4 支付有礼主订单, 5 渠道方主订单, 6 内容方主订单) |
| `settle_state`                  | int     | 结算状态 (0-待结算 1-结算中 2-结算完成)                                                              |
| `sub_merchant_id`               | string  | 子商户号                                                                                               |
| `user_id`                       | string  | 用户 ID                                                                                                |

#### `data.payment_info` (支付信息)

| 参数名          | 类型    | 说明                 |
| --------------- | ------- | -------------------- |
| `has_result`    | boolean | 是否存在内容         |
| `out_order_id`  | string  | 第三方单号 - 商户单号 |
| `transaction_id`| string  | 支付交易号 - 交易单号 |

#### `data.price_info` (价格信息)

| 参数名                   | 类型    | 说明               |
| ------------------------ | ------- | ------------------ |
| `collectibles`           | int     | 应收款，单位：分   |
| `earned_revenue`         | int     | 已收款，单位：分   |
| `goods_modified_amount`  | int     | 商品改价金额，单位：分 |
| `goods_total_count`      | int     | 商品总数           |
| `gross_total`            | int     | 商品总价，单位：分 |
| `has_result`             | boolean | 是否存在内容       |
| `shipment_fee`           | int     | 运费，单位：分     |
| `shipment_modified_amount`| int     | 运费改价金额，单位：分 |
| `total_modified_amount`  | int     | 总改价金额，单位：分 |

#### `data.third_party_info` (第三方额外信息)

包含 `douyin_info` 和 `quick_hand_info` 子对象。

*(省略详细字段)*

---

## 返回示例

```json
{
    "code": 0,
    "data": {
        "buyer_info": {
            "avatar_url": "",
            "comment": "",
            "has_result": false,
            "info_collect_phone_number": "",
            "nickname": "",
            "phone_number": "",
            "user_id": ""
        },
        "goods_info": {
            "goods_list": [{
                "actual_fee": 0,
                "app_id": "",
                "check_state": 0,
                "check_state_description": "",
                "discounts_info": {
                    "coupons_list": [{
                        "discount_amount": 0,
                        "discount_name": "",
                        "discount_sub_type": 0,
                        "discount_sub_type_description": ""
                    }],
                    "discounts_list": [{
                        "discount_amount": 0,
                        "discount_name": "",
                        "discount_sub_type": 0,
                        "discount_sub_type_description": ""
                    }],
                    "multi_coupons_usage": false,
                    "no_coupon_list": [{
                        "discount_amount": 0,
                        "discount_name": "",
                        "discount_sub_type": 0,
                        "discount_sub_type_description": ""
                    }],
                    "total_coupons_discount_amount": 0
                },
                "expire_desc": "",
                "expire_display": false,
                "expire_end": "",
                "expire_start": "",
                "goods_description": "",
                "goods_image": "",
                "goods_name": "",
                "goods_sn": "",
                "goods_spec_description": "",
                "modified_amount": 0,
                "paid_coupon_info": "", // 文档示例此处为字符串，但上方描述为array
                "period_type": 0,
                "quantity": 0,
                "refund_amount": 0,
                "refund_state": 0,
                "refund_state_description": "",
                "refundable_amount": 0,
                "relation_goods_id": "",
                "relation_goods_type": 0,
                "relation_goods_type_description": "",
                "remain_count": 0,
                "ship_state": 0,
                "ship_state_description": "",
                "sku_id": "",
                "sku_spec_code": "",
                "spec_value": "",
                "spu_id": "",
                "spu_type": "",
                "spu_type_description": "",
                "sub_total": 0,
                "tag_description": "",
                "unit_price": 0,
                "vs_commission": 0,
                "vs_nick_name": "",
                "vs_platform_fee": 0
            }],
            "has_result": false
        },
        "internal_extra_info": {
            // ... 省略内部结构 ...
        },
        "invoice_info": {
            "bank": "",
            "bank_account": "",
            "content": "",
            "email": "",
            "has_result": false,
            "phone_number": "",
            "registered_address": "",
            "registered_contact": "",
            "tax_id": "",
            "title": ""
        },
        "order_info": {
            "activity_description": "",
            "after_sale_show_state": 0,
            "app_id": "",
            "app_type": 0,
            "app_type_description": "",
            "can_modify_price": false,
            "cant_modify_price_reason": "",
            "channel_source_description": "",
            "channel_type": 0,
            "collection_type": 0,
            "collection_type_description": "",
            "community_name": "",
            "discount_description": "",
            "discount_jump_url": "",
            "distribution_description": "",
            "estimate_settle_time": "",
            "finder_nickname": "",
            "gift_available_count": 0,
            "gift_batch_id": "",
            "gift_claimed_count": 0,
            "gift_invalid_count": 0,
            "gift_total_count": 0,
            "goods_spu_type": 0,
            "has_result": false,
            "ks_author_id": "",
            "order_close_info": "",
            "order_close_reason": "",
            "order_close_type": 0,
            "order_close_type_description": "",
            "order_create_time": "",
            "order_id": "",
            "order_pay_time": "",
            "order_settle_time": "",
            "order_spu_type": "",
            "order_state": 0,
            "order_state_description": "",
            "order_type": 0,
            "order_type_description": "",
            "payment_type": 0,
            "payment_type_description": "",
            "plan_auto_cancel_time": "",
            "plan_auto_confirm_time": "",
            "plan_auto_confirm_timestamp": 0,
            "promoter_type": 0,
            "relation_app_id": "",
            "relation_order_id": "",
            "relation_order_type": 0,
            "settle_state": 0,
            "sub_merchant_id": "",
            "user_id": ""
        },
        "payment_info": {
            "has_result": false,
            "out_order_id": "",
            "transaction_id": ""
        },
        "price_info": {
            "collectibles": 0,
            "earned_revenue": 0,
            "goods_modified_amount": 0,
            "goods_total_count": 0,
            "gross_total": 0,
            "has_result": false,
            "shipment_fee": 0,
            "shipment_modified_amount": 0,
            "total_modified_amount": 0
        },
        "third_party_info": {
            "douyin_info": {
                "dy_nick_name": "",
                "has_result": false,
                "service_fee": 0
            },
            "quick_hand_info": {
                "author_id": "",
                "has_result": false,
                "item_id": "",
                "item_type": ""
            }
        }
    },
    "msg": ""
} 