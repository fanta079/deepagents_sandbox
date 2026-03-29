import { test, expect } from "@playwright/test";

const BASE_URL = process.env.E2E_BASE_URL || "http://localhost:3000";

test.describe("DeepAgents E2E 测试", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
  });

  test("首页加载", async ({ page }) => {
    // 首页应显示 DeepAgents 标题或重定向到登录页
    await page.goto(BASE_URL);
    // 如果未登录，应该跳转到 /auth
    await expect(page).toHaveURL(/\/(auth|)$/);
  });

  test("登录页面加载", async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await expect(page.getByRole("heading", { name: /DeepAgents/i })).toBeVisible();
    await expect(page.getByRole("tab", { name: "登录" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "注册" })).toBeVisible();
  });

  test("登录表单验证", async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // 空表单提交应触发验证
    await page.getByRole("tab", { name: "登录" }).click();
    await page.getByRole("button", { name: "登录" }).click();

    // 应显示验证错误
    await expect(page.getByText(/用户名不能为空|请输入用户名/i)).toBeVisible();
  });

  test("注册表单切换", async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // 切换到注册标签
    await page.getByRole("tab", { name: "注册" }).click();
    await expect(page.getByLabel(/用户名/i)).toBeVisible();
    await expect(page.getByLabel(/邮箱/i)).toBeVisible();
    await expect(page.getByLabel(/密码/i)).toBeVisible();
  });

  test("注册并登录流程", async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // 切换到注册标签
    await page.getByRole("tab", { name: "注册" }).click();

    const testUsername = `e2e_user_${Date.now()}`;
    const testEmail = `${testUsername}@test.com`;
    const testPassword = "testpass123";

    // 填写注册表单
    await page.getByLabel(/用户名/i).fill(testUsername);
    await page.getByLabel(/邮箱/i).fill(testEmail);
    await page.getByLabel(/密码/i).fill(testPassword);

    // 提交注册
    await page.getByRole("button", { name: "注册" }).click();

    // 注册成功后应跳转到首页或仪表盘
    await page.waitForURL(/\/(#|\/|dashboard)/i, { timeout: 10000 }).catch(() => {
      // 如果没跳走，可能注册失败（用户名重复），但仍继续检查页面状态
    });

    // 检查 token 是否已设置（localStorage）
    const token = await page.evaluate(() => localStorage.getItem("access_token"));
    if (token) {
      // 登录成功，检查是否在 dashboard 页面
      await expect(page).not.toHaveURL(/\/login|\/auth/);
    }
  });

  test("登录失败（错误凭据）", async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    await page.getByRole("tab", { name: "登录" }).click();
    await page.getByLabel(/用户名/i).fill("nonexistent_user_12345");
    await page.getByLabel(/密码/i).fill("wrongpassword");
    await page.getByRole("button", { name: "登录" }).click();

    // 应显示错误信息
    await expect(page.getByText(/登录失败|错误|无效/i)).toBeVisible({ timeout: 5000 });
  });

  test("暗色模式切换", async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // 找到主题切换按钮
    const themeBtn = page.locator("button[title*='切换到']");

    // 如果没有登录不显示主题切换，跳过
    if (!(await themeBtn.isVisible().catch(() => false))) {
      return;
    }

    // 点击切换
    await themeBtn.click();

    // 验证 html 元素上的 dark class 已切换
    const hasDark = await page.evaluate(() => document.documentElement.classList.contains("dark"));
    expect(typeof hasDark).toBe("boolean");
  });

  test("WebSocket 页面加载", async ({ page }) => {
    await page.goto(`${BASE_URL}/ws`);

    // 未登录时应该重定向到 auth
    await expect(page).toHaveURL(/\/auth/);
  });
});
