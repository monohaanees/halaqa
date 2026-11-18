import re, subprocess, tempfile, os

PATH = 'android/app/src/main/assets/index.html'
JAVA = 'android/app/src/main/java/com/monohaanees/halaqa/MainActivity.java'
GRADLE = 'android/app/build.gradle'

def rep(s, old, new):
    n = s.count(old)
    assert n == 1, 'المرساة وُجدت %d مرة (المطلوب مرة واحدة): %s' % (n, old[:60])
    return s.replace(old, new)

# ===================== index.html =====================
s = open(PATH, encoding='utf-8').read()
orig = s

# تأكد أن رقم نقطة الحفظ الجديد غير مستعمل من قبل
assert 'S.sn13' not in s and 'sn13:' not in s, 'sn13 مستعمل سابقاً'
assert 'autoRun' not in s, 'الباتش طُبّق سابقاً'

# 1) رقم الإصدار الظاهر
s = rep(s, "const VER='2026-11-17.1';", "const VER='2026-11-18.1';")

# 2) نقطة حفظ تلقائية عند أول تشغيل (sn13) + البيانات الجديدة تبدأ بها مسجّلة
s = rep(s, "if(!S.sn12){snap('قبل إصدار 2026-11-17.1');S.sn12=1;save()}",
"if(!S.sn12){snap('قبل إصدار 2026-11-17.1');S.sn12=1;save()}\nif(!S.sn13){snap('قبل إصدار 2026-11-18.1');S.sn13=1;save()}")
s = rep(s, "sn11:1,sn12:1,st:D.st", "sn11:1,sn12:1,sn13:1,st:D.st")

# 3) المنطق الجديد: نسخة تلقائية في الهاتف + فترة التذكير + سؤال «هل رُفعت؟»
NEW_JS = r'''const extDays=()=>S.ext?Math.floor((Date.now()-S.ext)/864e5):null;
/* ===== نسخ تلقائي في الهاتف وتذكير الرفع (2026-11-18) ===== */
const remDays=()=>{const n=Math.floor(+S.rdi);return n>=1&&n<=90?n:7};
const autoIv=()=>S.abi==='d'?'d':'w';
const dataFp=()=>fnv(JSON.stringify({st:S.st,log:S.log,ex:S.ex,adj:S.adj,set:S.set||{}}));
const autoDue=now=>{if(!S.st.length&&!S.log.length)return false;if(S.abf===dataFp())return false;if(!S.abt)return true;return autoIv()==='d'?iso(new Date(S.abt))!==iso(new Date(now)):now-S.abt>=7*864e5};
let ABUSY=0;
async function autoRun(force){
 if(ABUSY||!window.AndroidBridge||typeof AndroidBridge.autoSave!=='function')return'skip';
 const now=Date.now();
 if(!force&&!autoDue(now))return'skip';
 if(!S.st.length&&!S.log.length)return'empty';
 ABUSY=1;let res='fail';
 try{
  const tx=await pack(S.abp||''),d=new Date(now),nm='halaqa-auto-'+iso(d)+'-'+String(d.getHours()).padStart(2,'0')+String(d.getMinutes()).padStart(2,'0')+'.txt',r=String(AndroidBridge.autoSave(nm,btoa(unescape(encodeURIComponent(tx)))));
  if(r==='ok:'+tx.length){S.abt=now;S.abf=dataFp();S.abm='';res='ok'}
  else if(r==='perm'){S.abm='يلزم إذن التخزين: وافق عليه ثم اضغط «اكتب نسخة الآن»';res='perm'}
  else S.abm='تعذّرت الكتابة ('+r+')'
 }catch(e){S.abm='تعذّرت الكتابة'}
 ABUSY=0;try{save()}catch(e){}
 if(S.v==='cfg')render();
 return res}
async function autoNow(){const r=await autoRun(1);toast(r==='ok'?'كُتبت النسخة في مجلد التنزيلات':r==='empty'?'لا بيانات لنسخها':r==='skip'?'غير متاح هنا':(S.abm||'تعذّرت الكتابة'))}
const pendBanner=()=>{if(!S.pend)return'';const t=new Date(S.pend);return`<div class='bn'>فتحتَ المشاركة (${iso(t)} ${t.toTimeString().slice(0,5)}). هل وصلت النسخة فعلاً إلى درايف أو مكان آمن خارج الهاتف؟<div class='row' style='margin-top:6px'><button id='pyes'>نعم، رُفعت</button><button id='pno'>لا</button></div></div>`};
const abUI=()=>{const A=!!window.AndroidBridge,iv=autoIv(),t=S.abt?new Date(S.abt):null;
 return`<div class='card cl'><b>النسخ التلقائي والتذكير</b><div id='abpend'>${pendBanner()}</div>`+(A?`<div class='msg'>${t?'آخر نسخة تلقائية في الهاتف: '+iso(t)+' '+t.toTimeString().slice(0,5):'لم تُكتب نسخة تلقائية بعد'} (مجلد التنزيلات)${S.abm?`<br><span class='err'>${esc(S.abm)}</span>`:''}</div><label>تكرار النسخة التلقائية في الهاتف<select id='abi'><option value='w'${iv==='w'?' selected':''}>كل أسبوع</option><option value='d'${iv==='d'?' selected':''}>كل يوم</option></select></label><label>كلمة مرور النسخة التلقائية (اختيارية: وإن وضعتها فاحفظها خارج الهاتف، فضياعها يعني ضياع النسخة)<input type='password' id='abp' autocomplete='off' value='${qa(S.abp||'')}'></label><button id='abnow'>اكتب نسخة الآن</button>`:'')+`<label>تذكير رفع نسخة إلى درايف كل (أيام)<input id='rdi' inputmode='numeric' value='${remDays()}'></label><div class='msg'>عند حلول الموعد يظهر تنبيه في تبويب اليوم؛ اتصل بالإنترنت ثم اضغط «احفظ نسخة الآن» واختر درايف.</div></div>`};
/* ===== نهاية النسخ التلقائي ===== */'''
s = rep(s, "const extDays=()=>S.ext?Math.floor((Date.now()-S.ext)/864e5):null;", NEW_JS)

# 4) شريط التذكير: الفترة قابلة للتعديل + سؤال «هل رُفعت؟» + نص يذكّر بالإنترنت
s = rep(s, "const extBanner=()=>{const d=extDays();return d===null||d>=7?`<div class='bn'>",
           "const extBanner=()=>{const d=extDays();return pendBanner()+(d===null||d>=remDays()?`<div class='bn'>")
s = rep(s, " — احفظ نسخة الآن (أو من ⚙).<div", " — اتصل بالإنترنت ثم احفظ نسخة الآن واختر درايف.<div")
s = rep(s, "<button id='qbk'>💾 احفظ نسخة الآن</button></div></div>`:''};",
           "<button id='qbk'>💾 احفظ نسخة الآن</button></div></div>`:'')};")
s = rep(s, "style='${d===null||d>=7?'color:var(--bad)':''}'", "style='${d===null||d>=remDays()?'color:var(--bad)':''}'")

# 5) بطاقة الإعدادات الجديدة قبل بطاقة النسخ الاحتياطي
s = rep(s, "${bkUI()}", "${abUI()}${bkUI()}")

# 6) الأزرار: اكتب نسخة الآن / نعم رُفعت / لا
s = rep(s, "else if(id==='qbk')quickBk();else if(id==='bkmake')mkBackup();",
"else if(id==='qbk')quickBk();else if(id==='abnow')autoNow();else if(id==='pyes'){S.ext=Date.now();delete S.pend;save();toast('سُجّلت النسخة الخارجية');render()}else if(id==='pno'){delete S.pend;save();toast('لم تُسجَّل. أعد المحاولة من «احفظ نسخة الآن»');render()}else if(id==='bkmake')mkBackup();")

# 7) حقول الإعدادات الجديدة
s = rep(s, "else if(e.target.id==='rfm'){S.rfm=e.target.value;save();fillRp()}",
"else if(e.target.id==='rfm'){S.rfm=e.target.value;save();fillRp()}else if(e.target.id==='abi'){S.abi=e.target.value==='d'?'d':'w';save();render()}else if(e.target.id==='abp'){const v=e.target.value;if(v&&v.length<4){toast('كلمة المرور 4 أحرف على الأقل، أو اتركها فارغة');return}S.abp=v;save();toast('حُفظ')}else if(e.target.id==='rdi'){const n=Math.floor(+ND(e.target.value.trim()));if(!(n>=1&&n<=90)){toast('أدخل عدداً من 1 إلى 90');render();return}S.rdi=n;save();toast('حُفظ')}")

# 8) بعد ترحيل الحصة: نسخة تلقائية إن حلّ الموعد
s = rep(s, "save();toast('رُحّلت الحصة إلى السجل');render()}", "save();toast('رُحّلت الحصة إلى السجل');render();autoRun()}")

# 9) حاوية أندرويد: المشاركة لا تُسجَّل «تمت» إلا بعد جواب المعلم
s = rep(s, "if(ok){S.ext=Date.now();save();msgBk(k==='copy'?'نُسخ الملف.",
           "if(ok){if(k==='sh')S.pend=Date.now();else S.ext=Date.now();save();if(k==='sh'){const x=$('#abpend');if(x)x.innerHTML=pendBanner()}msgBk(k==='copy'?'نُسخ الملف.")
s = rep(s, ":'فتح خيار المشاركة؛ اختر التطبيق الذي تريد إرسال النسخة إليه.')}}",
           ":'فتح خيار المشاركة؛ اختر درايف أو مكاناً آمناً، ثم أجب عن سؤال «هل رُفعت؟» أعلى هذه البطاقة.')}}")
s = rep(s, "S.ext=Date.now();save();toast('فتح خيار المشاركة؛ اختر مكاناً آمناً خارج الهاتف (Drive أو غيره). لا يُسجَّل الحفظ إلا بعد أن تتأكد أن الملف وصل.')}",
"S.pend=Date.now();save();toast('فتح خيار المشاركة؛ اختر درايف أو مكاناً آمناً، ثم أجب عن سؤال «هل رُفعت؟» أعلى الصفحة.');render()}\n  document.addEventListener('visibilitychange',()=>{if(document.hidden)autoRun()});\n  setTimeout(()=>autoRun(),3000);")

assert s != orig

scripts = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', s, re.S)
assert scripts, 'لم أجد سكربتاً داخلياً'
for i, code in enumerate(scripts):
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
        f.write(code)
    r = subprocess.run(['node', '--check', f.name], capture_output=True, text=True)
    os.unlink(f.name)
    assert r.returncode == 0, 'خطأ صياغة في السكربت %d:\n%s' % (i, r.stderr)

# ===================== MainActivity.java =====================
j = open(JAVA, encoding='utf-8').read()
jo = j
assert 'autoSave' not in j, 'الباتش طُبّق سابقاً على جافا'

j = rep(j, "import android.content.ContentValues;",
           "import android.content.ContentUris;\nimport android.content.ContentValues;")
j = rep(j, "import android.net.Uri;", "import android.database.Cursor;\nimport android.net.Uri;")
j = rep(j, "import java.io.OutputStream;",
           "import java.io.ByteArrayOutputStream;\nimport java.io.InputStream;\nimport java.io.OutputStream;\nimport java.util.ArrayList;\nimport java.util.Arrays;")

JAVA_METHODS = r'''    private static final int KEEP_AUTO = 8;

    private boolean sameBytes(Uri uri, byte[] data) {
        try {
            InputStream in = getContentResolver().openInputStream(uri);
            if (in == null) return false;
            ByteArrayOutputStream bo = new ByteArrayOutputStream();
            byte[] buf = new byte[8192];
            int n;
            while ((n = in.read(buf)) != -1) bo.write(buf, 0, n);
            in.close();
            return Arrays.equals(bo.toByteArray(), data);
        } catch (Exception e) { return false; }
    }

    private void pruneAuto() {
        try {
            ArrayList<Uri> old = new ArrayList<>();
            Cursor c = getContentResolver().query(MediaStore.Downloads.EXTERNAL_CONTENT_URI,
                new String[]{MediaStore.Downloads._ID, MediaStore.Downloads.DISPLAY_NAME},
                MediaStore.Downloads.DISPLAY_NAME + " LIKE ?", new String[]{"halaqa-auto-%"},
                MediaStore.Downloads.DISPLAY_NAME + " DESC");
            if (c == null) return;
            int i = 0;
            while (c.moveToNext()) {
                i++;
                if (i > KEEP_AUTO) old.add(ContentUris.withAppendedId(MediaStore.Downloads.EXTERNAL_CONTENT_URI, c.getLong(0)));
            }
            c.close();
            for (Uri u : old) getContentResolver().delete(u, null, null);
        } catch (Exception e) { }
    }

    // نسخة تلقائية صامتة في مجلد التنزيلات: تُقرأ بعد الكتابة وتُقارن بايتاً ببايت، وتُحذف إن لم تتطابق.
    private String autoSaveNow(String name, String b64) {
        try {
            if (name == null || !name.matches("halaqa-auto-[0-9\\-]+\\.txt")) return "fail:name";
            byte[] data = Base64.decode(b64, Base64.DEFAULT);
            if (Build.VERSION.SDK_INT >= 29) {
                ContentValues v = new ContentValues();
                v.put(MediaStore.Downloads.DISPLAY_NAME, name);
                v.put(MediaStore.Downloads.MIME_TYPE, "text/plain");
                Uri uri = getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, v);
                if (uri == null) return "fail:insert";
                OutputStream os = getContentResolver().openOutputStream(uri);
                if (os == null) return "fail:open";
                os.write(data);
                os.close();
                if (!sameBytes(uri, data)) {
                    try { getContentResolver().delete(uri, null, null); } catch (Exception e2) { }
                    return "fail:verify";
                }
                pruneAuto();
                return "ok:" + data.length;
            }
            if (checkSelfPermission("android.permission.WRITE_EXTERNAL_STORAGE") != 0) {
                pendName = name; pendB64 = b64;
                runOnUiThread(() -> requestPermissions(new String[]{"android.permission.WRITE_EXTERNAL_STORAGE"}, PERM_REQ));
                return "perm";
            }
            File dir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS);
            if (!dir.exists()) dir.mkdirs();
            File f = new File(dir, name);
            FileOutputStream fo = new FileOutputStream(f);
            fo.write(data);
            fo.close();
            if (f.length() != data.length) return "fail:verify";
            return "ok:" + data.length;
        } catch (Exception e) {
            return "fail:" + e.getClass().getSimpleName();
        }
    }

    class Bridge {'''
j = rep(j, "    class Bridge {", JAVA_METHODS)
j = rep(j, "        public void share(String name, String b64) { shareNow(name, b64); }",
"""        public void share(String name, String b64) { shareNow(name, b64); }

        @JavascriptInterface
        public String autoSave(String name, String b64) { return autoSaveNow(name, b64); }""")
assert j != jo
open(JAVA, 'w', encoding='utf-8').write(j)

# ===================== build.gradle =====================
g = open(GRADLE, encoding='utf-8').read()
g = rep(g, 'versionCode 7', 'versionCode 8')
g = rep(g, "versionName '1.4.3'", "versionName '1.5.0'")
open(GRADLE, 'w', encoding='utf-8').write(g)

open(PATH, 'w', encoding='utf-8').write(s)
print('تم التعديل بنجاح وفحص الصياغة سليم')
