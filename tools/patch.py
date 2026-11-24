import re, subprocess, tempfile, os

PATH = 'android/app/src/main/assets/index.html'
GRADLE = 'android/app/build.gradle'

def rep(s, old, new):
    n = s.count(old)
    assert n == 1, 'المرساة وُجدت %d مرة (المطلوب مرة واحدة): %s' % (n, old[:60])
    return s.replace(old, new)

s = open(PATH, encoding='utf-8').read()
orig = s
assert 'pdfRank' in s, 'طبّق دفعة تصميم PDF (2026-11-19.3) أولاً'
assert 'pdfStu' not in s and 'sn17' not in s, 'الباتش طُبّق سابقاً'
assert "const VER='2026-11-19.3';" in s, 'الملف ليس بإصدار 2026-11-19.3 المتوقع'

# 1) الإصدار + نقطة حفظ تلقائية عند أول تشغيل (sn17)
s = rep(s, "const VER='2026-11-19.3';", "const VER='2026-11-24.1';")
s = rep(s, "if(!S.sn16){snap('قبل إصدار 2026-11-19.3');S.sn16=1;save()}",
"if(!S.sn16){snap('قبل إصدار 2026-11-19.3');S.sn16=1;save()}\nif(!S.sn17){snap('قبل إصدار 2026-11-24.1');S.sn17=1;save()}")
s = rep(s, "sn15:1,sn16:1,st:D.st", "sn15:1,sn16:1,sn17:1,st:D.st")

# 2) توحيد الترتيب: نقاط ثم صفحات ثم الاسم، ومراكز متتابعة (الشاشة + نص الواتساب + PDF)
s = rep(s, ".sort((a,b)=>b.pt-a.pt||b.pg-a.pg);A.forEach(o=>o.rk=1+A.filter(p=>p.pt>o.pt).length);",
           ".sort((a,b)=>b.pt-a.pt||b.pg-a.pg||a.n.localeCompare(b.n,'ar'));const PV=[...new Set(A.map(o=>o.pt))];A.forEach(o=>o.rk=1+PV.indexOf(o.pt));")

# 3) كتلة PDF الجديدة: سجل الطالب + ملخص الحلقة + بقية القوالب
NEW_BLOCK = r'''/* ===== تصدير PDF بقالب موحّد (2026-11-19) ===== */
const pdfCss=ft=>`@page{size:A4;margin:12mm 10mm 16mm 10mm;@bottom-left{content:"صفحة " counter(page) " من " counter(pages);font-size:10px;color:#667}@bottom-right{content:"${ft}";font-size:10px;color:#667}}*{box-sizing:border-box;-webkit-print-color-adjust:exact;print-color-adjust:exact}html,body{margin:0;padding:0}body{font-family:'Noto Naskh Arabic','Noto Sans Arabic','Droid Arabic Naskh',Tahoma,Arial,sans-serif;color:#1b2a2f;font-size:12.5px;line-height:1.5;direction:rtl}.hd{border:2px solid #0d7a63;border-radius:12px;background:#eef9f5;text-align:center;padding:8px 10px 9px;margin-bottom:8px}.hd .b{font-size:11px;color:#4a6a62}.hd .i{font-size:20px;font-weight:700;color:#0a6b56;margin:1px 0}.hd .t{font-size:13.5px;font-weight:700;color:#14493d;margin-top:2px}.hd .s{font-size:12px;color:#33564d;margin-top:2px}.pl{margin-top:6px}.pl span{display:inline-block;white-space:nowrap;border:1px solid #7cc4b0;background:#fff;color:#0a6b56;border-radius:999px;padding:1px 12px;margin:0 3px;font-size:12px;font-weight:700}table{width:100%;border-collapse:collapse}thead{display:table-header-group}tr{break-inside:avoid;page-break-inside:avoid}th{background:#0d6b57;color:#fff;border:1px solid #0d6b57;padding:6px 5px;font-size:12px;font-weight:700}td{border:1px solid #cfd8dc;padding:4px 6px;vertical-align:middle}tbody tr:nth-child(even){background:#f4f7f9}td.c,th.c{text-align:center}td.c{white-space:nowrap}.n{font-weight:700}.z{color:#a7b0b5;font-weight:400}.ok{color:#14803c;font-weight:700}.no{color:#c0262d;font-weight:700}.ng{color:#c0262d}.bd{display:inline-block;min-width:20px;height:20px;line-height:20px;border-radius:50%;background:#0d7a63;color:#fff;font-weight:700;font-size:11px;text-align:center}tr.g1 .bd{background:#d4a017}tr.g2 .bd{background:#6c7a89}tr.g3 .bd{background:#c8581a}tr.g1{background:#fff3b8!important}tr.g2{background:#e6ebf0!important}tr.g3{background:#fde3cf!important}tr.ab{background:#fdeeee!important}tr.ex{background:#fff6e3!important}.w{border:1px solid #c9a227;background:#fff7d6;padding:5px 8px;margin:6px 0;font-size:12px;border-radius:6px}.st{font-weight:700}.st.p{color:#14803c}.st.a{color:#c0262d}.st.e{color:#b26a00}.st.s{color:#1b5aa0}.d .pos{color:#14803c}.d .okl{color:#14803c;font-weight:700}.d .nol{color:#c0262d;font-weight:700}.dash{color:#a7b0b5}table.sm{border:0;margin-bottom:6px}table.sm td{border:0;padding:0;vertical-align:middle;background:none}table.sm td.rg{width:140px;text-align:center}.tl{display:inline-block;width:31%;margin:3px 1%;padding:6px 4px;border:1px solid #cfe3dc;border-radius:8px;background:#f4faf8;text-align:center;vertical-align:top}.tl.w4{width:23.5%;margin:3px .5%}.tl b{display:block;font-size:16px;color:#0a6b56}.tl small{display:block;font-size:10.5px;color:#556}.tl.p b{color:#14803c}.tl.a b{color:#c0262d}.tl.e b{color:#b26a00}.sec{font-size:13px;font-weight:700;color:#0a6b56;margin:12px 0 4px;border-bottom:2px solid #0d7a63;padding-bottom:2px;break-after:avoid;page-break-after:avoid}.sq{display:inline-block;width:22px;height:22px;line-height:22px;margin:2px;border-radius:5px;text-align:center;font-size:10px;font-weight:700;color:#fff}.sq.p{background:#2e9d5b}.sq.a{background:#c0262d}.sq.e{background:#e0a100}.sq.s{background:#1b5aa0}.lg{font-size:10.5px;color:#556;margin-top:3px}.lg i{display:inline-block;width:10px;height:10px;border-radius:2px;margin:0 8px 0 3px;vertical-align:middle}.bar{display:block;width:100%;height:9px;border-radius:5px;background:#dfe9e6;overflow:hidden}.bar i{display:block;height:9px;background:#0d7a63}.chip{display:inline-block;border:1px solid #cfe3dc;background:#f4faf8;border-radius:999px;padding:0 9px;margin:2px;font-size:11px;white-space:nowrap}.bdl{font-size:12px;margin:4px 0}.adm{margin:0 0 8px}.col{display:inline-block;width:48.5%;vertical-align:top;border:1px solid #cfe3dc;border-radius:8px;padding:5px 8px;margin:2px .4%;font-size:12px}.bx b.h2,.col b.h2{display:block;color:#0a6b56;margin-bottom:2px}.pgl{font-size:12px;margin:2px 0}.pgl b{color:#0a6b56}.tl.w6{width:15.3%;margin:3px .6%}.bx{border:1px solid #cfe3dc;border-radius:8px;padding:5px 8px;margin:4px 0;font-size:12px;background:#fff}`;
const cssStr=s=>String(s||'').replace(/["\\\n\r]/g,' ');
const pdfHtml=(ttl,head,body,foot)=>`<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>${esc(ttl)}</title><style>${pdfCss(cssStr(foot))}</style></head><body><div class="hd"><div class="b">بسم الله الرحمن الرحيم</div><div class="i">${esc(SET.hdr||'')}</div>${head}</div>${body}</body></html>`;
const pdfD=s=>String(s).replace(/(\d{4})-(\d{2})-(\d{2})/g,'\u200e$3-$2-$1\u200e');
const pdfN=(n,one,two,pl,sg)=>n===1?one:n===2?two:n+' '+(n<=10?pl:sg);
const pdfRank=A=>{const B=[...A].sort((a,b)=>b.pt-a.pt||b.pg-a.pg||a.n.localeCompare(b.n,'ar')),pts=[...new Set(B.map(o=>o.pt))];B.forEach(o=>{o.prk=1+pts.indexOf(o.pt)});return B};
const pdfCls=a=>a==='حاضر'?'p':a==='غائب'?'a':a==='غائب بعذر'?'e':'s';
const pdfRowc=a=>a==='غائب'?' class="ab"':a==='غائب بعذر'?' class="ex"':'';
const pdfDl=x=>{const c=/\(نجح/.test(x)?'okl':/\(رسب/.test(x)?'nol':/^ملاحظة إيجابية/.test(x)?'pos':'';return`<div${c?' class="'+c+'"':''}>${esc(x)}</div>`};
const pdfTile=(v,l,c,w)=>`<span class="tl${w?(w===6?' w6':' w4'):''}${c?' '+c:''}"><b>${v}</b><small>${l}</small></span>`;
const pdfRing=pct=>{const c=2*Math.PI*44,col=pct==null?'#a7b0b5':pct>=90?'#0d7a63':pct>=75?'#d99a00':'#c0262d';return`<svg width="124" height="124" viewBox="0 0 124 124"><circle cx="62" cy="62" r="44" fill="none" stroke="#dfe9e6" stroke-width="12"/>${pct>0?`<circle cx="62" cy="62" r="44" fill="none" stroke="${col}" stroke-width="12" stroke-linecap="round" stroke-dasharray="${(c*pct/100).toFixed(1)} ${c.toFixed(1)}" transform="rotate(-90 62 62)"/>`:''}<text x="62" y="62" text-anchor="middle" font-size="26" font-weight="700" fill="${col}">${pct==null?'—':pct+'%'}</text><text x="62" y="82" text-anchor="middle" font-size="11" fill="#556">نسبة الحضور</text></svg>`};
const pdfWd=d=>new Date(d+'T00:00:00').toLocaleDateString('ar',{weekday:'long'});
function pdfDay(date){
 const ls=text(date).split('\n'),re=/^(\d+)\. (.+) — (حاضر|غائب بعذر|غائب|حصة خاصة)$/,B=[],meta=[];let cur=null;
 ls.forEach(l=>{const m=re.exec(l);if(m){cur={i:m[1],n:m[2],a:m[3],d:[],p:''};B.push(cur);return}
  if(!cur){meta.push(l);return}
  const b=l.replace(/^\s*•\s*/,'').trim();if(!b)return;
  if(/^النقاط: /.test(b))cur.p=b.replace(/^النقاط: /,'');else cur.d.push(b)});
 if(!B.length)return{};
 const cn={p:0,a:0,e:0,s:0};B.forEach(o=>cn[pdfCls(o.a)]++);
 const ttl='سجل-'+date,title=meta[2]||'سجل المتابعة اليومي — '+date,extra=meta.slice(3).filter(Boolean),
  warn=extra.filter(x=>x.charAt(0)==='⚠'),info=extra.filter(x=>x.charAt(0)!=='⚠'),
  pills=`<div class="pl"><span>عدد الطلاب: ${B.length}</span><span>حاضر: ${cn.p}</span><span>غائب: ${cn.a}</span><span>بعذر: ${cn.e}</span>${cn.s?`<span>حصة خاصة: ${cn.s}</span>`:''}</div>`,
  head=`<div class="t">${pdfD(esc(title))}</div>`+info.map(x=>`<div class="s">${esc(x)}</div>`).join('')+warn.map(x=>`<div class="w">${esc(x)}</div>`).join('')+pills,
  body=`<table><thead><tr><th class="c" style="width:28px">#</th><th style="width:22%">اسم الطالب</th><th class="c" style="width:11%">الحضور</th><th>التفاصيل والمتابعة اليومية</th><th class="c" style="width:48px">النقاط</th></tr></thead><tbody>`+B.map(o=>`<tr${pdfRowc(o.a)}><td class="c">${o.i}</td><td class="n">${esc(o.n)}</td><td class="c"><span class="st ${pdfCls(o.a)}">${esc(o.a)}</span></td><td class="d">${o.d.length?o.d.map(pdfDl).join(''):'<span class="dash">—</span>'}</td><td class="c"><b class="${(+o.p)<0?'ng':''}">\u200e${esc(o.p||'0')}\u200e</b></td></tr>`).join('')+`</tbody></table>`;
 return{ttl,head,body,foot:(SET.hdr||'')+' ('+pdfD(date)+')'}}
function pdfStu(n,f,t){const st=byName(n);if(!st)return{};
 const neg=S.rneg!==0,R=stats(f,t,[n])[n],att=R.ses-R.ab-R.ex,pct=R.ses?Math.round(att/R.ses*100):null,
  ls=stext(n,f,t,neg).split('\n'),prog=[],days=[];let bd='',inD=false;
 ls.forEach(l=>{if(l==='سجل الأيام:'){inD=true;return}
  if(inD){const m=/^(\d{4}-\d{2}-\d{2}) — (.*) · النقاط (\S+)$/.exec(l);if(m){const p=m[2].split(' · ');days.push({d:m[1],a:p[0],x:p.slice(1),p:m[3]})}return}
  const m=/^التقدم في (.+?): (.*)$/.exec(l);if(m){prog.push([m[1],m[2]]);return}
  if(/^مصادر النقاط: /.test(l))bd=l.replace(/^مصادر النقاط: /,'')});
 const cp=(a,b)=>a[0]<b[0]?-1:a[0]>b[0]?1:0,
  rws=S.log.filter(r=>r[1]===n&&r[0]>=f&&r[0]<=t).sort(cp),
  sq=rws.map(r=>`<span class="sq ${r[26]==='خاصة'?'s':r[2]==='غائب'?'a':r[2]==='بعذر'?'e':'p'}">${+r[0].slice(8)}</span>`).join(''),
  trk=TR.map(x=>{const l=lastRank(st,x),T=CAT[x].length,e=CAT[x][l-1],nx=CAT[x][l],pd=S.ex.filter(y=>y[1]===n&&y[2]===x&&y[4]==='نجح').reduce((m,y)=>y[0]>m?y[0]:m,'');return{x,l,T,cur:e?e[8]:'—',pd:pd||'—',nx:nx?nx[8]:'—'}}).filter(o=>o.l>0),
  xs=S.ex.filter(x=>x[1]===n&&x[0]>=f&&x[0]<=t).sort(cp),
  tiles=[pdfTile(att,'حضر','p'),pdfTile(R.ab,'غاب','a'),pdfTile(R.ex,'بعذر','e'),pdfTile('\u200e'+R.pt+'\u200e','النقاط'),pdfTile(R.pg,'الصفحات'),pdfTile(R.rp,'الإعادات'),pdfTile(R.ses,'الحصص'),pdfTile(R.ok+' ✓ · '+R.no+' ✗','الاختبارات'),pdfTile(R.np+(neg?' · '+R.nn:''),neg?'ملاحظات + / −':'ملاحظات +')].join(''),
  head=`<div class="t" style="font-size:17px">${esc(n)}</div><div class="s">${esc(lvName(st)||st.lvl||'')}</div><div class="s">الفترة: من ${pdfD(f)} إلى ${pdfD(t)}</div>`;
 let body=`<table class="sm"><tr><td class="rg">${pdfRing(pct)}</td><td>${tiles}</td></tr></table>`;
 if(bd)body+=`<div class="sec">مصادر النقاط</div><div>${bd.split(' · ').map(x=>{const i=x.lastIndexOf(' ');return pdfTile('\u200e'+esc(x.slice(i+1))+'\u200e',esc(x.slice(0,i)),'',6)}).join('')}</div>`;
 body+=`<div class="sec">الحضور في الفترة <span class="z">· ${pdfN(rws.length,'حصة واحدة','حصتان','حصص','حصة')}</span></div><div>${sq||'<span class="z">لا حصص في هذه الفترة</span>'}</div><div class="lg"><i style="background:#2e9d5b"></i>حاضر<i style="background:#c0262d"></i>غائب<i style="background:#e0a100"></i>بعذر<i style="background:#1b5aa0"></i>خاصة</div>`;
 if(trk.length)body+=`<div class="sec">التقدم في الاختبارات</div><table><thead><tr><th>المسار</th><th style="width:26%">التقدم</th><th class="c">المرحلة</th><th>المرحلة الحالية</th><th class="c">آخر نجاح</th><th>القادمة</th></tr></thead><tbody>`+trk.map(o=>`<tr><td class="n">${esc(o.x)}</td><td><span class="bar"><i style="width:${Math.round(o.l/o.T*100)}%"></i></span></td><td class="c">${o.l} / ${o.T}</td><td>${esc(o.cur)}</td><td class="c">${pdfD(o.pd)}</td><td>${esc(o.nx)}</td></tr>`).join('')+`</tbody></table>`;
 if(prog.length)body+=`<div class="sec">الصفحات المسمَّعة في الفترة</div>`+prog.map(p=>`<div class="pgl"><b>${esc(p[0])}:</b> ${esc(p[1])}</div>`).join('');
 if(xs.length)body+=`<div class="sec">اختبارات الفترة</div><table><thead><tr><th class="c" style="width:16%">التاريخ</th><th style="width:20%">المسار</th><th>المرحلة</th><th class="c">النتيجة</th><th class="c">العلامة</th><th>ملاحظة</th></tr></thead><tbody>`+xs.map(x=>{const e=(CAT[x[2]]||[])[x[3]-1];return`<tr><td class="c">${pdfD(x[0])}</td><td>${esc(x[2])}</td><td>${esc(e?e[8]:'')}</td><td class="c"><span class="${x[4]==='نجح'?'ok':x[4]==='رسب'?'no':'z'}">${esc(x[4])}</span></td><td class="c">${esc(x[5]===''?'—':x[5])}</td><td>${esc(x[6]||'')}</td></tr>`}).join('')+`</tbody></table>`;
 body+=`<div class="sec">سجل الأيام</div>`+(days.length?`<table><thead><tr><th class="c" style="width:17%">التاريخ</th><th class="c" style="width:12%">الحالة</th><th>التفاصيل</th><th class="c" style="width:48px">النقاط</th></tr></thead><tbody>`+days.map(o=>`<tr${pdfRowc(o.a)}><td class="c"><b>${pdfD(o.d)}</b><br><span class="z">${esc(pdfWd(o.d))}</span></td><td class="c"><span class="st ${pdfCls(o.a)}">${esc(o.a)}</span></td><td class="d">${o.x.length?o.x.map(pdfDl).join(''):'<span class="dash">—</span>'}</td><td class="c"><b class="${(+o.p)<0?'ng':''}">\u200e${esc(o.p)}\u200e</b></td></tr>`).join('')+`</tbody></table>`:'<div class="z">لا سجل أيام</div>');
 return{ttl:'سجل-'+n+'-'+f+'-'+t,head,body,foot:(SET.hdr||'')+' — '+n+' ('+pdfD(f)+' إلى '+pdfD(t)+')'}}
const pdfAdm=(A,f,t)=>{const T=A.reduce((a,o)=>({s:a.s+o.ses,b:a.b+o.ab,e:a.e+o.ex,g:a.g+o.pg,k:a.k+o.ok,n:a.n+o.no}),{s:0,b:0,e:0,g:0,k:0,n:0}),
  pc=T.s?Math.round((T.s-T.b-T.e)/T.s*100):null,nm=new Set(A.map(o=>o.n)),
  ach=S.ex.filter(x=>x[0]>=f&&x[0]<=t&&x[4]==='نجح'&&nm.has(x[1])).sort((a,b)=>a[0]<b[0]?-1:a[0]>b[0]?1:0).map(x=>{const e=(CAT[x[2]]||[])[x[3]-1];return esc(x[1])+' — '+esc(x[2])+(e?': '+esc(e[8]):'')}),
  fu=S.pneg?[...new Set(alerts().filter(a=>/^(غاب|رسب)/.test(a[1])&&nm.has(a[0])).map(a=>esc(a[0])+' ('+esc(a[1])+')'))]:null,
  li=(a,k)=>a.length?a.slice(0,k).map(x=>`<div>• ${x}</div>`).join('')+(a.length>k?`<div class="z">و ${a.length-k} آخرين</div>`:''):'<div class="z">—</div>';
 return`<div class="adm">${pdfTile(pc==null?'—':pc+'%','نسبة حضور الحلقة','',1)}${pdfTile(T.b+' · '+T.e,'غياب · بعذر','',1)}${pdfTile(T.g,'مجموع الصفحات','',1)}${pdfTile(T.k+' ✓ · '+T.n+' ✗','الاختبارات','',1)}<div class="bx"><b class="h2">الإنجازات (اختبارات اجتازوها)</b>${li(ach,12)}</div>${fu?`<div class="bx"><b class="h2">يحتاج متابعة</b>${li(fu,12)}</div>`:''}</div>`};
function pdfSta(){const{k,f,t,A:A0,days}=pdata();if(!A0.length)return{};const A=pdfRank(A0),
 ttl='إحصائية-'+(k==='w'?'أسبوعية':'شهرية')+'-'+f+'-'+t,hs=pdfN(days,'حصة واحدة','حصتان','حصص','حصة'),
 head=`<div class="t">${k==='w'?'الإحصائية الأسبوعية':'الإحصائية الشهرية'} — من ${pdfD(f)} إلى ${pdfD(t)} (${hs})</div><div class="pl"><span>عدد الطلاب: ${pdfN(A.length,'طالب واحد','طالبان','طلاب','طالبًا')}</span><span>عدد الحصص: ${hs}</span></div>`,
 H=['الترتيب','اسم الطالب','النقاط','الصفحات','الإعادات','الحضور','غياب','بعذر','الاختبارات','ملاحظات إيجابية'].concat(S.pneg?['ملاحظات سلبية']:[]),
 zz=v=>v?v:`<span class="z">0</span>`,
 row=o=>{const g=o.prk<=3?' class="g'+o.prk+'"':'',at=(o.ses-o.ab-o.ex)+' من '+o.ses,
  c=[`<span class="bd">${o.prk}</span>`,`<span class="n">${esc(o.n)}</span>`,`<b class="${o.pt<0?'ng':''}">\u200e${o.pt}\u200e</b>`,zz(o.pg),zz(o.rp),(!o.ab&&!o.ex)?`<b>${at}</b>`:at,zz(o.ab),zz(o.ex),`<span class="${o.ok?'ok':'z'}">نجح ${o.ok}</span> · <span class="${o.no?'no':'z'}">رسب ${o.no}</span>`,zz(o.np)].concat(S.pneg?[o.nn?`<span class="no">${o.nn}</span>`:zz(0)]:[]);
  return`<tr${g}>${c.map((x,i)=>`<td class="${i===1?'':'c'}">${x}</td>`).join('')}</tr>`},
 body=pdfAdm(A,f,t)+`<table><thead><tr>${H.map((h,i)=>`<th class="${i===1?'':'c'}">${h}</th>`).join('')}</tr></thead><tbody>${A.map(row).join('')}</tbody></table>`;
 return{ttl,head,body,foot:(SET.hdr||'')+' (من '+pdfD(f)+' إلى '+pdfD(t)+')'}}
function pdfExport(kind,arg){
 try{
  const r=kind==='day'?pdfDay(rpRange()[0]):kind==='stu'?pdfStu(arg.n,arg.f,arg.t):pdfSta();
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

# 4) الأزرار: بطاقة الطالب + صفحة التقارير عند اختيار طالب
s = rep(s, "<button data-gr='1' style='width:100%'>تقرير هذا الطالب وإرساله لولي الأمر ←</button></div>",
           "<button data-gr='1' style='width:100%'>تقرير هذا الطالب وإرساله لولي الأمر ←</button><button id='spdf' style='width:100%'>📄 سجل الطالب PDF</button></div>")
s = rep(s, "${!st&&f===t?`<button id='rpdf'>📄 تصدير PDF</button>`:''}",
           "${!st&&f===t?`<button id='rpdf'>📄 تصدير PDF</button>`:st?`<button id='rpdf'>📄 سجل الطالب PDF</button>`:''}")
s = rep(s, "else if(id==='rpdf')pdfExport('day');",
           "else if(id==='rpdf'){const[f,t]=rpRange();S.rs?pdfExport('stu',{n:S.rs,f,t}):pdfExport('day')}else if(id==='spdf'){const all=[...S.st].sort((a,b)=>a.n.localeCompare(b.n,'ar')),n=S.cs&&byName(S.cs)?S.cs:all[0].n,mk=S.cm||S.day.date.slice(0,7),[f,t]=rng('m',mk+'-01');pdfExport('stu',{n,f,t})}")

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
g = rep(g, 'versionCode 11', 'versionCode 12')
g = rep(g, "versionName '1.6.1'", "versionName '1.7.0'")
open(GRADLE, 'w', encoding='utf-8').write(g)

open(PATH, 'w', encoding='utf-8').write(s)
print('تم التعديل بنجاح وفحص الصياغة سليم')
