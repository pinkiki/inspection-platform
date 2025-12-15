"""
模拟AI服务 - 用于MVP阶段的演示
"""
import random
from typing import List, Dict, Any
import uuid


class MockAIService:
    """模拟AI分析服务"""
    
    # 场景类型定义
    SCENE_TYPES = [
        {
            "id": "building",
            "name": "建筑外立面",
            "icon": "🏢",
            "description": "适用于建筑物外墙、玻璃幕墙的缺陷检测",
            "algorithms": ["外墙裂缝检测", "玻璃破损识别", "空鼓检测"]
        },
        {
            "id": "solar",
            "name": "光伏板",
            "icon": "☀️",
            "description": "适用于光伏电站的组件缺陷检测",
            "algorithms": ["热斑检测", "隐裂识别", "污染分析"]
        },
        {
            "id": "road",
            "name": "道路病害",
            "icon": "🛣️",
            "description": "适用于道路路面的病害检测",
            "algorithms": ["裂缝检测", "坑洞识别", "车辙分析"]
        },
        {
            "id": "power",
            "name": "电力设施",
            "icon": "⚡",
            "description": "适用于输电线路、变电设备的巡检",
            "algorithms": ["绝缘子检测", "导线异物", "设备锈蚀"]
        }
    ]
    
    # 问题类型定义
    ISSUE_TYPES = {
        "building": [
            {"type": "crack", "name": "裂缝", "severity": "danger", "description": "检测到长度约{length}cm的{direction}裂缝"},
            {"type": "stain", "name": "污渍", "severity": "warning", "description": "存在明显的水渍痕迹"},
            {"type": "damage", "name": "破损", "severity": "danger", "description": "局部区域存在明显破损"},
            {"type": "hollow", "name": "空鼓", "severity": "warning", "description": "检测到疑似空鼓区域"},
            {"type": "glass_crack", "name": "玻璃裂纹", "severity": "danger", "description": "玻璃表面存在裂纹"},
        ],
        "solar": [
            {"type": "hotspot", "name": "热斑", "severity": "danger", "description": "检测到异常高温热斑"},
            {"type": "crack", "name": "隐裂", "severity": "warning", "description": "电池片存在隐裂"},
            {"type": "dirt", "name": "污染", "severity": "caution", "description": "组件表面存在污染物"},
            {"type": "shadow", "name": "遮挡", "severity": "warning", "description": "存在局部遮挡"},
        ],
        "road": [
            {"type": "crack", "name": "裂缝", "severity": "warning", "description": "路面存在{type}裂缝"},
            {"type": "pothole", "name": "坑洞", "severity": "danger", "description": "检测到直径约{size}cm的坑洞"},
            {"type": "rut", "name": "车辙", "severity": "warning", "description": "存在明显车辙痕迹"},
            {"type": "subsidence", "name": "沉陷", "severity": "danger", "description": "局部路面沉陷"},
        ],
        "power": [
            {"type": "insulator_damage", "name": "绝缘子破损", "severity": "danger", "description": "绝缘子存在破损"},
            {"type": "foreign_object", "name": "异物", "severity": "warning", "description": "导线上发现异物"},
            {"type": "corrosion", "name": "锈蚀", "severity": "warning", "description": "金属部件出现锈蚀"},
            {"type": "deformation", "name": "变形", "severity": "caution", "description": "检测到轻微形变"},
        ]
    }
    
    @classmethod
    def analyze_scene(cls, image_count: int) -> Dict[str, Any]:
        """
        分析场景类型
        模拟返回最匹配的场景
        """
        # 随机选择一个场景作为主要识别结果
        primary_scene = random.choice(cls.SCENE_TYPES)
        
        # 为所有场景生成置信度
        results = []
        for scene in cls.SCENE_TYPES:
            if scene["id"] == primary_scene["id"]:
                confidence = 0.85 + random.random() * 0.12  # 0.85-0.97
            else:
                confidence = 0.3 + random.random() * 0.4  # 0.3-0.7
            
            results.append({
                **scene,
                "confidence": round(confidence, 2)
            })
        
        # 按置信度排序
        results.sort(key=lambda x: x["confidence"], reverse=True)
        
        return {
            "primary_scene": results[0],
            "all_scenes": results
        }
    
    @classmethod
    def detect_issues(cls, image_id: str, scene_type: str) -> Dict[str, Any]:
        """
        检测单张图片的问题
        """
        # 获取场景对应的问题类型
        issue_templates = cls.ISSUE_TYPES.get(scene_type, cls.ISSUE_TYPES["building"])
        
        # 决定是否有问题 (70%概率有问题)
        has_issue = random.random() > 0.3
        
        issues = []
        if has_issue:
            # 随机生成1-3个问题
            num_issues = random.randint(1, 3)
            selected_issues = random.sample(issue_templates, min(num_issues, len(issue_templates)))
            
            for issue_template in selected_issues:
                # 生成问题描述（替换模板变量）
                description = issue_template["description"]
                description = description.replace("{length}", str(random.randint(5, 30)))
                description = description.replace("{direction}", random.choice(["横向", "纵向", "斜向"]))
                description = description.replace("{type}", random.choice(["网状", "线性", "块状"]))
                description = description.replace("{size}", str(random.randint(5, 20)))
                
                issues.append({
                    "id": f"issue-{uuid.uuid4().hex[:8]}",
                    "type": issue_template["type"],
                    "name": issue_template["name"],
                    "severity": issue_template["severity"],
                    "description": description,
                    "confidence": round(0.6 + random.random() * 0.35, 2),
                    "bbox": {
                        "x": round(random.random() * 60 + 10, 1),
                        "y": round(random.random() * 60 + 10, 1),
                        "width": round(random.random() * 20 + 10, 1),
                        "height": round(random.random() * 20 + 10, 1)
                    }
                })
        
        # 计算整体置信度
        overall_confidence = round(0.7 + random.random() * 0.25, 2)
        
        # 确定状态
        if not issues:
            status = "success"
            suggestion = "状态良好，无需处理"
        elif any(i["severity"] == "danger" for i in issues):
            status = "danger"
            suggestion = "存在严重问题，建议立即处理"
        else:
            status = "warning"
            suggestion = "存在一般问题，建议安排检修"
        
        return {
            "image_id": image_id,
            "confidence": overall_confidence,
            "status": status,
            "issues": issues,
            "suggestion": suggestion,
            "gps": {
                "lat": round(31.2 + random.random() * 0.1, 6),
                "lng": round(121.4 + random.random() * 0.1, 6)
            }
        }
    
    @classmethod
    def get_report_templates(cls, scene_type: str) -> List[Dict[str, Any]]:
        """
        获取报告模板列表
        """
        return [
            {
                "id": "basic",
                "name": "基础检测报告",
                "description": "包含所有图像的问题检测、描述和处理建议",
                "icon": "📋",
                "features": ["单张图像问题标注", "问题清单汇总", "处理建议", "GPS定位信息"],
                "include_ortho": False,
                "include_3d": False,
                "estimated_time": "5-10 分钟",
                "price": "免费",
                "recommended": False
            },
            {
                "id": "ortho",
                "name": "正射影像报告",
                "description": "在基础报告上增加正射影像图，问题点位映射到正射图上",
                "icon": "🗺️",
                "features": ["基础报告全部功能", "正射影像生成", "问题点位映射", "区域统计分析"],
                "include_ortho": True,
                "include_3d": False,
                "estimated_time": "15-30 分钟",
                "price": "¥99",
                "recommended": False
            },
            {
                "id": "3d",
                "name": "三维模型报告",
                "description": "生成三维实景模型，问题点位在模型上立体展示",
                "icon": "🏗️",
                "features": ["基础报告全部功能", "三维模型重建", "问题三维标注", "量测功能"],
                "include_ortho": False,
                "include_3d": True,
                "estimated_time": "30-60 分钟",
                "price": "¥199",
                "recommended": False
            },
            {
                "id": "full",
                "name": "完整专业报告",
                "description": "包含正射影像和三维模型的完整专业巡检报告",
                "icon": "🎯",
                "features": ["基础报告全部功能", "正射影像图", "三维实景模型", "专业报告排版", "CAD导出"],
                "include_ortho": True,
                "include_3d": True,
                "estimated_time": "60-90 分钟",
                "price": "¥299",
                "recommended": True
            }
        ]


# 单例实例
mock_ai = MockAIService()

