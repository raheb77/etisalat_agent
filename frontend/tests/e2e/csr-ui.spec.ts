import { test, expect } from "@playwright/test";

const baseResponse = (overrides: Record<string, unknown> = {}) => ({
  answer: "باقة 55 جيجا سعرها 120 ريال شهرياً.",
  steps: ["تحقق من الباقة عبر التطبيق.", "أكد تفاصيل التسعير قبل الاشتراك."],
  citations: [
    {
      source: "docs/plans/55gb.md",
      chunk_id: "plan-55gb-price",
      score: 0.92,
    },
  ],
  confidence: 0.82,
  category: "plans",
  risk_level: "low",
  handoff: false,
  handoff_reason: "",
  handoff_payload: null,
  ...overrides,
});

test.beforeEach(async ({ page }) => {
  await page.route("**/health", (route) =>
    route.fulfill({
      status: 200,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
      body: JSON.stringify({ status: "ok" }),
    })
  );

  await page.route("**/query", async (route) => {
    if (route.request().method() === "OPTIONS") {
      await route.fulfill({
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type, X-Channel, X-Locale",
        },
        body: "",
      });
      return;
    }

    const payload = route.request().postDataJSON() as { question?: string };
    const question = payload?.question ?? "";

    if (question.includes("rate limit")) {
      await route.fulfill({
        status: 429,
        headers: {
          "Content-Type": "application/json",
          "Retry-After": "30",
          "Access-Control-Allow-Origin": "*",
        },
        body: JSON.stringify({
          error_code: "RATE_LIMIT",
          message: "Please retry in 30 seconds.",
        }),
      });
      return;
    }

    if (question.includes("عندي مشكلة")) {
      await route.fulfill({
        status: 200,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
        body: JSON.stringify(
          baseResponse({
            answer:
              "سؤالك غير واضح. للتوضيح: هل تقصد مشكلة في (الفاتورة) أو (الباقة) أو (الشبكة)؟ اذكر تفاصيل أكثر.",
            steps: [],
            citations: [],
            confidence: 0.5,
            category: "unknown",
            handoff: false,
            handoff_reason: "",
          })
        ),
      });
      return;
    }

    if (question.includes("بدون مصادر")) {
      await route.fulfill({
        status: 200,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
        body: JSON.stringify(
          baseResponse({
            answer: "لا توجد مصادر داعمة مباشرة. يرجى التصعيد.",
            steps: [],
            citations: [],
            confidence: 0.2,
            category: "billing",
            handoff: true,
            handoff_reason: "High risk category",
          })
        ),
      });
      return;
    }

    await route.fulfill({
      status: 200,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
      body: JSON.stringify(baseResponse()),
    });
  });
});

test("happy path: question -> answer with citations visible", async ({ page }) => {
  await page.goto("/");

  await page.getByTestId("question-input").fill("كم سعر باقة 55 جيجا؟");
  await page.getByTestId("send-button").click();

  await expect(page.getByTestId("response-panel")).toBeVisible();
  await expect(page.getByText("باقة 55 جيجا سعرها 120 ريال شهرياً.")).toBeVisible();
  await expect(page.getByTestId("citations-list")).toContainText(
    "docs/plans/55gb.md"
  );
});

test("ambiguous: clarification response (no citations, handoff=false)", async ({
  page,
}) => {
  await page.goto("/");

  await page.getByTestId("question-input").fill("عندي مشكلة");
  await page.getByTestId("send-button").click();

  await expect(page.getByText(/للتوضيح/i)).toBeVisible();
  await expect(page.getByText(/No citations returned/i)).toBeVisible();
});

test("no citations: handoff banner visible", async ({ page }) => {
  await page.goto("/");

  await page.getByTestId("question-input").fill("بدون مصادر");
  await page.getByTestId("send-button").click();

  await expect(page.getByTestId("handoff-banner")).toBeVisible();
});

test("rate limit: UI shows retry message", async ({ page }) => {
  await page.goto("/");

  await page.getByTestId("question-input").fill("rate limit");
  await page.getByTestId("send-button").click();

  await expect(page.getByTestId("error-banner")).toBeVisible();
  await expect(page.getByTestId("error-banner")).toContainText(
    "Please retry in 30 seconds."
  );
});

test("locale switch: ar-SA uses RTL, en-US uses LTR", async ({ page }) => {
  await page.goto("/");

  await page.getByTestId("question-input").fill("كم سعر باقة 55 جيجا؟");
  await page.getByTestId("send-button").click();

  await expect(page.getByTestId("response-panel")).toHaveAttribute("dir", "rtl");

  await page.getByTestId("locale-select").selectOption("en-US");
  await page.getByTestId("question-input").fill("كم سعر باقة 55 جيجا؟");
  await page.getByTestId("send-button").click();

  await expect(page.getByTestId("response-panel")).toHaveAttribute("dir", "ltr");
});
