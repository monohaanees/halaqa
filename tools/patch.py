import re, subprocess, tempfile, os

PATH = 'android/app/src/main/assets/index.html'
GRADLE = 'android/app/build.gradle'

def rep(s, old, new):
    n = s.count(old)
    assert n == 1, 'المرساة وُجدت %d مرة (المطلوب مرة واحدة): %s' % (n, old[:60])
    return s.replace(old, new)

s = open(PATH, encoding='utf-8').read()
orig = s

assert 'delDay' not in s and 'sn14' not in s, 'الباتش طُبّق سابقاً'
assert "const VER='2026-11-18.1';" in s, 'الملف ليس بإصدار 2026-11-18.1 المتوقع'

# 1) الإصدار + نقطة حفظ تلقائية عند أول تشغيل (sn14)
s = rep(s, "const VER='2026-11-18.1';", "const VER='2026-11-19.1';")
s = rep(s, "if(!S.sn13){snap('قبل إصدار 2026-11-18.1');S.sn13=1;save()}",
"if(!S.sn13){snap('قبل إصدار 2026-11-18.1');S.sn13=1;save()}\nif(!S.sn14){snap('قبل إصدار 2026-11-19.1');S.sn14=1;save()}")
s = rep(s, "sn11:1,sn12:1,sn13:1,st:D.st", "sn11:1,sn12:1,sn13:1,sn14:1,st:D.st")

# 2) الدوال الجديدة: حذف سجل يوم / نقل سجل يوم إلى تاريخ آخر
NEW_JS = r'''/* ===== نهاية النسخ التلقائي ===== */
/* ===== حذف/نقل سجل يوم مرحَّل (2026-11-19) ===== */
const dayRows=(date,sp)=>S.log.filter(r=>r[0]===date&&(r[26]==='خاصة')===sp);
function delDay(){const d=S.day,sp=isSp(),rows=dayRows(d.date,sp);if(!rows.length){toast('لا سجل مرحَّل لهذا التاريخ');return false}
 snap('قبل حذف سجل '+d.date);
 S.trash.push({k:'حصة',d:{date:d.date,sp:sp,rows:rows.slice(),ct:(S.ct||{})[d.date]||0},t:Date.now()});
 S.log=S.log.filter(r=>!(r[0]===d.date&&(r[26]==='خاصة')===sp));
 if(S.ct&&!S.log.some(r=>r[0]===d.date))delete S.ct[d.date];
 if(d.reop===d.date)d.reop='';
 save();toast('حُذف سجل '+d.date+' ونُقل إلى سلة المحذوفات (⚙ ← نقاط الحفظ والمحذوفات)');render();return true}
function mvDay(to){const d=S.day,sp=isSp(),from=d.date;
 if(!/^\d{4}-\d{2}-\d{2}$/.test(to||'')){toast('اختر التاريخ الجديد أولاً');return false}
 if(to===from){toast('هذا هو التاريخ نفسه');return false}
 const rows=dayRows(from,sp);if(!rows.length){toast('لا سجل مرحَّل لهذا التاريخ');return false}
 const names=new Set(rows.map(r=>r[1])),clash=S.log.filter(r=>r[0]===to&&(r[26]==='خاصة')===sp&&(!sp||names.has(r[1])));
 if(clash.length){toast('يوجد سجل مرحَّل في '+to+'؛ احذفه أولاً (يذهب للسلة) ثم أعد النقل');return false}
 snap('قبل نقل سجل '+from+' إلى '+to);
 rows.forEach(r=>{r[0]=to});
 S.ct=S.ct||{};const c=S.ct[from]||0;if(!S.log.some(r=>r[0]===from))delete S.ct[from];if(c&&!S.ct[to])S.ct[to]=c;
 d.date=to;d.reop='';save();toast('نُقل السجل من '+from+' إلى '+to);render();return true}
const dayTools=()=>{const d=S.day,sp=isSp();return`<div class='card'><b>تصحيح تاريخ هذا السجل</b><div class='msg'>إن سجّلته في يوم خطأ: انقله إلى التاريخ الصحيح، أو احذفه (يذهب إلى سلة المحذوفات ويمكن استرجاعه). النقاط المحسوبة وقت الترحيل تبقى كما هي.</div><label>نقل إلى تاريخ<input type='date' id='mvto'></label><button id='mvday'>نقل السجل إلى هذا التاريخ</button><button id='delday'>حذف ${sp?'السجل الخاص ل':'سجل '}${esc(d.date)}</button></div>`};
/* ===== نهاية حذف/نقل السجل ===== */'''
s = rep(s, "/* ===== نهاية النسخ التلقائي ===== */", NEW_JS)

# 3) أزرار التصحيح تظهر مع زر «إعادة الفتح» (الحصة العادية والخاصة)
s = rep(s, '<button id="reopen">إعادة فتحها للتعديل</button>`;', '<button id="reopen">إعادة فتحها للتعديل</button>${dayTools()}`;')
s = rep(s, "إعادة فتح الحصة الخاصة المرحَّلة لهذا التاريخ</button>", "إعادة فتح الحصة الخاصة المرحَّلة لهذا التاريخ</button>${dayTools()}")

# 4) معالج الأزرار: نقرتان للتأكيد
s = rep(s, "return}reopen()}else if(id==='xsave')saveEx();",
"return}reopen()}else if(id==='delday'){if(!b.dataset.ok){b.dataset.ok=1;b.textContent='اضغط للتأكيد: يُنقل السجل إلى سلة المحذوفات';return}delDay()}else if(id==='mvday'){const to=($('#mvto')||{}).value;if(!to){toast('اختر التاريخ الجديد أولاً');return}if(!b.dataset.ok){b.dataset.ok=1;b.textContent='اضغط للتأكيد: نقل السجل إلى '+to;return}mvDay(to)}else if(id==='xsave')saveEx();")

# 5) السلة: عرض واسترجاع نوع «حصة»
s = rep(s, ":esc(t.d[0])+' · '+esc(t.d[1])}",
           ":t.k==='حصة'?esc(t.d.date)+' · '+t.d.rows.length+' سجل'+(t.d.sp?' (خاصة)':''):esc(t.d[0])+' · '+esc(t.d[1])}")
s = rep(s, "\n (t.k==='اختبار'?S.ex:S.adj).push(t.d);save();toast('تمت الاستعادة من السلة');render();return true}",
"""
 if(t.k==='حصة'){const sp=!!t.d.sp,nm=new Set(t.d.rows.map(x=>x[1]));
  if(S.log.some(r=>r[0]===t.d.date&&(r[26]==='خاصة')===sp&&(!sp||nm.has(r[1])))){S.trash.splice(i,0,t);toast('يوجد سجل مرحَّل في '+t.d.date+' الآن؛ احذفه أو انقله أولاً ثم استرجع');return false}
  const miss=t.d.rows.filter(x=>!byName(x[1])).map(x=>x[1]);
  if(miss.length){S.trash.splice(i,0,t);toast('طلاب هذا السجل غير موجودين الآن: '+miss.slice(0,3).join('، ')+'؛ استرجعهم أولاً');return false}
  snap('قبل استرجاع سجل '+t.d.date);S.log.push(...t.d.rows);S.ct=S.ct||{};if(t.d.ct&&!S.ct[t.d.date])S.ct[t.d.date]=t.d.ct;save();toast('استُرجع سجل '+t.d.date);render();return true}
 (t.k==='اختبار'?S.ex:S.adj).push(t.d);save();toast('تمت الاستعادة من السلة');render();return true}""")

assert s != orig

scripts = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', s, re.S)
assert scripts, 'لم أجد سكربتاً داخلياً'
for i, code in enumerate(scripts):
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
        f.write(code)
    r = subprocess.run(['node', '--check', f.name], capture_output=True, text=True)
    os.unlink(f.name)
    assert r.returncode == 0, 'خطأ صياغة في السكربت %d:\n%s' % (i, r.stderr)

g = open(GRADLE, encoding='utf-8').read()
g = rep(g, 'versionCode 8', 'versionCode 9')
g = rep(g, "versionName '1.5.0'", "versionName '1.5.1'")
open(GRADLE, 'w', encoding='utf-8').write(g)

open(PATH, 'w', encoding='utf-8').write(s)
print('تم التعديل بنجاح وفحص الصياغة سليم')
