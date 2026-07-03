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

## ساختار

- `tripo_client.py` — کلاینت سبک برای Open API (ساخت تسک، polling، دانلود)
- `generate.py` — رابط خط فرمان
