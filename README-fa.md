# ferien-mcp 🏖️

mcp-name: io.github.mohammad-abbasi-sh/ferien-mcp

سرور MCP غیررسمی و **فقط‌خواندنی** برای **تعطیلات مدارس آلمان** (Schulferien) از طریق [API سایت ferien-api.de](https://ferien-api.de) (پروژهٔ bundesAPI): تعطیلات هر سال در هر ایالت فدرال، بررسی اینکه یک تاریخ در تعطیلات مدارس است یا نه، نزدیک‌ترین تعطیلات از یک تاریخ، و تعطیلات در یک بازهٔ زمانی. بدون کلید و بدون ورود.

> ساختهٔ محمد عباسی در چارچوب «کارخانهٔ MCP آلمان». وابسته به ferien-api.de / پروژهٔ bundesAPI نیست.

## برای ایجنت‌های هوش مصنوعی

به پیکربندی MCP Client اضافه کنید (stdio):

```json
{
  "mcpServers": {
    "ferien": {
      "command": "uvx",
      "args": ["ferien-mcp==0.1.0"]
    }
  }
}
```

یا به‌صورت محلی اجرا کنید: `python -m ferien_mcp.server` (نیازمند `mcp<2` و `httpx`).

## ابزارها

| ابزار | توضیح |
|------|-------|
| `ferien_list_holidays` | تعطیلات مدارس یک سال در یک ایالت فدرال (با فیلتر اختیاری ماه) |
| `ferien_is_holiday` | آیا یک تاریخ (YYYY-MM-DD) در تعطیلات مدارس یک ایالت است؟ |
| `ferien_next_holiday` | نزدیک‌ترین تعطیلات مدارس از یک تاریخ به بعد (اگر تاریخ در تعطیلات باشد، همان تعطیلات جاری را برمی‌گرداند؛ به سال بعد هم نگاه می‌کند) |
| `ferien_holidays_between` | تعطیلات مدارسی که با یک بازهٔ زمانی هم‌پوشانی دارند (حداکثر حدود ۲ سال) |
| `ferien_list_states` | هر ۱۶ ایالت فدرال |
| `ferien_health` | بررسی دسترسی به API (ok / blocked / error) — یک درخواست مؤدبانه |

نمونهٔ خروجی (`ferien_is_holiday` / ۲۰۲۶-۰۸-۱۰، BY):

```json
{"date": "2026-08-10", "weekday": "Monday", "weekday_de": "Montag",
 "state": "BY", "state_name": "Bayern", "is_holiday": true,
 "holidays": ["sommerferien bayern 2026"],
 "details": [{"name": "sommerferien bayern 2026", "kind": "sommerferien",
   "slug": "sommerferien bayern 2026-2026-BY", "state": "BY",
   "year": 2026, "start": "2026-08-03", "end": "2026-09-15",
   "duration_days": 44, "start_weekday": "Monday",
   "start_weekday_de": "Montag", "end_weekday": "Tuesday",
   "end_weekday_de": "Dienstag"}]}
```

نکته‌ها:
- کد ایالت‌ها دو حرفی است: BW، BY، BE، BB، HB، HH، HE، MV، NI، NW، RP، SL، SN، ST، SH، TH. **فهرست سراسری وجود ندارد** — تعطیلات مدارس به ایالت بستگی دارد، پس هر درخواست به یک ایالت نیاز دارد. فهرست کامل را از `ferien_list_states` بگیرید.
- نام تعطیلات آلمانی است («sommerferien bayern 2026»)؛ هر ردیف یک `kind` هم دارد (winterferien، frühjahrsferien، osterferien، pfingstferien، sommerferien، herbstferien، weihnachtsferien، beweglicher ferientag) و مدت آن به روز.
- **پوشش داده‌ها بسته به ایالت و سال فرق می‌کند**: API برای ایالت/سالی که داده ندارد فهرست خالی برمی‌گرداند — مثلاً برلین ۲۰۲۶ در ۲۰۲۶-۱۱-۱۴ خالی بود، در حالی که برلین ۲۰۲۵ هفت ورودی دارد. تاریخ‌های مهم را با منبع رسمی بررسی کنید.
- تعطیلاتِ میان‌سالی (مثلاً Weihnachtsferien که تا ژانویه ادامه دارد) در `ferien_holidays_between` لحاظ می‌شوند اگر با بازه هم‌پوشانی داشته باشند.
- سال‌های ۲۰۰۰ تا ۲۱۰۰ پذیرفته می‌شوند.
- این API برای هر IP محدودیت نرخ سخت‌گیرانه دارد (به گفتهٔ مستنداتش: «heavily abused, aggressive rate limiting is in place»). اگر پاسخی با HTTP 429 گرفتید، چند دقیقه صبر کنید و دوباره تلاش کنید — در ۲۰۲۶-۱۱-۱۴ محدودیت بعد از حدود ۱۰ دقیقه برطرف شد.

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
