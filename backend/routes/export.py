"""
导出相关路由
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import io
from datetime import datetime

# PIL imports for image processing
from PIL import Image as PILImage, ImageDraw, ImageFont

from database import get_db
from models.schemas import ProjectInfo, ExportRequest
from services.metadata_extractor import MetadataExtractor

# PDF generation imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

router = APIRouter()

# 尝试注册中文字体
try:
    # 尝试使用系统中文字体
    font_paths = [
        '/System/Library/Fonts/PingFang.ttc',  # macOS
        '/System/Library/Fonts/STHeiti Light.ttc',  # macOS alternative
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',  # Linux
        '/usr/share/fonts/wqy-zenhei/wqy-zenhei.ttc',  # Linux alternative
        'C:/Windows/Fonts/msyh.ttc',  # Windows
        'C:/Windows/Fonts/simsun.ttc',  # Windows alternative
    ]
    
    font_registered = False
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                font_registered = True
                break
            except:
                continue
    
    if not font_registered:
        # 如果没有找到中文字体，使用默认字体
        CHINESE_FONT = 'Helvetica'
    else:
        CHINESE_FONT = 'ChineseFont'
except Exception as e:
    print(f"字体注册警告: {e}")
    CHINESE_FONT = 'Helvetica'


# PDF生成请求模型
class PDFGenerateRequest(BaseModel):
    format: str = 'pdf'
    projectInfo: Dict[str, Any]
    detectionResults: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    analysisResult: Optional[Dict[str, Any]] = None
    template: Optional[Dict[str, Any]] = None


def draw_bboxes_on_image(image_path, issues):
    """在图片上绘制bbox标注框
    
    Args:
        image_path: 图片文件路径
        issues: 问题列表，每个问题包含bbox信息
    
    Returns:
        PIL Image对象
    """
    # 打开图片
    img = PILImage.open(image_path)
    draw = ImageDraw.Draw(img)
    
    # 获取图片尺寸
    img_width, img_height = img.size
    
    # 遍历所有问题，绘制bbox
    for issue in issues:
        bbox = issue.get('bbox', {})
        if not bbox:
            continue
        
        # 百分比坐标转换为像素坐标
        x = (bbox.get('x', 0) / 100) * img_width
        y = (bbox.get('y', 0) / 100) * img_height
        w = (bbox.get('width', 0) / 100) * img_width
        h = (bbox.get('height', 0) / 100) * img_height
        
        # 确定颜色
        severity = issue.get('severity', '')
        color_map = {
            'danger': '#ff5a7a',
            'warning': '#ffd166',
            'caution': '#5bd6ff'
        }
        color = color_map.get(severity, '#5bd6ff')
        
        # 绘制矩形框（加粗线条）
        for offset in range(4):  # 绘制4次模拟加粗
            draw.rectangle(
                [x + offset, y + offset, x + w - offset, y + h - offset],
                outline=color,
                width=1
            )
        
        # 绘制标签背景和文字
        label = f"{issue.get('name', '问题')} ({int(issue.get('confidence', 0.8) * 100)}%)"
        
        # 尝试使用系统字体
        try:
            # 尝试macOS中文字体
            font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 24)
        except:
            try:
                # 尝试其他系统字体
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            except:
                # 使用默认字体
                font = ImageFont.load_default()
        
        # 计算文字大小
        try:
            bbox_text = draw.textbbox((0, 0), label, font=font)
            text_width = bbox_text[2] - bbox_text[0]
            text_height = bbox_text[3] - bbox_text[1]
        except:
            # 如果textbbox不可用，使用估算
            text_width = len(label) * 12
            text_height = 20
        
        # 绘制标签背景
        label_x = x
        label_y = max(0, y - text_height - 10)
        draw.rectangle(
            [label_x, label_y, label_x + text_width + 10, label_y + text_height + 10],
            fill=color
        )
        
        # 绘制文字
        draw.text((label_x + 5, label_y + 5), label, fill='white', font=font)
    
    return img


def create_styles():
    """创建PDF样式"""
    styles = getSampleStyleSheet()
    
    # 标题样式
    styles.add(ParagraphStyle(
        name='ChineseTitle',
        fontName=CHINESE_FONT,
        fontSize=24,
        leading=30,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=colors.HexColor('#1a1a2e')
    ))
    
    # 副标题样式
    styles.add(ParagraphStyle(
        name='ChineseSubtitle',
        fontName=CHINESE_FONT,
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        spaceAfter=30,
        textColor=colors.HexColor('#666666')
    ))
    
    # 节标题样式
    styles.add(ParagraphStyle(
        name='ChineseSectionTitle',
        fontName=CHINESE_FONT,
        fontSize=16,
        leading=22,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor('#2d3748')
    ))
    
    # 正文样式
    styles.add(ParagraphStyle(
        name='ChineseBody',
        fontName=CHINESE_FONT,
        fontSize=10,
        leading=16,
        spaceAfter=8,
        textColor=colors.HexColor('#4a5568')
    ))
    
    # 小字样式
    styles.add(ParagraphStyle(
        name='ChineseSmall',
        fontName=CHINESE_FONT,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#718096')
    ))
    
    return styles


def generate_pdf_report(data: PDFGenerateRequest) -> io.BytesIO:
    """生成PDF报告"""
    buffer = io.BytesIO()
    
    # 创建PDF文档
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = create_styles()
    elements = []
    
    project_info = data.projectInfo or {}
    statistics = data.statistics or {}
    detection_results = data.detectionResults or []
    analysis_result = data.analysisResult or {}
    template = data.template or {}
    
    # 调试信息
    print(f"\n=== PDF生成调试信息 ===")
    print(f"检测结果数量: {len(detection_results)}")
    if detection_results:
        print(f"第一个检测结果的键: {detection_results[0].keys()}")
        print(f"第一个检测结果示例: {detection_results[0]}")
    
    # ==================== 封面 ====================
    elements.append(Spacer(1, 3*cm))
    
    # 报告标题
    title = project_info.get('name', '巡检报告')
    elements.append(Paragraph(title, styles['ChineseTitle']))
    
    # 副标题
    scene_name = analysis_result.get('sceneName', '智能巡检')
    elements.append(Paragraph(f"{scene_name} - AI智能分析报告", styles['ChineseSubtitle']))
    
    elements.append(Spacer(1, 2*cm))
    
    # 基本信息表格
    cover_data = [
        ['项目名称', project_info.get('name', '-')],
        ['巡检区域', project_info.get('area', project_info.get('location', '-'))],
        ['巡检人员', project_info.get('inspector', '-')],
        ['所属单位', project_info.get('company', '-')],
        ['报告编号', project_info.get('reportId', '-')],
        ['生成时间', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
    ]
    
    cover_table = Table(cover_data, colWidths=[4*cm, 10*cm])
    cover_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4a5568')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2d3748')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(cover_table)
    
    elements.append(PageBreak())
    
    # ==================== 摘要统计 ====================
    elements.append(Paragraph("一、报告摘要", styles['ChineseSectionTitle']))
    
    # 统计数据
    total_images = statistics.get('totalImages', len(detection_results))
    issue_count = statistics.get('issueCount', 0)
    avg_confidence = statistics.get('avgConfidence', 0)
    
    # 计算问题分布
    danger_count = sum(1 for r in detection_results if r.get('status') == 'danger')
    warning_count = sum(1 for r in detection_results if r.get('status') == 'warning')
    success_count = sum(1 for r in detection_results if r.get('status') == 'success')
    
    summary_text = f"""
    本次巡检共处理 {total_images} 张图片，检测出 {issue_count} 个问题。
    其中严重问题 {danger_count} 个，一般问题 {warning_count} 个，
    正常图片 {success_count} 张。平均检测置信度为 {avg_confidence}%。
    """
    elements.append(Paragraph(summary_text.strip(), styles['ChineseBody']))
    
    elements.append(Spacer(1, 0.5*cm))
    
    # 统计表格
    stats_data = [
        ['统计项', '数值'],
        ['总图片数', str(total_images)],
        ['问题总数', str(issue_count)],
        ['严重问题', str(danger_count)],
        ['一般问题', str(warning_count)],
        ['正常图片', str(success_count)],
        ['平均置信度', f"{avg_confidence}%"],
    ]
    
    stats_table = Table(stats_data, colWidths=[6*cm, 6*cm])
    stats_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(stats_table)
    
    elements.append(Spacer(1, 1*cm))
    
    # ==================== 任务信息 ====================
    elements.append(Paragraph("二、任务信息", styles['ChineseSectionTitle']))
    
    task_data = [
        ['项目', '内容'],
        ['巡检时间', project_info.get('inspectionPeriod', '-')],
        ['采集设备', project_info.get('deviceInfo', '-')],
        ['飞行高度', project_info.get('avgAltitude', '-')],
        ['GSD', project_info.get('gsd', '-')],
        ['天气条件', project_info.get('weather', '-')],
        ['GPS范围', project_info.get('gpsRange', '-')],
    ]
    
    task_table = Table(task_data, colWidths=[4*cm, 10*cm])
    task_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(task_table)
    
    elements.append(Spacer(1, 1*cm))
    
    # ==================== AI分析信息 ====================
    elements.append(Paragraph("三、AI分析信息", styles['ChineseSectionTitle']))
    
    algorithms = analysis_result.get('algorithms', [])
    algorithms_str = ', '.join(algorithms) if algorithms else '-'
    
    ai_data = [
        ['项目', '内容'],
        ['场景类型', analysis_result.get('sceneName', '-')],
        ['使用算法', algorithms_str],
        ['Pipeline ID', project_info.get('pipelineId', '-')],
        ['Trace ID', project_info.get('traceId', '-')],
    ]
    
    ai_table = Table(ai_data, colWidths=[4*cm, 10*cm])
    ai_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(ai_table)
    
    elements.append(PageBreak())
    
    # ==================== 问题清单 ====================
    elements.append(Paragraph("四、问题清单", styles['ChineseSectionTitle']))
    
    # 收集所有问题
    all_issues = []
    for idx, result in enumerate(detection_results):
        issues = result.get('issues', [])
        for issue in issues:
            all_issues.append({
                'id': issue.get('id', f'ISS-{idx}'),
                'name': issue.get('name', issue.get('type', '-')),
                'severity': issue.get('severity', '-'),
                'confidence': issue.get('confidence', 0),
                'description': issue.get('description', '-'),
                'image': result.get('name', result.get('filename', '-'))
            })
    
    if all_issues:
        # 问题表格头
        issue_header = ['序号', '问题ID', '问题类型', '严重程度', '置信度', '来源图片']
        issue_rows = [issue_header]
        
        severity_map = {
            'danger': '严重',
            'warning': '一般',
            'caution': '轻微'
        }
        
        for idx, issue in enumerate(all_issues[:50]):  # 限制显示前50条
            issue_rows.append([
                str(idx + 1),
                issue['id'],
                issue['name'][:15] + '...' if len(issue['name']) > 15 else issue['name'],
                severity_map.get(issue['severity'], issue['severity']),
                f"{int(issue['confidence'] * 100)}%",
                issue['image'][:20] + '...' if len(issue['image']) > 20 else issue['image']
            ])
        
        issue_table = Table(issue_rows, colWidths=[1.5*cm, 2.5*cm, 3.5*cm, 2*cm, 2*cm, 3*cm])
        issue_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
        ]))
        elements.append(issue_table)
        
        if len(all_issues) > 50:
            elements.append(Paragraph(f"...共 {len(all_issues)} 条问题，此处仅显示前50条", styles['ChineseSmall']))
    else:
        elements.append(Paragraph("未检测到问题。", styles['ChineseBody']))
    
    elements.append(Spacer(1, 1*cm))
    
    # ==================== 问题详情（按图片分组） ====================
    if all_issues:
        elements.append(PageBreak())
        elements.append(Paragraph("五、问题详情（按图片分组）", styles['ChineseSectionTitle']))
        
        # 按图片分组问题
        image_groups = {}
        for result in detection_results:
            if result.get('issues') and len(result.get('issues', [])) > 0:
                image_id = result.get('id', '')
                image_groups[image_id] = {
                    'name': result.get('name', '') or result.get('filename', ''),
                    'preview_url': result.get('preview_url', '') or result.get('previewUrl', ''),
                    'filename': result.get('filename', ''),
                    'issues': result.get('issues', [])
                }
        
        # 只显示前5张图片
        for group_idx, (image_id, group_data) in enumerate(list(image_groups.items())[:5]):
            if group_idx > 0:
                elements.append(Spacer(1, 0.5*cm))
            
            # 图片标题
            elements.append(Paragraph(
                f"图片: {group_data['name']} （共 {len(group_data['issues'])} 个问题）",
                styles['ChineseBody']
            ))
            elements.append(Spacer(1, 0.2*cm))
            
            # 添加图片
            preview_url = group_data['preview_url']
            filename = group_data['filename']
            
            print(f"\n处理图片组 #{group_idx}: {group_data['name']}")
            print(f"preview_url: {preview_url}")
            print(f"filename: {filename}")
            
            # 转换为文件系统路径
            image_path = None
            if preview_url and preview_url.startswith('/uploads/'):
                image_path = preview_url[1:]
            elif preview_url:
                image_path = preview_url.lstrip('/')
            
            # 尝试多种可能的路径
            possible_paths = []
            if image_path:
                cwd = os.getcwd()
                possible_paths.extend([
                    image_path,
                    f"../{image_path}",
                    f"inspection-platform/{image_path}",
                    os.path.join(cwd, image_path),
                    os.path.join(cwd, 'inspection-platform', image_path)
                ])
            
            print(f"当前工作目录: {os.getcwd()}")
            print(f"尝试的路径: {possible_paths}")
            
            image_added = False
            for img_path in possible_paths:
                print(f"检查路径: {img_path}, 存在: {os.path.exists(img_path)}")
                if os.path.exists(img_path):
                    try:
                        # 在图片上绘制所有bbox标注
                        annotated_img = draw_bboxes_on_image(img_path, group_data['issues'])
                        
                        # 保存到临时BytesIO
                        img_buffer = io.BytesIO()
                        annotated_img.save(img_buffer, format='JPEG', quality=95)
                        img_buffer.seek(0)
                        
                        # 从BytesIO创建reportlab Image对象
                        img = Image(img_buffer, width=14*cm, height=10*cm, kind='proportional')
                        elements.append(img)
                        image_added = True
                        print(f"✓ 成功添加标注图片: {img_path}")
                        break
                    except Exception as e:
                        print(f"✗ 无法处理图片 {img_path}: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
            
            if not image_added:
                elements.append(Paragraph(
                    f"[证据图片: {filename or preview_url}]",
                    styles['ChineseSmall']
                ))
                print(f"✗ 未找到图片文件")
            
            # 列出所有问题
            elements.append(Spacer(1, 0.3*cm))
            elements.append(Paragraph("检测到的问题：", styles['ChineseBody']))
            
            severity_map = {
                'danger': '严重',
                'warning': '一般',
                'caution': '轻微'
            }
            
            for issue_idx, issue in enumerate(group_data['issues']):
                severity_color = {
                    'danger': '#e53e3e',
                    'warning': '#dd6b20',
                    'caution': '#3182ce'
                }.get(issue.get('severity', ''), '#4a5568')
                
                issue_name = issue.get('name', '') or issue.get('type', '-')
                issue_desc = issue.get('description', '-')
                issue_conf = issue.get('confidence', 0)
                issue_severity = severity_map.get(issue.get('severity', ''), issue.get('severity', '-'))
                
                elements.append(Paragraph(
                    f"{issue_idx + 1}. <font color='{severity_color}'>【{issue_severity}】</font> {issue_name}",
                    styles['ChineseBody']
                ))
                elements.append(Paragraph(
                    f"   描述: {issue_desc} | 置信度: {int(issue_conf * 100)}%",
                    styles['ChineseSmall']
                ))
                elements.append(Spacer(1, 0.1*cm))
            
            elements.append(Spacer(1, 0.3*cm))
        
        if len(image_groups) > 5:
            elements.append(Paragraph(f"...更多问题详情请查看完整报告（共 {len(image_groups)} 张图片）", styles['ChineseSmall']))
    
    # ==================== 审计信息 ====================
    elements.append(PageBreak())
    elements.append(Paragraph("六、审计信息", styles['ChineseSectionTitle']))
    
    audit_data = [
        ['项目', '内容'],
        ['报告编号', project_info.get('reportId', '-')],
        ['Trace ID', project_info.get('traceId', '-')],
        ['巡检人员', project_info.get('inspector', '-')],
        ['复核人员', project_info.get('reviewedBy', '待分配')],
        ['审批人员', project_info.get('approvedBy', '待分配')],
        ['生成时间', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
    ]
    
    audit_table = Table(audit_data, colWidths=[4*cm, 10*cm])
    audit_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(audit_table)
    
    elements.append(Spacer(1, 1*cm))
    
    # 备注
    notes = project_info.get('notes', '')
    if notes:
        elements.append(Paragraph("备注:", styles['ChineseBody']))
        elements.append(Paragraph(notes, styles['ChineseSmall']))
    
    elements.append(Spacer(1, 2*cm))
    
    # 页脚声明
    elements.append(Paragraph(
        "本报告由AI智能巡检系统自动生成，检测结果仅供参考。"
        "请结合实际情况进行判断和处置。",
        styles['ChineseSmall']
    ))
    
    # 构建PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer


@router.post("/generate-pdf")
async def generate_pdf(request: PDFGenerateRequest):
    """
    生成PDF报告并返回文件流
    """
    try:
        # 生成PDF
        pdf_buffer = generate_pdf_report(request)
        
        # 生成文件名
        project_name = request.projectInfo.get('name', '巡检报告')
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{project_name}_{date_str}.pdf"
        
        # 返回文件流
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{filename}"
            }
        )
    except Exception as e:
        print(f"PDF生成错误: {e}")
        raise HTTPException(status_code=500, detail=f"PDF生成失败: {str(e)}")


@router.put("/project-info/{project_id}")
async def update_project_info(project_id: str, info: ProjectInfo):
    """
    更新项目信息
    """
    async with get_db() as db:
        await db.execute(
            """UPDATE projects SET 
               name = ?, location = ?, inspection_date = ?, 
               inspector = ?, company = ?, status = ?
               WHERE id = ?""",
            (info.name, info.location, info.inspection_date,
             info.inspector, info.company, "info_updated", project_id)
        )
        await db.commit()
    
    return {"message": "项目信息已更新"}


@router.get("/project-info/{project_id}")
async def get_project_info(project_id: str):
    """
    获取项目信息
    """
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM projects WHERE id = ?",
            (project_id,)
        )
        project = await cursor.fetchone()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        return {
            "id": project["id"],
            "name": project["name"],
            "location": project["location"],
            "inspection_date": project["inspection_date"],
            "inspector": project["inspector"],
            "company": project["company"],
            "scene_type": project["scene_type"],
            "template_id": project["template_id"],
            "status": project["status"],
            "created_at": project["created_at"]
        }


@router.post("/generate/{project_id}")
async def generate_report(project_id: str, request: ExportRequest):
    """
    生成报告
    MVP阶段只返回模拟的成功响应
    """
    # 验证项目存在
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM projects WHERE id = ?",
            (project_id,)
        )
        project = await cursor.fetchone()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
    
    # MVP阶段返回模拟响应
    filename = f"inspection_report_{project_id}.{request.format}"
    
    return {
        "message": "报告生成成功",
        "download_url": f"/api/export/download/{project_id}/{request.format}",
        "filename": filename
    }


@router.get("/download/{project_id}/{format}")
async def download_report(project_id: str, format: str):
    """
    下载报告
    MVP阶段返回提示信息
    """
    # 验证项目存在
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT name FROM projects WHERE id = ?",
            (project_id,)
        )
        project = await cursor.fetchone()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
    
    # MVP阶段返回提示
    return {
        "message": "MVP阶段暂不支持实际下载，完整功能开发中",
        "project_id": project_id,
        "format": format,
        "project_name": project["name"]
    }


@router.get("/metadata/{project_id}")
async def get_export_metadata(project_id: str):
    """
    获取导出所需的自动提取元数据
    """
    # 验证项目存在
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM projects WHERE id = ?",
            (project_id,)
        )
        project = await cursor.fetchone()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 获取图片列表（模拟）
        images = []  # 实际应该从数据库查询
        
        # 获取检测结果（模拟）
        detection_results = []  # 实际应该从数据库查询
        
        # 提取元数据
        metadata = MetadataExtractor.extract_all_metadata(
            project_id=project_id,
            images=images,
            detection_results=detection_results,
            scene_type=project.get('scene_type', 'unknown'),
            algorithms=[]  # 实际应该从项目数据获取
        )
        
        return metadata


@router.post("/basic/{project_id}")
async def generate_basic_report(project_id: str):
    """
    生成基础报告PDF
    """
    # 验证项目存在
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM projects WHERE id = ?",
            (project_id,)
        )
        project = await cursor.fetchone()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
    
    # MVP阶段返回模拟响应
    filename = f"basic_report_{project_id}.pdf"
    
    return {
        "message": "基础报告生成成功",
        "download_url": f"/api/export/download/{project_id}/pdf",
        "filename": filename
    }


@router.get("/statistics/{project_id}")
async def get_statistics(project_id: str):
    """
    获取项目统计信息
    """
    async with get_db() as db:
        # 获取图片总数
        cursor = await db.execute(
            "SELECT COUNT(*) as count FROM images WHERE project_id = ?",
            (project_id,)
        )
        image_count = (await cursor.fetchone())["count"]
        
        # 获取检测结果统计
        cursor = await db.execute(
            """SELECT 
               COUNT(*) as total,
               SUM(CASE WHEN status = 'danger' THEN 1 ELSE 0 END) as danger_count,
               SUM(CASE WHEN status = 'warning' THEN 1 ELSE 0 END) as warning_count,
               SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
               AVG(confidence) as avg_confidence
               FROM detection_results WHERE project_id = ?""",
            (project_id,)
        )
        stats = await cursor.fetchone()
        
        # 获取问题总数
        cursor = await db.execute(
            """SELECT COUNT(*) as count FROM issues 
               WHERE detection_id IN (SELECT id FROM detection_results WHERE project_id = ?)""",
            (project_id,)
        )
        issue_count = (await cursor.fetchone())["count"]
        
        return {
            "project_id": project_id,
            "total_images": image_count,
            "detected_images": stats["total"] or 0,
            "danger_count": stats["danger_count"] or 0,
            "warning_count": stats["warning_count"] or 0,
            "success_count": stats["success_count"] or 0,
            "total_issues": issue_count,
            "avg_confidence": round(stats["avg_confidence"] or 0, 2)
        }
