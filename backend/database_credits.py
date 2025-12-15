"""
创建积分相关数据库表
"""
import sqlite3
import os

def create_credit_tables(db_path):
    """创建积分相关的数据库表"""

    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建用户表（如果不存在）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            avatar TEXT,
            join_date TEXT NOT NULL,
            total_projects INTEGER DEFAULT 0,
            total_reports INTEGER DEFAULT 0,
            last_login TEXT,
            credits_balance INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 创建积分历史记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS credit_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('earn', 'spend')),
            amount INTEGER NOT NULL,
            reason TEXT NOT NULL,
            balance_before INTEGER NOT NULL,
            balance_after INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # 创建步骤快照表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS step_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            step INTEGER NOT NULL,
            step_name TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            image_count INTEGER DEFAULT 0,
            template_name TEXT,
            data TEXT, -- JSON格式的快照数据
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_credit_history_user_id ON credit_history(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_credit_history_timestamp ON credit_history(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_step_snapshots_user_id ON step_snapshots(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_step_snapshots_timestamp ON step_snapshots(timestamp)')

    # 检查是否已有用户，如果没有则创建默认用户
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]

    if user_count == 0:
        # 创建默认用户
        cursor.execute('''
            INSERT INTO users (id, name, email, join_date, credits_balance)
            VALUES (1, '张三', 'zhangsan@example.com', '2024-01-15', 1100)
        ''')

        # 添加初始积分记录
        cursor.execute('''
            INSERT INTO credit_history (user_id, type, amount, reason, balance_before, balance_after)
            VALUES (1, 'earn', 1000, '注册赠送', 0, 1000)
        ''')

        cursor.execute('''
            INSERT INTO credit_history (user_id, type, amount, reason, balance_before, balance_after)
            VALUES (1, 'earn', 50, '签到奖励', 1000, 1050)
        ''')

        cursor.execute('''
            INSERT INTO credit_history (user_id, type, amount, reason, balance_before, balance_after)
            VALUES (1, 'earn', 50, '活动奖励', 1050, 1100)
        ''')

    conn.commit()
    conn.close()
    print(f"积分相关表创建完成: {db_path}")

if __name__ == "__main__":
    db_path = os.path.join(os.path.dirname(__file__), 'inspection.db')
    create_credit_tables(db_path)