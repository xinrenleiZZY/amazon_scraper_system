import json
import re
import sys
from pathlib import Path

# 直接导入（因为 config.py 在父目录）
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings, get_input_folder, get_processed_data_dir
# .parents[1] = backend/app/scraper
# .parents[2] = backend/app
# .parents[3] = backend
# .parents[4] = 项目根目录
# ── 一键修改区 ──────────────────────────────
POSTAL_CODE = settings.DEFAULT_POSTAL_CODE                             # 邮编
RAW_DATA_DIR = get_input_folder()                                      # 输入文件夹路径
OUTPUT_DIR   = get_processed_data_dir()                                # 输出文件夹路径
# ────────────────────────────────────────────


def _extract_asins(url: str) -> list:
    m = re.search(r"lp_asins=([^&]+)", url or "")
    if not m:
        return []
    return re.split(r"%2C", m.group(1), flags=re.IGNORECASE)


def _process_sb(item: dict) -> None:
    asins = _extract_asins(item.get("url", ""))
    if not asins:
        return
    if len(asins) == 1:
        item["asin"] = asins[0]
        if not item.get("inner_products"):
            item["ad_type"] = "SP"
    else:
        item["asin"] = ",".join(asins)


def process(file_path: str) -> None:
    path = Path(file_path)
    keyword = path.stem.split("_")[0]

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    for item in data:
        item["postal_code"] = POSTAL_CODE
        item["keyword"] = keyword
        item["index"] = f"{item['page']}_{item['data_index']}"
        scraped_at = item.get("scraped_at", "")
        item["date"] = scraped_at[:10] if scraped_at else ""
        if item.get("ad_type") == "SB":
            _process_sb(item)

    out_path = OUTPUT_DIR / (path.stem + "_processed.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Done → {out_path}  ({len(data)} records)")


if __name__ == "__main__":
    folder = Path(RAW_DATA_DIR)
    json_files = list(folder.glob("*.json"))
    print(f"当前工作目录: {Path.cwd()}")
    print(f"RAW_DATA_DIR 配置: {RAW_DATA_DIR}")
    print(f"实际完整路径: {Path(RAW_DATA_DIR).absolute()}")
    print(f"文件夹是否存在: {Path(RAW_DATA_DIR).exists()}")
    if not json_files:
        print(f"No JSON files found in {folder}")
    else:
        print(f"Found {len(json_files)} JSON file(s)")
        for file in json_files:
            process(str(file))
