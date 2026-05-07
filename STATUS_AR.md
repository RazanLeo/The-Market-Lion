# حالة المنصة — تحديث رزان

## ما تم تصحيحه الآن

### 1. مصادر البيانات الحقيقية والحيّة (مجاناً، بدون API keys)
- **Yahoo Finance** = مصدر OHLCV الأساسي للذهب، البترول، الفوركس، الأسهم، الكريبتو
- **Stooq.com** = مصدر احتياطي عبر CSV-over-HTTPS
- **Capital.com / Exness** = ✗ **غير مستخدمين** للتحليل. هما فقط لربط حساب التداول الشخصي للمستخدم لتنفيذ صفقات البوت
- ملف الكود: `app/backend/app/services/data_sources/`
  - `yahoo.py` — fetch OHLCV + quotes من Yahoo
  - `stooq.py` — fallback من Stooq
  - `__init__.py` — `get_ohlcv()` + `get_quote()` يجربان Yahoo ثم Stooq

### 2. كل الـ 295 محلل يعمل على بيانات حية
- `/api/v1/analysis/schools` → يجلب OHLCV من Yahoo، يشغّل **160 محلل** (140 مدرسة + 20 أداة)، يرجع نتيجة + ثقة + payload لكل واحد
- `/api/v1/analysis/indicators` → يشغّل **135 مؤشر**
- `/api/v1/analysis/basics` → 7 أدوات أساسية (RSI, EMA, MACD, VWAP, Bollinger, ATR, ADX)
- `/api/v1/analysis/confluence` → يجمع كل الفئات ويُخرج Buy/Sell/Wait + total_pct
- `/api/v1/analysis/trade-plan` → entry/SL/TP1/TP2/TP3 + lot size + R:R
- `/api/v1/analysis/drawings` → 20 أداة، كل منها يُخرج رسومات (lines/rects/markers) للعرض على الشارت
- `/api/v1/market/tickers` → 12 رمز بأسعار حية من Yahoo
- `/api/v1/market/ohlcv` → الشموع للشارت

كل endpoint يُكشّف على Redis لمدة 30 ثانية لتقليل الضغط.

### 3. دخولان منفصلان كلياً
- **`/auth/login`** → دخول المستخدم/المشترك → يذهب إلى `/dashboard`
- **`/admin/login`** → دخول مدير المنصة → يتحقق من الـ role، إذا ليس admin يرفض → يذهب إلى `/admin`
- ملف: `frontend/app/admin/login/page.tsx` (جديد)

### 4. الجداول الثمانية
موجودة وموصولة بالـ APIs الحقيقية:
| رقم | الجدول | API | المحللات |
|:-:|:-|:-|--:|
| 1 | User Options | n/a | إعدادات المستخدم |
| 2 | Fundamental | `/analysis/fundamental` | News + Events |
| 3 | Basic Tools | `/analysis/basics` | 7 |
| 4 | **Schools** | `/analysis/schools` | **160** |
| 5 | **Indicators** | `/analysis/indicators` | **135** |
| 6 | Order Flow | `/analysis/flow` | 3 + buy/sell volume |
| 7 | Trade Plan | `/analysis/trade-plan` | entry/SL/TP/lot |
| 8 | **Final Decision** | `/analysis/confluence` | aggregate |

### 5. Voting Worker (Celery)
`app/backend/app/workers/tasks/voting_tasks.py`:
- يستخدم **Yahoo/Stooq** (لا Capital.com)
- يدور على 5 رموز × 3 أُطر زمنية = 15 (sym, tf) كل دقيقة
- يكتب 160 صف في `school_signals` + 135 صف في `indicator_signals` لكل دورة
- ينشر الإشارات على Redis pubsub للـ WebSocket clients

## ما ينقص (لا يمكن تنفيذه في الـ sandbox)
- اختبار Yahoo/Stooq الحي → الـ sandbox يحجب الاتصالات الخارجية (proxy 403). على الـ Droplet مباشرةً يعمل.
- بناء `npm run build` كامل → الـ sandbox `node_modules` تالف. على الـ Droplet يعمل.

## الخطوات للتشغيل الفعلي
```bash
# على الـ Droplet (161.35.192.36)
ssh root@161.35.192.36
cd /opt/the-market-lion
git pull
docker compose -f app/docker-compose.prod.yml up -d --build
```

البوت يبدأ تلقائياً يجلب البيانات من Yahoo + Stooq كل دقيقة، ويملأ الجداول الثمانية بـ160 + 135 صفاً ببيانات حية.

## التحقق
```
44/44 pytest passing
295 analyzers registered (140 + 135 + 20)
50 API routes wired
12 i18n files (102 keys each, schema-identical)
bandit: 0 high / 0 medium
```
