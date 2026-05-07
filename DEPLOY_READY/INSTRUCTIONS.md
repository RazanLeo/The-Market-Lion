# تعليمات النشر — Dashboard كامل مع كل القوائم من الإكسيل

## ما الذي تم بناؤه

ملف `app/frontend/app/dashboard/page.tsx` (680 سطر) يحتوي على:

### الجداول الكاملة من ملف الإكسيل
- **23 أداة** في جدول الأدوات الأساسية (Price Action, S&R, Trend Lines, MAs 200/60/7/21, FRAMA 126, Channels, SMC+ICT, Supply/Demand, Wyckoff, Fibonacci, RSI Divergence, Bookmap)
- **47 مدرسة** في جدول مدارس التحليل الفني (Dow, IPDA, Andrews, P&F, Darvas, Weinstein, Fractal, Turtle, Elliott, Wyckoff, Hurst, DeMark, Kondratieff, VSA, Market Profile, VWAP, AMT, Footprint, DarkPool, Volume Profile/TPO, Fib Fans, Gann, Harmonic, Sacred Geometry, Renko, Heikin Ashi, Kagi, Three Line Break, Range Bars, Tick Charts, Mean Reversion, Intermarket, COT, Breadth, Seasonality, AI/ML, Mansfield, CANSLIM, Gann Time, Momentum, Gann Star, Fib Time, Cyclic, Astrology, Sessions, Volume Charts)
- **135+ مؤشر** مصنّف (اتجاه/زخم/تقلب/حجم/دعم-مقاومة/أنظمة متكاملة/سلوك مؤسسي/Lion مخصص) بما فيها 20 مؤشر Lion مخصص (ARC, BUMP, DUMP, ROAR, CLAW, MANE, PRIDE, HUNT, FANG, JUMP, CUB, KING, SAFARI, EYES, PAW, TAIL, DEN, ROCK, SNARE, HEART)
- **8 بنود البوك ماب** (Order Flow, DOM, Cumulative Delta, Absorbed Volume, Iceberg, BSL, SSL, Liquidity Sweep)
- **30 بند خطة التداول** (الرصيد، نسبة المخاطرة، الرافعة، اللوت، الهامش بكل أنواعه، السوق، الأصل، نوع التداول، الإطار، الشراء/البيع، الدخول، الأهداف 1/2/3 + النهائي، وقف الخسارة + التحريك، التعزيز، البيب، الربح، الخسارة، العمولة + السبريد + السواب، التراكمي، التقييم اليومي/الأسبوعي/الشهري)

### المتطلبات الأربعة من رزان كلها مطبّقة
1. **9 إطارات زمنية كأعمدة** بجانب كل صف (1M, 5M, 15M, 30M, 1H, 4H, 1D, 1W, 1Mo) — كل خلية تعرض شراء/بيع + نسبة الثقة بلون أحمر/أخضر
2. **زر تشغيل/إيقاف الرسم على الشارت** لكل صف (جميع المدارس والأدوات والمؤشرات)
3. **القرار النهائي حسب الإطار الزمني** لكل جدول (شريط سفلي مع 9 خانات)
4. **القرار النهائي لكامل التحليل** في بطاقة Confluence مع 9 خانات إطارات + النسبة الإجمالية + التقسيم إلى 5 محاور

### إضافات
- **الشعار** الأسد الذهبي بالتاج محفوظ في `app/frontend/public/brand/logo.jpg` ومدمج في الهيدر بحجم 48x48px مع حلقة ذهبية
- **شريط أسعار حيّ** متحرك (12 رمز)
- **شارت TradingView** مدمج مع 4 مؤشرات افتراضية (BB, RSI, MACD, VWAP)
- **18 رمز** للاختيار (XAUUSD, XAGUSD, EURUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, BRENT, USOIL, BTCUSD, ETHUSD, NAS100, SPX500, US30, GER40, UK100)
- **5 وسطاء** (Capital.com, IC Markets, Pepperstone, Exness, Saxo)

## ملفات النشر

- `dashboard-v2.tar.gz` — ضغط 134KB يحوي page.tsx + logo.jpg
- `dashboard-v2.b64` — base64 جاهز للـ paste injection (179KB)

## أوامر النشر على السيرفر

```bash
# 1) فك الضغط في مكان مؤقت
cd /tmp && rm -rf feextract && mkdir feextract
base64 -d /tmp/dash.b64 > /tmp/dash.tar.gz
tar tzf /tmp/dash.tar.gz | head
tar xzf /tmp/dash.tar.gz -C /tmp/feextract

# 2) نسخ الملفات إلى مكانها
cp /tmp/feextract/app/dashboard/page.tsx /opt/the-market-lion/app/frontend/app/dashboard/page.tsx
mkdir -p /opt/the-market-lion/app/frontend/public/brand
cp /tmp/feextract/public/brand/logo.jpg /opt/the-market-lion/app/frontend/public/brand/logo.jpg

# 3) إعادة بناء صورة Docker
cd /opt/the-market-lion/app/frontend
docker build -t ghcr.io/razanleo/the-market-lion-frontend:latest .

# 4) إعادة تشغيل الحاوية
cd /opt/the-market-lion/app
docker compose -f docker-compose.prod.yml -f docker-compose.override.yml up -d --no-deps --force-recreate frontend

# 5) التحقق
sleep 8 && curl -s -o /dev/null -w "%{http_code}" http://localhost/dashboard
```

## نقطة الانقطاع

جلسة DO Web Console انتهت وتطلب إعادة مصادقة. بمجرد تسجيل الدخول من جديد، يمكن إكمال النشر بنفس آلية الـ chunked-paste السابقة (10 دفعات × 1500 حرف).

MD5 verify: `9465414c0315c1195eae2319932513a5  dashboard-v2.tar.gz`
