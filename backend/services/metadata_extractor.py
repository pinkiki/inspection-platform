"""
元数据提取服务
从图片和项目数据中提取元数据用于报告生成
"""
import uuid
from datetime import datetime
from typing import Dict, List, Optional


class MetadataExtractor:
    """元数据提取器"""
    
    @staticmethod
    def generate_report_id(scene_type: str) -> str:
        """生成报告ID"""
        prefix_map = {
            'building': 'FCD',
            'solar': 'PV',
            'road': 'ROAD',
            'power': 'PWR'
        }
        prefix = prefix_map.get(scene_type, 'RPT')
        
        date_str = datetime.now().strftime('%Y%m%d')
        random_id = str(uuid.uuid4().int)[:4].zfill(4)
        
        return f"{prefix}-{date_str}-{random_id}"
    
    @staticmethod
    def generate_trace_id() -> str:
        """生成追踪ID"""
        return f"trace-{uuid.uuid4().hex[:12]}"
    
    @staticmethod
    def generate_pipeline_id(scene_type: str) -> str:
        """生成Pipeline ID"""
        year_month = datetime.now().strftime('%Y.%m')
        return f"PIPE-{scene_type.upper()}-{year_month}"
    
    @staticmethod
    def extract_gps_bounds(images: List[Dict]) -> Dict:
        """提取GPS边界"""
        coords = []
        for img in images:
            if img.get('gps_lat') and img.get('gps_lng'):
                coords.append({
                    'lat': img['gps_lat'],
                    'lng': img['gps_lng']
                })
        
        if not coords:
            return {
                'min_lat': None,
                'max_lat': None,
                'min_lng': None,
                'max_lng': None,
                'center_lat': None,
                'center_lng': None
            }
        
        lats = [c['lat'] for c in coords]
        lngs = [c['lng'] for c in coords]
        
        return {
            'min_lat': min(lats),
            'max_lat': max(lats),
            'min_lng': min(lngs),
            'max_lng': max(lngs),
            'center_lat': sum(lats) / len(lats),
            'center_lng': sum(lngs) / len(lngs)
        }
    
    @staticmethod
    def extract_time_range(images: List[Dict]) -> Dict:
        """提取拍摄时间范围"""
        # 模拟提取时间（实际应该从EXIF读取）
        now = datetime.now()
        return {
            'start_time': now.isoformat(),
            'end_time': now.isoformat()
        }
    
    @staticmethod
    def extract_device_info(images: List[Dict]) -> Dict:
        """提取设备信息"""
        # 模拟提取（实际应该从EXIF读取）
        return {
            'device_make': 'DJI',
            'device_model': 'Mavic 3',
            'camera_model': 'Hasselblad L2D-20c',
            'camera_resolution': '20MP'
        }
    
    @staticmethod
    def calculate_statistics(images: List[Dict], detection_results: List[Dict]) -> Dict:
        """计算统计信息"""
        total_size = sum(img.get('file_size', 0) for img in images)
        total_issues = sum(len(r.get('issues', [])) for r in detection_results)
        
        return {
            'total_images': len(images),
            'total_size': total_size,
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'total_issues': total_issues,
            'avg_altitude': '80m AGL',  # 模拟
            'gsd': '约 2.2 cm/pixel'     # 模拟
        }
    
    @staticmethod
    def extract_all_metadata(project_id: str, images: List[Dict], 
                            detection_results: List[Dict], 
                            scene_type: str,
                            algorithms: List[str]) -> Dict:
        """提取所有元数据"""
        return {
            'report_id': MetadataExtractor.generate_report_id(scene_type),
            'trace_id': MetadataExtractor.generate_trace_id(),
            'pipeline_id': MetadataExtractor.generate_pipeline_id(scene_type),
            'gps_bounds': MetadataExtractor.extract_gps_bounds(images),
            'time_range': MetadataExtractor.extract_time_range(images),
            'device_info': MetadataExtractor.extract_device_info(images),
            'statistics': MetadataExtractor.calculate_statistics(images, detection_results),
            'scene_type': scene_type,
            'algorithms': algorithms,
            'generated_at': datetime.now().isoformat(),
            'report_version': 'v1.0'
        }

