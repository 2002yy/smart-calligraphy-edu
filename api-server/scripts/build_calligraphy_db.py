"""碑帖数据库构建脚本

一键扫描碑帖图片目录，自动构建 SQLite 数据库。
支持两种数据源：
  A. chinese-calligraphy-dataset（GitHub 开源，138,499 张）
     https://github.com/luoyuqi-lab/chinese-calligraphy-dataset
     下载后 dataset 目录结构：
       chinese-calligraphy-dataset/
       ├── label_character.csv  (含 filename, character_id, character 等字段)
       └── 永/
       │   ├── 永_欧阳询_01.jpg
       │   └── 永_王羲之_01.jpg
       ├── 大/...

  B. 自定义目录（如 test-images/good/）

用法:
  python scripts/build_calligraphy_db.py
  python scripts/build_calligraphy_db.py --dataset <路径>  # 指定数据集路径
"""

import argparse
import csv
import sqlite3
import shutil
import sys
import time
from pathlib import Path

# 确保能找到 api-server
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "smart_calligraphy.db"
STORAGE_TARGET = ROOT / "storage" / "calligraphy_db"

# ============================================================
# 数据库表结构
# ============================================================
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS calligraphy_db (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character TEXT NOT NULL,         -- 字（永、大、中...）
    calligrapher TEXT NOT NULL,      -- 书法家
    style TEXT DEFAULT '',           -- 字体风格（欧楷、颜楷...）
    source TEXT DEFAULT '',          -- 碑帖出处
    period TEXT DEFAULT '',          -- 年代
    image_path TEXT NOT NULL UNIQUE, -- 相对于 storage/ 的路径
    description TEXT DEFAULT '',     -- 描述
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_cb_character ON calligraphy_db(character);
CREATE INDEX IF NOT EXISTS idx_b_calligrapher ON calligraphy_db(calligrapher);
"""


def connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript(CREATE_TABLE_SQL)
    return conn


def count_existing(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM calligraphy_db").fetchone()[0]


# ============================================================
# 数据源 A: chinese-calligraphy-dataset（按字分类 JPG 版）
# ============================================================
def import_char_dataset(conn: sqlite3.Connection, dataset_path: Path) -> int:
    """导入 chinese-calligraphy-dataset"""
    label_csv = dataset_path / "label_character.csv"
    if not label_csv.exists():
        print(f"  [SKIP] 未找到 {label_csv}")
        return 0

    count = 0
    with open(label_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row.get("filename", "").strip()
            char = row.get("character", "").strip()
            calligrapher = row.get("calligrapher", row.get("writer", "")).strip()
            if not filename or not char or not calligrapher:
                continue

            # 源文件路径
            src = dataset_path / char / filename
            if not src.exists():
                continue

            # 目标路径
            rel_path = f"{calligrapher}/{char}_{filename}"
            dst = STORAGE_TARGET / rel_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists():
                shutil.copy2(src, dst)

            try:
                conn.execute(
                    """INSERT OR IGNORE INTO calligraphy_db
                       (character, calligrapher, image_path) VALUES (?, ?, ?)""",
                    (char, calligrapher, f"/storage/calligraphy_db/{rel_path}"),
                )
                if conn.total_changes > 0:
                    count += 1
            except sqlite3.IntegrityError:
                pass

            if count > 0 and count % 5000 == 0:
                conn.commit()
                print(f"    已导入 {count} 条...")

    conn.commit()
    return count


# ============================================================
# 数据源 B: 按书法家/风格/字 三级目录
# ============================================================
def import_nested_dirs(conn: sqlite3.Connection, root: Path) -> int:
    """导入三级目录：书法家/字体/字.jpg"""
    count = 0
    for calligrapher_dir in sorted(root.iterdir()):
        if not calligrapher_dir.is_dir():
            continue
        calligrapher = calligrapher_dir.name

        for style_dir in sorted(calligrapher_dir.iterdir()):
            if not style_dir.is_dir():
                continue
            style = style_dir.name

            for img_file in sorted(style_dir.iterdir()):
                if not img_file.is_file():
                    continue
                # 文件名去掉后缀就是字
                char = img_file.stem
                if len(char.encode("utf-8")) != 3:  # 不是单个汉字
                    continue

                rel_path = f"{calligrapher}/{style}/{img_file.name}"
                dst = STORAGE_TARGET / rel_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                if not dst.exists():
                    shutil.copy2(img_file, dst)

                try:
                    conn.execute(
                        """INSERT OR IGNORE INTO calligraphy_db
                           (character, calligrapher, style, image_path) VALUES (?, ?, ?, ?)""",
                        (char, calligrapher, style, f"/storage/calligraphy_db/{rel_path}"),
                    )
                    if conn.total_changes > 0:
                        count += 1
                except sqlite3.IntegrityError:
                    pass

                if count > 0 and count % 1000 == 0:
                    conn.commit()
                    print(f"    已导入 {count} 条...")

    conn.commit()
    return count


# ============================================================
# 数据源 C: 已有 test-images/good/
# ============================================================
def import_test_images(conn: sqlite3.Connection, test_dir: Path) -> int:
    """导入已有测试图片作为种子数据"""
    # 文件名拼音 → 汉字映射
    PINYIN_MAP = {
        "yong": "永",
        "da": "大",
        "zhong": "中",
        "mu": "木",
        "ren": "人",
        "wangxizhi": "永",
        "ouyangxun": "永",
    }
    CALLIGRAPHER_MAP = {
        "wangxizhi": "王羲之",
        "ouyangxun": "欧阳询",
        "yan": "颜真卿",
    }

    count = 0
    for img_file in sorted(test_dir.iterdir()):
        if not img_file.is_file():
            continue
        fname = img_file.stem.lower()

        # 从文件名提取汉字（拼音映射）
        char = ""
        for pinyin, hanzi in PINYIN_MAP.items():
            if pinyin in fname:
                char = hanzi
                break
        if not char:
            continue

        # 从文件名猜测书法家
        calligrapher = "unknown"
        for key, name in CALLIGRAPHER_MAP.items():
            if key in fname:
                calligrapher = name
                break

        rel_path = f"seed/{img_file.name}"
        dst = STORAGE_TARGET / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(img_file, dst)

        try:
            conn.execute(
                """INSERT OR IGNORE INTO calligraphy_db
                   (character, calligrapher, image_path) VALUES (?, ?, ?)""",
                (char, calligrapher, f"/storage/calligraphy_db/{rel_path}"),
            )
            if conn.total_changes > 0:
                count += 1
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    return count


# ============================================================
# 主入口
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="构建碑帖数据库")
    parser.add_argument("--dataset", type=str, help="chinese-calligraphy-dataset 的路径")
    parser.add_argument("--nested", type=str, help="三级目录（书法家/字体/字）的根路径")
    args = parser.parse_args()

    STORAGE_TARGET.mkdir(parents=True, exist_ok=True)
    conn = connect_db()

    existing = count_existing(conn)
    print(f"当前数据库已有 {existing} 条碑帖记录\n")

    total = 0

    # 1. 导入已有测试图片（种子数据）
    test_dir = ROOT.parent / "test-images" / "good"
    if test_dir.exists():
        print(f"[种子] 扫描 {test_dir}...")
        c = import_test_images(conn, test_dir)
        print(f"  → 导入 {c} 条种子数据\n")
        total += c

    # 2. 导入大数据集（如果指定了路径）
    if args.dataset:
        dataset_path = Path(args.dataset)
        if dataset_path.exists():
            print(f"[数据集] 扫描 {dataset_path}...")
            c = import_char_dataset(conn, dataset_path)
            print(f"  → 导入 {c} 条\n")
            total += c
        else:
            print(f"[数据集] 路径不存在: {args.dataset}")

    # 3. 导入三级目录（如果指定了路径）
    if args.nested:
        nested_path = Path(args.nested)
        if nested_path.exists():
            print(f"[目录] 扫描 {nested_path}...")
            c = import_nested_dirs(conn, nested_path)
            print(f"  → 导入 {c} 条\n")
            total += c
        else:
            print(f"[目录] 路径不存在: {args.nested}")

    conn.close()

    if total > 0:
        print(f"✅ 共导入 {total} 条碑帖记录")
        print(f"   数据库: {DB_PATH}")
        print(f"   图片存储: {STORAGE_TARGET}")
    else:
        print("⚠️ 未导入任何数据")
        print("   可传入一个数据集路径再次运行：")
        print("   python scripts/build_calligraphy_db.py --dataset <数据集根目录>")

    # 打印前 10 条验证
    conn = connect_db()
    rows = conn.execute("SELECT character, calligrapher, image_path FROM calligraphy_db LIMIT 10").fetchall()
    conn.close()
    if rows:
        print(f"\n数据库前 {len(rows)} 条记录：")
        for r in rows:
            print(f"  字={r[0]}  书法家={r[1]}  路径={r[2]}")


if __name__ == "__main__":
    main()
