"""Fix all 4 P0 issues"""
import os

ROOT = r"C:\Users\96967\Desktop\大创\code"

# === P0-1: Frontend polling in student.ts ===
fp1 = os.path.join(ROOT, "student-app", "src", "stores", "student.ts")
with open(fp1, encoding="utf-8") as f:
    s = f.read()

old_fn = """  async function submitAndEvaluate() {
    // 一键提交 + 评测：优先 Qwen，失败自动降级 Mock
    if (submitting.value || evaluating.value) return;

    evaluating.value = true;
    try {
      const homework = await submitHomework();
      if (!homework) return;

      try {
        await studentApi.startEvaluation(homework.id, "qwen", true);
      } catch {
        await studentApi.startEvaluation(homework.id, "auto", true);
      }
      evaluation.value = await studentApi.getEvaluation(homework!.id);
      growth.value = await studentApi.getGrowth(user.value!.id);
      setNotice("AI 评测完成，结果卡片已更新。", "success");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "AI 评测失败。", "error");
    } finally {
      evaluating.value = false;
    }
  }"""

new_fn = """  async function waitEvaluationFinished(homeworkId: number, maxRetries = 40): Promise<Evaluation> {
    for (let i = 0; i < maxRetries; i++) {
      const result = await studentApi.getEvaluation(homeworkId);
      if (result.status === "finished") return result;
      if (result.status === "failed") throw new Error("AI 评测失败，请稍后重试");
      await new Promise((r) => setTimeout(r, 1500));
    }
    throw new Error("评测超时，请稍后刷新查看结果");
  }

  async function submitAndEvaluate() {
    if (submitting.value || evaluating.value) return;
    evaluating.value = true;
    try {
      const homework = await submitHomework();
      if (!homework) return;

      let provider: "qwen" | "auto" = "qwen";
      try {
        await studentApi.startEvaluation(homework.id, "qwen", true);
      } catch {
        provider = "auto";
        await studentApi.startEvaluation(homework.id, "auto", true);
      }

      evaluation.value = await waitEvaluationFinished(homework.id);
      growth.value = await studentApi.getGrowth(user.value!.id);
      setNotice(provider === "qwen" ? "AI 评分已完成" : "AI 评测完成，结果卡片已更新。", "success");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "AI 评测失败。", "error");
    } finally {
      evaluating.value = false;
    }
  }"""

assert old_fn in s, "P0-1: submitAndEvaluate not found!"
s = s.replace(old_fn, new_fn)
with open(fp1, "w", encoding="utf-8") as f:
    f.write(s)
print("P0-1 OK")


# === P0-2: Backend thread failed status ===
fp2 = os.path.join(ROOT, "api-server", "app", "services", "evaluation_service.py")
with open(fp2, encoding="utf-8") as f:
    s = f.read()

old_except = """            except Exception:
                import traceback; traceback.print_exc()"""

new_except = """            except Exception:
                import traceback; traceback.print_exc()
                try:
                    _ev2 = EvaluationRepository.get_by_homework_id(_db, homework_id)
                    if _ev2:
                        EvaluationRepository.update_evaluation(_db, _ev2, status="failed", advice_text="AI 评测异常，请稍后重试或切换 Mock 模式。")
                        _db.commit()
                except Exception:
                    pass"""

assert old_except in s, "P0-2: except block not found!"
s = s.replace(old_except, new_except)
with open(fp2, "w", encoding="utf-8") as f:
    f.write(s)
print("P0-2 OK")


# === P0-3: CI path fix ===
fp3 = os.path.join(ROOT, ".github", "workflows", "ci.yml")
with open(fp3, encoding="utf-8") as f:
    s = f.read()

s = s.replace("working-directory: code/", "working-directory: ")
assert "working-directory: api-server" in s, "P0-3: path fix not applied!"
with open(fp3, "w", encoding="utf-8") as f:
    f.write(s)
print("P0-3 OK")


# === P0-4: package.json test scripts ===
for app in ["teacher-web", "student-app"]:
    fp4 = os.path.join(ROOT, app, "package.json")
    with open(fp4, encoding="utf-8") as f:
        s = f.read()

    # Add "test" script if not present
    if '"test"' not in s:
        s = s.replace('"preview": "vite preview"', '"preview": "vite preview",\n    "test": "vitest run"')
        with open(fp4, "w", encoding="utf-8") as f:
            f.write(s)
        print(f"P0-4 [{app}] OK")
    else:
        print(f"P0-4 [{app}] already has test script")

# Also add test step to CI for student-app
with open(fp3, encoding="utf-8") as f:
    s = f.read()

# Add vitest step for student-app (has the tests)
if "vitest" not in s:
    s = s.replace(
        "      - name: Build\n        run: npm run build",
        "      - name: Build\n        run: npm run build\n      - name: Test\n        run: npm test"
    )
    with open(fp3, "w", encoding="utf-8") as f:
        f.write(s)
    print("P0-4 [CI test step] OK")

print("\nAll P0 fixes applied!")
