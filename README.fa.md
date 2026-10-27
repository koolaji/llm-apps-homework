# تمرین‌های دوره LLM Apps — Prompt Engineering · Tool Use · MCP

راه‌حل تمرین‌های دوره اپلیکیشن‌های LLM، همه با داکر اجرا می‌شوند.

سه فصل با یک خط داستانی واحد — از اصول Prompt Engineering تا یک
**MCP Server مالی چند-ابزاره** (بورس ایران + طلا + نرخ دلار):

| فصل | پوشه | خروجی |
|---|---|---|
| Prompt Engineering | `exercises/ex1..ex5` | ۵ اپ کوچک LangChain با خروجی ساختاریافته |
| Tool Use | `tool_use/` | ابزار `get_stock_info` بورس تهران + ابزار اخبار `search_stock_news` (اختیاری) + JSON Schema + تست Function Calling |
| MCP | `mcp_server/` | سرور MCP با ۳ ابزار الزامی + ابزار اخبار + پرامپت ترکیبی اجباری + رابط وب (UI) |

> صورت اصلی تمرین‌ها در [`docs/`](docs/) و **گزارش کامل تحویل** در
> [`docs/REPORT.fa.md`](docs/REPORT.fa.md) آمده است.
> (English README: [`README.md`](README.md))

## شروع سریع

```bash
cp .env.example .env        # کلیدها را پر کنید
docker compose build        # ساخت همه ایمیج‌ها
docker compose run --rm ex1 # یا هر تمرین دیگر
```

### کلیدهای `.env`

| کلید | استفاده | نحوه گرفتن |
|---|---|---|
| `ANTHROPIC_BASE_URL` | همه‌جا | endpoint سازگار با Anthropic |
| `ANTHROPIC_API_KEY` | همه‌جا | توکن API شما |
| `LLM_MODEL` | همه‌جا | نام مدل (پیش‌فرض `GLM-5.3-Flash`) |
| `NAVASAN_API_KEY` | ابزار نرخ دلار در MCP | رایگان از بات تلگرام `@navasan_contact_bot` |

**فایل `.env` را هرگز کامیت نکنید.** نبودِ کلید navasan همچنین سناریوی
تست خرابیِ MCP است: مدل باید نبود داده را صریح بگوید، نه حدس بزند.

## تمرین‌های Prompt Engineering

هر پنج تمرین از `init_chat_model` + `ChatPromptTemplate` + Pydantic +
`with_structured_output` استفاده می‌کنند و اصول Role/Delimiter/Output
Format/عدم-حدس‌زدن در آن‌ها رعایت شده است.

```bash
docker compose --profile exercises run --rm ex1   # تحلیل نظر محصول
docker compose --profile exercises run --rm ex2   # استخراج رزومه (فارسی/انگلیسی/ناقص)
docker compose --profile exercises run --rm ex3   # طبقه‌بندی تیکت پشتیبانی
docker compose --profile exercises run --rm ex4   # تولید محتوا با Few-shot
docker compose --profile exercises run --rm ex5   # تحلیل جلسه (پرامپت V1/V2/V3)
```

برای مقایسه نسخه‌های پرامپت تمرین ۵:

```bash
docker compose run --rm ex5 python -m exercises.ex5_meeting.analyze_meeting --version v1
docker compose run --rm ex5 python -m exercises.ex5_meeting.analyze_meeting --version v2
docker compose run --rm ex5   # نسخه نهایی v3
```

توضیح تغییرات هر نسخه در `exercises/ex5_meeting/prompts.py` (قسمت `CHANGELOG`).

## فصل Tool Use

```bash
# تست‌های پذیرش: فراخوانی درست، خطای نماد نامعتبر، اعتبار schema.json
# و یک round trip واقعی با Function Calling کلود
docker compose --profile tool-use run --rm tool-test

# تحلیل تکنیکال یک نماد — پرامپت استفاده از ابزار را اجباری می‌کند
docker compose --profile tool-use run --rm tool-analysis
```

فایل‌ها: `tool_use/stock_info.py` (امضا و docstring اجباری تمرین)،
`tool_use/schema.json`، `tool_use/news_search.py` و `news_search.schema.json`
(تمرین اختیاری: سرچ اخبار وب با Bing News RSS — فقط کتابخانه استاندارد، بدون کلید)،
`tool_use/test_function_calling.py`،
`tool_use/offline_test.py` (تست بدون دسترسی به TSETMC) و
`tool_use/technical_analysis.py` (از هر دو ابزار استفاده می‌کند).

## فصل MCP

```bash
# کلاینت اسکریپتی: بررسی tools/list، سؤال طلای داخلی (هر دو ابزار باید صدا زده شوند)
docker compose --profile mcp run --rm mcp-test

# تست خرابی: کلید نامعتبر navasan → مدل باید بگوید کدام داده نبود
docker compose --profile mcp run --rm mcp-test python mcp_server/client_test.py --break-usd

# سؤال بیشتر: تحلیل روند بازار (شامل ابزار اخبار)
docker compose --profile mcp run --rm mcp-test python mcp_server/client_test.py --trend

# تمرین اختیاری: رابط وب روی سرور MCP → http://localhost:8000
docker compose --profile mcp up -d --build mcp-ui
# (توقف: docker compose --profile mcp down)
```

رابط وب (`mcp_server/ui.py`، با Starlette + uvicorn که هر دو همراه خود پکیج
`mcp` نصب می‌شوند) یک نشست MCP دائمی به ساب‌پروسس سرور نگه می‌دارد؛ یعنی هر
سؤال واقعاً از پروتکل MCP رد می‌شود و در صفحه پاسخ، ابزارهای فراخوانی‌شده
نمایش داده می‌شوند.

### اتصال به Claude Desktop

```json
{
  "mcpServers": {
    "finance": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "--env-file", "/absolute/path/to/.env", "llm-apps-homework-mcp-finance"]
    }
  }
}
```

بعد از `docker compose build` نام ایمیج `llm-apps-homework-mcp-finance` است.

### پرامپت ترکیبی (بخش ب)

سؤال «قیمت طلای داخلی الان تقریباً چقدره؟» با یک ابزار قابل پاسخ نیست:

```
هر گرم طلای ۲۴ عیار (تومان) = (قیمت انس ÷ ۳۱٫۱) × نرخ دلار
هر گرم طلای ۱۸ عیار = ۲۴ عیار × ۰٫۷۵
```

پرامپت سیستم (`mcp_server/prompts.py`) مدل را قدم‌به‌قدم وادار می‌کند هر دو
ابزار را صدا بزند، اعداد خام را نشان دهد و در صورت خطای ابزار، بدون حدس
صریحاً نبود داده را اعلام کند.

## ساختار پروژه

```
common/llm.py               فکتوری مشترک init_chat_model (بر اساس env)
exercises/ex1..ex5          اپ‌های Prompt Engineering + نمونه‌های تست هر کدام
tool_use/                   ابزار بورس، ابزار اخبار، schema ها، تست‌های پذیرش و آفلاین
mcp_server/
  server.py                 سرور FastMCP (stdio): ۳ ابزار الزامی + اخبار
  tools/stock_info.py       استفاده مجدد از tool_use/stock_info.py
  tools/gold_price.py       gold-api.com (رایگان، بدون کلید)
  tools/usd_rate.py         navasan.tech (کلید رایگان از بات تلگرام)
  schemas/                  یک schema جدا برای هر ابزار جدید
  prompts.py                پرامپت ترکیبی طلا + پرامپت روند + پرامپت UI
  client_test.py            کلاینت MCP اسکریپتی + چک‌های پذیرش
  ui.py                     رابط وب اختیاری (Starlette) روی سرور MCP
  mock_navasan.py           سرور شبیه‌ساز navasan برای تست بدون کلید
docker/requirements-base.txt وابستگی‌های مشترک همه ایمیج‌ها
docker-compose.yml          یک سرویس برای هر خروجی، profile برای هر فصل
docs/                       صورت تمرین‌ها + گزارش تحویل (REPORT.fa.md)
```

## اجرای محلی (بدون داکر)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r docker/requirements-base.txt
export $(grep -v '^#' .env | xargs)
python -m exercises.ex1_review.analyze_review
python tool_use/offline_test.py
python mcp_server/client_test.py
```

## نکات

- دیتای بورس از **TSETMC** با `pytse-client` گرفته می‌شود (انتخاب این مسیر
  در گزارش فصل Tool Use مستند شده است).
- TSETMC بعضی IPهای خارج از ایران را بلاک می‌کند؛ در این حالت
  `tool_use/offline_test.py` همه‌چیز غیر از اتصال واقعی را تأیید می‌کند.
- مدلِ endpoint به‌صورت پیش‌فرض بلوک‌های thinking تولید می‌کند؛
  `common/llm.py` آن را برای خروجی ساختاریافتهٔ سریع و قابل‌پیش‌بینی غیرفعال می‌کند.
- خطاهای ابزارها به‌صورت `{"error": ...}` داخل خروجی برمی‌گردند تا مدل
  صریح بگوید کدام داده در دسترس نبود (بند ۴ چک‌لیست MCP).
- برای تست بدون کلید navasan: `python mcp_server/mock_navasan.py` سپس
  `NAVASAN_LATEST_URL=http://127.0.0.1:8765/latest NAVASAN_API_KEY=test-key`.
- اگر build داکر روی شبکه ضعیف روی pip گیر کرد:
  `docker build --network=host -f <dockerfile> .`
- pin ها: `mcp<2` (در نسخه ۲ نام FastMCP تغییر کرده) و `pandas<3`
  (pytse-client روی API پانداس ۲ ساخته شده) — در `docker/requirements-base.txt`.
