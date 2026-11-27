# باتش إصدار 2026-11-27.1 (1.8.1 / 14) — المحادثة الخامسة
# 1) شارة «مرحَّلة ✓» لا تلتف  2) مربع «القادم» لا يستطيل  3) الشريط العلوي يتصغر ويتحاذى بحسب عرض الشاشة (كل العنوان ظاهر)
# 4) تصفية تبويب اليوم تشمل المسارات (الوسوم العادية: رشيدي، تهذيب١، عمّ، تهذيب٢، تبارك، تلاوة، غيب) إضافة إلى المجموعات الخاصة
import re,sys,subprocess
H='android/app/src/main/assets/index.html'; G='android/app/build.gradle'
h=open(H,encoding='utf-8').read(); g=open(G,encoding='utf-8').read()
if '/*v5b*/' in h: sys.exit('طُبّق سابقاً')
def rep(s,a,b):
    assert s.count(a)==1,('مرساة',a[:60],s.count(a)); return s.replace(a,b)
def opt(s,a,b,done):  # يطبّق إن لم يكن طُبّق من الباتش السابق
    if done in s: return s
    return rep(s,a,b)
h=opt(h,"const VER='2026-11-26.1';","const VER='2026-11-27.1';","const VER='2026-11-27.1';")
h=opt(h,"sn17:1,sn18:1,st:D.st","sn17:1,sn18:1,sn19:1,st:D.st","sn18:1,sn19:1,st:D.st")
h=opt(h,"if(!S.sn18){snap('قبل إصدار 2026-11-26.1');S.sn18=1;save()}","if(!S.sn18){snap('قبل إصدار 2026-11-26.1');S.sn18=1;save()}\nif(!S.sn19){snap('قبل إصدار 2026-11-27.1');S.sn19=1;save()}","if(!S.sn19){snap('قبل إصدار 2026-11-27.1')")
g=opt(g,"versionCode 13","versionCode 14","versionCode 14"); g=opt(g,"versionName '1.8.0'","versionName '1.8.1'","versionName '1.8.1'")
# CSS
NEWCSS=(".xq.nx{flex:0 0 auto;order:0;font-size:0;color:inherit}/*v5b*/"
 ".hd{font-size:calc(var(--hs,1)*16px);gap:.35em;padding:10px .75em;overflow:hidden}"
 ".hd b{font-size:1.2em;flex:1 0 auto;white-space:nowrap}"
 ".hd .badge{font-size:.75em;padding:.15em .65em;white-space:nowrap;flex:none}"
 ".hd input{font-size:.95em;width:9em;flex:none;min-width:0}"
 ".hd button{font-size:1em;padding:.4em .7em;min-width:0}")
OLD2=".xq.nx{flex:0 0 auto;order:0;font-size:0;color:inherit}.hd .badge{white-space:nowrap;flex:none}.hd b{min-width:0;overflow:hidden;text-overflow:ellipsis}"
if OLD2 in h: h=rep(h,OLD2,NEWCSS)
else: h=rep(h,".xql{font-size:12px;color:var(--mu);margin:6px 0}",".xql{font-size:12px;color:var(--mu);margin:6px 0}"+NEWCSS)
# التصفية
FN=("function stTags(s){return lvName(s).replace(/ \\(يدوي\\)/,'').split(' + ').filter(Boolean)}\n"
"function dtgOk(s){const g=S.dtg;if(!g)return true;if(g.indexOf('م:')===0)return stTags(s).includes(g.slice(2));return s.g===g}\n"
"function dtgOpts(){const A=active(S.day.date),C={};A.forEach(s=>stTags(s).forEach(t=>C[t]=(C[t]||0)+1));const O=['رشيدي','تهذيب١','تهذيب اللسان','عمّ','تهذيب٢','تبارك','تلاوة','حفظ','غيب'],T=Object.keys(C).sort((a,b)=>{const x=O.indexOf(a),y=O.indexOf(b);return(x<0?99:x)-(y<0?99:y)}),G=allTags();"
"if(!T.length&&!G.length)return'';return `<select id='dtg' style='margin-top:6px'><option value=''>كل الطلاب</option>${T.length?`<optgroup label='حسب المسار'>${T.map(t=>`<option value='م:${qa(t)}'${S.dtg==='م:'+t?' selected':''}>${esc(t)} (${C[t]})</option>`).join('')}</optgroup>`:''}${G.length?`<optgroup label='حسب المجموعة'>${G.map(x=>`<option value='${qa(x)}'${x===S.dtg?' selected':''}>${esc(x)}</option>`).join('')}</optgroup>`:''}</select>`}\n"
"function fitHd(){const h=document.querySelector('.hd');if(!h)return;let s=1;h.style.setProperty('--hs','1');while(h.scrollWidth>h.clientWidth+1&&s>0.5){s-=0.04;h.style.setProperty('--hs',s.toFixed(2))}}\n")
h=rep(h,"let FOC=null,FQ='',MODE='',TODO=0;","let FOC=null,FQ='',MODE='',TODO=0;\n"+FN)
a=h.index("${allTags().length?`<select id='dtg'"); e="</select>`:''}"; b=h.index(e,a)+len(e)
assert h.count("${allTags().length?`<select id='dtg'")==1
h=h[:a]+"${dtgOpts()}"+h[b:]
h=rep(h,"(!S.dtg||s.g===S.dtg)&&q.every","dtgOk(s)&&q.every")
assert h.count(".filter(s=>!S.dtg||s.g===S.dtg)")==2; h=h.replace(".filter(s=>!S.dtg||s.g===S.dtg)",".filter(dtgOk)")
h=rep(h,"التصفية بالمجموعة للعرض فقط","التصفية للعرض فقط")
h=rep(h,"\nrender();\n","\nrender();\nfitHd();addEventListener('resize',fitHd);try{new MutationObserver(fitHd).observe(document.getElementById('bd'),{childList:true,characterData:true,subtree:true})}catch(e){}\n")
for m in re.finditer(r'<script[^>]*>(.*?)</script>',h,re.S):
    open('/tmp/_s.js','w',encoding='utf-8').write(m.group(1))
    assert subprocess.run(['node','--check','/tmp/_s.js']).returncode==0,'node --check فشل'
open(H,'w',encoding='utf-8').write(h); open(G,'w',encoding='utf-8').write(g); print('تم')
