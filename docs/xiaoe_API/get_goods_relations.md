# 查询商品列表 2.0 (xe.goods.list.get/4.0.0)

用于查询店铺内的商品列表信息。

## 权限要求

需要拥有 **商品管理-查询** 权限。

## 请求说明

*   **请求方式:** `POST`
*   **请求头:** `Content-Type: application/json`
*   **接口地址:** `https://api.xiaoe-tech.com/xe.goods.list.get/4.0.0`
*   **频率限制:** 10秒 3000次

## 请求参数

| 参数名                | 必选 | 类型   | 说明                                                                                                                                                                                                                                                                                                       |
| :-------------------- | :--- | :----- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `access_token`        | 是   | string | 专属token                                                                                                                                                                                                                                                                                                  |
| `page`                | 是   | int    | 分页，默认第一页                                                                                                                                                                                                                                                                                           |
| `page_size`           | 是   | int    | 页数，默认10条，最大100，超过100默认返回100条                                                                                                                                                                                                                                                                |
| `goods_name`          | 否   | string | 商品名称（支持模糊）                                                                                                                                                                                                                                                                                       |
| `resource_type`       | 否   | int    | 资源类型：1-图文, 2-音频, 3-视频, 4-直播, 5-会员, 6-专栏, 7-圈子, 8-大专栏, 9-活动管理, 16-付费打卡, 20-电子书, 21-实物商品, 23-超级会员, 25-训练营营期, 29-线下课, 31-小班课, 34-练习, 35-班课, 37-大班课, 41-有价优惠券, 42-课时包, 45-AI互动课, 46-付费问答, 47-付费问答-答主, 50-课程（训练营pro） |
| `has_distribute`      | 否   | int    | 是否参与推广: 0-未参与, 1-参与 (不传默认返回所有数据)                                                                                                                                                                                                                                                      |
| `sale_status`         | 否   | int    | 上架状态: 1-上架, 0-下架, 2-待上架, 3-上架+待上架 (不传默认返回所有数据)                                                                                                                                                                                                                                    |
| `is_return_deleted`   | 否   | int    | 是否删除: 0-正常, 1-已删除 (不传默认返回所有数据)                                                                                                                                                                                                                                                          |
| `is_return_forbid`    | 否   | int    | 商品是否被封禁: 0-否, 1-是 (不传默认返回所有数据)                                                                                                                                                                                                                                                        |
| `is_return_stop_sell` | 否   | int    | 是否停售: 0-否, 1-是 (不传默认返回所有数据)                                                                                                                                                                                                                                                              |
| `is_return_sell_type` | 否   | int    | 售卖方式: 1-独立售卖, 2-关联售卖（商品放入专栏/会员/训练营中售卖） (不传默认返回所有数据)                                                                                                                                                                                                                         |
| `is_return_display`   | 否   | int    | 是否显示: 0-否(隐藏状态), 1-是(显示状态) (不传默认返回所有数据)                                                                                                                                                                                                                                               |
| `is_return_sell_mode` | 否   | array  | 售卖类型: 1-自营, 2-内容市场, 3-课程商品 (不传默认返回所有数据)                                                                                                                                                                                                                                           |
| `is_return_zero_price`| 否   | int    | 是否返回0元商品: 0-否, 1-是 (不传默认返回所有价格包括0元的商品)                                                                                                                                                                                                                                          |
| `is_return_password`  | 否   | int    | 是否加密: 0-不加密, 1-加密 (不传默认返回所有商品)                                                                                                                                                                                                                                                          |
| `is_return_public`    | 否   | int    | 是否公开售卖: 0-不公开, 1-公开 (不传默认返回所有商品)                                                                                                                                                                                                                                                    |
| `start_time`          | 否   | string | 创建开始时间筛选 (传了则`end_time`必填, 时间范围查询不能超过15天, 格式: YYYY-mm-dd H:i:s)                                                                                                                                                                                                                   |
| `end_time`            | 否   | string | 创建结束时间筛选 (传了则`start_time`必填, 时间范围查询不能超过15天, 格式: YYYY-mm-dd H:i:s)                                                                                                                                                                                                                   |

## 请求示例

```json
{
    "resource_type": "21",
    "access_token": "xe_xxxxx",
    "page": 1,
    "page_size": 10
}
```

## 返回参数

| 参数名             | 类型   | 说明                 | 备注                             |
| :----------------- | :----- | :------------------- | :------------------------------- |
| `code`             | int    | 状态码               | 0为请求成功，其它为请求失败      |
| `msg`              | string | 请求状态描述信息     |                                  |
| `data.current_page`| int    | 当前页数             |                                  |
| `data.list`        | array  | 商品列表             | 详见下文 `data.list` 商品列表说明 |
| `data.total`       | int    | 总商品数             |                                  |

### `data.list` 商品列表说明

| 参数名                | 类型   | 说明                              | 备注                                 |
| :-------------------- | :----- | :-------------------------------- | :----------------------------------- |
| `app_id`              | string | 店铺ID                            |                                      |
| `id`                  | int    | id                                |                                      |
| `resource_id`         | string | 资源id（唯一值）                  |                                      |
| `spu_id`              | string | 统一商品id                        |                                      |
| `spu_type`            | string | 统一商品类型                      |                                      |
| `goods_category_id`   | string | 商品分类id                        |                                      |
| `goods_name`          | string | 商品名称                          |                                      |
| `goods_img`           | array  | 商品封面图（默认封面图）          |                                      |
| `custom_cover`        | string | 主图视频自定义封面                |                                      |
| `sell_type`           | int    | 付费类型                          | 1-独立售卖, 2-关联售卖               |
| `price_low`           | int    | 商品最低价（取自sku中最低价值）   | 单位：分                             |
| `price_high`          | int    | 商品高价（取自最低价所在sku对应划线价） | 单位：分                             |
| `price_line`          | int    | 划线价(取值price_low所在sku划线价)| 单位：分                             |
| `visit_num`           | int    | 访问量                            |                                      |
| `goods_tag`           | string | 商品标签                          |                                      |
| `goods_tag_is_show`   | int    | 商品标签是否展示                  | 0:不展示; 1:展示                    |
| `sale_status`         | int    | 上架状态                          | 0-下架, 1-上架, 2-待上架             |
| `is_timing_sale`      | int    | 是否定时上架                      | 1-是, 0-否                          |
| `timing_sale`         | string | 定时上架时间                      |                                      |
| `sale_at`             | string | 上架的时间                        |                                      |
| `has_distribute`      | int    | 是否参与推广分销                  | 0-否, 1-是                          |
| `video_img_url`       | string | 主图视频封面url                   |                                      |
| `is_goods_package`    | int    | 是否带货                          | 0-否, 1-是                          |
| `is_display`          | int    | 是否显示                          | 0-否(隐藏状态), 1-是(显示状态)        |
| `is_stop_sell`        | int    | 是否停售                          | 0-否, 1-是                          |
| `is_forbid`           | int    | 商品是否被封禁                    | 0-否, 1-是                          |
| `is_ignore`           | int    | 商品是否被忽略                    | 0-否, 1-是                          |
| `limit_purchase`      | int    | 限购数量                          |                                      |
| `stock_deduct_mode`   | int    | 扣库存方式                        | 0-付款减库存, 1-拍下减库存          |
| `appraise_num`        | int    | 评价数                            |                                      |
| `show_stock`          | int    | 是否展示库存                      | 0-不展示, 1-展示                    |
| `is_best`             | int    | 是否精品                          | 0-否, 1-是                          |
| `is_hot`              | int    | 是否热销产品                      | 0-否, 1-是                          |
| `is_new`              | int    | 是否新品                          | 0-否, 1-是                          |
| `is_recom`            | int    | 是否推荐                          | 0-否, 1-是                          |
| `distribution_pattern`| int    | 配送方式                          |                                      |
| `freight`             | int    | 运费                              | 单位：分                             |
| `audit_reason`        | string | 审核原因                          |                                      |
| `audit_time`          | string | 审核时间                          |                                      |
| `audit_user_id`       | string | 审核人user_id                     |                                      |
| `spu_extend`          | string | 业务侧扩展字段                    |                                      |
| `parent_spu_id`       | string | 父级的spu_id                      |                                      |
| `parent_app_id`       | string | 父级的app_id                      |                                      |
| `is_uniform_freight`  | int    | 是否是统一运费                    | 1:统一运费, 2:运费模板              |
| `freight_template_id` | int    | 运费模板ID                        |                                      |
| `img_url_compressed`  | string | 压缩后的列表配图url               |                                      |
| `is_deleted`          | int    | 是否删除                          | 0-正常, 1-已删除                    |
| `created_at`          | string | 创建时间                          |                                      |
| `updated_at`          | string | 更新时间                          |                                      |
| `attr`                | array  | 属性信息                          |                                      |
| `extend`              | array  | 扩展                              | 例如 `extend[0].sell_num` 售卖数量   |

## 返回示例

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
                "id": 72896,
                "img_url_compressed": "https://wechatapppro-1252524126.file.myqcloud.com/apppcHqlTPT3482/image/b_u_5b73e35149a67_ypMtbWtO/kvw18b1x0vfo.jpg",
                "is_best": 0,
                "is_deleted": 0,
                "is_display": 1,
                "is_forbid": 0,
                "is_goods_package": 0,
                "is_hot": 0,
                "is_ignore": 0,
                "is_new": 0,
                "price_high": 300,
                "price_line": 0,
                "price_low": 300,
                "resource_id": "g_61a4a307a6344_DfOA1bCn",
                "resource_type": 41,
                "sale_at": "2021-11-29 17:53:12",
                "sale_status": 1,
                "sell_type": 1,
                "show_stock": 1,
                "spu_extend": "",
                "spu_id": "g_61a4a307a6344_DfOA1bCn",
                "spu_type": "VCP",
                "stock_deduct_mode": 0,
                "timing_sale": "",
                "updated_at": "0000-00-00 00:00:00",
                "video_img_url": "",
                "visit_num": 0
            }
        ],
        "total": 46598
    },
    "msg": "success"
}