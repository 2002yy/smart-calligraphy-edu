"""Replace submitting/evaluating booleans with explicit state machine"""
import sys, os

ROOT = r"C:\Users\96967\Desktop\大创\code"
fp = os.path.join(ROOT, "student-app", "src", "stores", "student.ts")

with open(fp, encoding="utf-8") as f:
    src = f.read()

# 1. Type definition
src = src.replace(
    'type NoticeType = "info" | "success" | "error";',
    'type NoticeType = "info" | "success" | "error";\ntype SubmitStage = "idle" | "uploading" | "uploaded" | "evaluating" | "waiting" | "finished" | "failed";'
)

# 2. Replace boolean refs
src = src.replace(
    "  const submitting = ref(false);\n  const evaluating = ref(false);",
    '  const submitStage = ref<SubmitStage>("idle");'
)

# 3. submitHomework: submitting -> submitStage
src = src.replace("submitting.value = true;", 'submitStage.value = "uploading";')
src = src.replace("submitting.value = false;", "")
# Fix the success path in submitHomework - add submitStage update
src = src.replace(
    '      growth.value = await studentApi.getGrowth(user.value.id);\n      setNotice("作业提交成功，可以继续发起 AI 评测。", "success");\n      return latestHomework.value;\n    } catch (error) {\n      setNotice(error instanceof Error ? error.message : "作业提交失败。", "error");\n      return null;\n    } finally {',
    '      submitStage.value = "uploaded";\n      setNotice("作业提交成功，可以继续发起 AI 评测。", "success");\n      return latestHomework.value;\n    } catch (error) {\n      submitStage.value = "failed";\n      setNotice(error instanceof Error ? error.message : "作业提交失败。", "error");\n      return null;\n    }'
)

# 4. evaluateHomework: evaluating -> submitStage
src = src.replace(
    '    evaluating.value = true;\n    if (provider === "openai") {',
    '    submitStage.value = "evaluating";\n    if (provider === "openai") {'
)
src = src.replace(
    '      setNotice(error instanceof Error ? error.message : "AI 评测失败。", "error");\n    } finally {\n      evaluating.value = false;\n    }',
    '      submitStage.value = "failed";\n      setNotice(error instanceof Error ? error.message : "AI 评测失败。", "error");\n    } finally {\n      submitStage.value = submitStage.value === "evaluating" ? "idle" : submitStage.value;\n    }'
)

# 5. submitAndEvaluate - complete rewrite using markers
old_sae = """  async function submitAndEvaluate() {
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

new_sae = """  async function submitAndEvaluate() {
    if (submitStage.value !== "idle") return;
    try {
      const homework = await submitHomework();
      if (!homework) { submitStage.value = "failed"; return; }

      submitStage.value = "evaluating";
      let provider: "qwen" | "auto" = "qwen";
      try { await studentApi.startEvaluation(homework.id, "qwen", true); }
      catch { provider = "auto"; await studentApi.startEvaluation(homework.id, "auto", true); }

      submitStage.value = "waiting";
      evaluation.value = await waitEvaluationFinished(homework.id);
      growth.value = await studentApi.getGrowth(user.value!.id);
      submitStage.value = "finished";
      setNotice(provider === "qwen" ? "AI 评分已完成" : "AI 评测完成，结果卡片已更新。", "success");
    } catch (error) {
      submitStage.value = "failed";
      setNotice(error instanceof Error ? error.message : "AI 评测失败。", "error");
    }
  }"""

if old_sae not in src:
    print("ERROR: submitAndEvaluate not found!")
    print("Trying line check...")
    for i, l in enumerate(src.split("\\n")):
        if "async function submitAndEvaluate" in l:
            print(f"Found at line {i+1}: {l.strip()}")
    sys.exit(1)
src = src.replace(old_sae, new_sae)

# 6. submitAndEvaluateWithOpenAI
old_sae2 = """  async function submitAndEvaluateWithOpenAI() {
    // DEPRECATED: 仅在调试时使用，默认隐藏
    if (submitting.value || evaluating.value) return;
    evaluating.value = true;
    try {
      const homework = await submitHomework();
      if (!homework) return;
      await evaluateHomework("openai");
    } finally {
      evaluating.value = false;
    }
  }"""

new_sae2 = """  async function submitAndEvaluateWithOpenAI() {
    // DEPRECATED: 仅在调试时使用，默认隐藏
    if (submitStage.value !== "idle") return;
    submitStage.value = "evaluating";
    try {
      const homework = await submitHomework();
      if (!homework) { submitStage.value = "failed"; return; }
      await evaluateHomework("openai");
    } finally {
      if (submitStage.value === "evaluating") submitStage.value = "idle";
    }
  }"""

if old_sae2 not in src:
    print("ERROR: submitAndEvaluateWithOpenAI not found!")
    sys.exit(1)
src = src.replace(old_sae2, new_sae2)

# 7. Return statement
src = src.replace(
    "    submitting,\n    evaluating,\n    submitAndEvaluate,",
    "    submitStage,\n    submitAndEvaluate,"
)

with open(fp, "w", encoding="utf-8") as f:
    f.write(src)
print("student.ts OK")

# ====== Vue template ======
fp2 = os.path.join(ROOT, "student-app", "src", "views", "StudentSubmitPage.vue")
with open(fp2, encoding="utf-8") as f:
    src2 = f.read()

# 1. Destructure
src2 = src2.replace(
    "const { user, loading, selectedTask, submitForm, latestHomework, evaluation, submitting, evaluating, previewUrl } =",
    "const { user, loading, selectedTask, submitForm, latestHomework, evaluation, submitStage, previewUrl } ="
)

# 2. uploadStage -> displayStage using submitStage
src2 = src2.replace(
    "const uploadStage = computed(() => {\n  if (evaluating.value) {\n    return \"evaluating\";\n  }\n\n  if (evaluation.value) {\n    return \"review\";\n  }\n\n  if (latestHomework.value) {\n    return \"uploaded\";\n  }\n\n  return \"idle\";\n});",
    "const uploadStage = computed(() => {\n  if (evaluation.value) return \"review\";\n  return submitStage.value;\n});"
)

# 3. Watch
src2 = src2.replace(
    "watch(evaluating, (isEvaluating) => {\n  if (isEvaluating) {",
    "watch(() => submitStage.value === \"evaluating\" || submitStage.value === \"waiting\", (isActive) => {\n  if (isActive) {"
)
src2 = src2.replace(
    "  } else if (!isEvaluating && !evaluation.value) {",
    "  } else if (!isActive && !evaluation.value) {"
)

# 4. Button disabled states
src2 = src2.replace(
    ":disabled=\"submitting || evaluating\"",
    ":disabled=\"submitStage !== 'idle' && submitStage !== 'uploaded' && submitStage !== 'finished'\""
)
src2 = src2.replace(
    "v-if=\"evaluating && !submitting\"",
    "v-if=\"submitStage === 'evaluating' || submitStage === 'waiting'\""
)

# 5. Hero button text
src2 = src2.replace(
    "{{ submitting && evaluating ? \"提交并评测中...\" : \"提交作业并评测\" }}",
    "{{ submitStage === 'evaluating' || submitStage === 'waiting' ? \"提交并评测中...\" : \"提交作业并评测\" }}"
)

# 6. "仅提交作业" button
src2 = src2.replace(
    ":disabled=\"submitting || evaluating\" @click=\"store.submitHomework()\"",
    ":disabled=\"submitStage === 'uploading' || submitStage === 'evaluating'\" @click=\"store.submitHomework()\""
)

# 7. Ghost button (evaluate)
src2 = src2.replace(
    ":disabled=\"evaluating || !latestHomework\" @click=\"store.evaluateHomework()\"",
    ":disabled=\"submitStage === 'evaluating' || submitStage === 'waiting' || !latestHomework\" @click=\"store.evaluateHomework()\""
)
src2 = src2.replace(
    "v-if=\"evaluating\" class=\"btn-spinner dark\"",
    "v-if=\"submitStage === 'evaluating'\" class=\"btn-spinner dark\""
)

# 8. Transition conditions
src2 = src2.replace(
    "(submitStage === 'evaluating' || submitStage === 'waiting') && !evaluation && !chainVisible",
    "evaluating_condition_placeholder"
)
# Actually the transition conditions were already updated. Let me check what's there.

with open(fp2, "w", encoding="utf-8") as f:
    f.write(src2)
print("StudentSubmitPage.vue OK")

print("\nDone!")
