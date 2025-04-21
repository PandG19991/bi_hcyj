"""
小鹅通订单数据同步示例
"""
from datetime import datetime, timedelta
import time
from loguru import logger
import pymysql

from xiaoe_config import XIAOE_CONFIG
from xiaoe_client import XiaoeClient
from xiaoe_transformers import transform_order, transform_order_items
from retry_decorator import retry

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',  # 替换为实际的数据库主机
    'user': 'root',       # 替换为实际的数据库用户
    'password': 'password', # 替换为实际的数据库密码
    'database': 'xiaoe_sync',
    'charset': 'utf8mb4'
}

@retry(max_tries=3, delay=2, exceptions=(pymysql.Error,))
def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

def save_order(conn, order):
    """保存订单到数据库"""
    cursor = conn.cursor()
    try:
        # 检查订单是否已存在
        cursor.execute(
            "SELECT id FROM orders WHERE order_id = %s",
            (order['order_id'],)
        )
        exists = cursor.fetchone()
        
        if exists:
            # 更新订单
            sql = """
            UPDATE orders SET
                user_id = %s,
                price = %s,
                coupon_price = %s,
                refund_money = %s,
                order_state = %s,
                order_state_text = %s,
                resource_type = %s,
                resource_type_text = %s,
                ship_state = %s,
                ship_state_text = %s,
                pay_way = %s,
                client_type = %s,
                collection_way = %s,
                after_sales_state = %s,
                team_buy_state = %s,
                sales_state = %s,
                updated_at = NOW()
            WHERE order_id = %s
            """
            cursor.execute(sql, (
                order['user_id'],
                order['price'],
                order['coupon_price'],
                order['refund_money'],
                order['order_state'],
                order['order_state_text'],
                order['resource_type'],
                order['resource_type_text'],
                order['ship_state'],
                order['ship_state_text'],
                order['pay_way'],
                order['client_type'],
                order['collection_way'],
                order['after_sales_state'],
                order['team_buy_state'],
                order['sales_state'],
                order['order_id']
            ))
            logger.info(f"更新订单: {order['order_id']}")
        else:
            # 插入新订单
            sql = """
            INSERT INTO orders (
                order_id, user_id, price, coupon_price, refund_money,
                order_state, order_state_text, resource_type, resource_type_text,
                ship_state, ship_state_text, pay_way, client_type, collection_way,
                after_sales_state, team_buy_state, sales_state, created_at, pay_time
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            cursor.execute(sql, (
                order['order_id'],
                order['user_id'],
                order['price'],
                order['coupon_price'],
                order['refund_money'],
                order['order_state'],
                order['order_state_text'],
                order['resource_type'],
                order['resource_type_text'],
                order['ship_state'],
                order['ship_state_text'],
                order['pay_way'],
                order['client_type'],
                order['collection_way'],
                order['after_sales_state'],
                order['team_buy_state'],
                order['sales_state'],
                order['created_at'],
                order['pay_time']
            ))
            logger.info(f"插入新订单: {order['order_id']}")
        
        return True
    except Exception as e:
        logger.error(f"保存订单失败: {e}")
        return False
    finally:
        cursor.close()

def save_order_items(conn, items):
    """保存订单商品到数据库"""
    if not items:
        return True
    
    cursor = conn.cursor()
    try:
        # 删除旧的订单商品
        cursor.execute(
            "DELETE FROM order_items WHERE order_id = %s",
            (items[0]['order_id'],)
        )
        
        # 插入新的订单商品
        sql = """
        INSERT INTO order_items (
            order_id, product_id, product_name, quantity, price
        ) VALUES (
            %s, %s, %s, %s, %s
        )
        """
        
        for item in items:
            cursor.execute(sql, (
                item['order_id'],
                item['product_id'],
                item['product_name'],
                item['quantity'],
                item['price']
            ))
        
        logger.info(f"保存订单商品 {len(items)} 条, 订单ID: {items[0]['order_id']}")
        return True
    except Exception as e:
        logger.error(f"保存订单商品失败: {e}")
        return False
    finally:
        cursor.close()

def record_sync_task(conn, task_type, start_time, end_time, status, records_count=0, error_message=None):
    """记录同步任务状态"""
    cursor = conn.cursor()
    try:
        sql = """
        INSERT INTO sync_tasks (
            task_type, start_time, end_time, status, records_count, error_message
        ) VALUES (
            %s, %s, %s, %s, %s, %s
        )
        """
        cursor.execute(sql, (
            task_type,
            start_time,
            end_time,
            status,
            records_count,
            error_message
        ))
        conn.commit()
        logger.info(f"记录同步任务: {task_type}, 状态: {status}, 记录数: {records_count}")
    except Exception as e:
        logger.error(f"记录同步任务失败: {e}")
    finally:
        cursor.close()

def get_last_sync_time(conn, task_type='orders'):
    """获取上次同步的时间"""
    cursor = conn.cursor()
    try:
        sql = """
        SELECT MAX(end_time) FROM sync_tasks
        WHERE task_type = %s AND status = 'success'
        """
        cursor.execute(sql, (task_type,))
        result = cursor.fetchone()
        if result and result[0]:
            return result[0].strftime('%Y-%m-%d %H:%M:%S')
        
        # 如果没有记录，默认返回7天前的时间
        return (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logger.error(f"获取上次同步时间失败: {e}")
        return (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
    finally:
        cursor.close()

def sync_orders(start_time=None, end_time=None):
    """同步订单数据"""
    client = XiaoeClient(XIAOE_CONFIG)
    
    # 如果未指定时间范围，默认同步前一天的数据
    if not start_time:
        end_time_dt = datetime.now()
        start_time_dt = end_time_dt - timedelta(days=1)
        
        start_time = start_time_dt.strftime('%Y-%m-%d %H:%M:%S')
        end_time = end_time_dt.strftime('%Y-%m-%d %H:%M:%S')
    
    logger.info(f"开始同步订单数据, 时间范围: {start_time} 至 {end_time}")
    
    page = 1
    page_size = 50
    total_count = 0
    success_count = 0
    
    conn = get_db_connection()
    task_start_time = datetime.now()
    
    try:
        while True:
            response = client.get_orders(
                page=page,
                page_size=page_size,
                start_time=start_time,
                end_time=end_time,
                order_state=2  # 已支付成功的订单
            )
            
            if response.get('code') != 0:
                error_msg = f"获取订单列表失败: {response.get('msg')}"
                logger.error(error_msg)
                record_sync_task(
                    conn, 
                    'orders', 
                    start_time, 
                    end_time, 
                    'failed', 
                    total_count, 
                    error_msg
                )
                break
            
            orders = response.get('data', {}).get('list', [])
            if not orders:
                logger.info(f"没有更多订单数据，已同步 {total_count} 条")
                break
            
            total_count += len(orders)
            logger.info(f"获取订单数据 {len(orders)} 条，第 {page} 页")
            
            # 处理订单数据
            for order_data in orders:
                try:
                    # 转换数据格式
                    order = transform_order(order_data)
                    items = transform_order_items(order_data)
                    
                    # 保存到数据库
                    if save_order(conn, order) and save_order_items(conn, items):
                        success_count += 1
                        conn.commit()
                    else:
                        conn.rollback()
                        
                except Exception as e:
                    conn.rollback()
                    logger.error(f"处理订单数据失败: {e}")
            
            page += 1
            # 小鹅通API限制最多查询100页
            if page > 100:
                logger.info("已达到最大页数限制 (100页)")
                break
        
        # 记录同步任务状态
        task_end_time = datetime.now()
        record_sync_task(
            conn, 
            'orders', 
            start_time, 
            end_time, 
            'success', 
            success_count
        )
                
        logger.info(f"订单数据同步完成, 总计: {total_count}, 成功: {success_count}")
    except Exception as e:
        # 记录同步任务失败状态
        task_end_time = datetime.now()
        record_sync_task(
            conn, 
            'orders', 
            start_time, 
            end_time, 
            'failed', 
            success_count, 
            str(e)
        )
        logger.error(f"同步订单数据异常: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # 配置日志
    logger.add("logs/xiaoe_sync_{time}.log", rotation="10 MB", retention="7 days")
    
    try:
        # 获取数据库连接
        conn = get_db_connection()
        
        # 获取上次同步时间
        start_time = get_last_sync_time(conn)
        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn.close()
        
        # 同步订单数据
        sync_orders(start_time, end_time)
        
    except Exception as e:
        logger.error(f"执行同步任务失败: {e}") 