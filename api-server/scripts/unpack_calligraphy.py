"""解压并导入书法数据集（按书法家分类的 GIF 版）

用法：
  1. 从 Google Drive 下载数据集：
     https://drive.google.com/file/d/1XznQ_wCSU3QvxnT5W5LeCZw4uF92FOcU
     将 calligraphy_by_artist.zip 放到 api-server/ 目录下

  2. 运行本脚本：
     python scripts/unpack_calligraphy.py

  3. 验证：
     curl "http://localhost:8000/api/v1/calligraphy/match?character=永"
"""

import zipfile
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZIP_PATH = ROOT / "calligraphy_by_artist.zip"
DB_PATH = ROOT / "smart_calligraphy.db"
STORAGE_TARGET = ROOT / "storage" / "calligraphy_db"
EXTRACT_DIR = ROOT / "storage" / "_calligraphy_raw"

# 书法家名称映射（目录名 → 中文名）
CALLIGRAPHER_MAP = {
    "ouyangxun": "欧阳询",
    "wangxizhi": "王羲之",
    "yan_zhenqing": "颜真卿",
    "liugongquan": "柳公权",
    "zhao_mengfu": "赵孟頫",
    "mi_fu": "米芾",
    "su_shi": "苏轼",
    "huang_tingjian": "黄庭坚",
    "cai_xiang": "蔡襄",
    "dong_qichang": "董其昌",
    "wen_zhengming": "文徵明",
    "tang_yin": "唐寅",
}


def main():
    if not ZIP_PATH.exists():
        print(f"❌ 请先将数据集文件放到: {ZIP_PATH}")
        print(f"   下载地址: https://drive.google.com/file/d/1XznQ_wCSU3QvxnT5W5LeCZw4uF92FOcU")
        sys.exit(1)

    # 1. 解压
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[1/3] 解压中（167MB）...")
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        zf.extractall(EXTRACT_DIR)
    print(f"      解压到: {EXTRACT_DIR}")

    # 2. 遍历目录，导入数据库 + 复制图片
    print(f"[2/3] 导入数据库...")
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS calligraphy_db (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            character TEXT NOT NULL,
            calligrapher TEXT NOT NULL,
            style TEXT DEFAULT '',
            source TEXT DEFAULT '',
            period TEXT DEFAULT '',
            image_path TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cb_char ON calligraphy_db(character)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cb_caller ON calligraphy_db(calligrapher)")

    # 先清空旧数据（种子数据不再需要）
    conn.execute("DELETE FROM calligraphy_db")
    STORAGE_TARGET.mkdir(parents=True, exist_ok=True)

    count = 0
    # 目录结构: calligrapher_name/character.gif
    for dir_path in sorted(EXTRACT_DIR.iterdir()):
        if not dir_path.is_dir():
            continue
        eng_name = dir_path.name  # 如 ouyangxun
        calligrapher = CALLIGRAPHER_MAP.get(eng_name, eng_name)

        for gif_file in sorted(dir_path.glob("*.gif")):
            char = gif_file.stem  # 文件名就是字
            if not char or len(char.encode("utf-8")) != 3:
                continue

            # 复制到 storage
            rel_path = f"{eng_name}/{char}.gif"
            dst = STORAGE_TARGET / rel_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            with open(gif_file, "rb") as f_src, open(dst, "wb") as f_dst:
                f_dst.write(f_src.read())

            conn.execute(
                "INSERT OR IGNORE INTO calligraphy_db (character, calligrapher, image_path) VALUES (?, ?, ?)",
                (char, calligrapher, f"/storage/calligraphy_db/{rel_path}"),
            )
            if conn.total_changes:
                count += 1

            if count > 0 and count % 5000 == 0:
                conn.commit()
                print(f"      已导入 {count} 条...")

    conn.commit()

    # 3. 清理临时文件
    print(f"[3/3] 清理临时文件...")
    import shutil
    shutil.rmtree(EXTRACT_DIR)

    total = conn.execute("SELECT COUNT(*) FROM calligraphy_db").fetchone()[0]
    print(f"\n✅ 完成！共导入 {total} 条碑帖记录")
    print(f"   数据库: {DB_PATH}")
    print(f"   图片:   {STORAGE_TARGET}")

    # 验证
    chars = conn.execute("SELECT DISTINCT character FROM calligraphy_db ORDER BY RANDOM() LIMIT 8").fetchall()
    print(f"\n   随机 8 个字（验证用）:")
    for (c,) in chars:
        arts = conn.execute("SELECT calligrapher FROM calligraphy_db WHERE character=? LIMIT 3", (c,)).fetchall()
        names = [a[0] for a in arts]
        print(f"      「{c}」 → {', '.join(names)} 等 {conn.execute('SELECT COUNT(*) FROM calligraphy_db WHERE character=?', (c,)).fetchone()[0]} 位书法家")

    conn.close()


if __name__ == "__main__":
    main()
