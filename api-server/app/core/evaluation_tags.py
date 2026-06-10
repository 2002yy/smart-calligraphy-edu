"""书法评测标签常量 —— 后端全局唯一来源

所有模块（Qwen 白名单、仪表盘统计、标签趋势）应从此文件导入，
避免 POSITIVE_TAGS / ISSUE_TAGS / TAG_CATEGORIES 出现多个副本。

设计原则：
1. 模型能从单张静态图片判断
2. 学生能理解，教师端能展示
3. 数量适中，不扩散选择
"""

# ── 正向标签（16 个）─────────────────────────────────────────────
POSITIVE_TAGS: set[str] = {
    # 结构 / 结体
    "结构工整",
    "结构稳定",
    "主笔突出",
    "收放自然",
    "疏密得当",
    "穿插合理",
    "避让自然",
    # 重心
    "重心稳当",
    "重心居中",
    # 笔画 / 笔法
    "笔法到位",
    "笔画有力",
    "运笔流畅",
    "起收笔清晰",
    # 布局 / 章法
    "大小协调",
    "间距均匀",
    # 呈现 / 整洁
    "整体整洁",
}

# ── 问题标签（40 个）─────────────────────────────────────────────
ISSUE_TAGS: set[str] = {
    # 结构 / 结体
    "结构失衡",
    "结构松散",
    "中宫松散",
    "中宫过紧",
    "主笔不突出",
    "比例失调",
    "部件错位",
    "部件拥挤",
    "穿插不当",
    "避让不足",
    "收放失衡",
    "字形歪斜",
    # 重心
    "重心不稳",
    "重心偏左",
    "重心偏右",
    "重心偏上",
    "重心偏下",
    "左右失衡",
    "上下失衡",
    # 笔画 / 笔法
    "笔法有误",
    "运笔生硬",
    "笔画无力",
    "笔画过细",
    "笔画过粗",
    "粗细失衡",
    "起笔草率",
    "收笔草率",
    "起收笔不清",
    "横画不稳",
    "竖画不直",
    "撇捺角度不当",
    "转折生硬",
    # 布局 / 章法
    "大小不一",
    "间距不均",
    "行列不齐",
    "布局拥挤",
    "留白不当",
    # 呈现 / 图片质量
    "墨迹不匀",
    "页面不整洁",
    "图像不清晰",
}

ALLOWED_TAGS: set[str] = POSITIVE_TAGS | ISSUE_TAGS

# ── 标签 → 维度分类映射（用于统计分组）────────────────────────
TAG_CATEGORIES: dict[str, str] = {
    # 正向
    "结构工整": "structure",
    "结构稳定": "structure",
    "主笔突出": "structure",
    "收放自然": "structure",
    "疏密得当": "structure",
    "穿插合理": "structure",
    "避让自然": "structure",
    "重心稳当": "center",
    "重心居中": "center",
    "笔法到位": "stroke",
    "笔画有力": "stroke",
    "运笔流畅": "stroke",
    "起收笔清晰": "stroke",
    "大小协调": "layout",
    "间距均匀": "layout",
    "整体整洁": "presentation",
    # 结构问题
    "结构失衡": "structure",
    "结构松散": "structure",
    "中宫松散": "structure",
    "中宫过紧": "structure",
    "主笔不突出": "structure",
    "比例失调": "structure",
    "部件错位": "structure",
    "部件拥挤": "structure",
    "穿插不当": "structure",
    "避让不足": "structure",
    "收放失衡": "structure",
    "字形歪斜": "structure",
    # 重心问题
    "重心不稳": "center",
    "重心偏左": "center",
    "重心偏右": "center",
    "重心偏上": "center",
    "重心偏下": "center",
    "左右失衡": "center",
    "上下失衡": "center",
    # 笔法问题
    "笔法有误": "stroke",
    "运笔生硬": "stroke",
    "笔画无力": "stroke",
    "笔画过细": "stroke",
    "笔画过粗": "stroke",
    "粗细失衡": "stroke",
    "起笔草率": "stroke",
    "收笔草率": "stroke",
    "起收笔不清": "stroke",
    "横画不稳": "stroke",
    "竖画不直": "stroke",
    "撇捺角度不当": "stroke",
    "转折生硬": "stroke",
    # 布局问题
    "大小不一": "layout",
    "间距不均": "layout",
    "行列不齐": "layout",
    "布局拥挤": "layout",
    "留白不当": "layout",
    # 呈现问题
    "墨迹不匀": "presentation",
    "页面不整洁": "presentation",
    "图像不清晰": "presentation",
}


def tag_category(tag: str) -> str:
    """返回标签所属维度，未知标签返回 'other'。"""
    return TAG_CATEGORIES.get(tag, "other")


def is_positive(tag: str) -> bool:
    """判断标签是否为正向标签。"""
    return tag in POSITIVE_TAGS


def is_issue(tag: str) -> bool:
    """判断标签是否为问题标签。"""
    return tag in ISSUE_TAGS
