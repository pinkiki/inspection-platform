"""
用户相关路由 - 使用数据库版本
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
import sqlite3
import os
from pydantic import BaseModel

router = APIRouter(prefix="/api/user", tags=["user"])

class UserInfo(BaseModel):
    id: int
    name: str
    email: str
    avatar: Optional[str] = None
    join_date: str
    total_projects: int
    total_reports: int
    last_login: str

class CreditRecord(BaseModel):
    id: int
    user_id: int
    type: str  # 'earn' or 'spend'
    amount: int
    reason: str
    balance_before: int
    balance_after: int
    timestamp: str

class StepSnapshot(BaseModel):
    id: int
    user_id: int
    step: int
    step_name: str
    timestamp: str
    image_count: int
    template_name: str
    data: dict  # JSON格式的快照数据

class UserProfile(BaseModel):
    user_info: UserInfo
    current_credits: int
    total_used: int
    total_earned: int
    level: str
    next_level_info: Optional[dict]
    total_credit_records: int  # 新增：总记录数

def get_db_connection():
    """获取数据库连接"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'inspection.db')
    return sqlite3.connect(db_path)

def calculate_user_level(total_earned: int) -> str:
    """根据累计获得积分计算用户等级"""
    if total_earned >= 5000: return "VIP 5"
    if total_earned >= 3000: return "VIP 4"
    if total_earned >= 2000: return "VIP 3"
    if total_earned >= 1000: return "VIP 2"
    if total_earned >= 500: return "VIP 1"
    return "普通用户"

def calculate_next_level_info(current_level: str, total_earned: int) -> dict:
    """获取下一等级信息"""
    levels = [
        {"name": "普通用户", "required": 0, "next": "VIP 1"},
        {"name": "VIP 1", "required": 500, "next": "VIP 2"},
        {"name": "VIP 2", "required": 1000, "next": "VIP 3"},
        {"name": "VIP 3", "required": 2000, "next": "VIP 4"},
        {"name": "VIP 4", "required": 3000, "next": "VIP 5"},
        {"name": "VIP 5", "required": 5000, "next": None}
    ]

    current_level_info = next((l for l in levels if l["name"] == current_level), None)
    if not current_level_info or not current_level_info["next"]:
        return None

    next_level_info = next((l for l in levels if l["name"] == current_level_info["next"]), None)
    if not next_level_info:
        return None

    credits_needed = max(0, next_level_info["required"] - total_earned)
    credits_from_last_level = total_earned - current_level_info["required"]
    credits_per_level = next_level_info["required"] - current_level_info["required"]
    progress = min(100, max(0, (credits_from_last_level / credits_per_level) * 100))

    return {
        "level": next_level_info["name"],
        "credits_needed": credits_needed,
        "progress": progress
    }

@router.get("/profile")
async def get_user_profile(user_id: int = 1):
    """获取用户个人信息"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 获取用户基本信息
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        raise HTTPException(status_code=404, detail="用户不存在")

    user_info = {
        "id": user_row[0],
        "name": user_row[1],
        "email": user_row[2],
        "avatar": user_row[3],
        "join_date": user_row[4],
        "total_projects": user_row[5] or 0,
        "total_reports": user_row[6] or 0,
        "last_login": user_row[7] or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # 获取积分记录
    cursor.execute('''
        SELECT * FROM credit_history
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT 50
    ''', (user_id,))

    credit_rows = cursor.fetchall()

    # 计算统计数据（使用正确的索引）
    # 数据库表结构: id(0), user_id(1), type(2), amount(3), reason(4), balance_before(5), balance_after(6), timestamp(7), created_at(8)
    current_credits = user_row[8]  # credits_balance
    total_used = sum(row[3] for row in credit_rows if row[2] == 'spend')      # row[2]=type, row[3]=amount
    total_earned = sum(row[3] for row in credit_rows if row[2] == 'earn')     # row[2]=type, row[3]=amount

    # 计算用户等级
    level = calculate_user_level(total_earned)
    next_level_info = calculate_next_level_info(level, total_earned)

    # 获取步骤快照
    cursor.execute('''
        SELECT * FROM step_snapshots
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT 10
    ''', (user_id,))

    snapshot_rows = cursor.fetchall()
    snapshots = [
        {
            "id": row[0], "user_id": row[1], "step": row[2], "step_name": row[3],
            "timestamp": row[4], "image_count": row[5], "template_name": row[6], "data": eval(row[7]) if row[7] else {}
        } for row in snapshot_rows
    ]

    conn.close()

    return {
        "user_info": user_info,
        "current_credits": current_credits,
        "total_used": total_used,
        "total_earned": total_earned,
        "level": level,
        "next_level_info": next_level_info,
        "step_snapshots": snapshots,
        "total_credit_records": len(credit_rows)
    }

@router.get("/credit-history")
async def get_credit_history(
    user_id: int = 1,
    page: int = 1,
    page_size: int = 10
):
    """获取用户积分历史记录（支持分页）"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 检查用户是否存在
    cursor.execute('SELECT COUNT(*) FROM users WHERE id = ?', (user_id,))
    if cursor.fetchone()[0] == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="用户不存在")

    # 获取总记录数（最多50条）
    cursor.execute('SELECT COUNT(*) FROM credit_history WHERE user_id = ?', (user_id,))
    total_records = min(cursor.fetchone()[0], 50)

    # 分页计算
    limit = min(page_size, 50)
    offset = (page - 1) * limit

    # 获取分页数据
    cursor.execute('''
        SELECT * FROM credit_history
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
    ''', (user_id, limit, offset))

    rows = cursor.fetchall()

    # 转换为字典格式
    # 数据库表结构: id(0), user_id(1), type(2), amount(3), reason(4), balance_before(5), balance_after(6), timestamp(7), created_at(8)
    records = [
        {
            "id": row[0],
            "user_id": row[1],
            "type": row[2],
            "amount": row[3],
            "reason": row[4],
            "balance_before": row[5],
            "balance_after": row[6],
            "timestamp": row[7]
        } for row in rows
    ]

    total_pages = (total_records + page_size - 1) // page_size

    conn.close()

    return {
        "records": records,
        "pagination": {
            "current_page": page,
            "page_size": limit,
            "total_records": total_records,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

def add_credit_record(user_id: int, record_type: str, amount: int, reason: str, balance_before: int, balance_after: int):
    """添加积分记录到数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 使用UTC时间戳
    current_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        INSERT INTO credit_history (user_id, type, amount, reason, balance_before, balance_after, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, record_type, amount, reason, balance_before, balance_after, current_time))

    # 更新用户积分余额
    cursor.execute('UPDATE users SET credits_balance = ? WHERE id = ?', (balance_after, user_id))

    conn.commit()
    conn.close()

def add_credit_record_async(user_id: int, record_type: str, amount: int, reason: str):
    """异步添加积分记录"""
    add_credit_record(user_id, record_type, amount, reason, 0, 0)

@router.post("/snapshots")
async def save_snapshot(snapshot: dict, user_id: int = 1):
    """保存步骤快照"""
    import json
    conn = get_db_connection()
    cursor = conn.cursor()

    # 检查是否已存在10条快照，如果有则删除最早的
    cursor.execute('''
        SELECT COUNT(*) FROM step_snapshots WHERE user_id = ?
    ''', (user_id,))
    count = cursor.fetchone()[0]

    if count >= 10:
        # 删除最早的快照
        cursor.execute('''
            DELETE FROM step_snapshots
            WHERE id IN (
                SELECT id FROM step_snapshots
                WHERE user_id = ?
                ORDER BY timestamp ASC
                LIMIT 1
            )
        ''', (user_id,))

    # 插入新快照
    cursor.execute('''
        INSERT INTO step_snapshots (user_id, step, step_name, image_count, template_name, data)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        snapshot.get('step', 0),
        snapshot.get('stepName', ''),
        snapshot.get('imageCount', 0),
        snapshot.get('templateName', ''),
        json.dumps(snapshot.get('data', {}))
    ))

    conn.commit()
    snapshot_id = cursor.lastrowid
    conn.close()

    return {"success": True, "snapshot_id": snapshot_id}

@router.post("/snapshots/{snapshot_id}/restore")
async def restore_snapshot(snapshot_id: int, user_id: int = 1):
    """恢复步骤快照"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 获取快照数据
    cursor.execute('''
        SELECT * FROM step_snapshots WHERE id = ? AND user_id = ?
    ''', (snapshot_id, user_id))

    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="快照不存在")

    snapshot = {
        "id": row[0],
        "user_id": row[1],
        "step": row[2],
        "step_name": row[3],
        "timestamp": row[4],
        "image_count": row[5],
        "template_name": row[6],
        "data": eval(row[7]) if row[7] else {}
    }

    conn.close()

    return {"success": True, "snapshot": snapshot}

if __name__ == "__main__":
    # 测试函数
    create_credit_tables(os.path.join(os.path.dirname(__file__), '..', 'inspection.db'))