"""Update README with Alembic section and test count"""
import os

ROOT = r"C:\Users\96967\Desktop\大创\code"
fp = os.path.join(ROOT, "README.md")

with open(fp, encoding="utf-8") as f:
    s = f.read()

# Update test count 28 -> 29
s = s.replace("**28**", "**29**")

# Add Alembic section before Testing section
old = "## 7. \U0001f9ea Testing / Quality"
new = """## 7. \U0001f5c4️ Database Migration

Use Alembic for schema migration. Auto-runs on dev startup; manual for production.

```bash
cd api-server
alembic upgrade head           # apply pending migrations
alembic history                # view migration history
alembic revision --autogenerate -m "description"  # generate from model changes
```

- **dev** environment: `init_db()` runs `alembic upgrade head`, falls back to `create_all` on failure
- **production / staging**: migration failure blocks startup (no silent fallback)

Config in `alembic.ini` + `alembic/env.py` (auto-imports all models).

---

## 7. \U0001f9ea Testing / Quality"""

assert old in s, "Testing section not found!"
s = s.replace(old, new)

with open(fp, "w", encoding="utf-8") as f:
    f.write(s)
print("README updated")
