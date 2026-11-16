import re, subprocess, sys, tempfile, os

PATH = 'android/app/src/main/assets/index.html'

def rep(s, old, new):
    n = s.count(old)
    assert n == 1, 'المرساة وُجدت %d مرة (المطلوب مرة واحدة): %s' % (n, old[:60])
    return s.replace(old, new)

s = open(PATH, encoding='utf-8').read()
orig = s

# 1) إصلاح زر «احفظ نسخة الآن» داخل الـAPK: استعمال الجسر الأصلي بدل مشاركة المتصفح
s = rep(s, "إرسال النسخة إليه.')}}}",
"""إرسال النسخة إليه.')}}
 window.quickBk=async function(){const pw=(($('#qpw')||{}).value)||'';if(pw&&pw.length<4){toast('كلمة المرور 4 أحرف على الأقل، أو اتركها فارغة');return}
  let tx;try{tx=await pack(pw)}catch(e){toast('تعذّر إنشاء النسخة');return}
  const nm='halaqa-backup-'+S.day.date+'.txt',b64=btoa(unescape(encodeURIComponent(tx)));
  try{AndroidBridge.share(nm,b64)}catch(e){toast('تعذّر فتح المشاركة، جرّب «تنزيل ملف» من ⚙');return}
  S.ext=Date.now();save();toast('فتح خيار المشاركة؛ اختر مكاناً آمناً خارج الهاتف (Drive أو غيره). لا يُسجَّل الحفظ إلا بعد أن تتأكد أن الملف وصل.')}
}""")

# 2) نقطة حفظ تلقائية عند أول تشغيل بعد هذا الإصدار
s = rep(s, "if(!S.sn6){snap('قبل تحديث دفعة حماية البيانات');S.sn6=1;save()}",
"if(!S.sn6){snap('قبل تحديث دفعة حماية البيانات');S.sn6=1;save()}\nif(!S.sn7){snap('قبل إصلاح النسخة السريعة في الأندرويد');S.sn7=1;save()}")

assert s != orig

# فحص صياغة كل سكربت داخلي بـ node
scripts = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', s, re.S)
assert scripts, 'لم أجد سكربتاً داخلياً'
for i, code in enumerate(scripts):
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
        f.write(code)
    r = subprocess.run(['node', '--check', f.name], capture_output=True, text=True)
    os.unlink(f.name)
    assert r.returncode == 0, 'خطأ صياغة في السكربت %d:\n%s' % (i, r.stderr)

open(PATH, 'w', encoding='utf-8').write(s)

# رفع رقم الإصدار حتى يُقبل التثبيت فوق القديم
G = 'android/app/build.gradle'
g = open(G, encoding='utf-8').read()
g = rep(g, 'versionCode 5', 'versionCode 6')
g = rep(g, "versionName '1.4.1'", "versionName '1.4.2'")
open(G, 'w', encoding='utf-8').write(g)

print('تم التعديل بنجاح وفحص الصياغة سليم')
