"""
步骤快照API接口
"""
import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from database import get_db
from models import (
    StepSnapshot,
    StepSnapshotCreate,
    StepSnapshotResponse,
    SnapshotListItem,
    STEP_NAMES
)

router = APIRouter(prefix="/api/snapshots", tags=["快照"])
security = HTTPBearer()


async def get_current_user_id(token: str = Depends(security)) -> int:
    """获取当前用户ID（简化版本，实际应该解析JWT）"""
    # 这里应该从token中解析用户ID
    # 暂时返回固定用户ID 1
    return 1


@router.post("/", response_model=StepSnapshotResponse, status_code=status.HTTP_201_CREATED)
async def create_snapshot(
    snapshot_data: StepSnapshotCreate,
    user_id: int = Depends(get_current_user_id)
):
    """
    保存步骤快照

    - step_index: 当前步骤索引 (0-5)
    - step_route: 当前步骤路由路径
    - snapshot_data: 该步骤及之前的所有业务数据
    - name: 快照名称（可选）
    - description: 快照描述（可选）
    """
    try:
        # 验证步骤索引和路由是否匹配
        valid_routes = ["/", "/analysis", "/template", "/review", "/advanced", "/export"]
        if snapshot_data.step_route not in valid_routes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid step route"
            )

        # 将快照数据序列化为JSON字符串
        snapshot_json = json.dumps(snapshot_data.snapshot_data, ensure_ascii=False)

        # 插入数据库
        async with get_db() as db:
            # 先删除该用户在相同步骤的旧快照（保留离当前时间最近的）
            await db.execute(
                """
                DELETE FROM step_snapshots
                WHERE user_id = ? AND step_index = ?
                """,
                (user_id, snapshot_data.step_index)
            )

            # 插入新快照
            cursor = await db.execute(
                """
                INSERT INTO step_snapshots
                (user_id, step_index, step_route, snapshot_data, name, description, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    snapshot_data.step_index,
                    snapshot_data.step_route,
                    snapshot_json,
                    snapshot_data.name,
                    snapshot_data.description,
                    datetime.now().isoformat()
                )
            )

            snapshot_id = cursor.lastrowid
            await db.commit()

            # 获取创建的快照
            cursor = await db.execute(
                """
                SELECT id, step_index, step_route, name, description, created_at, updated_at
                FROM step_snapshots
                WHERE id = ?
                """,
                (snapshot_id,)
            )
            row = await cursor.fetchone()

            return StepSnapshotResponse(
                id=row["id"],
                step_index=row["step_index"],
                step_route=row["step_route"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                name=row["name"],
                description=row["description"]
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save snapshot: {str(e)}"
        )


@router.get("/", response_model=List[SnapshotListItem])
async def get_snapshots(
    user_id: int = Depends(get_current_user_id)
):
    """
    获取用户的所有步骤快照列表
    """
    try:
        async with get_db() as db:
            cursor = await db.execute(
                """
                SELECT id, step_index, step_route, name, created_at
                FROM step_snapshots
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id,)
            )
            rows = await cursor.fetchall()

            snapshots = []
            for row in rows:
                step_name = STEP_NAMES.get(row["step_index"], f"步骤 {row['step_index'] + 1}")
                snapshots.append(
                    SnapshotListItem(
                        id=row["id"],
                        step_index=row["step_index"],
                        step_route=row["step_route"],
                        step_name=step_name,
                        created_at=datetime.fromisoformat(row["created_at"]),
                        name=row["name"]
                    )
                )

            return snapshots

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch snapshots: {str(e)}"
        )


@router.get("/{snapshot_id}", response_model=StepSnapshot)
async def get_snapshot(
    snapshot_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """
    获取特定的步骤快照详情
    """
    try:
        async with get_db() as db:
            cursor = await db.execute(
                """
                SELECT id, user_id, step_index, step_route, snapshot_data,
                       name, description, created_at, updated_at
                FROM step_snapshots
                WHERE id = ? AND user_id = ?
                """,
                (snapshot_id, user_id)
            )
            row = await cursor.fetchone()

            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Snapshot not found"
                )

            # 解析快照数据
            snapshot_data = json.loads(row["snapshot_data"])

            return StepSnapshot(
                id=row["id"],
                user_id=row["user_id"],
                step_index=row["step_index"],
                step_route=row["step_route"],
                snapshot_data=snapshot_data,
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                name=row["name"],
                description=row["description"]
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch snapshot: {str(e)}"
        )


@router.delete("/{snapshot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_snapshot(
    snapshot_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """
    删除步骤快照
    """
    try:
        async with get_db() as db:
            cursor = await db.execute(
                "DELETE FROM step_snapshots WHERE id = ? AND user_id = ?",
                (snapshot_id, user_id)
            )

            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Snapshot not found"
                )

            await db.commit()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete snapshot: {str(e)}"
        )


@router.post("/{snapshot_id}/restore", response_model=dict)
async def restore_snapshot(
    snapshot_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """
    恢复步骤快照（返回快照数据和路由信息）

    前端根据返回的信息进行：
    1. 路由跳转
    2. 数据恢复
    3. 步骤条更新

    恢复快照需要扣除20积分
    """
    RESTORE_COST = 20  # 恢复快照所需的积分

    try:
        # 先检查用户积分是否足够
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT credits_balance FROM users WHERE id = ?",
                (user_id,)
            )
            user_row = await cursor.fetchone()

            if not user_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            current_credits = user_row[0]

            if current_credits < RESTORE_COST:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail=f"积分不足，恢复快照需要{RESTORE_COST}积分，当前余额：{current_credits}积分"
                )

            # 扣除积分
            balance_before = current_credits
            balance_after = current_credits - RESTORE_COST

            await db.execute(
                "UPDATE users SET credits_balance = ?, updated_at = ? WHERE id = ?",
                (balance_after, datetime.now().isoformat(), user_id)
            )

            # 记录积分变动历史
            await db.execute(
                """
                INSERT INTO credit_history
                (user_id, amount, type, reason, balance_before, balance_after, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    -RESTORE_COST,
                    'spend',
                    f'恢复步骤快照 (ID: {snapshot_id})',
                    balance_before,
                    balance_after,
                    datetime.now().isoformat()
                )
            )

            await db.commit()

        # 获取快照详情
        snapshot = await get_snapshot(snapshot_id, user_id)

        return {
            "success": True,
            "data": {
                "step_index": snapshot.step_index,
                "step_route": snapshot.step_route,
                "snapshot_data": snapshot.snapshot_data,
                "credits_deducted": RESTORE_COST,
                "balance_after": balance_after,
                "message": f"快照恢复成功，已扣除{RESTORE_COST}积分"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore snapshot: {str(e)}"
        )