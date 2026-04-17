# backend/app/scraper/dataprocess.py
"""
原始爬虫数据预处理
功能：为原始JSON添加 postal_code, keyword, index 字段
"""

import json
import re
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# 使用相对导入
from backend.app.config import settings, get_input_folder, get_processed_data_dir


def _extract_asins(url: str) -> list:
    """从SB广告URL中提取ASIN列表"""
    m = re.search(r"lp_asins=([^&]+)", url or "")
    if not m:
        return []
    return re.split(r"%2C", m.group(1), flags=re.IGNORECASE)


def _process_sb(item: dict) -> None:
    """处理SB广告：提取ASIN"""
    asins = _extract_asins(item.get("url", ""))
    if not asins:
        return
    if len(asins) == 1:
        item["asin"] = asins[0]
        if not item.get("inner_products"):
            item["ad_type"] = "SP"
    else:
        item["asin"] = ",".join(asins)


def process_file(file_path: str, postal_code: int = None) -> Path:
    """
    处理单个JSON文件
    
    :param file_path: 输入文件路径
    :param postal_code: 邮编（默认从配置读取）
    :return: 输出文件路径
    """
    path = Path(file_path)
    
    # 跳过已处理的文件
    if "_processed" in path.stem:
        print(f"⏭️ 跳过已处理文件: {path.name}")
        return None
    
    keyword = path.stem.split("_")[0]
    
    # 使用配置中的邮编
    if postal_code is None:
        postal_code = settings.DEFAULT_POSTAL_CODE
    
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    
    for item in data:
        item["postal_code"] = postal_code
        item["keyword"] = keyword
        item["index"] = f"{item['page']}_{item['data_index']}"
        
        if item.get("ad_type") == "SB":
            _process_sb(item)
    
    # 保存到处理文件夹
    output_folder = get_processed_data_dir()
    out_filename = path.stem + "_processed.json"
    out_path = output_folder / out_filename
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 处理完成: {out_path} ({len(data)} 条记录)")
    return out_path


def process_all_files(input_folder: str = None):
    """
    批量处理文件夹中的所有JSON文件
    """
    if input_folder is None:
        input_folder = settings.INPUT_FOLDER
    
    folder = Path(input_folder)
    
    if not folder.exists():
        print(f"❌ 文件夹不存在: {folder}")
        return []
    
    json_files = list(folder.glob("*.json"))
    
    # 排除已处理的文件
    json_files = [f for f in json_files if "_processed" not in f.stem]
    
    if not json_files:
        print(f"⚠️ 在 {folder} 中未找到未处理的JSON文件")
        return []
    
    print(f"📁 找到 {len(json_files)} 个JSON文件")
    
    results = []
    for file in json_files:
        print(f"\n📄 处理: {file.name}")
        out_path = process_file(str(file))
        if out_path:
            results.append(out_path)
    
    print(f"\n✅ 完成！共处理 {len(results)} 个文件")
    return results


# 命令行入口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='预处理爬虫JSON数据')
    parser.add_argument('-f', '--file', type=str, help='指定单个文件路径')
    parser.add_argument('-d', '--dir', type=str, help='指定输入文件夹')
    
    args = parser.parse_args()
    
    if args.file:
        process_file(args.file)
    else:
        process_all_files(args.dir)