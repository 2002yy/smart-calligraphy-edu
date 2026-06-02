"""导入 chinese-calligraphy-dataset（JPG 按字分类版）

直接扫描 zip 并提取图片到 storage/calligraphy_db/{字}/{编号}.jpg
"""

import sqlite3
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZIP_PATH = ROOT / "chinese-calligraphy-dataset.zip"
DB_PATH = ROOT / "smart_calligraphy.db"
STORAGE_TARGET = ROOT / "storage" / "calligraphy_db"


def main():
    if not ZIP_PATH.exists():
        print(f"❌ 未找到: {ZIP_PATH}")
        sys.exit(1)

    STORAGE_TARGET.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS calligraphy_db (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            character TEXT NOT NULL,
            calligrapher TEXT DEFAULT '',
            image_path TEXT NOT NULL UNIQUE,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cb_char ON calligraphy_db(character)")
    conn.execute("DELETE FROM calligraphy_db")

    print("正在扫描并提取图片（674MB，138,462 张）...")
    print("这需要几分钟，请等待...\n")

    zf = zipfile.ZipFile(str(ZIP_PATH), "r", metadata_encoding="gbk")
    names = zf.namelist()

    count = 0
    char_count = {}
    start = time.time()

    for entry in names:
        if not entry.endswith(".jpg") and not entry.endswith(".png"):
            continue

        # 路径: chinese-calligraphy-dataset/{字}/{编号}.jpg
        parts = entry.replace("\\", "/").split("/")
        if len(parts) != 3:
            continue

        char = parts[1]  # 中文字
        fname = parts[2]  # 编号.jpg
        if not char or not fname:
            continue

        # 只存编号，不存全名
        char_dir = STORAGE_TARGET / char
        char_dir.mkdir(exist_ok=True)
        dst = char_dir / fname

        if not dst.exists():
            data = zf.read(entry)
            dst.write_bytes(data)

        try:
            conn.execute(
                "INSERT OR IGNORE INTO calligraphy_db (character, image_path) VALUES (?, ?)",
                (char, f"/storage/calligraphy_db/{char}/{fname}"),
            )
            if conn.total_changes:
                count += 1
                char_count[char] = char_count.get(char, 0) + 1
        except sqlite3.IntegrityError:
            pass

        if count > 0 and count % 20000 == 0:
            conn.commit()
            elapsed = time.time() - start
            print(f"  {count}/138,462 张（{elapsed:.0f}s）...")

    conn.commit()
    zf.close()

    elapsed = time.time() - start
    total_char = len(char_count)
    print(f"\n✅ 完成！用时 {elapsed:.0f} 秒")
    print(f"   {count} 张图片，{total_char} 个汉字")

    # 验证
    for test_char in ["永", "大", "中", "人", "木"]:
        c = char_count.get(test_char, 0)
        if c > 0:
            print(f"   「{test_char}」→ {c} 张")
        else:
            print(f"   「{test_char}」→ 未找到")

    conn.close()


if __name__ == "__main__":
    main()
