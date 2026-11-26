import re, subprocess, tempfile, os

PATH = 'android/app/src/main/assets/index.html'
GRADLE = 'android/app/build.gradle'

def rep(s, old, new):
    n = s.count(old)
    assert n == 1, 'المرساة وُجدت %d مرة (المطلوب مرة واحدة): %s' % (n, old[:60])
    return s.replace(old, new)

s = open(PATH, encoding='utf-8').read()
orig = s
assert 'pdfStu' in s, 'طبّق دفعة سجل الطالب (2026-11-24.1) أولاً'
assert 'nextStage' not in s and 'sn18' not in s, 'الباتش طُبّق سابقاً'
assert "const VER='2026-11-24.1';" in s, 'الملف ليس بإصدار 2026-11-24.1 المتوقع'

# ---------- 1) الإصدار + نقطة حفظ (sn18) ----------
s = rep(s, "const VER='2026-11-24.1';", "const VER='2026-11-26.1';")
s = rep(s, "if(!S.sn17){snap('قبل إصدار 2026-11-24.1');S.sn17=1;save()}",
"if(!S.sn17){snap('قبل إصدار 2026-11-24.1');S.sn17=1;save()}\nif(!S.sn18){snap('قبل إصدار 2026-11-26.1');S.sn18=1;save()}")
s = rep(s, "sn16:1,sn17:1,st:D.st", "sn16:1,sn17:1,sn18:1,st:D.st")

# ---------- 2) عنوان التطبيق: سطر واحد على كل الشاشات ----------
s = rep(s, ".hd b{font-size:19px;flex:1}", ".hd b{font-size:19px;flex:1;white-space:nowrap}")
s = rep(s, ".hd input{width:auto}", ".hd input{width:auto;min-width:0;flex:0 1 150px}@media(max-width:400px){.hd b{font-size:17px}.badge{font-size:11px;padding:2px 8px}}")

# ---------- 3) CSS مربعات الاختبارات داخل التطبيق ----------
APP_CSS = (".xqt{margin:8px 0 4px;font-weight:700}.xqt small{color:var(--mu);font-weight:400;margin-inline-start:6px}"
 ".xqg{display:flex;flex-wrap:wrap;gap:6px}.xqb{display:inline-flex;flex-wrap:wrap;align-items:center;justify-content:center;gap:3px;border:1px solid var(--mu);border-radius:8px;padding:3px 5px;max-width:78px}"
 ".xqb i{font-style:normal;font-size:11px;color:var(--mu);width:100%;text-align:center;line-height:1.2}"
 ".xq{width:18px;height:18px;min-width:0;min-height:0;padding:0;line-height:0;font-size:0;border-radius:4px;border:1px solid var(--mu);background:transparent}"
 ".xq.d{background:#2e9d5b;border-color:#2e9d5b}.xq.bs{background:#2e9d5b55;border-color:#2e9d5b}.xq.nx{outline:2px solid #f59e42;outline-offset:1px}.xql{font-size:12px;color:var(--mu);margin:6px 0}\n")
s = rep(s, "</style>\n</head>", APP_CSS + "</style>\n</head>")

# ---------- 4) منطق «الاختبار القادم» ----------
s = rep(s, "function nextEx(st,c){const ts=TR.filter(t=>CC[t]===c),t=ts.find(t=>lastRank(st,t)<CAT[t].length)||ts[ts.length-1],e=CAT[t][lastRank(st,t)];return e?{t,e,trig:IX[c][e[7]]||0}:null}",
"function nextEx(st,c){const ts=TR.filter(t=>CC[t]===c),t=ts.find(t=>lastRank(st,t)<CAT[t].length)||ts[ts.length-1],ns=nextStage(st,t),e=ns?CAT[t][ns-1]:null,cf=exCfg(st.n,t);return e?{t,e,trig:IX[c][e[7]]||0,man:!!(cf.s||cf.d===-1)}:null}")
s = rep(s, "A.push([st.n,(p>nx.trig?'تجاوز حدّ ':'مستحق: ')+nx.e[8]])",
           "A.push([st.n,(p>nx.trig?'تجاوز حدّ ':'مستحق: ')+nx.e[8]+(nx.man?' (يدوي)':'')])")
s = rep(s, "const t=$('#xt').value,lr=lastRank(st,t),f=S.ex.filter(x=>x[1]===st.n&&x[2]===t&&x[3]===lr+1&&x[4]==='رسب'&&x[0]>rd(st.n,t)).length;",
           "const t=$('#xt').value,lr=lastRank(st,t),nsx=nextStage(st,t)||lr+1,f=S.ex.filter(x=>x[1]===st.n&&x[2]===t&&x[3]===nsx&&x[4]==='رسب'&&x[0]>rd(st.n,t)).length;")
s = rep(s, "${i===lr?' selected':''}", "${i===nsx-1?' selected':''}")
s = rep(s, "+(f?' · رسب '+f+' مرة في القادم'+(f>=3?' <span class=\"err\">⚠ يلزم إعادة الجزء</span>':''):'')}",
           "+(f?' · رسب '+f+' مرة في القادم'+(f>=3?' <span class=\"err\">⚠ يلزم إعادة الجزء</span>':''):'');{const g=$('#xgrid');if(g)g.innerHTML=exGridHtml(st,t)+'<div class=\"xql\">انقر مربعاً: اجعله الاختبار القادم، أو اختره في النموذج.</div>'}}")

# ---------- 5) أماكن العرض: تبويب الاختبارات + بطاقة الطالب + النقر ----------
s = rep(s, '<div id="xh" class="msg"></div>', '<div id="xh" class="msg"></div><div id="xgrid"></div>')
s = rep(s, "+tbl(['المسار','الحالة','التقدم','منجز','آخر منجز','آخر نجاح','القادم'],ex)+",
           "+exCard(st)+'<details><summary class=\"msg\">جدول المسارات التفصيلي</summary>'+tbl(['المسار','الحالة','التقدم','منجز','آخر منجز','آخر نجاح','القادم'],ex)+'</details>'+")
s = rep(s, "else if(b.dataset.undo)undo();", "else if(b.dataset.undo)undo();else if(b.dataset.xq)exSheet(b.dataset.xq);")

# ---------- 6) كتلة المربعات والاختبار القادم ----------
EX_BLOCK = r'''/* ===== مربعات الاختبارات والاختبار القادم (2026-11-26) ===== */
const exCfg=(n,t)=>(((S.set||{}).nx)||{})[n+'|'+t]||{};
function exInfo(st,t){const rs=rsAd(st.n,t),dR=rs?rs[0]:'';let m=(st.r||{})[t]||0;const done=new Map(),base=new Set();
 S.ex.forEach(x=>{if(x[1]===st.n&&x[2]===t&&(x[4]==='نجح'||x[4]==='إعفاء')){if(x[0]>dR){const o=done.get(x[3]);if(o===undefined||x[0]>o)done.set(x[3],x[0])}else if(x[3]>m)m=x[3]}});
 if(rs)m=rs[2]==='مرحلة'?+rs[5]:Math.min(m,rsRank(t,+rs[5],+rs[4]||0));
 for(let i=1;i<=m;i++){base.add(i);if(!done.has(i))done.set(i,'')}
 return{done,base,m}}
function nextStage(st,t){const N=CAT[t].length,lr=lastRank(st,t),c=exCfg(st.n,t),I=exInfo(st,t);
 if(c.s>=1&&c.s<=N&&!I.done.has(c.s))return c.s;
 if(c.s||c.d===-1){const d=c.d===-1?-1:1;let a=c.s,ld='';
  if(!a)S.ex.forEach(x=>{if(x[1]===st.n&&x[2]===t&&(x[4]==='نجح'||x[4]==='إعفاء')&&x[0]>=ld){ld=x[0];a=x[3]}});
  if(a)for(let k=a+d;k>=1&&k<=N;k+=d)if(!I.done.has(k))return k}
 return lr<N?lr+1:0}
function exGridHtml(st,only,pdf,f,t2){const P=pdf?'pq':'xq',tr=TR.filter(t=>only?t===only:(lv(st).includes(CC[t])||exInfo(st,t).done.size>0));
 if(!tr.length)return'';
 return tr.map(t=>{const I=exInfo(st,t),cat=CAT[t],nx=nextStage(st,t),seen=new Set(),parts=[],
  sq=e=>{const s=e[4],d=I.done.get(s),cl=P+(d===undefined?'':pdf?(d&&d>=f&&d<=t2?' dn':' d'):(d===''?' bs':' d'))+(s===nx?' nx':'');
   return pdf?`<span class="${cl}"></span>`:`<button class="${cl}" data-xq="${qa(st.n)}|${t}|${s}" title="${esc(e[8])}"></button>`};
  cat.forEach(e=>{if(e[1]==='حزب'||e[1]==='جزء'){const p=e[2];if(seen.has(p))return;seen.add(p);
    const h1=cat.find(x=>x[1]==='حزب'&&x[2]===p&&x[3]===1),h2=cat.find(x=>x[1]==='حزب'&&x[2]===p&&x[3]===2),w=cat.find(x=>x[1]==='جزء'&&x[2]===p);
    parts.push(`<span class="${P}b"><i>${p}</i>${[h1,h2,w].map(x=>x?sq(x):'').join('')}</span>`)}
   else parts.push(`<span class="${P}b ${P}c"><i>${esc(e[8].replace(/^مرحلة /,''))}</i>${sq(e)}</span>`)});
  return`<div class="${P}t"><b>${esc(t)}</b><small>منجز ${I.done.size} من ${cat.length}</small></div><div class="${P}g">${parts.join('')}</div>`}).join('')}
const exCard=st=>{const g=exGridHtml(st);return g?`<div class='card'><b>مسار الاختبارات</b>${g}<div class='xql'>أخضر = منجز · أخضر خافت = محسوب من نقطة البداية · إطار برتقالي = الاختبار القادم · انقر مربعاً لخياراته</div></div>`:''};
function exSheet(spec){const p=spec.split('|'),s=+p.pop(),t=p.pop(),n=p.join('|'),st=byName(n),e=(CAT[t]||[])[s-1];if(!st||!e)return;
 const I=exInfo(st,t),c=exCfg(n,t),d=I.done.get(s),nx=nextStage(st,t),dir=c.d===-1?-1:1,
  state=d===undefined?'لم يُنجز':(d?'أُنجز بتاريخ '+d:'محسوب منجزاً (نقطة البداية أو تصحيح)'),
  el=document.createElement('div');el.className='md';
 el.innerHTML=`<div class="card"><b>${esc(n)}</b><div class="msg">${esc(t)} · ${esc(e[8])}</div><div class="msg">${esc(state)}${s===nx?' · هو القادم الآن'+(c.s?' (محدد يدوياً)':''):''}</div><button class="pri" id="xsn">اجعله اختباره القادم</button>${c.s?'<button id="xsc">إلغاء التحديد اليدوي</button>':''}<label>اتجاه الاختبارات بعد كل نجاح<select id="xsd"><option value="1"${dir===1?' selected':''}>تصاعدي (حسب الكتالوج)</option><option value="-1"${dir===-1?' selected':''}>تنازلي (عكس الكتالوج)</option></select></label>${$('#xe')?'<button id="xsf">اختره في نموذج التسجيل</button>':''}<button id="xcl">إغلاق</button></div>`;
 document.body.appendChild(el);
 const setCfg=f=>{S.set=S.set||{};S.set.nx=S.set.nx||{};const k=n+'|'+t,o=S.set.nx[k]||(S.set.nx[k]={});f(o);if(!o.s&&o.d!==-1)delete S.set.nx[k];S.xs=n;save();el.remove();render()};
 el.onclick=ev=>{const b=ev.target.closest('button');if(ev.target===el||(b&&b.id==='xcl')){el.remove();return}if(!b)return;
  if(b.id==='xsn'){setCfg(o=>{o.s=s});toast('صار هو الاختبار القادم')}
  else if(b.id==='xsc'){setCfg(o=>{delete o.s});toast('أُلغي التحديد اليدوي')}
  else if(b.id==='xsf'){$('#xs').value=n;$('#xt').value=t;fillEx();$('#xe').value=String(s);el.remove()}};
 el.onchange=ev=>{if(ev.target.id==='xsd'){const v=+ev.target.value;setCfg(o=>{if(v===-1)o.d=-1;else delete o.d});toast('حُفظ الاتجاه')}}}
/* ===== نهاية مربعات الاختبارات ===== */'''

# ---------- 7) PDF: مربعات الاختبارات بدل شريط المسار + صفحة الاختبارات المنجزة ----------
s = rep(s, ".tl.w6{width:15.3%;margin:3px .6%}",
 ".tl.w6{width:15.3%;margin:3px .6%}.pqt{margin:8px 0 3px;font-weight:700;color:#0a6b56}.pqt small{color:#667;font-weight:400;margin-inline-start:6px}.pqg{line-height:0}"
 ".pqb{display:inline-block;vertical-align:top;border:1px solid #cfd8dc;border-radius:6px;padding:2px 3px;margin:2px;text-align:center;width:56px;line-height:1.2}"
 ".pqb i{display:block;font-style:normal;font-size:9px;color:#667}.pqc{width:84px}.pq{display:inline-block;width:11px;height:11px;margin:1px;border:1px solid #9aa5ad;border-radius:2px;vertical-align:middle}"
 ".pq.d{background:#8fd1a8;border-color:#2e9d5b}.pq.dn{background:#14803c;border-color:#14803c}.pq.nx{outline:2px solid #e0a100}")
i = s.index("if(trk.length)body+=")
j = s.index("</tbody></table>`;", i) + len("</tbody></table>`;")
s = s[:i] + "body+=pdfSquares(st,f,t);" + s[j:]
# pdfAdm الجديد (مربعات علوية فقط) + صفحة الاختبارات المنجزة
a = s.index("const pdfAdm=")
b = s.index("function pdfSta(){")
NEW_ADM = r'''const pdfAdm=(A,f,t)=>{const T=A.reduce((a,o)=>({s:a.s+o.ses,b:a.b+o.ab,e:a.e+o.ex,g:a.g+o.pg,k:a.k+o.ok,n:a.n+o.no}),{s:0,b:0,e:0,g:0,k:0,n:0}),
  pc=T.s?Math.round((T.s-T.b-T.e)/T.s*100):null;
 return`<div class="adm">${pdfTile(pc==null?'—':pc+'%','نسبة حضور الحلقة','',1)}${pdfTile(T.b+' · '+T.e,'غياب · بعذر','',1)}${pdfTile(T.g,'مجموع الصفحات','',1)}${pdfTile(T.k+' ✓ · '+T.n+' ✗','الاختبارات','',1)}</div>`};
const pdfExamsPage=(A,f,t)=>{const nm=new Map(A.map(o=>[o.n,o.prk])),
  R=S.ex.filter(x=>x[0]>=f&&x[0]<=t&&(x[4]==='نجح'||x[4]==='إعفاء')&&nm.has(x[1])).sort((a,b)=>nm.get(a[1])-nm.get(b[1])||a[1].localeCompare(b[1],'ar')||(a[0]<b[0]?-1:a[0]>b[0]?1:0)),
  rows=R.map((x,i)=>{const e=(CAT[x[2]]||[])[x[3]-1];return`<tr><td class="c">${i+1}</td><td class="n">${esc(x[1])}</td><td>${esc(x[2])}</td><td>${esc(e?e[8]:'')}</td><td class="c"><span class="${x[4]==='نجح'?'ok':'st e'}">${x[4]==='نجح'?'نجح':'إعفاء'}</span></td><td class="c">${pdfD(x[0])}</td></tr>`}).join(''),
  nmS=new Set(A.map(o=>o.n)),
  fu=S.pneg?[...new Set(alerts().filter(a=>/^(غاب|رسب)/.test(a[1])&&nmS.has(a[0])).map(a=>esc(a[0])+' ('+esc(a[1])+')'))]:null;
 return`<div style="break-before:page;page-break-before:always"><div class="sec" style="margin-top:0">الاختبارات المنجزة في الفترة (${R.length})</div>`+(R.length?`<table><thead><tr><th class="c" style="width:28px">#</th><th>الطالب</th><th>المسار</th><th>المرحلة</th><th class="c">النتيجة</th><th class="c">التاريخ</th></tr></thead><tbody>${rows}</tbody></table>`:'<div class="z">لا اختبارات منجزة في هذه الفترة</div>')
  +(fu?`<div class="sec">يحتاج متابعة</div><div class="bx">${fu.length?fu.map(x=>`<div>• ${x}</div>`).join(''):'<div class="z">—</div>'}</div>`:'')+`</div>`};
const pdfSquares=(st,f,t)=>{const g=exGridHtml(st,'',1,f,t);return g?`<div class="sec">مسار الاختبارات</div>${g}<div class="lg"><i style="background:#14803c"></i>أُنجز في هذه الفترة<i style="background:#8fd1a8"></i>أُنجز قبلها<i style="background:#fff;border:1px solid #9aa5ad"></i>لم يُنجز<i style="background:#fff;outline:2px solid #e0a100"></i>القادم</div>`:''};
'''
s = s[:a] + NEW_ADM + s[b:]
s = rep(s, "${A.map(row).join('')}</tbody></table>`;", "${A.map(row).join('')}</tbody></table>`+pdfExamsPage(A,f,t);")
s = rep(s, "/* ===== نهاية تصدير PDF ===== */", "/* ===== نهاية تصدير PDF ===== */\n" + EX_BLOCK)

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
g = rep(g, 'versionCode 12', 'versionCode 13')
g = rep(g, "versionName '1.7.0'", "versionName '1.8.0'")
open(GRADLE, 'w', encoding='utf-8').write(g)

open(PATH, 'w', encoding='utf-8').write(s)
print('تم التعديل بنجاح وفحص الصياغة سليم')
