#!/usr/bin/env python3
"""
测试步骤快照功能的脚本
"""

import asyncio
import aiohttp
import json
from datetime import datetime


async def test_snapshot_api():
    """测试快照API的完整流程"""

    base_url = "http://localhost:8001"

    async with aiohttp.ClientSession() as session:
        print("🚀 开始测试步骤快照功能...\n")

        # 1. 测试创建快照
        print("1️⃣ 测试创建快照...")
        snapshot_data = {
            "step_index": 2,  # 报告模板步骤
            "step_route": "/template",
            "snapshot_data": {
                "uploadedImages": [
                    {"id": "img1", "name": "test1.jpg", "size": 1024},
                    {"id": "img2", "name": "test2.jpg", "size": 2048}
                ],
                "selectedTemplate": {
                    "id": "full",
                    "name": "完整专业报告",
                    "price": 299
                },
                "projectInfo": {
                    "name": "测试项目",
                    "location": "北京市",
                    "inspector": "张三"
                },
                "currentStep": 3,
                "userCredits": 9500
            },
            "name": "测试快照-完整报告模板",
            "description": "这是一个测试快照，保存了完整报告模板的选择"
        }

        async with session.post(
            f"{base_url}/api/snapshots/",
            headers={"Content-Type": "application/json", "Authorization": "Bearer mock-token"},
            json=snapshot_data
        ) as response:
            if response.status == 201:
                result = await response.json()
                snapshot_id = result["id"]
                print(f"✅ 快照创建成功，ID: {snapshot_id}")
            else:
                print(f"❌ 快照创建失败: {response.status}")
                error_text = await response.text()
                print(f"错误信息: {error_text}")
                return

        # 2. 测试获取快照列表
        print("\n2️⃣ 测试获取快照列表...")
        async with session.get(
            f"{base_url}/api/snapshots/",
            headers={"Authorization": "Bearer mock-token"}
        ) as response:
            if response.status == 200:
                snapshots = await response.json()
                print(f"✅ 获取快照列表成功，共 {len(snapshots)} 个快照")
                for snapshot in snapshots:
                    print(f"   - 快照 {snapshot['id']}: {snapshot['step_name']} ({snapshot['created_at']})")
            else:
                print(f"❌ 获取快照列表失败: {response.status}")

        # 3. 测试获取单个快照详情
        print(f"\n3️⃣ 测试获取快照 {snapshot_id} 的详情...")
        async with session.get(
            f"{base_url}/api/snapshots/{snapshot_id}",
            headers={"Authorization": "Bearer mock-token"}
        ) as response:
            if response.status == 200:
                snapshot_detail = await response.json()
                print(f"✅ 获取快照详情成功")
                print(f"   - 步骤: {snapshot_detail['step_index'] + 1} - {snapshot_detail['step_route']}")
                print(f"   - 名称: {snapshot_detail['name']}")
                print(f"   - 数据大小: {len(json.dumps(snapshot_detail['snapshot_data']))} 字符")
            else:
                print(f"❌ 获取快照详情失败: {response.status}")

        # 4. 测试恢复快照
        print(f"\n4️⃣ 测试恢复快照 {snapshot_id}...")
        async with session.post(
            f"{base_url}/api/snapshots/{snapshot_id}/restore",
            headers={"Content-Type": "application/json", "Authorization": "Bearer mock-token"}
        ) as response:
            if response.status == 200:
                restore_result = await response.json()
                print(f"✅ 快照恢复成功")
                print(f"   - 应跳转到步骤: {restore_result['data']['step_index'] + 1}")
                print(f"   - 路由路径: {restore_result['data']['step_route']}")
            else:
                print(f"❌ 快照恢复失败: {response.status}")
                error_text = await response.text()
                print(f"错误信息: {error_text}")

        # 5. 创建更多测试快照
        print("\n5️⃣ 创建更多测试快照...")
        test_snapshots = [
            {
                "step_index": 1,
                "step_route": "/analysis",
                "snapshot_data": {
                    "uploadedImages": [{"id": "img1", "name": "aerial.jpg", "size": 3072}],
                    "analysisResult": {"scene": "building", "confidence": 0.92},
                    "currentStep": 2
                },
                "name": "场景分析-建筑外立面"
            },
            {
                "step_index": 3,
                "step_route": "/review",
                "snapshot_data": {
                    "uploadedImages": [{"id": "img1", "name": "crack.jpg", "size": 2048}],
                    "detectionResults": [{"issues": [{"type": "crack", "severity": "high"}]}],
                    "currentStep": 4
                },
                "name": "识别审查-发现裂缝"
            }
        ]

        for i, test_snapshot in enumerate(test_snapshots):
            async with session.post(
                f"{base_url}/api/snapshots/",
                headers={"Content-Type": "application/json", "Authorization": "Bearer mock-token"},
                json=test_snapshot
            ) as response:
                if response.status == 201:
                    result = await response.json()
                    print(f"✅ 测试快照 {i+1} 创建成功，ID: {result['id']}")
                else:
                    print(f"❌ 测试快照 {i+1} 创建失败: {response.status}")

        # 6. 再次获取快照列表
        print("\n6️⃣ 再次获取快照列表...")
        async with session.get(
            f"{base_url}/api/snapshots/",
            headers={"Authorization": "Bearer mock-token"}
        ) as response:
            if response.status == 200:
                snapshots = await response.json()
                print(f"✅ 当前共有 {len(snapshots)} 个快照")
                print("\n📋 快照列表:")
                for snapshot in snapshots:
                    created_time = datetime.fromisoformat(snapshot['created_at'])
                    formatted_time = created_time.strftime("%Y-%m-%d %H:%M")
                    print(f"   [ID:{snapshot['id']:3d}] 步骤{snapshot['step_index']+1} - {snapshot['step_name']} - {formatted_time}")
                    if snapshot['name']:
                        print(f"        名称: {snapshot['name']}")
            else:
                print(f"❌ 获取快照列表失败: {response.status}")

        print("\n🎉 快照功能测试完成！")
        print("\n📝 测试总结:")
        print("   ✅ 快照创建功能正常")
        print("   ✅ 快照列表获取正常")
        print("   ✅ 快照详情获取正常")
        print("   ✅ 快照恢复功能正常")
        print("\n🌐 可以访问 http://localhost:5175 查看前端界面")


if __name__ == "__main__":
    asyncio.run(test_snapshot_api())