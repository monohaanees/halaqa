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
assert 'delDay' in s, 'طبّق دفعة حذف/نقل السجل (2026-11-19.1) أولاً'
assert 'pdfExport' not in s and 'sn15' not in s, 'الباتش طُبّق سابقاً'
assert "const VER='2026-11-19.1';" in s, 'الملف ليس بإصدار 2026-11-19.1 المتوقع'

# 1) الإصدار + نقطة حفظ تلقائية عند أول تشغيل (sn15)
s = rep(s, "const VER='2026-11-19.1';", "const VER='2026-11-19.2';")
s = rep(s, "if(!S.sn14){snap('قبل إصدار 2026-11-19.1');S.sn14=1;save()}",
"if(!S.sn14){snap('قبل إصدار 2026-11-19.1');S.sn14=1;save()}\nif(!S.sn15){snap('قبل إصدار 2026-11-19.2');S.sn15=1;save()}")
s = rep(s, "sn13:1,sn14:1,st:D.st", "sn13:1,sn14:1,sn15:1,st:D.st")

# 2) محرك التصدير: قالب واحد ثابت، والجدول يتمدد مع المحتوى
NEW_JS = r'''/* ===== نهاية حذف/نقل السجل ===== */
/* ===== تصدير PDF بقالب موحّد (2026-11-19) ===== */
const pdfCss=`@page{size:A4;@bottom-center{content:"صفحة " counter(page) " من " counter(pages);font-size:10px;color:#666}}*{box-sizing:border-box}html,body{margin:0;padding:0}body{font-family:'Noto Naskh Arabic','Noto Sans Arabic','Droid Arabic Naskh',Tahoma,Arial,sans-serif;color:#111;font-size:12.5px;line-height:1.55;direction:rtl}.h{text-align:center;margin-bottom:10px}.h .b{font-size:13px;color:#444}.h .i{font-size:18px;font-weight:700;margin:2px 0}.h .t{font-size:15px;font-weight:700;margin-top:4px}.h .s{font-size:12px;color:#444}table{width:100%;border-collapse:collapse;margin-top:8px}thead{display:table-header-group}tr{break-inside:avoid;page-break-inside:avoid}th{background:#e9eef2;border:1px solid #9aa5ad;padding:5px 6px;font-size:12px}td{border:1px solid #b9c1c7;padding:4px 6px;vertical-align:top}td.c,th.c{text-align:center}.n{font-weight:700}.w{border:1px solid #c9a227;background:#fff7d6;padding:5px 8px;margin:6px 0;font-size:12px}`;
const pdfHtml=(ttl,head,body)=>`<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>${esc(ttl)}</title><style>${pdfCss}</style></head><body><div class="h"><div class="b">بسم الله الرحمن الرحيم</div><div class="i">${esc(SET.hdr||'')}</div>${head}</div>${body}</body></html>`;
const pdfD=s=>String(s).replace(/(\d{4})-(\d{2})-(\d{2})/g,'\u200e$3-$2-$1\u200e');
const pdfN=(n,one,two,pl,sg)=>n===1?one:n===2?two:n+' '+(n<=10?pl:sg);
function pdfDay(date){
 const ls=text(date).split('\n'),re=/^(\d+)\. (.+) — (حاضر|غائب بعذر|غائب|حصة خاصة)$/,B=[],meta=[];let cur=null;
 ls.forEach(l=>{const m=re.exec(l);if(m){cur={i:m[1],n:m[2],a:m[3],d:[],p:''};B.push(cur);return}
  if(!cur){meta.push(l);return}
  const b=l.replace(/^\s*•\s*/,'').trim();if(!b)return;
  if(/^النقاط: /.test(b))cur.p=b.replace(/^النقاط: /,'');else cur.d.push(b)});
 if(!B.length)return{};
 const ttl='سجل-'+date,title=meta[2]||'سجل المتابعة اليومي — '+date,extra=meta.slice(3).filter(Boolean),
  warn=extra.filter(x=>x.charAt(0)==='⚠'),info=extra.filter(x=>x.charAt(0)!=='⚠'),
  head=`<div class="t">${pdfD(esc(title))}</div>`+info.map(x=>`<div class="s">${esc(x)}</div>`).join('')+warn.map(x=>`<div class="w">${esc(x)}</div>`).join(''),
  body=`<table><thead><tr><th class="c">#</th><th>اسم الطالب</th><th class="c">الحضور</th><th>التفاصيل والمتابعة اليومية</th><th class="c">النقاط</th></tr></thead><tbody>`+B.map(o=>`<tr><td class="c">${o.i}</td><td class="n">${esc(o.n)}</td><td class="c">${esc(o.a)}</td><td>${o.d.length?o.d.map(x=>`<div>${esc(x)}</div>`).join(''):'—'}</td><td class="c">\u200e${esc(o.p||'0')}\u200e</td></tr>`).join('')+`</tbody></table>`;
 return{ttl,head,body}}
function pdfSta(){const{k,f,t,A,days}=pdata();if(!A.length)return{};
 const ttl='إحصائية-'+(k==='w'?'أسبوعية':'شهرية')+'-'+f+'-'+t,
  head=`<div class="t">${k==='w'?'الإحصائية الأسبوعية':'الإحصائية الشهرية'} — من ${pdfD(f)} إلى ${pdfD(t)} (${pdfN(days,'حصة واحدة','حصتان','حصص','حصة')})</div><div class="s">عدد الطلاب: ${pdfN(A.length,'طالب واحد','طالبان','طلاب','طالبًا')} · عدد الحصص: ${pdfN(days,'حصة واحدة','حصتان','حصص','حصة')}</div>`,
  H=['الترتيب','اسم الطالب','النقاط','الصفحات','الإعادات','الحضور','غياب','بعذر','الاختبارات','ملاحظات إيجابية'].concat(S.pneg?['ملاحظات سلبية']:[]),
  body=`<table><thead><tr>${H.map((h,i)=>`<th class="${i===1?'':'c'}">${h}</th>`).join('')}</tr></thead><tbody>`+A.map(o=>{const c=[o.rk,esc(o.n),o.pt,o.pg,o.rp,(o.ses-o.ab-o.ex)+' من '+o.ses,o.ab,o.ex,'نجح '+o.ok+' · رسب '+o.no,o.np].concat(S.pneg?[o.nn]:[]);return`<tr>${c.map((x,i)=>`<td class="${i===1?'n':'c'}">${i===2?'\u200e'+x+'\u200e':x}</td>`).join('')}</tr>`}).join('')+`</tbody></table>`;
 return{ttl,head,body}}
function pdfExport(kind){
 try{
  const r=kind==='day'?pdfDay(rpRange()[0]):pdfSta();
  if(!r.body){toast('لا بيانات للتصدير');return}
  const html=pdfHtml(r.ttl,r.head,r.body);
  if(window.AndroidBridge&&typeof AndroidBridge.printHtml==='function'){AndroidBridge.printHtml(r.ttl,html);return}
  const fr=document.createElement('iframe');fr.style.cssText='position:fixed;right:0;bottom:0;width:0;height:0;border:0';document.body.appendChild(fr);
  fr.onload=()=>{try{fr.contentWindow.focus();fr.contentWindow.print()}catch(e){toast('تعذّرت الطباعة')}setTimeout(()=>fr.remove(),60000)};
  fr.srcdoc=html
 }catch(e){toast('تعذّر التصدير')}}
/* ===== نهاية تصدير PDF ===== */'''
s = rep(s, "/* ===== نهاية حذف/نقل السجل ===== */", NEW_JS)

# 3) الأزرار: صفحة الإحصائية، وصفحة التقارير (سجل يوم واحد لكل الطلاب)
s = rep(s, "<button class='pri' id='pcp' style='width:100%'>نسخ الترتيب للواتساب</button>",
           "<button class='pri' id='pcp' style='width:100%'>نسخ الترتيب للواتساب</button><button id='pcpdf' style='width:100%'>📄 تصدير PDF</button>")
s = rep(s, "<button class='pri' id='rcp'>نسخ</button>",
           "<button class='pri' id='rcp'>نسخ</button>${!st&&f===t?`<button id='rpdf'>📄 تصدير PDF</button>`:''}")
s = rep(s, "else if(id==='pcp')copyStr(ptext());",
           "else if(id==='pcp')copyStr(ptext());else if(id==='pcpdf')pdfExport('sta');else if(id==='rpdf')pdfExport('day');")

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
assert 'printHtml' not in j, 'الباتش طُبّق سابقاً على جافا'
assert 'autoSaveNow' in j, 'طبّق دفعة النسخ التلقائي أولاً'

j = rep(j, "import android.content.ContentUris;", "import android.content.ContentUris;\nimport android.content.Context;")
j = rep(j, "import android.os.Environment;",
           "import android.os.Environment;\nimport android.print.PrintAttributes;\nimport android.print.PrintDocumentAdapter;\nimport android.print.PrintManager;")

JAVA_METHODS = r'''    private WebView printWv;

    // تصدير PDF: تُحمَّل الصفحة في WebView مخفي ثم تُفتح نافذة الطباعة الأصلية (حفظ بصيغة PDF أو مشاركة).
    private void printNow(final String title, String html) {
        try {
            final WebView w = new WebView(this);
            printWv = w;
            final boolean[] done = {false};
            w.setWebViewClient(new WebViewClient() {
                @Override
                public void onPageFinished(WebView v, String url) {
                    if (done[0]) return;
                    done[0] = true;
                    try {
                        PrintManager pm = (PrintManager) getSystemService(Context.PRINT_SERVICE);
                        PrintDocumentAdapter ad = v.createPrintDocumentAdapter(title);
                        PrintAttributes attrs = new PrintAttributes.Builder()
                            .setMediaSize(PrintAttributes.MediaSize.ISO_A4)
                            .setMinMargins(new PrintAttributes.Margins(600, 600, 600, 600))
                            .build();
                        pm.print(title, ad, attrs);
                    } catch (Exception e) { toast("تعذّر فتح نافذة الطباعة"); }
                }
            });
            w.loadDataWithBaseURL(null, html, "text/html", "UTF-8", null);
        } catch (Exception e) { toast("تعذّر التصدير"); }
    }

    private static final int KEEP_AUTO = 8;'''
j = rep(j, "    private static final int KEEP_AUTO = 8;", JAVA_METHODS)
j = rep(j, "        public String autoSave(String name, String b64) { return autoSaveNow(name, b64); }",
"""        public String autoSave(String name, String b64) { return autoSaveNow(name, b64); }

        @JavascriptInterface
        public void printHtml(final String title, final String html) {
            runOnUiThread(() -> printNow(title, html));
        }""")
assert j != jo
open(JAVA, 'w', encoding='utf-8').write(j)

# ===================== build.gradle =====================
g = open(GRADLE, encoding='utf-8').read()
g = rep(g, 'versionCode 9', 'versionCode 10')
g = rep(g, "versionName '1.5.1'", "versionName '1.6.0'")
open(GRADLE, 'w', encoding='utf-8').write(g)

open(PATH, 'w', encoding='utf-8').write(s)
print('تم التعديل بنجاح وفحص الصياغة سليم')
