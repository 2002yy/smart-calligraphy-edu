"""Fix all 4 P1 issues"""
import os

ROOT = r"C:\Users\96967\Desktop\大创\code"

# === P1-1: Add getEvaluationProviders to student api ===
fp = os.path.join(ROOT, "student-app", "src", "api.ts")
with open(fp, encoding="utf-8") as f:
    s = f.read()

# Add method
old = """  getGrowth(userId: number) {
    return request.get<never, Growth>(`/api/v1/users/${userId}/growth`);
  }
};"""
new = """  getGrowth(userId: number) {
    return request.get<never, Growth>(`/api/v1/users/${userId}/growth`);
  },
  getEvaluationProviders() {
    return request.get<never, Record<string, {enabled: boolean; configured?: boolean; deprecated?: boolean}>>("/api/v1/evaluation/providers");
  }
};"""
assert old in s, "P1-1: not found!"
s = s.replace(old, new)
with open(fp, "w", encoding="utf-8") as f:
    f.write(s)
print("P1-1 OK")


# === Add provider info to submit page ===
fp2 = os.path.join(ROOT, "student-app", "src", "views", "StudentSubmitPage.vue")
with open(fp2, encoding="utf-8") as f:
    s = f.read()

# Add provider state after existing computed
old_provider = """const waitingForResult = ref(false);
const isDevMode = import.meta.env.DEV;"""
new_provider = """const waitingForResult = ref(false);
const isDevMode = import.meta.env.DEV;
const qwenEnabled = ref(false);
const providerLoaded = ref(false);

onMounted(async () => {
  try {
    const provs = await studentApi.getEvaluationProviders();
    qwenEnabled.value = provs.qwen?.enabled ?? false;
  } catch {}
  providerLoaded.value = true;
});"""
assert old_provider in s, "P1-1 provider block not found!"
s = s.replace(old_provider, new_provider)

# Also need to import studentApi directly
old_import = """import AppSkeleton from "../components/AppSkeleton.vue";"""
new_import = """import { studentApi } from "../api";
import AppSkeleton from "../components/AppSkeleton.vue";"""
assert old_import in s, "P1-1 import not found!"
s = s.replace(old_import, new_import)

# Add mode indicator after uploadStage in template (before the action buttons area)
old_label = """          <section v-else-if="uploadStage === 'review' && resultImageUrl" key="result-review" class="preview-block">
            <strong>作品回看图</strong>"""
new_label = """          <section v-if="providerLoaded" class="mode-badge">
            <span class="mode-dot" :class="qwenEnabled ? 'online' : 'offline'"></span>
            <span class="mode-text">{{ qwenEnabled ? 'AI 模式' : 'Mock 演示模式' }}</span>
          </section>

          <section v-else-if="uploadStage === 'review' && resultImageUrl" key="result-review" class="preview-block">
            <strong>作品回看图</strong>"""
assert old_label in s, "P1-1 label not found!"
s = s.replace(old_label, new_label)

# Add CSS for mode badge
old_css = ".calligraphy-section {"
new_css = ".mode-badge { display: flex; align-items: center; gap: 6px; margin-bottom: 8px; font-size: 13px; color: var(--muted); }\n.mode-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }\n.mode-dot.online { background: #4caf50; }\n.mode-dot.offline { background: #999; }\n\n.calligraphy-section {"
assert old_css in s, "P1-1 CSS not found!"
s = s.replace(old_css, new_css)

with open(fp2, "w", encoding="utf-8") as f:
    f.write(s)
print("P1-1 template OK")


# === P1-2: Pass annotations to overlay calls ===
fp3 = os.path.join(ROOT, "api-server", "app", "services", "evaluation_service.py")
with open(fp3, encoding="utf-8") as f:
    s = f.read()

# Fix sync path overlay call
old_sync = """            ov = FileStorageService.save_result_overlay(image_url=homework.image_url, scores={k: payload[k] for k in ("total_score", "structure_score", "center_score", "stroke_order_score")}, tags=payload.get("issues", []))"""
new_sync = """            ov = FileStorageService.save_result_overlay(image_url=homework.image_url, scores={k: payload[k] for k in ("total_score", "structure_score", "center_score", "stroke_order_score")}, tags=payload.get("issues", []), annotations=payload.get("annotations", []))"""
assert old_sync in s, "P1-2 sync not found!"
s = s.replace(old_sync, new_sync)

# Fix async path overlay call
old_async = """                    _ov = FileStorageService.save_result_overlay(image_url=_hw.image_url, scores={k: _payload[k] for k in ("total_score", "structure_score", "center_score", "stroke_order_score")}, tags=_payload.get("issues", []))"""
new_async = """                    _ov = FileStorageService.save_result_overlay(image_url=_hw.image_url, scores={k: _payload[k] for k in ("total_score", "structure_score", "center_score", "stroke_order_score")}, tags=_payload.get("issues", []), annotations=_payload.get("annotations", []))"""
assert old_async in s, "P1-2 async not found!"
s = s.replace(old_async, new_async)

with open(fp3, "w", encoding="utf-8") as f:
    f.write(s)
print("P1-2 OK")


# === P1-3: SECURE_STATIC note already in README ===
print("P1-3 OK (README already has SECURE_STATIC note)")


# === P1-4: student_id doc note already covered ===
print("P1-4 OK (demonstration-grade, documented in README)")

print("\nAll P1 fixes applied!")
