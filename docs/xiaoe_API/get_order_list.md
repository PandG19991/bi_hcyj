# 获取订单列表 2.0 (xe.ecommerce.order.list/1.0.0)

用于获取店铺的订单列表。

**来源:** [官方文档](https://api-doc.xiaoe-tech.com/api_list/order/get_order_list_1.0.2.html)

## 基本信息

*   **接口地址:** `https://api.xiaoe-tech.com/xe.ecommerce.order.list/1.0.0`
*   **请求方式:** `POST`
*   **请求头:** `Content-Type: application/json`
*   **频率限制:** 1秒 20次
*   **权限要求:** (文档未明确说明，通常需要订单相关权限)

## 请求参数

| 参数名               | 必选 | 类型   | 说明                                                                                                                                                                                                                                                                                       |
| :------------------- | :--- | :----- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `access_token`       | 是   | string | 专属token                                                                                                                                                                                                                                                                                |
| `created_time_start` | 是   | string | 下单时间，开始。格式: `YYYY-MM-DD HH:MM:SS`。与结束时间的差值不能超过31天。                                                                                                                                                                                                                  |
| `created_time_end`   | 是   | string | 下单时间，截止。格式: `YYYY-MM-DD HH:MM:SS`。                                                                                                                                                                                                                                               |
| `aftersale_show_state`| 否  | int    | 售后状态: 0-无, 1-售后中, 2-部分退款, 3-全额退款                                                                                                                                                                                                                                          |
| `order_state`        | 否   | int    | 订单状态: 0-待付款, 1-待成交, 2-待发货, 3-已发货, 4-已完成, 5-已关闭                                                                                                                                                                                                                          |
| `settle_status`      | 否   | int    | 结算状态: 0-待结算, 1-结算中, 2-结算完成                                                                                                                                                                                                                                                   |
| `page`               | 否   | int    | 页码，从1开始，不传默认为1                                                                                                                                                                                                                                                                   |
| `page_size`          | 否   | int    | 单页记录条数，限制100以内，不传默认为100                                                                                                                                                                                                                                                     |
| `user_id`            | 否   | string | 用户ID，示例：`u_62cbf09430aa2_3pcvv3UNJ1`                                                                                                                                                                                                                                                 |
| `order_id`           | 否   | string | 订单号，示例：`o_1657532578_62cbf0a27b7b1_313860000`                                                                                                                                                                                                                                           |
| `order_type`         | 否   | string | 订单类型: 1-交易订单, 2-导入订单, 3-渠道采购订单（内容市场）, 4-兑换订单                                                                                                                                                                                                                        |
| `settle_time_start`  | 否   | string | 结算时间，开始。格式: `YYYY-MM-DD HH:MM:SS`。与结束时间差值不能超过31天。                                                                                                                                                                                                                      |
| `settle_time_end`    | 否   | string | 结算时间，截止。格式: `YYYY-MM-DD HH:MM:SS`。                                                                                                                                                                                                                                               |
| `pay_time_start`     | 否   | string | 支付时间，开始。格式: `YYYY-MM-DD HH:MM:SS`。与结束时间差值不能超过31天。                                                                                                                                                                                                                      |
| `pay_time_end`       | 否   | string | 支付时间，截止。格式: `YYYY-MM-DD HH:MM:SS`。                                                                                                                                                                                                                                               |
| `update_time_start`  | 否   | string | 更新时间，开始。格式: `YYYY-MM-DD HH:MM:SS`。与结束时间差值不能超过31天。                                                                                                                                                                                                                      |
| `update_time_end`    | 否   | string | 更新时间，截止。格式: `YYYY-MM-DD HH:MM:SS`。                                                                                                                                                                                                                                               |
| `order_by`           | 否   | string | 排序条件，默认按筛选时间进行排序，可传 `created_at`、`pay_time`、`settle_time`、`updated_at`                                                                                                                                                                                                      |
| `marketing_play`     | 否   | array  | 营销玩法筛选，1-推广员, 3-优惠券。目前只能传单数组 `[1]` 或 `[3]` 筛选订单。                                                                                                                                                                                                                    |
| `order_asc`          | 否   | string | 排序规则，`asc` 表示升序，默认按时间降序。                                                                                                                                                                                                                                                 |

### 特殊说明

1.  `created_time`、`settle_time`、`pay_time`、`update_time` 的开始和结束时间差值不能超过 **31天**。
2.  若传多个时间条件筛选订单，筛选时间与默认排序时间的优先级如下： `pay_time` > `settle_time` > `updated_time` > `created_time`。
3.  若所有时间条件都不传，假设当天时间为 `2023-04-18`，则默认筛选的订单条件为：`created_at >= '2023-03-19 00:00:00' AND created_at <= '2023-04-19 00:00:00'`。
4.  其他筛选时间场景逻辑较为复杂，建议参考官方文档或测试确认。

## 请求示例

```json
{
    "access_token": "xe_xxxxx",
    "page": 1, // 注意页码从 1 开始
    "page_size": 1,
    "aftersale_show_state": 1, // 售后中
    "settle_status": 0,        // 待结算
    "order_state": 1,          // 待成交
    "created_time_start": "2022-11-14 00:00:00",
    "created_time_end": "2022-11-14 12:00:00