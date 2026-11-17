import re, subprocess, tempfile, os

PATH = 'android/app/src/main/assets/index.html'

def rep(s, old, new):
    n = s.count(old)
    assert n == 1, 'المرساة وُجدت %d مرة (المطلوب مرة واحدة): %s' % (n, old[:60])
    return s.replace(old, new)

s = open(PATH, encoding='utf-8').read()
orig = s

# تأكد أن رقم نقطة الحفظ الجديد غير مستعمل من قبل
assert 'S.sn12' not in s and 'sn12:' not in s, 'sn12 مستعمل سابقاً'

# 1) رقم الإصدار الظاهر في الإعدادات
s = rep(s, "const VER='2026-11-14.1';", "const VER='2026-11-17.1';")

# 2) نقطة حفظ تلقائية حقيقية عند أول تشغيل (الرقم الجديد sn12)
s = rep(s, "if(!S.sn5){snap('قبل تحديث الدفعة الأولى (النقاط والتقارير والإعدادات)');S.sn5=1;save()}",
"if(!S.sn5){snap('قبل تحديث الدفعة الأولى (النقاط والتقارير والإعدادات)');S.sn5=1;save()}\nif(!S.sn12){snap('قبل إصدار 2026-11-17.1');S.sn12=1;save()}")

# 3) البيانات الجديدة تبدأ وعلامة sn12 مسجلة
s = rep(s, "sn11:1,st:D.st", "sn11:1,sn12:1,st:D.st")

assert s != orig

scripts = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', s, re.S)
assert scripts, 'لم أجد سكربتاً داخلياً'
for i, code in enumerate(scripts):
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
        f.write(code)
    r = subprocess.run(['node', '--check', f.name], capture_output=True, text=True)
    os.unlink(f.name)
    assert r.returncode == 0, 'خطأ صياغة في السكربت %d:\n%s' % (i, r.stderr)

open(PATH, 'w', encoding='utf-8').write(s)

G = 'android/app/build.gradle'
g = open(G, encoding='utf-8').read()
g = rep(g, 'versionCode 6', 'versionCode 7')
g = rep(g, "versionName '1.4.2'", "versionName '1.4.3'")
open(G, 'w', encoding='utf-8').write(g)

print('تم التعديل بنجاح وفحص الصياغة سليم')
