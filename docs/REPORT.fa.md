# گزارش تمرین‌ها — تحلیلگر مالی هوشمند

> گزارش تحویل تمرین‌های دوره: فصل‌های Prompt Engineering، Tool Use و MCP.
> راهنمای اجرا در [`README.fa.md`](../README.fa.md) آمده است.

---

## ۱. فصل Prompt Engineering — پنج تمرین (`exercises/`)

همه تمرین‌ها با یک الگوی مشترک ساخته شده‌اند: `init_chat_model` +
`ChatPromptTemplate` + مدل Pydantic + `with_structured_output`.
مدل از طریق یک endpoint سازگار با Anthropic (z.ai) فراخوانی می‌شود و
تنظیمات آن فقط از طریق متغیرهای محیطی (`.env`) خوانده می‌شود.

اصول Prompt Engineering که در هر پنج تمرین رعایت شده:

| اصل | پیاده‌سازی |
|---|---|
| Role | نقش مدل در System Prompt مشخص شده (تحلیلگر نظر، استخراج‌گر رزومه، ...) |
| Delimiter | متن ورودی همیشه بین تگ‌های `<review>`، `<resume>`، `<transcript>` قرار می‌گیرد |
| Output Format | اسکیمای Pydantic با توضیح تک‌تک فیلدها |
| جلوگیری از Hallucination | دستور صریح «اگر اطلاعات نیست، None/لیست خالی برگردان» + فیلدهای optional با default |

نکته فنی مهم: در ابتدا فیلدهای اجباریِ غیر-nullable باعث می‌شد وقتی مدل
خروجی خالی (`{}`) می‌داد (مثلاً برای رزومه ناقص)، parse شکست بخورد. راه‌حل:
همه فیلدها default دارند تا «نبودِ اطلاعات» معنادار باشد، نه خطا.

### تمرین ۱ — تحلیل نظر محصول (`analyze_review`)
- ۶ نظر تست: کاملاً مثبت، کاملاً منفی، خنثی، تک‌جمله‌ای، مثبت با ایراد جزئی، مبهم.
- نتیجه اجرا: همه ۶ مورد خروجی ساختاریافته درست دادند؛ نظر مبهم →
  `sentiment: neutral` و امتیاز ۳ بدون حدس اضافه. ✅

### تمرین ۲ — استخراج اطلاعات رزومه (`extract_resume_info`)
- سه رزومه: فارسی کامل، انگلیسی کامل، ناقص (بدون تلفن/سابقه).
- رزومه ناقص → فیلدهای خالی `[]`/`None` و خلاصه فقط بر اساس متن موجود.
- اسامی و مهارت‌ها (Python, Django, React, ...) درست استخراج شدند. ✅

### تمرین ۳ — تبدیل پیام مشتری به تیکت (`classify_support_ticket`)
- معیار priority به‌صورت rubric صریح در پرامپت آمده (critical تا low).
- ۵ پیام تست از خود صورت تمرین: نتیجه —
  Login+دلاین امروز → `critical/authentication`، پرداخت → `high/payment`،
  باگ فنی → `medium/technical`، سؤال ساده → `low/account`، مشتری عصبانی →
  `high` با `sentiment: angry`. ✅
- طبق صورت تمرین، از `SystemMessage` به‌صورت object واقعی استفاده شده است.

### تمرین ۴ — تولید محتوا با Few-shot (`generate_technical_content`)
- دو مثال few-shot داخل پرامپت تفاوت beginner/intermediate و
  LinkedIn post/Tutorial را نشان می‌دهند؛ پرامپت ثابتِ «جایگذاری متغیر» نیست.
- تست با ۳ ترکیب (RAG/فارسی/LinkedIn، Docker/مبتدی/توضیح کوتاه،
  Git rebase/چیت‌شیت) → عمق، لحن و ساختار خروجی واقعاً تغییر کرد. ✅

### تمرین ۵ — تحلیل جلسه + توسعه تکراری پرامپت (`analyze_meeting`)
- سه نسخه پرامپت در `prompts.py` نگه داشته شده با `CHANGELOG`:
  - **V1:** پیش‌نویس اولیه — بدون Role، بدون delimiter و بدون قانون ضدهلوسینیشن؛
    از نظر ساختاری هیچ چیزی مانع حدس زدن owner یا قاطی شدن پیشنهاد با تصمیم نیست.
  - **V2:** اضافه شدن Role، delimiter ترنسکریپت و قانون «None بگذار، حدس نزن».
  - **V3:** تفکیک صریح «تصمیم» از «پیشنهاد» با cue های فارسی، جدا کردن افراد از پروژه‌ها.
- نکته پیاده‌سازی: ترنسکریپت فقط یک‌بار در Human Message می‌رود (در V1 بدون
  delimiter به‌صورت عمدی، چون یکی از اصلاحات V2 همان اضافه‌شدن delimiter است)
  و System Prompt فقط دستورالعمل‌ها را دارد.
- نتیجه V3 روی transcript فارسی نمونه: `سعید/پنجشنبه` استخراج شد،
  برای تسک‌های بدون owner/deadline مقدار `null` برگشت، و «ایده دارک مود»
  به‌عنوان تصمیم ثبت نشد. ✅

---

## ۲. فصل Tool Use — ابزار `get_stock_info` (`tool_use/`)

### تصمیم فنی (طبق خواسته تمرین)
از **`pytse-client`** استفاده شده (نه API غیررسمی) — ساده‌تر، نگهداری‌شده،
و پوشش دیتای لحظه‌ای و تاریخی. امضای تابع و docstring دقیقاً مطابق نمونه
اجباری تمرین است و کلیدهای خروجی همان‌هایی که خواسته شده بود.
(تنها تفاوت: `market_cap` همیشه `None` است چون pytse-client این فیلد را
در دسترس نمی‌گذارد؛ طبق قرارداد تمرین optional است و حدس زده نشده.)

### چک‌لیست پذیرش

| مورد | وضعیت |
|---|---|
| `get_stock_info("فولاد")` بدون خطا و برگرداندن dict | ✅ (در محیط بدون دسترسی به TSETMC با mock — تست `offline_test.py`؛ روی شبکه ایران اجرای واقعی) |
| نماد نامعتبر `"XYZ123"` → `ValueError` با پیام واضح | ✅ تست واقعی بدون نیاز به شبکه |
| فایل جدا `schema.json` | ✅ `tool_use/schema.json` |
| تست کوچک پاس‌دادن خروجی به Function Calling در Claude API | ✅ `offline_test.py::test_claude_round_trip` — یک round trip واقعی با API |
| پرامپت تحلیل تکنیکال با اجبار به استفاده از ابزار | ✅ `technical_analysis.py` — پرامپت تحلیل را منوط به فراخوانی ابزار می‌کند |
| ابزار سرچ اخبار (اختیاری) | ✅ `news_search.py::search_stock_news` — با Bing News RSS (بخش بعد) |

### تمرین اختیاری — ابزار سرچ اخبار (`search_stock_news`)

- منبع: **Bing News RSS** (`format=RSS`) — بدون کلید، بدون کتابخانه اضافه
  (فقط `urllib` و `xml.etree` از کتابخانه استاندارد) و از ایران هم قابل
  دسترس. نتایج مطابق شرایط Bing صرفاً برای نمایش/استفاده شخصی و غیرتجاری
  رندر می‌شوند (در docstring ذکر شده).
- همان قوانین فصل: Type Hint + Google Docstring + خروجی dict مستند +
  `ValueError` برای ورودی نامعتبر + `RuntimeError` برای عدم دسترسی منبع
  (بدون کرش) + فایل جدا `news_search.schema.json`.
- خروجی: تا ۱۰ خبر با `title`، `link`، `source`، `published` (ISO-8601) و
  `summary`، مرتب‌شده از تازه‌ترین.
- تست: ۵ چک جدید در `offline_test.py` (پارس RSS با mock، مرتب‌سازی و
  `count`، اعتبارسنجی ورودی، خطای منبع، اعتبار schema) — همه PASS، داخل
  کانتینر هم اجرا شد.
- در `technical_analysis.py` هم wired شده: مدل علاوه بر `get_stock_info`
  می‌تواند برای زمینه از اخبار استفاده کند (تحلیل عددی همچنان فقط از داده
  نماد).

### محدودیت محیطی
TSETMC سرورهای خارج از ایران (از جمله IP دیتاسنتر) را بلاک می‌کند؛ به همین
دلیل `tool_use/offline_test.py` اضافه شده که Ticker را mock می‌کند و
همه‌چیز غیر از اتصال واقعی را تأیید می‌کند (شکل خروجی، محاسبه درصد تغییر،
خطاها، و round trip با Claude API).

---

## ۳. فصل MCP — سرور مالی چند-ابزاره (`mcp_server/`)

### بخش الف — سه Tool الزامی + یک Tool اختیاری

| Tool | منبع | کلید |
|---|---|---|
| `get_stock_info` | TSETMC (همان تمرین فصل قبل — import شده، کپی نشده) | — |
| `get_gold_price` | gold-api.com | رایگان |
| `get_usd_rate` | navasan.tech | رایگان از بات `@navasan_contact_bot` |
| `search_stock_news` (اختیاری) | Bing News RSS | رایگان |

- ساختار پروژه دقیقاً مطابق پیشنهاد تمرین است (`server.py` + `tools/`).
- `tools/list` توسط SDK هندل می‌شود (طبق نکته خود تمرین).
- هر دو تابع جدید همان قوانین فصل قبل را دارند: Type Hint + Google
  Docstring + **Schema جدا** در `mcp_server/schemas/*.schema.json`
  (اعتبارسنجی این فایل‌ها بخشی از `client_test.py` است).
- خطاهای API به‌جای کرش، به‌صورت `{"error": ...}` داخل همان خروجی ابزار
  برمی‌گردند تا مدل بتواند صریح بگوید کدام داده نبود — نه اینکه حدس بزند.
- برای تست بدون کلید، `mock_navasan.py` اضافه شده (کلید معتبر: `test-key`).

### بخش ب — پرامپت ترکیبی

سناریوی تمرین: «قیمت طلای داخلی الان تقریباً چقدره؟» — پرامپت
(`prompts.py::GOLD_PRICE_PROMPT`) مدل را مجبور می‌کند **هر دو** ابزار را
صدا بزند چون فرمول نهایی به هر دو عدد وابسته است:

```
هر گرم ۲۴ عیار = (انس ÷ ۳۱٫۱) × نرخ دلار
هر گرم ۱۸ عیار = ۲۴ عیار × ۰٫۷۵
```

### چک‌لیست پذیرش (خروجی واقعی `client_test.py`)

| مورد | وضعیت |
|---|---|
| هر سه Tool الزامی (+ اختیاری اخبار) ثبت و قابل فراخوانی | ✅ `tools/list` → چهار ابزار |
| مدل هر دو ابزار (طلا + دلار) را صدا بزند | ✅ لاگ: `get_gold_price({})` سپس `get_usd_rate({})` |
| عدد نهایی منطقی باشد | ✅ با انس ۳۹۹۶٫۹$ و دلار ۱٬۱۱۸٬۰۰۰: گرم ۲۴ عیار ≈ ۱۴۳٫۷M و ۱۸ عیار ≈ ۱۰۷٫۸M تومان — با محاسبه دستی چک شد |
| خطای API → اعلام صریح، بدون حدس | ✅ تست `--break-usd`: مدل گفت «نرخ دلار در دسترس نبود» و محاسبه نکرد |

تست‌های بیشتر: سؤال روند بازار با `--trend` (پرامپت دوم `TREND_PROMPT`؛
در آخرین اجرا هر سه ابزار `get_gold_price`، `get_stock_info` و
`search_stock_news` فراخوانی شدند).

### تمرین اختیاری (پرامپت کامل‌تر + UI)

هر دو انجام شد:

- **پرامپت کامل‌تر:** `prompts.py::UI_PROMPT` — یک پرامپت ترکیبی که هر سوال
  مالی را به ابزار درست route می‌کند (نماد ← `get_stock_info`، اخبار ←
  `search_stock_news`، طلا/دلار برای فرمول گرم طلا) و قواعد «حدس نزن» و
  «اعلام صریح داده‌ی غایب» را حفظ می‌کند. `TREND_PROMPT` هم برای استفاده از
  اخبار (به‌عنوان جایگزین تحلیلی وقتی داده لحظه‌ای نیست) کامل شد.
- **UI:** `mcp_server/ui.py` — صفحه وب فارسی (RTL) با Starlette + uvicorn
  (هر دو وابستهٔ خود پکیج `mcp` هستند؛ هیچ نصب اضافه‌ای لازم نیست). بک‌اند
  یک **نشست MCP دائمی** به ساب‌پروسس `server.py` نگه می‌دارد، پس هر سوال
  واقعاً از پروتکل MCP می‌گذرد؛ صفحه پاسخ ابزارهای فراخوانی‌شده و زمان پاسخ
  را نشان می‌دهد.
- اجرا: `docker compose --profile mcp up -d --build mcp-ui` →
  `http://localhost:8000`
- تأیید: سوال طلای داخلی از طریق UI → فراخوانی `get_gold_price` و
  `get_usd_rate` روی همان نشست MCP و محاسبه فرمول (انس ~۴٬۰۰۵$، دلار
  ۱٬۱۱۸٬۰۰۰ → گرم ۱۸ عیار ≈ ۱۰۸ میلیون تومان) — در venv و داخل کانتینر هر
  دو تست شد. سوال روند با `--trend` هر سه ابزار (شامل اخبار فولاد) را صدا
  زد و برای دادهٔ غایب TSETMC «حدس نزن» را رعایت کرد.

---

## ۴. داکر

- هر خروجی یک ایمیج مستقل؛ `docker-compose.yml` با profile برای هر فصل.
- تمام تنظیمات (کلیدها، مدل، endpoint) فقط از `.env` — هیچ secretی در
  ایمیج یا ریپو نیست.
- نسخه‌های pin شده در `docker/requirements-base.txt`: `mcp<2` (در 2.x
  نام FastMCP عوض شده)، `pandas<3` (pytse-client روی API پانداس ۲ است).

## ۵. نحوه اجرای تست‌ها

```bash
cp .env.example .env            # کلیدها را پر کنید
docker compose build
docker compose --profile exercises run --rm ex1      # تا ex5
docker compose run --rm ex5 python -m exercises.ex5_meeting.analyze_meeting --version v1
docker compose --profile tool-use run --rm tool-test
docker compose --profile mcp run --rm mcp-test
docker compose --profile mcp run --rm mcp-test python mcp_server/client_test.py --break-usd
docker compose --profile mcp up -d --build mcp-ui    # UI اختیاری → localhost:8000
```
