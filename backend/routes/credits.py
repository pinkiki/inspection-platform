"""
积分管理相关路由
"""
from fastapi import APIRouter, HTTPException
from typing import Dict
from datetime import datetime
from models.schemas import (
    UserCredits,
    DeductCreditsRequest,
    DeductCreditsResponse,
    CreditsHistoryResponse,
    CreditTransaction
)

router = APIRouter(prefix="/api/credits", tags=["credits"])

# 简单的内存存储，实际应该使用数据库
# 格式: {user_id: {credits: int, history: []}}
credits_store: Dict[str, Dict] = {}


def get_or_create_user_credits(user_id: str = "default_user") -> Dict:
    """获取或创建用户积分记录"""
    if user_id not in credits_store:
        credits_store[user_id] = {
            "credits": 10000,  # 初始积分
            "history": []
        }
    return credits_store[user_id]


@router.get("", response_model=UserCredits)
async def get_credits(user_id: str = "default_user"):
    """获取用户积分余额"""
    user_credits = get_or_create_user_credits(user_id)
    
    return UserCredits(
        user_id=user_id,
        credits=user_credits["credits"],
        history=[
            CreditTransaction(
                id=i,
                amount=trans["amount"],
                reason=trans["reason"],
                balance=trans["balance"],
                timestamp=trans["timestamp"]
            )
            for i, trans in enumerate(user_credits["history"])
        ]
    )


@router.post("/deduct", response_model=DeductCreditsResponse)
async def deduct_credits(request: DeductCreditsRequest, user_id: str = "default_user"):
    """扣除积分"""
    user_credits = get_or_create_user_credits(user_id)
    
    # 检查积分是否足够
    if user_credits["credits"] < request.amount:
        return DeductCreditsResponse(
            success=False,
            new_balance=user_credits["credits"],
            message="积分不足"
        )
    
    # 扣除积分
    user_credits["credits"] -= request.amount
    
    # 记录交易历史
    transaction = {
        "amount": -request.amount,
        "reason": request.reason,
        "balance": user_credits["credits"],
        "timestamp": datetime.now().isoformat()
    }
    user_credits["history"].insert(0, transaction)
    
    # 限制历史记录数量
    if len(user_credits["history"]) > 50:
        user_credits["history"] = user_credits["history"][:50]
    
    return DeductCreditsResponse(
        success=True,
        new_balance=user_credits["credits"],
        message=f"成功扣除 {request.amount} 积分"
    )


@router.post("/add")
async def add_credits(amount: int, reason: str, user_id: str = "default_user"):
    """增加积分（充值或退款）"""
    user_credits = get_or_create_user_credits(user_id)
    
    # 增加积分
    user_credits["credits"] += amount
    
    # 记录交易历史
    transaction = {
        "amount": amount,
        "reason": reason,
        "balance": user_credits["credits"],
        "timestamp": datetime.now().isoformat()
    }
    user_credits["history"].insert(0, transaction)
    
    # 限制历史记录数量
    if len(user_credits["history"]) > 50:
        user_credits["history"] = user_credits["history"][:50]
    
    return {
        "success": True,
        "new_balance": user_credits["credits"],
        "message": f"成功增加 {amount} 积分"
    }


@router.get("/history", response_model=CreditsHistoryResponse)
async def get_credits_history(user_id: str = "default_user", limit: int = 50):
    """获取积分历史记录"""
    user_credits = get_or_create_user_credits(user_id)
    
    history = user_credits["history"][:limit]
    
    return CreditsHistoryResponse(
        history=[
            CreditTransaction(
                id=i,
                amount=trans["amount"],
                reason=trans["reason"],
                balance=trans["balance"],
                timestamp=trans["timestamp"]
            )
            for i, trans in enumerate(history)
        ],
        current_balance=user_credits["credits"]
    )

