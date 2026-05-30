import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { chromium } from "playwright";

const edgePath = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const screenshotDir = path.join(__dirname, "screenshots");

function ensureDir() {
  if (!fs.existsSync(screenshotDir)) {
    fs.mkdirSync(screenshotDir, { recursive: true });
  }
}

async function firstReachable(page, urls) {
  for (const url of urls) {
    try {
      const response = await page.goto(url, { waitUntil: "domcontentloaded", timeout: 12000 });
      if (response && response.ok()) {
        return url;
      }
    } catch (_) {
      // Try next port.
    }
  }

  throw new Error(`No reachable URL found in: ${urls.join(", ")}`);
}

async function verifySwagger(browser) {
  const page = await browser.newPage();
  const url = await firstReachable(page, ["http://127.0.0.1:8000/docs"]);
  await page.waitForTimeout(1500);
  const title = await page.title();
  console.log(`[OK] 后端 Swagger 已打开：${url} | 页面标题：${title}`);
  await page.close();
}

async function verifyTeacher(browser) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1200 } });
  const url = await firstReachable(page, ["http://[::1]:5173", "http://[::1]:5175", "http://localhost:5175"]);
  await page.waitForSelector("text=智慧书法", { timeout: 15000 });
  await page.fill('input[placeholder="teacher01"]', "teacher01");
  await page.fill('input[type="password"]', "123456");
  await page.getByRole("button", { name: /连接后端|重新同步/ }).click();
  await page.waitForTimeout(2200);

  const routes = [
    { name: "teacher-dashboard", to: "/" },
    { name: "teacher-manage", to: "/manage" },
    { name: "teacher-tasks", to: "/tasks" },
    { name: "teacher-reviews", to: "/reviews" }
  ];

  for (const route of routes) {
    await page.goto(`${url}${route.to}`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(900);
    await page.screenshot({ path: path.join(screenshotDir, `${route.name}.png`), fullPage: true });
  }

  const pageTitle = await page.locator("h2").first().textContent();
  console.log(`[OK] 教师端已打开：${url} | 页面标题：${pageTitle?.trim() ?? "未知"}`);
  await page.close();
}

async function verifyStudent(browser) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1200 } });
  const url = await firstReachable(page, ["http://[::1]:5174", "http://[::1]:5176", "http://localhost:5174"]);
  await page.waitForSelector("text=智慧书法", { timeout: 15000 });
  await page.fill('input[placeholder="student01"]', "student01");
  await page.fill('input[type="password"]', "123456");
  await page.getByRole("button", { name: /连接后端|重新同步/ }).click();
  await page.waitForTimeout(2200);

  const routes = [
    { name: "student-overview", to: "/" },
    { name: "student-tasks", to: "/tasks" },
    { name: "student-submit", to: "/submit" },
    { name: "student-growth", to: "/growth" }
  ];

  for (const route of routes) {
    await page.goto(`${url}${route.to}`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(900);
    await page.screenshot({ path: path.join(screenshotDir, `${route.name}.png`), fullPage: true });
  }

  const pageTitle = await page.locator("h2").first().textContent();
  console.log(`[OK] 学生端已打开：${url} | 页面标题：${pageTitle?.trim() ?? "未知"}`);
  await page.close();
}

async function main() {
  ensureDir();

  const browser = await chromium.launch({
    headless: true,
    executablePath: edgePath
  });

  try {
    await verifySwagger(browser);
    await verifyTeacher(browser);
    await verifyStudent(browser);
    console.log(`[DONE] Playwright 视觉验收完成，截图目录：${screenshotDir}`);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error("[FAIL] Playwright 视觉验收失败：");
  console.error(error);
  process.exit(1);
});
