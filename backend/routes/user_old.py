from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from models.user import UserProfile, CreditRecord, StepSnapshot

router = APIRouter(prefix="/api/user", tags=["user"])

# 模拟用户数据（实际应该从数据库获取）
USERS_DB = {
    1: {
        "id": 1,
        "name": "张三",
        "email": "zhangsan@example.com",
        "avatar": None,
        "join_date": "2024-01-15",
        "total_projects": 12,
        "total_reports": 8,
        "last_login": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
}

# 模拟积分记录数据 - 生成测试数据用于分页
def generate_credit_history():
    records = []
    current_balance = 10000

    # 注册赠送
    current_balance += 1000
    records.append({
        "id": 1, "user_id": 1, "type": "earn", "amount": 1000, "reason": "注册赠送",
        "timestamp": (datetime.now() - timedelta(days=90)).isoformat(), "balance": current_balance
    })

    # 生成45条测试记录
    for i in range(2, 48):
        # 随机类型和金额
        import random
        is_earn = random.choice([True, False]) if i % 5 != 0 else True  # 每5条中有1条是获得记录

        if is_earn:
            amount = random.choice([100, 200, 500])
            reason = random.choice(["签到奖励", "完成任务", "推荐奖励", "活动奖励"])
            current_balance += amount
        else:
            amount = random.choice([20, 99, 199, 299])
            reason = random.choice(["生成基础报告", "生成正射影像报告", "场景重新分析", "生成三维模型报告", "恢复步骤快照"])
            current_balance -= amount

        records.append({
            "id": i, "user_id": 1, "type": "earn" if is_earn else "spend",
            "amount": amount if is_earn else -amount, "reason": reason,
            "timestamp": (datetime.now() - timedelta(days=(90-i*2))).isoformat(), "balance": current_balance
        })

    return records

CREDIT_HISTORY_DB = {
    1: generate_credit_history()
}

# 模拟步骤快照数据
STEP_SNAPSHOTS_DB = {
    1: []
}

def get_user_level(total_earned: int) -> str:
    """根据累计获得积分计算用户等级"""
    if total_earned >= 5000: return "VIP 5"
    if total_earned >= 3000: return "VIP 4"
    if total_earned >= 2000: return "VIP 3"
    if total_earned >= 1000: return "VIP 2"
    if total_earned >= 500: return "VIP 1"
    return "普通用户"

def get_next_level_info(current_level: str, total_earned: int) -> dict:
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
    """获取用户个人信息（不包含完整的积分历史）"""
    # 获取用户基本信息
    if user_id not in USERS_DB:
        raise HTTPException(status_code=404, detail="用户不存在")

    user_info = USERS_DB[user_id]

    # 获取积分记录
    credit_records = CREDIT_HISTORY_DB.get(user_id, [])
    # 计算当前余额 = 最后一条记录的余额，如果没有则用store中的积分
    if credit_records:
        current_credits = credit_records[-1]["balance"]
    else:
        current_credits = 10000  # 默认积分
    total_used = sum(abs(r["amount"]) for r in credit_records if r["type"] == "spend")
    total_earned = sum(r["amount"] for r in credit_records if r["type"] == "earn")

    # 计算用户等级
    level = get_user_level(total_earned)
    next_level_info = get_next_level_info(level, total_earned)

    # 获取步骤快照
    snapshots = STEP_SNAPSHOTS_DB.get(user_id, [])

    return {
        "user_info": user_info,
        "current_credits": current_credits,
        "total_used": total_used,
        "total_earned": total_earned,
        "level": level,
        "next_level_info": next_level_info,
        "step_snapshots": snapshots,
        "total_credit_records": len(credit_records)  # 返回总记录数，用于分页
    }

@router.get("/credit-history")
async def get_credit_history(
    user_id: int = 1,
    page: int = 1,
    page_size: int = 10
):
    """获取用户积分历史记录（支持分页）"""
    if user_id not in USERS_DB:
        raise HTTPException(status_code=404, detail="用户不存在")

    credit_records = CREDIT_HISTORY_DB.get(user_id, [])

    # 最多只保留50条记录
    max_records = 50
    limited_records = credit_records[:max_records]

    # 分页计算
    total_records = len(limited_records)
    total_pages = (total_records + page_size - 1) // page_size
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    paginated_records = limited_records[start_idx:end_idx]

    return {
        "records": paginated_records,
        "pagination": {
            "current_page": page,
            "page_size": page_size,
            "total_records": total_records,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

@router.post("/snapshots")
async def create_snapshot(user_id: int = 1, snapshot_data: dict = None):
    """创建步骤快照"""
    if user_id not in STEP_SNAPSHOTS_DB:
        STEP_SNAPSHOTS_DB[user_id] = []

    snapshot = {
        "id": len(STEP_SNAPSHOTS_DB[user_id]) + 1,
        "user_id": user_id,
        "step": snapshot_data.get("step", 1),
        "step_name": snapshot_data.get("step_name", "步骤1"),
        "timestamp": datetime.now().isoformat(),
        "image_count": snapshot_data.get("image_count", 0),
        "template_name": snapshot_data.get("template_name", "未选择"),
        "data": snapshot_data or {}
    }

    # 添加到快照列表，最多保留10个
    STEP_SNAPSHOTS_DB[user_id].insert(0, snapshot)
    if len(STEP_SNAPSHOTS_DB[user_id]) > 10:
        STEP_SNAPSHOTS_DB[user_id] = STEP_SNAPSHOTS_DB[user_id][:10]

    return {"message": "快照创建成功", "snapshot_id": snapshot["id"]}

@router.post("/snapshots/{snapshot_id}/restore")
async def restore_snapshot(snapshot_id: int, user_id: int = 1):
    """恢复步骤快照"""
    if user_id not in STEP_SNAPSHOTS_DB:
        raise HTTPException(status_code=404, detail="用户快照不存在")

    snapshots = STEP_SNAPSHOTS_DB[user_id]
    snapshot = next((s for s in snapshots if s["id"] == snapshot_id), None)

    if not snapshot:
        raise HTTPException(status_code=404, detail="快照不存在")

    # 检查积分是否足够（恢复需要20积分）
    credit_records = CREDIT_HISTORY_DB.get(user_id, [])
    if credit_records:
        current_credits = credit_records[-1]["balance"]
    else:
        current_credits = 10000  # 默认积分
    if current_credits < 20:
        raise HTTPException(status_code=400, detail="积分不足，无法恢复快照")

    # 恢复快照（实际应该更新用户的当前项目状态）
    # 这里简化处理，只移除快照
    STEP_SNAPSHOTS_DB[user_id] = [s for s in snapshots if s["id"] != snapshot_id]

    # 扣除积分
    # 实际应该在这里调用积分扣除逻辑

    return {"message": "快照恢复成功", "restored_data": snapshot["data"]}

@router.get("/snapshots")
async def get_user_snapshots(user_id: int = 1):
    """获取用户的步骤快照列表"""
    return STEP_SNAPSHOTS_DB.get(user_id, [])

@router.delete("/snapshots/{snapshot_id}")
async def delete_snapshot(snapshot_id: int, user_id: int = 1):
    """删除步骤快照"""
    if user_id not in STEP_SNAPSHOTS_DB:
        raise HTTPException(status_code=404, detail="用户快照不存在")

    original_count = len(STEP_SNAPSHOTS_DB[user_id])
    STEP_SNAPSHOTS_DB[user_id] = [s for s in STEP_SNAPSHOTS_DB[user_id] if s["id"] != snapshot_id]

    if len(STEP_SNAPSHOTS_DB[user_id]) == original_count:
        raise HTTPException(status_code=404, detail="快照不存在")

    return {"message": "快照删除成功"}