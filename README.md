# MomentMeter — practical Office tutorials

القناة: https://www.youtube.com/@MomentMeter-z1e

## الاتجاه الحالي — 10 أكتوبر 2026

المشروع الآن Shorts تقنية أصلية عن Microsoft Excel وWord وPowerPoint، مع تعليق إنجليزي Pocket TTS 3.3.0 بصوت Alba، كابشن متزامن، 1080×1920/30fps/H.264/AAC، بلا موسيقى أو اشتراكات مدفوعة. اتجاه الحيوانات الموجود في بعض الكود القديم متروك؛ لا تستخدم مهامه كخطة إنتاج حالية.

المصدر التشغيلي الدائم للحالات هو MomentMeter-publishing-log.json الخاص بالمشروع، مع بصمة الملف ومعرّف YouTube وحالات prepared / awaiting_user_approval / scheduled / published منفصلة. المتصفح المتصل يفوّض النشر المباشر في Studio للشرح المكتبي؛ لا ينقل تسجيل الدخول إلى GitHub Actions أو يمنح API OAuth. راجع المحتوى قبل إعادة محاولة رفع غير مؤكد.

## الحالة المؤكدة

9 Shorts منشورة حتى بداية هذا التحديث، ومنها PowerPoint Morph `cnrbbOisDyk` وWord Table of Contents `02anMB7bvy4`. حلقتا Excel Ctrl+T وPaste Values لهما مواعيد 11 و12 أكتوبر في السجل؛ تحقق من المنصة قبل تغييرهما. iPhone يتطلب عرضاً وموافقة صريحة قبل النشر. لا تعتبر الجدولة نشراً.

## أدوات الجودة والتشغيل

- Remotion: مشاهد وأمثلة أصلية وتوقيت يعتمد الإطارات.
- faster-whisper: فحص تطابق النص والكابشن بتوقيت الكلمات؛ لا يثبت استماعاً شخصياً.
- FFmpeg: فك ترميز كامل، clipping، LUFS/true peak، تحليل الفيديو وcontact sheets.
- `office/publication_preflight.py`: بوابة محلية للهوية والبصمة والتكرار والسقف اليومي وأدلة الجودة. لا ترفع فيديو ولا تتعامل مع كلمات المرور؛ التقييم التحريري والفحص البصري منفصلان.
- Agent Reach / yt-dlp: بحث عام للأفكار فقط، دون نسخ فيديوهات الغير أو استخدام cookies. عدادات منافسين تراكمية لا تثبت ترنداً حالياً.

## النشر

YouTube Studio المباشر هو المسار المستخدم الآن. قبل النشر: verify exact channel → reconcile content → inspect full export → upload audited hash → metadata/sources/rights/disclosure → not made for kids → complete checks → public → confirm returned URL → update permanent log. توقّف عند CAPTCHA واتبع تسليم المتصفح، دون تجاوز.

الحد التحريري الأقصى 3 مقاطع أصلية مختلفة يومياً؛ ليس وعداً بإنتاج ثلاثة يومياً. Metricool المجاني له سقف منفصل 20 منشوراً شهرياً. الاحتياطي الجاهز لا يتجاوز 7. ربط OAuth وYouTube Data API المستقل غير مفعل لهذا المستودع، فلا تعتبر ملفات uploader أو workflow القديم نشرًا آلياً عاملاً.

## الكود القديم

`CLOUD.md` و`cloud.py` و`data/jobs/` وworkflows القديمة محفوظة للتاريخ ولا تمثل اتجاه الإنتاج الحالي. أسرار Google لا توضع في الكود أو الشات. تشغيل GitHub Actions القديم لم يُستبدل هنا بمحرك إنتاج أو نشر غير مُختبر.
