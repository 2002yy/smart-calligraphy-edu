import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { chromium } from "playwright";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const screenshotDir = path.join(__dirname, "screenshots");

function ensureDir() {
  if (!fs.existsSync(screenshotDir)) fs.mkdirSync(screenshotDir, { recursive: true });
}

async function main() {
  ensureDir();

  // ── 配置：根据实际运行端口调整 ──
  const API = "http://127.0.0.1:8000";
  const TEACHER = "http://localhost:5173";
  const STUDENT = "http://localhost:5174";

  const browser = await chromium.launch({ headless: true });

  try {
    // ── 1. 后端 API 冒烟 ──
    console.log("\n=== 1/4 后端 API 冒烟 ===");
    const apiOk = await fetch(`${API}/`).then(r => r.ok).catch(() => false);
    console.log(apiOk ? "[OK]  后端可达" : "[FAIL] 后端不可达");

    // 登录教师
    const teacherLogin = await fetch(`${API}/api/v1/auth/login`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: "teacher01", password: "123456" }),
    }).then(r => r.json()).catch(() => null);
    const teacherOk = teacherLogin?.data?.access_token;
    console.log(teacherOk ? "[OK]  教师登录" : "[FAIL] 教师登录");

    // 登录学生
    const studentLogin = await fetch(`${API}/api/v1/auth/login`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: "student01", password: "123456" }),
    }).then(r => r.json()).catch(() => null);
    const studentOk = studentLogin?.data?.access_token;
    console.log(studentOk ? "[OK]  学生登录" : "[FAIL] 学生登录");

    // Mock 评测链路
    if (teacherOk && studentOk) {
      const th = teacherLogin.data.access_token;
      const sh = studentLogin.data.access_token;
      const sid = studentLogin.data.user.id;

      // 查任务
      const tasks = await fetch(`${API}/api/v1/tasks`, {
        headers: { Authorization: `Bearer ${th}` },
      }).then(r => r.json()).then(d => d.data || []);
      const taskId = tasks[0]?.id;
      console.log(taskId ? `[OK]  任务列表，首个任务 ID=${taskId}` : "[WARN] 无任务");

      // 上传 + 提交 + Mock 评测
      if (taskId) {
        const png = Buffer.from([
          137,80,78,71,13,10,26,10,0,0,0,13,73,72,68,82,0,0,0,1,0,0,0,1,
          8,2,0,0,0,144,119,83,222,0,0,0,12,73,68,65,84,8,215,99,248,207,
          192,0,0,0,2,0,1,226,0,0,0,63,0,0,0,0,0,0,0,
        ]);

        const upload = await fetch(`${API}/api/v1/homework/upload`, {
          method: "POST",
          headers: { Authorization: `Bearer ${sh}` },
          body: (() => {
            const fd = new FormData();
            fd.append("task_id", String(taskId));
            fd.append("student_id", String(sid));
            fd.append("file", new Blob([png], { type: "image/png" }), "test.png");
            return fd;
          })(),
        }).then(r => r.json()).then(d => d.data);
        const hwId = upload?.homework_id;
        console.log(hwId ? `[OK]  上传作业 homework_id=${hwId}` : "[FAIL] 上传作业");

        if (hwId) {
          await fetch(`${API}/api/v1/homework`, {
            method: "POST",
            headers: { Authorization: `Bearer ${sh}`, "Content-Type": "application/json" },
            body: JSON.stringify({ homework_id: hwId, task_id: taskId, student_id: sid, image_url: upload.file_url }),
          });

          const evalResp = await fetch(`${API}/api/v1/evaluation/start`, {
            method: "POST",
            headers: { Authorization: `Bearer ${sh}`, "Content-Type": "application/json" },
            body: JSON.stringify({ homework_id: hwId, provider: "mock", force_refresh: true }),
          }).then(r => r.json()).then(d => d.data);

          if (evalResp?.status === "finished") {
            console.log(`[OK]  Mock 评测完成，provider=${evalResp.provider}`);
          } else {
            console.log("[FAIL] Mock 评测失败");
          }

          const evalResult = await fetch(`${API}/api/v1/evaluation/${hwId}`, {
            headers: { Authorization: `Bearer ${sh}` },
          }).then(r => r.json()).then(d => d.data);
          if (evalResult?.total_score > 0) {
            console.log(`[OK]  评测结果：总分 ${evalResult.total_score}/10，${evalResult.tags?.length ?? 0} 个标签`);
          } else {
            console.log("[FAIL] 评测结果缺失");
          }

          // 教师端批阅回流
          const reviews = await fetch(`${API}/api/v1/reviews?teacher_id=1`, {
            headers: { Authorization: `Bearer ${th}` },
          }).then(r => r.json()).then(d => d.data || []);
          console.log(reviews.length > 0 ? `[OK]  教师端可见批阅记录 ${reviews.length} 条` : "[WARN] 教师端无批阅（首次需要新作业）");

          // 看板数据
          const dash = await fetch(`${API}/api/v1/dashboard/class/1`, {
            headers: { Authorization: `Bearer ${th}` },
          }).then(r => r.json()).then(d => d.data);
          if (dash?.homework_count > 0) {
            console.log(`[OK]  教学看板：提交 ${dash.homework_count}，已评测 ${dash.evaluated_count}`);
          } else {
            console.log("[WARN] 看板数据为空");
          }
        }
      }
    }

    // ── 2. 教师端 UI 冒烟 ──
    console.log("\n=== 2/4 教师端 UI ===");
    const tp = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    try {
      await tp.goto(TEACHER, { waitUntil: "domcontentloaded", timeout: 15000 });
      await tp.waitForSelector("text=智慧书法", { timeout: 10000 });
      await tp.fill('input[placeholder="teacher01"]', "teacher01");
      await tp.fill('input[type="password"]', "123456");
      await tp.getByRole("button", { name: /连接后端/ }).click();
      await tp.waitForTimeout(2000);
      await tp.screenshot({ path: path.join(screenshotDir, "teacher-logged-in.png"), fullPage: false });
      console.log("[OK]  教师端登录并截图");
    } catch (e) {
      console.log("[WARN] 教师端 UI 异常:", e.message?.slice(0, 60));
    } finally {
      await tp.close();
    }

    // ── 3. 学生端 UI 冒烟 ──
    console.log("\n=== 3/4 学生端 UI ===");
    const sp = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    try {
      await sp.goto(STUDENT, { waitUntil: "domcontentloaded", timeout: 15000 });
      await sp.waitForSelector("text=智慧书法", { timeout: 10000 });
      await sp.fill('input[placeholder="student01"]', "student01");
      await sp.fill('input[type="password"]', "123456");
      await sp.getByRole("button", { name: /连接后端/ }).click();
      await sp.waitForTimeout(2000);
      await sp.screenshot({ path: path.join(screenshotDir, "student-logged-in.png"), fullPage: false });
      console.log("[OK]  学生端登录并截图");
    } catch (e) {
      console.log("[WARN] 学生端 UI 异常:", e.message?.slice(0, 60));
    } finally {
      await sp.close();
    }

    console.log("\n=== 4/4 完成 ===");
    console.log(`截图已保存至 ${screenshotDir}`);
  } finally {
    await browser.close();
  }
}

main().catch((e) => { console.error("[FAIL]", e); process.exit(1); });
