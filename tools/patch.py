import re, subprocess, tempfile, os

PATH = 'android/app/src/main/assets/index.html'
GRADLE = 'android/app/build.gradle'

def rep(s, old, new):
    n = s.count(old)
    assert n == 1, 'المرساة وُجدت %d مرة (المطلوب مرة واحدة): %s' % (n, old[:60])
    return s.replace(old, new)

s = open(PATH, encoding='utf-8').read()
orig = s
assert 'pdfExport' in s, 'طبّق دفعة تصدير PDF (2026-11-19.2) أولاً'
assert 'pdfRank' not in s and 'sn16' not in s, 'الباتش طُبّق سابقاً'
assert "const VER='2026-11-19.2';" in s, 'الملف ليس بإصدار 2026-11-19.2 المتوقع'

# 1) الإصدار + نقطة حفظ تلقائية عند أول تشغيل (sn16)
s = rep(s, "const VER='2026-11-19.2';", "const VER='2026-11-19.3';")
s = rep(s, "if(!S.sn15){snap('قبل إصدار 2026-11-19.2');S.sn15=1;save()}",
"if(!S.sn15){snap('قبل إصدار 2026-11-19.2');S.sn15=1;save()}\nif(!S.sn16){snap('قبل إصدار 2026-11-19.3');S.sn16=1;save()}")
s = rep(s, "sn14:1,sn15:1,st:D.st", "sn14:1,sn15:1,sn16:1,st:D.st")

# 2) استبدال كتلة تصدير PDF كاملة بالتصميم الجديد
NEW_BLOCK = r'''/* ===== تصدير PDF بقالب موحّد (2026-11-19) ===== */
const pdfCss=ft=>`@page{size:A4;margin:12mm 10mm 16mm 10mm;@bottom-left{content:"صفحة " counter(page) " من " counter(pages);font-size:10px;color:#667}@bottom-right{content:"${ft}";font-size:10px;color:#667}}*{box-sizing:border-box;-webkit-print-color-adjust:exact;print-color-adjust:exact}html,body{margin:0;padding:0}body{font-family:'Noto Naskh Arabic','Noto Sans Arabic','Droid Arabic Naskh',Tahoma,Arial,sans-serif;color:#1b2a2f;font-size:12.5px;line-height:1.5;direction:rtl}.hd{border:2px solid #0d7a63;border-radius:12px;background:#eef9f5;text-align:center;padding:8px 10px 9px;margin-bottom:8px}.hd .b{font-size:11px;color:#4a6a62}.hd .i{font-size:20px;font-weight:700;color:#0a6b56;margin:1px 0}.hd .t{font-size:13.5px;font-weight:700;color:#14493d;margin-top:2px}.hd .s{font-size:12px;color:#33564d;margin-top:2px}.pl{margin-top:6px}.pl span{display:inline-block;white-space:nowrap;border:1px solid #7cc4b0;background:#fff;color:#0a6b56;border-radius:999px;padding:1px 12px;margin:0 3px;font-size:11.5px;font-weight:700}table{width:100%;border-collapse:collapse}thead{display:table-header-group}tr{break-inside:avoid;page-break-inside:avoid}th{background:#0d6b57;color:#fff;border:1px solid #0d6b57;padding:6px 5px;font-size:12px;font-weight:700}td{border:1px solid #cfd8dc;padding:4px 6px;vertical-align:middle}tbody tr:nth-child(even){background:#f4f7f9}td.c,th.c{text-align:center}.n{font-weight:700}.z{color:#a7b0b5;font-weight:400}.ok{color:#14803c;font-weight:700}.no{color:#c0262d;font-weight:700}.ng{color:#c0262d}.bd{display:inline-block;min-width:20px;height:20px;line-height:20px;border-radius:50%;background:#0d7a63;color:#fff;font-weight:700;font-size:11px;text-align:center}tr.g1 .bd{background:#d4a017}tr.g2 .bd{background:#6c7a89}tr.g3 .bd{background:#c8581a}tr.g1{background:#fff3b8!important}tr.g2{background:#e6ebf0!important}tr.g3{background:#fde3cf!important}tr.ab{background:#fdeeee!important}tr.ex{background:#fff6e3!important}.w{border:1px solid #c9a227;background:#fff7d6;padding:5px 8px;margin:6px 0;font-size:12px;border-radius:6px}.st{font-weight:700}.st.p{color:#14803c}.st.a{color:#c0262d}.st.e{color:#b26a00}.st.s{color:#1b5aa0}.d .pos{color:#14803c}.d .okl{color:#14803c;font-weight:700}.d .nol{color:#c0262d;font-weight:700}.dash{color:#a7b0b5}`;
const cssStr=s=>String(s||'').replace(/["\\\n\r]/g,' ');
const pdfHtml=(ttl,head,body,foot)=>`<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>${esc(ttl)}</title><style>${pdfCss(cssStr(foot))}</style></head><body><div class="hd"><div class="b">بسم الله الرحمن الرحيم</div><div class="i">${esc(SET.hdr||'')}</div>${head}</div>${body}</body></html>`;
const pdfD=s=>String(s).replace(/(\d{4})-(\d{2})-(\d{2})/g,'\u200e$3-$2-$1\u200e');
const pdfN=(n,one,two,pl,sg)=>n===1?one:n===2?two:n+' '+(n<=10?pl:sg);
const pdfRank=A=>{const B=[...A].sort((a,b)=>b.pt-a.pt||b.pg-a.pg||a.n.localeCompare(b.n,'ar')),pts=[...new Set(B.map(o=>o.pt))];B.forEach(o=>{o.prk=1+pts.indexOf(o.pt)});return B};
function pdfDay(date){
 const ls=text(date).split('\n'),re=/^(\d+)\. (.+) — (حاضر|غائب بعذر|غائب|حصة خاصة)$/,B=[],meta=[];let cur=null;
 ls.forEach(l=>{const m=re.exec(l);if(m){cur={i:m[1],n:m[2],a:m[3],d:[],p:''};B.push(cur);return}
  if(!cur){meta.push(l);return}
  const b=l.replace(/^\s*•\s*/,'').trim();if(!b)return;
  if(/^النقاط: /.test(b))cur.p=b.replace(/^النقاط: /,'');else cur.d.push(b)});
 if(!B.length)return{};
 const cls=a=>a==='حاضر'?'p':a==='غائب'?'a':a==='غائب بعذر'?'e':'s',rowc=a=>a==='غائب'?' class="ab"':a==='غائب بعذر'?' class="ex"':'',
  dl=x=>{const c=/\(نجح/.test(x)?'okl':/\(رسب/.test(x)?'nol':/^ملاحظة إيجابية/.test(x)?'pos':'';return`<div${c?' class="'+c+'"':''}>${esc(x)}</div>`},
  cn={p:0,a:0,e:0,s:0};B.forEach(o=>cn[cls(o.a)]++);
 const ttl='سجل-'+date,title=meta[2]||'سجل المتابعة اليومي — '+date,extra=meta.slice(3).filter(Boolean),
  warn=extra.filter(x=>x.charAt(0)==='⚠'),info=extra.filter(x=>x.charAt(0)!=='⚠'),
  pills=`<div class="pl"><span>عدد الطلاب: ${B.length}</span><span>حاضر: ${cn.p}</span><span>غائب: ${cn.a}</span><span>بعذر: ${cn.e}</span>${cn.s?`<span>حصة خاصة: ${cn.s}</span>`:''}</div>`,
  head=`<div class="t">${pdfD(esc(title))}</div>`+info.map(x=>`<div class="s">${esc(x)}</div>`).join('')+warn.map(x=>`<div class="w">${esc(x)}</div>`).join('')+pills,
  body=`<table><thead><tr><th class="c" style="width:28px">#</th><th style="width:22%">اسم الطالب</th><th class="c" style="width:11%">الحضور</th><th>التفاصيل والمتابعة اليومية</th><th class="c" style="width:48px">النقاط</th></tr></thead><tbody>`+B.map(o=>`<tr${rowc(o.a)}><td class="c">${o.i}</td><td class="n">${esc(o.n)}</td><td class="c"><span class="st ${cls(o.a)}">${esc(o.a)}</span></td><td class="d">${o.d.length?o.d.map(dl).join(''):'<span class="dash">—</span>'}</td><td class="c"><b class="${(+o.p)<0?'ng':''}">\u200e${esc(o.p||'0')}\u200e</b></td></tr>`).join('')+`</tbody></table>`;
 return{ttl,head,body,foot:(SET.hdr||'')+' ('+pdfD(date)+')'}}
function pdfSta(){const{k,f,t,A:A0,days}=pdata();if(!A0.length)return{};const A=pdfRank(A0),
 ttl='إحصائية-'+(k==='w'?'أسبوعية':'شهرية')+'-'+f+'-'+t,hs=pdfN(days,'حصة واحدة','حصتان','حصص','حصة'),
 head=`<div class="t">${k==='w'?'الإحصائية الأسبوعية':'الإحصائية الشهرية'} — من ${pdfD(f)} إلى ${pdfD(t)} (${hs})</div><div class="pl"><span>عدد الطلاب: ${pdfN(A.length,'طالب واحد','طالبان','طلاب','طالبًا')}</span><span>عدد الحصص: ${hs}</span></div>`,
 H=['الترتيب','اسم الطالب','النقاط','الصفحات','الإعادات','الحضور','غياب','بعذر','الاختبارات','ملاحظات إيجابية'].concat(S.pneg?['ملاحظات سلبية']:[]),
 zz=v=>v?v:`<span class="z">0</span>`,
 row=o=>{const g=o.prk<=3?' class="g'+o.prk+'"':'',at=(o.ses-o.ab-o.ex)+' من '+o.ses,
  c=[`<span class="bd">${o.prk}</span>`,`<span class="n">${esc(o.n)}</span>`,`<b class="${o.pt<0?'ng':''}">\u200e${o.pt}\u200e</b>`,zz(o.pg),zz(o.rp),(!o.ab&&!o.ex)?`<b>${at}</b>`:at,zz(o.ab),zz(o.ex),`<span class="${o.ok?'ok':'z'}">نجح ${o.ok}</span> · <span class="${o.no?'no':'z'}">رسب ${o.no}</span>`,zz(o.np)].concat(S.pneg?[o.nn?`<span class="no">${o.nn}</span>`:zz(0)]:[]);
  return`<tr${g}>${c.map((x,i)=>`<td class="${i===1?'':'c'}">${x}</td>`).join('')}</tr>`},
 body=`<table><thead><tr>${H.map((h,i)=>`<th class="${i===1?'':'c'}">${h}</th>`).join('')}</tr></thead><tbody>${A.map(row).join('')}</tbody></table>`;
 return{ttl,head,body,foot:(SET.hdr||'')+' (من '+pdfD(f)+' إلى '+pdfD(t)+')'}}
function pdfExport(kind){
 try{
  const r=kind==='day'?pdfDay(rpRange()[0]):pdfSta();
  if(!r.body){toast('لا بيانات للتصدير');return}
  const html=pdfHtml(r.ttl,r.head,r.body,r.foot);
  if(window.AndroidBridge&&typeof AndroidBridge.printHtml==='function'){AndroidBridge.printHtml(r.ttl,html);return}
  const fr=document.createElement('iframe');fr.style.cssText='position:fixed;right:0;bottom:0;width:0;height:0;border:0';document.body.appendChild(fr);
  fr.onload=()=>{try{fr.contentWindow.focus();fr.contentWindow.print()}catch(e){toast('تعذّرت الطباعة')}setTimeout(()=>fr.remove(),60000)};
  fr.srcdoc=html
 }catch(e){toast('تعذّر التصدير')}}
/* ===== نهاية تصدير PDF ===== */'''
A = '/* ===== تصدير PDF بقالب موحّد (2026-11-19) ===== */'
B = '/* ===== نهاية تصدير PDF ===== */'
assert s.count(A) == 1 and s.count(B) == 1, 'علامتا كتلة PDF غير موجودتين مرة واحدة'
i, j = s.index(A), s.index(B) + len(B)
assert i < j
s = s[:i] + NEW_BLOCK + s[j:]

assert s != orig
scripts = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', s, re.S)
assert scripts, 'لم أجد سكربتاً داخلياً'
for k, code in enumerate(scripts):
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
        f.write(code)
    r = subprocess.run(['node', '--check', f.name], capture_output=True, text=True)
    os.unlink(f.name)
    assert r.returncode == 0, 'خطأ صياغة في السكربت %d:\n%s' % (k, r.stderr)

g = open(GRADLE, encoding='utf-8').read()
g = rep(g, 'versionCode 10', 'versionCode 11')
g = rep(g, "versionName '1.6.0'", "versionName '1.6.1'")
open(GRADLE, 'w', encoding='utf-8').write(g)

open(PATH, 'w', encoding='utf-8').write(s)
print('تم التعديل بنجاح وفحص الصياغة سليم')
