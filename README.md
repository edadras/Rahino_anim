# Rahino_anim — Tripo3D pipeline

پروژه‌ی ساخت مدل و انیمیشن سه‌بعدی با [Tripo3D](https://studio.tripo3d.ai) از طریق Open API.

## راه‌اندازی

1. از [platform.tripo3d.ai](https://platform.tripo3d.ai) (همان اکانت استودیو) یک API Key بگیرید.
2. کلید را ست کنید — یکی از دو راه:
   - متغیر محیطی: `export TRIPO_API_KEY=tsk_...`
   - یا `cp .env.example .env` و کلید را داخل `.env` بگذارید (این فایل کامیت نمی‌شود).
3. وابستگی‌ها: `pip install -r requirements.txt`

> **Claude Code on the web:** در تنظیمات Environment باید دامنه‌های
> `api.tripo3d.ai` و `tripo-data.rg1.data.tripo3d.ai` (یا کلاً `*.tripo3d.ai`)
> در network allowlist مجاز باشند.

## استفاده

```bash
python generate.py balance                      # کردیت باقی‌مانده
python generate.py text "a cartoon rhino"       # متن → مدل سه‌بعدی (GLB)
python generate.py image ./photo.jpg            # عکس → مدل سه‌بعدی
python generate.py rig <model_task_id>          # ریگ کردن مدل برای انیمیشن
python generate.py animate <rig_task_id> --animation preset:run
python generate.py status <task_id>             # وضعیت یک تسک
python generate.py download <task_id>           # دانلود خروجی‌های تسک
```

خروجی‌ها در `outputs/<task_id>/` ذخیره می‌شوند و همه‌ی تسک‌ها در داشبورد
اکانت Tripo شما هم قابل مشاهده‌اند (و قابل import به Studio).

## پایپ‌لاین کاراکتر زنده

کل زنجیره (عکس → مدل → ریگ → چند انیمیشن) با یک دستور:

```bash
python pipeline.py assets/rahino.png
```

خروجی‌ها در `assets/` ذخیره می‌شوند و وضعیت هر مرحله در
`assets/pipeline_state.json` می‌ماند (اجرای دوباره، مراحل تمام‌شده را
دوباره نمی‌سازد و کردیت اضافه مصرف نمی‌کند).

مسیر فایل‌های GLB در `viewer/models/manifest.json` تنظیم می‌شود
(می‌تواند مستقیم به `assets/…` اشاره کند). نمایشگر را از ریشه‌ی ریپو serve کنید:

```bash
python -m http.server 8000
# سپس http://localhost:8000/viewer/
```

نمایشگر (three.js) امکانات زیر را دارد:
- سوییچ نرم بین انیمیشن‌ها (idle/walk/run/jump/…)
- **حرکات لحظه‌ای بدون انیمیشن از قبل ساخته** (procedural): تکان سر، بای‌بای،
  تعظیم، دست بالا، نگاه به چپ/راست — با چرخاندن مستقیم استخوان‌های ریگ،
  روی هر انیمیشنِ در حال پخش سوار می‌شوند
- لیپ‌سینک با فایل صوتی یا میکروفون (دامنه‌ی صدا → استخوان فک یا morph target)
- چرخش/زوم دوربین

### API حرکات (برای اتصال به سیستم خودتان)

در کنسول مرورگر یا از کد جاوااسکریپت:

```js
rahino.list()                  // فهرست حرکات موجود
rahino.do('بای‌بای')           // اجرای حرکت (holdها با اجرای دوباره آزاد می‌شوند)
rahino.bones                   // دسترسی مستقیم به استخوان‌ها (Head, R_Upperarm, …)

// تعریف حرکت جدید فقط با داده — بدون کد:
rahino.gestures['شانه بالا'] = { dur: 1.2, tracks: [
  { bone: 'L_Clavicle', axis: 'x', amp: 0.4 },   // محورها جهانی‌اند
  { bone: 'R_Clavicle', axis: 'x', amp: -0.4 },
]};
rahino.do('شانه بالا');
```

قرارداد محورها (کاراکتر رو به +X): `z` = خم شدن جلو/عقب، `y` = چرخش چپ/راست،
`x` = بالا بردن جانبی دست‌ها. `cycles` حرکت را نوسانی می‌کند (مثل تکان دادن)،
`hold: true` حالت را نگه می‌دارد تا دوباره صدا زده شود.

## ساختار

- `tripo_client.py` — کلاینت سبک برای Open API (ساخت تسک، polling، دانلود)
- `generate.py` — رابط خط فرمان تک‌مرحله‌ای
- `pipeline.py` — زنجیره‌ی کامل کاراکتر (عکس تا انیمیشن) با resume
- `viewer/` — نمایشگر وب کاراکتر زنده با لیپ‌سینک
