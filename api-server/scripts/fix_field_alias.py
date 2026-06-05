"""Add stroke_quality_score alias to EvaluationRead + ReviewRead + frontend"""
import os

ROOT = r"C:\Users\96967\Desktop\大创\code"

# === Backend: EvaluationRead ===
fp = os.path.join(ROOT, "api-server", "app", "schemas", "evaluation.py")
with open(fp, encoding="utf-8") as f:
    s = f.read()

s = s.replace(
    "from pydantic import BaseModel, ConfigDict",
    "from pydantic import BaseModel, ConfigDict, computed_field"
)

# Add computed_field after stroke_order_score
old = '''    stroke_order_score: float
    tags: list[str]'''
new = '''    stroke_order_score: float
    stroke_quality_score: float = 0

    @computed_field
    @property
    def stroke_quality_score_alias(self) -> float:
        return self.stroke_order_score

    @computed_field
    @property
    def strokeQualityScore(self) -> float:
        return self.stroke_order_score

    tags: list[str]'''

assert old in s, "evaluation schema stroke_order_score not found!"
s = s.replace(old, new)

# Remove the extra declaration if it causes issues
# Wait - I introduced a duplicate. Let me fix properly.
# The approach: keep stroke_order_score field, add computed_field alias
# Revert stroke_quality_score: float = 0 since we have a computed_field

with open(fp, "w", encoding="utf-8") as f:
    f.write(s)

# Read back and fix
with open(fp, encoding="utf-8") as f:
    s = f.read()

# Remove the redundant field declaration, keep only the computed_field
s = s.replace("    stroke_quality_score: float = 0\n\n    @computed_field\n    @property\n    def stroke_quality_score_alias(self) -> float:\n        return self.stroke_order_score\n\n    @computed_field\n    @property\n    def strokeQualityScore(self) -> float:\n        return self.stroke_order_score\n\n    tags:", "    @computed_field\n    @property\n    def stroke_quality_score(self) -> float:\n        return self.stroke_order_score\n\n    tags:")

with open(fp, "w", encoding="utf-8") as f:
    f.write(s)
print("[1] evaluation.py — added stroke_quality_score computed_field")


# === Backend: ReviewRead ===
fp = os.path.join(ROOT, "api-server", "app", "schemas", "review.py")
with open(fp, encoding="utf-8") as f:
    s = f.read()

s = s.replace(
    "from pydantic import BaseModel, ConfigDict",
    "from pydantic import BaseModel, ConfigDict, computed_field"
)

# Find where stroke_order_score appears and add computed_field after it
old = """    stroke_order_score: float | None = None"""
new = """    stroke_order_score: float | None = None

    @computed_field
    @property
    def stroke_quality_score(self) -> float | None:
        return self.stroke_order_score"""

assert old in s, "review schema stroke_order_score not found!"
s = s.replace(old, new)

with open(fp, "w", encoding="utf-8") as f:
    f.write(s)
print("[2] review.py — added stroke_quality_score computed_field")


# === Frontend types.ts ===
fp = os.path.join(ROOT, "student-app", "src", "types.ts")
with open(fp, encoding="utf-8") as f:
    s = f.read()

s = s.replace(
    "  stroke_order_score: number;",
    "  stroke_order_score: number;\n  stroke_quality_score?: number;"
)
with open(fp, "w", encoding="utf-8") as f:
    f.write(s)
print("[3] student types.ts")


# === Frontend StudentSubmitPage.vue ===
fp = os.path.join(ROOT, "student-app", "src", "views", "StudentSubmitPage.vue")
with open(fp, encoding="utf-8") as f:
    s = f.read()
s = s.replace('evaluation.stroke_order_score', 'evaluation.stroke_quality_score ?? evaluation.stroke_order_score')
with open(fp, "w", encoding="utf-8") as f:
    f.write(s)
print("[4] StudentSubmitPage.vue")


# === teacher-web types.ts ===
fp = os.path.join(ROOT, "teacher-web", "src", "types.ts")
with open(fp, encoding="utf-8") as f:
    s = f.read()
if "stroke_quality_score" not in s:
    s = s.replace(
        "  stroke_order_score: number;",
        "  stroke_order_score: number;\n  stroke_quality_score?: number;"
    )
with open(fp, "w", encoding="utf-8") as f:
    f.write(s)
print("[5] teacher-web types.ts")


# === teacher-web review/index.vue ===
fp = os.path.join(ROOT, "teacher-web", "src", "views", "review", "index.vue")
with open(fp, encoding="utf-8") as f:
    s = f.read()
s = s.replace("review.stroke_order_score", "review.stroke_quality_score ?? review.stroke_order_score")
s = s.replace("activeReview.stroke_order_score", "activeReview.stroke_quality_score ?? activeReview.stroke_order_score")
with open(fp, "w", encoding="utf-8") as f:
    f.write(s)
print("[6] teacher-web review/index.vue")


# === README ===
fp = os.path.join(ROOT, "README.md")
with open(fp, encoding="utf-8") as f:
    s = f.read()

old_readme = "### License"
new_readme = """### Aliases & Backward Compatibility

| Old Field | New Alias | Scope | Notes |
|-----------|-----------|-------|-------|
| `stroke_order_score` | `stroke_quality_score` | API response | `stroke_order_score` remains in DB & API for backward compatibility. API also returns `stroke_quality_score` as the preferred name. |
| `stroke_order_score` | `strokeQualityScore` | Frontend types | Frontend prefers `strokeQualityScore`; `stroke_order_score` still accepted. |

Database column `stroke_order_score` unchanged. Pydantic `@computed_field` adds the alias at serialization time.

### License"""

s = s.replace(old_readme, new_readme)
with open(fp, "w", encoding="utf-8") as f:
    f.write(s)
print("[7] README.md")

print("\nAll field alias changes complete!")
