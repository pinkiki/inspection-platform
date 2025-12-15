"""
积分管理相关路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict
from datetime import datetime, timezone
import sqlite3
import os

router = APIRouter(prefix="/api/credits", tags=["credits"])


def get_db_connection():
    """获取数据库连接"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'inspection.db')
    return sqlite3.connect(db_path)


class DeductCreditsRequest(BaseModel):
    user_id: int
    amount: int
    reason: str
    balance_before: int
    balance_after: int


class AddCreditsRequest(BaseModel):
    user_id: int
    amount: int
    reason: str
    balance_before: int
    balance_after: int


@router.post("/deduct")
async def deduct_credits(request: DeductCreditsRequest):
    """扣除积分并记录到数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 检查用户是否存在
        cursor.execute('SELECT credits_balance FROM users WHERE id = ?', (request.user_id,))
        user_row = cursor.fetchone()

        if not user_row:
            conn.close()
            return {"success": False, "message": "用户不存在"}

        # 检查积分是否足够
        if user_row[0] < request.amount:
            conn.close()
            return {"success": False, "message": "积分不足"}

        # 使用UTC时间戳
        current_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

        # 添加积分记录
        cursor.execute('''
            INSERT INTO credit_history (user_id, type, amount, reason, balance_before, balance_after, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (request.user_id, 'spend', request.amount, request.reason,
              request.balance_before, request.balance_after, current_time))

        # 更新用户积分余额
        cursor.execute('UPDATE users SET credits_balance = ? WHERE id = ?',
                      (request.balance_after, request.user_id))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "new_balance": request.balance_after,
            "message": f"成功扣除 {request.amount} 积分"
        }
    except Exception as e:
        conn.close()
        return {"success": False, "message": f"扣除积分失败: {str(e)}"}


@router.post("/add")
async def add_credits(request: AddCreditsRequest):
    """增加积分并记录到数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 检查用户是否存在
        cursor.execute('SELECT COUNT(*) FROM users WHERE id = ?', (request.user_id,))
        if cursor.fetchone()[0] == 0:
            conn.close()
            return {"success": False, "message": "用户不存在"}

        # 使用UTC时间戳
        current_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

        # 添加积分记录
        cursor.execute('''
            INSERT INTO credit_history (user_id, type, amount, reason, balance_before, balance_after, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (request.user_id, 'earn', request.amount, request.reason,
              request.balance_before, request.balance_after, current_time))

        # 更新用户积分余额
        cursor.execute('UPDATE users SET credits_balance = ? WHERE id = ?',
                      (request.balance_after, request.user_id))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "new_balance": request.balance_after,
            "message": f"成功增加 {request.amount} 积分"
        }
    except Exception as e:
        conn.close()
        return {"success": False, "message": f"增加积分失败: {str(e)}"}
