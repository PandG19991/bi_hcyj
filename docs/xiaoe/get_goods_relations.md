# 小鹅通 API 文档：获取商品关系链 2.0

**接口名称:** 获取商品关系链 2.0

**接口地址:** `/xe.goods.relations.get/2.0.0`

**请求方式:** `POST`

**请求头:** `Content-Type: application/json`

**频率限制:** `1秒10次`

**来源:** [https://api-doc.xiaoe-tech.com/api_list/product/get_goods_relations_2.html](https://api-doc.xiaoe-tech.com/api_list/product/get_goods_relations_2.html)

---

## 接口说明

查询商品列表信息，包含商品关联关系信息，如课程关联的直播间、实物商品关联的优惠券等。

---

## 请求参数

| 参数名           | 必选 | 类型       | 说明                                                                      |
| --------------- | ---- | ---------- | ------------------------------------------------------------------------- |
| `access_token`  | 是   | string     | 专属 token                                                                |
| `page_index`    | 否   | int        | 页码，默认为 1                                                            |
| `page_size`     | 否   | int        | 每页数量，默认为 10，最大值为 50                                            |
| `ids`           | 否   | array[string]| 商品资源id列表，最多支持20个                                                  |
| `goods_type`    | 否   | int        | 商品类型: 1-图文 2-音频 3-视频 4-直播 5-活动 6-专栏 7-会员 8-大专栏 19-电子书 20-实物 21-面授 25-小社群 26-训练营 34-超级会员 35-拼团 41-优惠券 42-知识福袋 43-日历 44-训练营pro 46-加群服务 51-付费问答 |
| `keyword`       | 否   | string     | 关键词搜索 (商品名称)                                                     |
| `sale_status`   | 否   | int        | 上架状态：0-待上架，1-已上架                                                |
| `start_time`    | 否   | string     | 创建起始时间, `YYYY-MM-DD HH:mm:ss`                                       |
| `end_time`      | 否   | string     | 创建结束时间, `YYYY-MM-DD HH:mm:ss`                                       |
| `is_query_all`  | 否   | int        | 是否查询全部状态的商品，1-是，0-否 (默认只查正常状态)                         |
| `goods_tag_type`| 否   | int        | 商品标签：1-热门推荐 2-最新上架                                             |

---

## 请求示例

```json
{
    "access_token": "xe_xxxxx",
    "page_index": 1,
    "page_size": 10,
    "goods_type": 3
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

| 参数名        | 类型    | 说明                    |
| ------------- | ------- | ----------------------- |
| `current_page`| int     | 当前页码                |
| `list`        | array   | 商品列表 (结构见下文)   |
| `total`       | int     | 总数                    |

### `data.list[]` 商品对象结构

| 参数名                | 类型     | 说明                                      |
| ----------------------- | -------- | ----------------------------------------- |
| `id`                    | string   | 商品资源 ID (`resource_id`)               |
| `app_id`                | string   | 店铺 ID                                   |
| `goods_name`            | string   | 商品名称                                  |
| `goods_category_id`     | string   | 商品类目 ID (?)                           |
| `goods_img`             | array[string]| 商品封面图列表 (取第一个即可?)             |
| `goods_tag`             | string   | 商品标签名称                              |
| `goods_tag_is_show`     | int      | 是否显示标签 (1是, 0否)                   |
| `resource_type`         | int      | 商品类型码 (同请求参数 `goods_type`)      |
| `resource_id`           | string   | 商品资源 ID (同 `id`)                     |
| `spu_id`                | string   | SPU ID (同 `id`, `resource_id`)           |
| `spu_type`              | string   | SPU 类型 (e.g., "VDO", "SPU" 等)          |
| `sell_mode`             | int      | 售卖模式 (1-永久有效, 2-限时有效)         |
| `period_type`           | int      | 有效期类型 (0-永久, 1-购买后X天...)     |
| `period`                | int      | 有效期值 (配合 `period_type`)             |
| `period_value`          | string   | 有效期展示值                              |
| `price_low`             | int      | 最低价格 (单位：分)                       |
| `price_high`            | int      | 最高价格 (单位：分)                       |
| `price_line`            | int      | 划线价 (单位：分)                         |
| `is_free`               | int      | 是否免费 (1是, 0否)                       |
| `is_timing_sale`        | int      | 是否定时开售 (1是, 0否)                   |
| `timing_sale`           | string   | 定时开售时间 (`YYYY-MM-DD HH:mm:ss`)        |
| `can_sold_start`        | string   | 可售卖开始时间                            |
| `can_sold_end`          | string   | 可售卖结束时间                            |
| `limit_purchase`        | int      | 是否限购 (1是, 0否)                       |
| `stock_deduct_mode`     | int      | 库存扣减模式 (0-付款, 1-拍下)             |
| `show_stock`            | int      | 是否显示库存 (1是, 0否)                   |
| `sell_type`             | int      | 售卖方式 (1-单独售卖, 2-打包售卖)         |
| `is_public`             | int      | 是否公开 (1是, 0否)                       |
| `is_display`            | int      | 是否显示 (1是, 0否)                       |
| `is_forbid`             | int      | 是否禁止访问 (1是, 0否)                   |
| `is_password`           | int      | 是否需要密码 (1是, 0否)                   |
| `is_single`             | int      | 是否单品 (1是, 0否)                       |
| `is_goods_package`      | int      | 是否商品包 (1是, 0否)                     |
| `is_ignore`             | int      | 是否忽略 (?)                              |
| `has_distribute`        | int      | 是否参与分销 (1是, 0否)                   |
| `is_stop_sell`          | int      | 是否停售 (1是, 0否)                       |
| `sale_status`           | int      | 上架状态 (0-下架/待上架, 1-已上架)        |
| `sale_at`               | string   | 上架时间 (`YYYY-MM-DD HH:mm:ss`)          |
| `appraise_num`          | int      | 评价数                                    |
| `visit_num`             | int      | 访问数 (?)                                |
| `pv`                    | int      | 浏览量                                    |
| `uv`                    | int      | 访客数                                    |
| `is_best`               | int      | 是否精选 (0否 1是)                        |
| `is_hot`                | int      | 是否热销 (0否 1是)                        |
| `is_new`                | int      | 是否新品 (0否 1是)                        |
| `is_recom`              | int      | 是否推荐 (0否 1是)                        |
| `distribution_pattern`  | int      | 配送方式 (1-无需配送/虚拟, 2-快递)      |
| `freight`               | int      | 运费 (单位：分)                           |
| `audit_reason`          | string   | 审核原因                                  |
| `audit_time`            | string   | 审核时间                                  |
| `audit_user_id`         | string   | 审核人 user_id                          |
| `spu_extend`            | string   | 业务侧扩展字段                            |
| `parent_spu_id`         | string   | 父级 SPU ID                               |
| `parent_app_id`         | string   | 父级 App ID                               |
| `is_uniform_freight`    | int      | 是否统一运费 (1是, 2-运费模板)            |
| `freight_template_id`   | int      | 运费模板 ID                               |
| `img_url_compressed`    | string   | 压缩后的列表配图 URL                      |
| `is_deleted`            | int      | 是否删除 (0正常 1已删除)                  |
| `created_at`            | string   | 创建时间                                  |
| `updated_at`            | string   | 更新时间                                  |
| `attr`                  | array    | 属性信息 (结构未详细说明)                 |
| `extend.sell_num`       | int      | 售卖数量 (在 extend[0].sell_num ?)      |

---

## 响应示例

```json
{
    "code": 0,
    "data": {
        "current_page": 1,
        "list": [
            {
                "app_id": "apppcHqlTPT3482",
                "appraise_num": 0,
                "audit_reason": "",
                "audit_time": "0000-00-00 00:00:00",
                "audit_user_id": null,
                "attr": [],
                "can_sold_end": "0000-00-00 00:00:00",
                "can_sold_start": "0000-00-00 00:00:00",
                "created_at": "2022-05-31 18:48:10",
                "custom_cover": "",
                "distribution_pattern": 1,
                "extend": [],
                "freight": 0,
                "freight_template_id": 0,
                "goods_category_id": "",
                "goods_img": [
                    "https://wechatapppro-1252524126.file.myqcloud.com/apppcHqlTPT3482/image/b_u_5b73e35149a67_ypMtbWtO/kvw18b1x0vfo.jpg"
                ],
                "goods_name": "有价优惠券外部码库值测试",
                "goods_tag": "有价优惠券",
                "goods_tag_is_show": 1,
                "has_distribute": 0,
                "id": 72896, // 注意这里是 id
                "img_url_compressed": "https://wechatapppro-1252524126.file.myqcloud.com/apppcHqlTPT3482/image/b_u_5b73e35149a67_ypMtbWtO/kvw18b1x0vfo.jpg",
                "is_best": 0,
                "is_deleted": 0,
                "is_display": 1,
                "is_forbid": 0,
                "is_free": 0,
                "is_goods_package": 0,
                "is_hot": 0,
                "is_ignore": 0,
                "is_new": 0,
                "is_password": 0,
                "is_public": 1,
                "is_recom": 0,
                "is_single": 1,
                "is_stop_sell": 0,
                "is_timing_sale": 0,
                "is_uniform_freight": 1,
                "limit_purchase": 0,
                "parent_app_id": "",
                "parent_spu_id": "",
                "period": -1,
                "period_type": 0,
                "period_value": "",
                "price_high": 300, // 分
                "price_line": 0,
                "price_low": 300, // 分
                "pv": 0,
                "resource_id": "g_61a4a307a6344_DfOA1bCn",
                "resource_type": 41,
                "sale_at": "2021-11-29 17:53:12",
                "sale_status": 1,
                "sell_mode": 1,
                "sell_type": 1,
                "show_stock": 1,
                "spu_extend": "",
                "sku": [],
                "spu_id": "g_61a4a307a6344_DfOA1bCn",
                "spu_type": "VCP",
                "stock": [],
                "stock_deduct_mode": 0,
                "timing_sale": "",
                "updated_at": "0000-00-00 00:00:00",
                "uv": 0,
                "video_img_url": "",
                "visit_num": 0,
                "wx_goods_category_id": ""
            }
            // ... more products
        ],
        "total": 46598
    },
    "msg": "success"
}
``` 