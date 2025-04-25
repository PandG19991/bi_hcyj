# 小鹅通 API 文档：获取订单详情 2.0 (xe.ecommerce.order.detail/1.0.0)

获取指定订单的详细信息。

**来源:** [官方文档](https://api-doc.xiaoe-tech.com/api_list/order/get_order_details_2.html)

## 基本信息

*   **接口地址:** `https://api.xiaoe-tech.com/xe.ecommerce.order.detail/1.0.0`
*   **请求方式:** `POST`
*   **请求头:** `Content-Type: application/json`
*   **频率限制:** 1秒 20次
*   **权限要求:** 订单管理-查询

## 请求参数

| 参数名         | 必选 | 类型   | 说明      |
| :------------- | :--- | :----- | :-------- |
| `access_token` | 是   | string | 专属token |
| `order_id`     | 是   | string | 订单ID    |

## 请求示例

```json
{
    "access_token": "xe_xxxxx",
    "order_id": "o_xxxxxx_xxxxxxx"
}
```

## 返回参数

| 参数名                   | 类型   | 说明           |
| :----------------------- | :----- | :------------- |
| `code`                   | int    | 请求结果码 (0 表示成功) |
| `msg`                    | string | 描述信息       |
| `data`                   | object | 数据对象       |
| `data.buyer_info`        | object | 买家信息       |
| `data.goods_info`        | object | 商品信息       |
| `data.internal_extra_info`| object | 内部额外信息   |
| `data.invoice_info`      | object | 发票信息       |
| `data.order_info`        | object | 订单信息       |
| `data.payment_info`      | object | 支付信息       |
| `data.price_info`        | object | 价格信息       |
| `data.third_party_info`  | object | 第三方额外信息 |

### 买家信息 (`data.buyer_info`)

| 参数名                       | 类型    | 说明                |
| :--------------------------- | :------ | :------------------ |
| `avatar_url`                 | string  | 买家头像            |
| `comment`                    | string  | 买家留言            |
| `has_result`                 | boolean | 是否存在内容        |
| `info_collect_phone_number`  | string  | 买家信息采集手机号  |
| `nickname`                   | string  | 买家昵称            |
| `phone_number`               | string  | 买家手机号          |
| `user_id`                    | string  | 买家用户ID          |

### 商品信息 (`data.goods_info`)

| 参数名         | 类型    | 说明           |
| :------------- | :------ | :------------- |
| `goods_list`   | array   | 商品列表       |
| `has_result`   | boolean | 是否存在内容   |

#### 商品列表项 (`data.goods_info.goods_list[]`)

| 参数名                              | 类型    | 说明                                                                 |
| :---------------------------------- | :------ | :------------------------------------------------------------------- |
| `actual_fee`                        | int     | 商品实收金额 (分)                                                      |
| `app_id`                            | string  | 店铺 ID                                                              |
| `check_state`                       | int     | 核销状态 (0-无, 1-待核销, 2-已核销, 3-已失效, 4-部分核销)               |
| `check_state_description`           | string  | 核销状态描述                                                         |
| `discounts_info`                    | object  | 商品优惠信息                                                         |
| `expire_desc`                       | string  | 商品有效期描述                                                       |
| `expire_display`                    | boolean | 是否显示过期时间                                                     |
| `expire_end`                        | string  | 商品有效期结束时间                                                   |
| `expire_start`                      | string  | 商品有效期开始时间                                                   |
| `goods_description`                 | string  | 商品描述                                                             |
| `goods_image`                       | string  | 商品图片                                                             |
| `goods_name`                        | string  | 商品名称                                                             |
| `goods_sn`                          | string  | 商品编码                                                             |
| `goods_spec_description`            | string  | 商品规格描述                                                         |
| `modified_amount`                   | int     | 商品改价金额 (分)                                                    |
| `paid_coupon_info`                  | array   | 有价优惠券信息 (详见下文)                                            |
| `period_type`                       | int     | 商品有效期类型 (0-长期有效, 1-具体时间前有效, 2-有效期时间范围(秒))     |
| `quantity`                          | int     | 商品数量                                                             |
| `refund_amount`                     | int     | 商品退款金额 (分)                                                    |
| `refund_state`                      | int     | 退款状态 (0-无, 1-售后中, 2-部分退款, 3-全额退款)                     |
| `refund_state_description`          | string  | 退款状态描述                                                         |
| `refundable_amount`                 | int     | 商品可退金额 (分)                                                    |
| `relation_goods_id`                 | string  | 关联商品 ID (order goods id)                                         |
| `relation_goods_type`               | int     | 关联商品类型 (0-无, 1-虚拟带货主商品, 2-实物带货主商品, 3-内容分销市场主商品, 4-总分店总店商品) |
| `relation_goods_type_description`   | string  | 关联商品类型描述 (例如: \"套餐商品\")                                  |
| `remain_count`                      | int     | 剩余核销次数                                                         |
| `ship_state`                        | int     | 发货状态                                                             |
| `ship_state_description`            | string  | 发货状态描述                                                         |
| `sku_id`                            | string  | 规格 ID                                                              |
| `sku_spec_code`                     | string  | 规格编码                                                             |
| `spec_value`                        | string  | 商品规格附加值 (例如 OLC 线下课需要)                                 |
| `spu_id`                            | string  | 商品 ID                                                              |
| `spu_type`                          | string  | 商品一级类型 (0-知识商品, 1-实物商品, 2-服务类商品, 3-打赏, 4-红包, 5-知识/实物商品) |
| `spu_type_description`              | string  | 商品类型描述                                                         |
| `sub_total`                         | int     | 商品小计 (实付金额 - 改价金额) (分)                                    |
| `tag_description`                   | string  | 商品标签描述                                                         |
| `unit_price`                        | int     | 商品单价 (分)                                                        |
| `vs_commission`                     | int     | 视频号小店主播佣金 (分)                                              |
| `vs_nick_name`                      | string  | 视频号小店主播昵称                                                   |
| `vs_platform_fee`                   | int     | 视频号小店平台服务费 (分)                                            |

##### 商品优惠信息 (`data.goods_info.goods_list[].discounts_info`)

| 参数名                              | 类型    | 说明                          |
| :---------------------------------- | :------ | :---------------------------- |
| `coupons_list`                      | array   | 优惠券列表 (详见下文)         |
| `discounts_list`                    | array   | 优惠列表 (详见下文)           |
| `multi_coupons_usage`               | boolean | 是否多张优惠券叠加使用        |
| `no_coupon_list`                    | array   | 不包含优惠券的优惠列表 (详见下文) |
| `total_coupons_discount_amount`     | int     | 优惠券总金额 (分)             |

###### 优惠券/优惠列表项 (`coupons_list[]`, `discounts_list[]`, `no_coupon_list[]`)

| 参数名                           | 类型   | 说明             |
| :------------------------------- | :----- | :--------------- |
| `discount_amount`                | int    | 优惠金额 (分)    |
| `discount_name`                  | string | 优惠名称         |
| `discount_sub_type`              | int    | 二级优惠类型     |
| `discount_sub_type_description`  | string | 二级优惠类型描述 |

##### 有价优惠券信息 (`data.goods_info.goods_list[].paid_coupon_info[]`)

| 参数名            | 类型   | 说明                |
| :---------------- | :----- | :------------------ |
| `app_id`          | array  | 店铺 ID             |
| `coupon_code`     | string | 有价优惠券 code     |
| `coupon_password` | string | 有价优惠券卡密    |
| `goods_id`        | string | 商品 ID             |
| `order_id`        | string | 订单 ID             |
| `receive_at`      | string | 领取时间            |
| `stat`            | int    | 状态 (固定为 2 领取) |
| `user_id`         | string | 领取用户            |

### 内部额外信息 (`data.internal_extra_info`)

| 参数名                   | 类型   | 说明               |
| :----------------------- | :----- | :----------------- |
| `after_sale_info`        | object | 售后信息 (详见下文)   |
| `consignee_info`         | object | 收货信息 (详见下文)   |
| `content_distribution_info` | object | 内容分销信息 (详见下文)|
| `indentor_info`          | object | 订货商信息 (详见下文) |
| `logistics_info`         | object | 物流信息 (详见下文)   |
| `refund_info`            | object | 退款信息 (详见下文)   |
| `student_info`           | object | 学生信息 (详见下文)   |
| `talent_douyin_info`     | object | 达人抖音号信息 (详见下文) |
| `veri_code_info`         | object | 核销信息 (详见下文)   |

#### 售后信息 (`data.internal_extra_info.after_sale_info`)

| 参数名                | 类型    | 说明            |
| :-------------------- | :------ | :-------------- |
| `after_sale_records`  | array   | 售后记录 (详见下文) |
| `has_result`          | boolean | 是否存在内容    |

##### 售后记录 (`data.internal_extra_info.after_sale_info.after_sale_records[]`)

| 参数名          | 类型   | 说明     |
| :-------------- | :----- | :------- |
| `after_sale_id` | string | 售后单号 |
| `goods_name`    | string | 商品名称 |

#### 收货信息 (`data.internal_extra_info.consignee_info`)

| 参数名                  | 类型    | 说明                                           |
| :---------------------- | :------ | :--------------------------------------------- |
| `address`               | string  | 收货地址 / 提货地址                            |
| `address_city`          | string  | 地址-市                                        |
| `address_county`        | string  | 地址-区                                        |
| `address_detail`        | string  | 地址-详细地址                                  |
| `address_province`      | string  | 地址-省                                        |
| `contact`               | string  | 收货人联系方式 / 联系方式                      |
| `contact_country_code`  | string  | 收货人联系方式国际区号 / 联系方式国际区号    |
| `express_type`          | int     | 收货类型 (1-物流配送, 2-自提)                  |
| `full_contact`          | string  | 收货人联系方式 (国际区号 联系方式) / 联系方式 |
| `has_result`            | boolean | 是否存在内容                                   |
| `name`                  | string  | 收货人姓名 / 提货人                            |

#### 内容分销信息 (`data.internal_extra_info.content_distribution_info`)

| 参数名                         | 类型    | 说明                                                                 |
| :----------------------------- | :------ | :------------------------------------------------------------------- |
| `channel_order_actual_price`   | int     | 渠道方订单实收金额 (用于显示在内容方退款弹窗的“订单金额”) (分)         |
| `distribution_amount`          | int     | 分成金额 (分)                                                        |
| `distribution_ratio`           | number  | 分销比例                                                             |
| `has_result`                   | boolean | 是否存在内容                                                         |
| `is_channel`                   | boolean | 是否为渠道方                                                         |
| `market_name`                  | string  | 分销市场名称                                                         |
| `relation_app_image`           | string  | 关联的商铺图片                                                       |
| `relation_app_name`            | string  | 关联的商铺名称 (如果本店铺是分销方, 则关联的是内容方商铺名称; 反之亦然) |
| `type_description`             | string  | 分销类型描述                                                         |

#### 订货商信息 (`data.internal_extra_info.indentor_info`)

| 参数名                      | 类型    | 说明                |
| :-------------------------- | :------ | :------------------ |
| `has_result`                | boolean | 是否存在内容        |
| `indentor_avatar`           | string  | 订货商头像          |
| `indentor_deduct_quota`     | int     | 订货商消耗额度      |
| `indentor_id`               | string  | 订货商ID            |
| `indentor_name`             | string  | 订货商姓名          |
| `indentor_phone`            | string  | 订货商手机号        |
| `indentor_remaining_quota`  | int     | 订货商剩余额度      |
| `indentor_staff_id`         | string  | 订货商员工ID        |
| `indentor_staff_name`       | string  | 订货商员工姓名      |
| `indentor_staff_phone`      | string  | 订货商员工手机号    |

#### 物流信息 (`data.internal_extra_info.logistics_info`)

| 参数名           | 类型    | 说明            |
| :--------------- | :------ | :-------------- |
| `has_result`     | boolean | 是否存在内容    |
| `packages_info`  | array   | 包裹信息 (详见下文) |

##### 包裹信息 (`data.internal_extra_info.logistics_info.packages_info[]`)

| 参数名                           | 类型   | 说明                                     |
| :------------------------------- | :----- | :--------------------------------------- |
| `departure_time`                 | string | 发货时间                                 |
| `electronic_order_fail_reason`   | string | 电子面单失败原因                         |
| `express_id`                     | string | 物流单号                                 |
| `logistics_company_name`         | string | 物流公司名称                             |
| `logistics_state_description`    | string | 物流状态描述                             |
| `package_goods_info`             | array  | 包裹内商品信息 (结构同 `data.goods_info.goods_list[]`) |
| `package_trace_info`             | array  | 物流轨迹信息 (详见下文)                   |
| `parcel_id`                      | string | 物流包裹 ID                              |
| `shipment_type`                  | int    | 发货类型 (1-自行联系快递, 2-在线下单)     |

###### 物流轨迹信息 (`data.internal_extra_info.logistics_info.packages_info[].package_trace_info[]`)

| 参数名 | 类型   | 说明     |
| :----- | :----- | :------- |
| `text` | string | 文字描述 |
| `time` | string | 时间     |

#### 退款信息 (`data.internal_extra_info.refund_info`)

| 参数名           | 类型    | 说明            |
| :--------------- | :------ | :-------------- |
| `has_result`     | boolean | 是否存在内容    |
| `refund_records` | array   | 退款记录 (详见下文) |

##### 退款记录 (`data.internal_extra_info.refund_info.refund_records[]`)

| 参数名                   | 类型   | 说明                                      |
| :----------------------- | :----- | :---------------------------------------- |
| `after_sale_id`          | string | 售后单号                                  |
| `goods_info`             | object | 商品信息 (结构同 `data.goods_info.goods_list[]`) |
| `is_delete_purchase`     | int    | 是否删除订购关系 (1-是, 0-否)              |
| `operator`               | string | 操作人                                    |
| `refund_amount`          | int    | 退款金额 (分)                             |
| `refund_state`           | int    | 退款状态 (0-待退款, 1-退款中, 2-退款成功, 3-退款失败) |
| `refund_state_description`| string | 退款状态描述                              |
| `refund_time`            | string | 退款时间                                  |
| `refund_type`            | int    | 退款类型 (1-全额退款, 2-部分退款)           |
| `refund_type_description`| string | 退款类型描述                              |
| `remark`                 | string | B端退款备注                               |

#### 学生信息 (`data.internal_extra_info.student_info`)

| 参数名                       | 类型    | 说明                |
| :--------------------------- | :------ | :------------------ |
| `birth_date`                 | string  | 出生日期            |
| `c_data`                     | array   | 学生资料 (详见下文) |
| `contact_address`            | string  | 联系地址            |
| `course_offline_id`          | string  | 线下课程 ID         |
| `gender`                     | int     | 性别                |
| `grade`                      | string  | 年级                |
| `has_result`                 | boolean | 是否存在内容        |
| `intention_school`           | string  | 意向上课学校        |
| `intention_school_address`   | string  | 意向上课地点        |
| `intention_time`             | string  | 意向上课时间        |
| `name`                       | string  | 学生姓名            |
| `order_id`                   | string  | 订单 ID             |
| `phone`                      | string  | 联系方式            |
| `user_id`                    | string  | 用户 ID             |
| `wechat_id`                  | string  | 微信号              |

##### 学生资料 (`data.internal_extra_info.student_info.c_data[]`)

| 参数名  | 类型   | 说明 |
| :------ | :----- | :--- |
| `key`   | string | 键   |
| `value` | string | 值   |

#### 达人抖音号信息 (`data.internal_extra_info.talent_douyin_info`)

| 参数名             | 类型    | 说明           |
| :----------------- | :------ | :------------- |
| `has_result`       | boolean | 是否存在内容   |
| `nickname`         | string  | 抖音达人昵称   |
| `talent_douyin_id` | string  | 达人抖音号     |

#### 核销信息 (`data.internal_extra_info.veri_code_info`)

| 参数名           | 类型    | 说明            |
| :--------------- | :------ | :-------------- |
| `has_result`     | boolean | 是否存在内容    |
| `remain_count`   | int     | 剩余核销次数    |
| `veri_code_list` | array   | 核销码列表 (详见下文) |

##### 核销码列表 (`data.internal_extra_info.veri_code_info.veri_code_list[]`)

| 参数名             | 类型   | 说明                                             |
| :----------------- | :----- | :----------------------------------------------- |
| `app_id`           | string | App ID                                           |
| `check_time`       | string | 核销时间                                         |
| `check_type`       | int    | 核销类型                                         |
| `goods_img`        | string | 商品图片                                         |
| `operator`         | string | 操作人                                           |
| `operator_contact` | string | 操作人联系方式                                   |
| `order_id`         | string | 订单号                                           |
| `price`            | int    | 价格 (分?)                                       |
| `sku_id`           | string | 规格 ID                                          |
| `spu_id`           | string | 商品 ID                                          |
| `spu_name`         | string | 商品名称                                         |
| `status`           | int    | 核销状态 (0-无, 1-待核销, 2-已核销, 3-已失效, 4-部分核销) |
| `status_description`| string | 核销状态描述                                     |
| `user_contact`     | string | 用户联系方式                                     |
| `user_id`          | string | 用户 ID                                          |
| `user_name`        | string | 用户名                                           |
| `veri_code`        | string | 核销码                                           |

### 发票信息 (`data.invoice_info`)

| 参数名              | 类型    | 说明         |
| :------------------ | :------ | :----------- |
| `bank`              | string  | 开户银行     |
| `bank_account`      | string  | 银行账户     |
| `content`           | string  | 发票内容     |
| `email`             | string  | 收票邮箱     |
| `has_result`        | boolean | 是否存在内容 |
| `phone_number`      | string  | 收票手机号   |
| `registered_address`| string  | 注册地址     |
| `registered_contact`| string  | 注册电话     |
| `tax_id`            | string  | 企业税号     |
| `title`             | string  | 发票抬头     |

### 订单信息 (`data.order_info`)

| 参数名                           | 类型    | 说明                                                                 |
| :------------------------------- | :------ | :------------------------------------------------------------------- |
| `activity_description`           | string  | 营销活动描述                                                         |
| `after_sale_show_state`          | int     | 售后状态 (0-无, 1-售后中, 2-部分退款, 3-全额退款)                     |
| `app_id`                         | string  | 商铺 ID                                                              |
| `app_type`                       | int     | 商铺类型                                                             |
| `app_type_description`           | string  | 商铺类型描述                                                         |
| `can_modify_price`               | boolean | 是否可以修改价格                                                     |
| `cant_modify_price_reason`       | string  | 无法修改价格原因                                                     |
| `channel_source_description`     | string  | 渠道来源描述                                                         |
| `channel_type`                   | int     | 渠道类型 (0-商详页, 1-直播间, 2-广告渠道)                            |
| `channel_alive_id`               | string  | 渠道直播ID                                                           |
| `collection_type`                | int     | 收款类型                                                             |
| `collection_type_description`    | string  | 收款类型描述                                                         |
| `community_name`                 | string  | 圈子名称                                                             |
| `discount_description`           | string  | 优惠描述 (不算营销活动)                                              |
| `discount_jump_url`              | string  | 兑换码/邀请码跳转链接                                                |
| `redeem_batch_id`                | string  | 兑换码批次id                                                         |
| `redeem_activity_id`             | string  | 兑换码活动id                                                         |
| `redeem_code`                    | string  | 兑换码码号                                                           |
| `distribution_description`       | string  | 分销描述                                                             |
| `estimate_settle_time`           | string  | 订单预估结算时间 (视频号小店使用字段 t(订单完成时间) 22)               |
| `estimate_settle_time_description`| string | 订单预估结算时间描述                                                  |
| `finder_nickname`                | string  | 视频号分销主播名                                                     |
| `gift_available_count`           | int     | 买赠订单赠品可用数量                                                 |
| `gift_batch_id`                  | string  | 买赠订单批次 ID                                                      |
| `gift_claimed_count`             | int     | 买赠订单赠品已使用数量                                               |
| `gift_invalid_count`             | int     | 买赠订单赠品已失效数量                                               |
| `gift_total_count`               | int     | 买赠订单赠品总数量                                                   |
| `goods_spu_type`                 | int     | 商品一级类型 (0-知识商品, 1-实物商品, 2-服务类商品, 3-打赏, 4-红包) |
| `has_result`                     | boolean | 是否存在内容                                                         |
| `ks_author_id`                   | string  | 快手ID                                                               |
| `order_close_info`               | string  | 订单关闭信息                                                         |
| `order_close_reason`             | string  | 订单关闭原因                                                         |
| `order_close_type`               | int     | 订单关闭类型 (0-未关闭, 1-自动取消, 2-用户手动取消, 3-商家取消, 4-全额退款, 5-拼团失败, 6-系统取消) |
| `order_close_type_description`   | string  | 订单关闭类型描述                                                     |
| `order_create_time`              | string  | 订单创建时间                                                         |
| `order_id`                       | string  | 订单 ID                                                              |
| `order_pay_time`                 | string  | 订单支付状态变更时间                                                 |
| `order_settle_time`              | string  | 订单结算状态变更时间                                                 |
| `order_spu_type`                 | string  | 订单商品类型 (用`|`分隔, 例如 \"ITX|VDO\")                            |
| `order_state`                    | int     | 订单状态 (0-待付款, 1-待成交, 2-待发货, 3-已发货, 4-已完成, 5-已关闭) |
| `order_state_description`        | string  | 订单状态描述                                                         |
| `order_type`                     | int     | 订单类型 (1-交易订单, 2-导入订单, 3-渠道采购订单(内容市场), 4-兑换订单) |
| `order_type_description`         | string  | 订单类型描述                                                         |
| `payment_type`                   | int     | 支付类型 (1-微信支付, 2-支付宝支付, 3-线下支付, 4-百度支付, 8-虚拟币, 9-支付宝花呗) |
| `payment_type_description`       | string  | 支付类型描述                                                         |
| `plan_auto_cancel_time`          | string  | 订单计划自动取消时间                                                 |
| `plan_auto_confirm_time`         | string  | 订单计划自动确认时间                                                 |
| `plan_auto_confirm_timestamp`    | int     | 订单计划自动确认时间戳                                               |
| `promoter_type`                  | int     | 推广员订单类型 (0-非推广员订单, 1-推广员订单)                        |
| `relation_app_id`                | string  | 关联商铺 ID                                                          |
| `relation_order_id`              | string  | 关联订单 ID                                                          |
| `relation_order_type`            | int     | 关联订单类型 (1-带货主订单, 2-带货副订单, 3-买赠主订单, 4-支付有礼主订单, 5-渠道方主订单, 6-内容方主订单) |
| `settle_state`                   | int     | 结算状态 (0-待结算, 1-结算中, 2-结算完成)                          |
| `sub_merchant_id`                | string  | 子商户号                                                             |
| `user_id`                        | string  | 用户 ID                                                              |

### 支付信息 (`data.payment_info`)

| 参数名         | 类型    | 说明                   |
| :------------- | :------ | :--------------------- |
| `has_result`   | boolean | 是否存在内容           |
| `out_order_id` | string  | 第三方单号 - 商户单号  |
| `transaction_id`| string | 支付交易号 - 交易单号  |

### 价格信息 (`data.price_info`)

| 参数名                   | 类型    | 说明             |
| :----------------------- | :------ | :--------------- |
| `collectibles`           | int     | 应收款 (分)      |
| `earned_revenue`         | int     | 已收款 (分)      |
| `goods_modified_amount`  | int     | 商品改价金额 (分)|
| `goods_total_count`      | int     | 商品总数         |
| `gross_total`            | int     | 商品总价 (分)    |
| `has_result`             | boolean | 是否存在内容     |
| `shipment_fee`           | int     | 运费 (分)        |
| `shipment_modified_amount`| int    | 运费改价金额 (分)|
| `total_modified_amount`  | int     | 总改价金额 (分)  |

### 第三方额外信息 (`data.third_party_info`)

| 参数名            | 类型   | 说明            |
| :---------------- | :----- | :-------------- |
| `douyin_info`     | object | 抖音信息 (详见下文) |
| `quick_hand_info` | object | 快手信息 (详见下文) |

#### 抖音信息 (`data.third_party_info.douyin_info`)

| 参数名         | 类型    | 说明             |
| :------------- | :------ | :--------------- |
| `dy_nick_name` | string  | 抖音主播昵称     |
| `has_result`   | boolean | 是否存在内容     |
| `service_fee`  | int     | 抖音服务费 (分)  |

#### 快手信息 (`data.third_party_info.quick_hand_info`)

| 参数名      | 类型    | 说明                   |
| :---------- | :------ | :--------------------- |
| `author_id` | string  | 快手ID                 |
| `has_result`| boolean | 是否存在内容           |
| `item_id`   | string  | 直播ID或视频ID         |
| `item_type` | string  | `VIDEO`:短视频, `LIVE`:直播 |

## 返回示例

```json
{
    "code": 0,
    "msg": "success", // 示例中为空, 实际应有描述
    "data": {
        "buyer_info": {
            "avatar_url": "https://example.com/avatar.jpg",
            "comment": "请尽快发货",
            "has_result": true,
            "info_collect_phone_number": "13800138001",
            "nickname": "买家昵称",
            "phone_number": "13800138000",
            "user_id": "u_xxxxxx"
        },
        "goods_info": {
            "goods_list": [
                {
                    "actual_fee": 1000, // 10.00元
                    "app_id": "app_xxxxxx",
                    "check_state": 0,
                    "check_state_description": "无",
                    "discounts_info": {
                        "coupons_list": [
                            {
                                "discount_amount": 100, // 1.00元
                                "discount_name": "满减券",
                                "discount_sub_type": 1,
                                "discount_sub_type_description": "店铺优惠券"
                            }
                        ],
                        "discounts_list": [],
                        "multi_coupons_usage": false,
                        "no_coupon_list": [],
                        "total_coupons_discount_amount": 100
                    },
                    "expire_desc": "长期有效",
                    "expire_display": true,
                    "expire_end": "",
                    "expire_start": "",
                    "goods_description": "商品详细描述",
                    "goods_image": "https://example.com/goods.jpg",
                    "goods_name": "示例商品",
                    "goods_sn": "SN123456",
                    "goods_spec_description": "红色 L码",
                    "modified_amount": 0,
                    "paid_coupon_info": [], // 示例中为空
                    "period_type": 0,
                    "quantity": 1,
                    "refund_amount": 0,
                    "refund_state": 0,
                    "refund_state_description": "无",
                    "refundable_amount": 1000,
                    "relation_goods_id": "",
                    "relation_goods_type": 0,
                    "relation_goods_type_description": "",
                    "remain_count": 0,
                    "ship_state": 0,
                    "ship_state_description": "未发货", // 示例需要填充
                    "sku_id": "sku_xxxxxx",
                    "sku_spec_code": "RED-L",
                    "spec_value": "",
                    "spu_id": "spu_xxxxxx",
                    "spu_type": "1", // 实物商品
                    "spu_type_description": "实物商品",
                    "sub_total": 1000,
                    "tag_description": "热卖",
                    "unit_price": 1100, // 11.00元 (优惠前)
                    "vs_commission": 0,
                    "vs_nick_name": "",
                    "vs_platform_fee": 0
                }
            ],
            "has_result": true
        },
        "internal_extra_info": {
            // ... (内部信息根据实际情况填充)
            "after_sale_info": { "has_result": false },
            "consignee_info": {
                "address": "广东省深圳市南山区xx路xx号",
                "address_city": "深圳市",
                "address_county": "南山区",
                "address_detail": "xx路xx号",
                "address_province": "广东省",
                "contact": "13900139000",
                "contact_country_code": "+86",
                "express_type": 1,
                "full_contact": "+86 13900139000",
                "has_result": true,
                "name": "收货人姓名"
            },
            "content_distribution_info": { "has_result": false },
            "indentor_info": { "has_result": false },
            "logistics_info": { "has_result": false },
            "refund_info": { "has_result": false },
            "student_info": { "has_result": false },
            "talent_douyin_info": { "has_result": false },
            "veri_code_info": { "has_result": false }
        },
        "invoice_info": {
            "bank": "中国工商银行",
            "bank_account": "622202xxxxxxxxxxxx",
            "content": "办公用品",
            "email": "invoice@example.com",
            "has_result": true,
            "phone_number": "13700137000",
            "registered_address": "公司注册地址",
            "registered_contact": "0755-12345678",
            "tax_id": "91440300MA5FXXXXXX",
            "title": "公司发票抬头"
        },
        "order_info": {
            "activity_description": "",
            "after_sale_show_state": 0,
            "app_id": "app_xxxxxx",
            "app_type": 1,
            "app_type_description": "普通店铺", // 示例值
            "can_modify_price": true,
            "cant_modify_price_reason": "",
            "channel_source_description": "直接访问",
            "channel_type": 0,
            "collection_type": 1,
            "collection_type_description": "线上收款", // 示例值
            "community_name": "",
            "discount_description": "优惠券",
            "discount_jump_url": "",
            "distribution_description": "",
            "estimate_settle_time": "", // 仅视频号小店有
            "finder_nickname": "",
            "gift_available_count": 0,
            "gift_batch_id": "",
            "gift_claimed_count": 0,
            "gift_invalid_count": 0,
            "gift_total_count": 0,
            "goods_spu_type": 1,
            "has_result": true,
            "ks_author_id": "",
            "order_close_info": "",
            "order_close_reason": "",
            "order_close_type": 0,
            "order_close_type_description": "未关闭",
            "order_create_time": "2023-10-26 10:00:00",
            "order_id": "o_xxxxxx_xxxxxxx",
            "order_pay_time": "2023-10-26 10:05:00",
            "order_settle_time": "",
            "order_spu_type": "PHY", // 实物商品示例
            "order_state": 2, // 待发货
            "order_state_description": "待发货",
            "order_type": 1,
            "order_type_description": "交易订单",
            "payment_type": 1,
            "payment_type_description": "微信支付",
            "plan_auto_cancel_time": "2023-10-27 10:00:00",
            "plan_auto_confirm_time": "", // 待发货状态一般为空
            "plan_auto_confirm_timestamp": 0,
            "promoter_type": 0,
            "relation_app_id": "",
            "relation_order_id": "",
            "relation_order_type": 0,
            "settle_state": 0,
            "sub_merchant_id": "",
            "user_id": "u_xxxxxx"
        },
        "payment_info": {
            "has_result": true,
            "out_order_id": "商户单号_xxxx",
            "transaction_id": "微信支付交易号_xxxx"
        },
        "price_info": {
            "collectibles": 1000, // 应收款 = 商品总价 - 优惠 + 运费 - 改价
            "earned_revenue": 1000, // 已收款
            "goods_modified_amount": 0,
            "goods_total_count": 1,
            "gross_total": 1100, // 商品原价总和
            "has_result": true,
            "shipment_fee": 0, // 运费
            "shipment_modified_amount": 0,
            "total_modified_amount": 0
        },
        "third_party_info": {
            "douyin_info": { "has_result": false },
            "quick_hand_info": { "has_result": false }
        }
    }
}