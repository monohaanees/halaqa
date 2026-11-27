# باتش 2026-11-27.1 (1.8.1 / 14): إصلاح التفاف شارة «مرحَّلة ✓» + استطالة مربع «القادم» + sn19
import re,sys
H='android/app/src/main/assets/index.html'; G='android/app/build.gradle'
h=open(H,encoding='utf-8').read(); g=open(G,encoding='utf-8').read()
if "const VER='2026-11-27.1'" in h: sys.exit('طُبّق سابقاً')
def rep(s,a,b):
    assert s.count(a)==1,('مرساة',a[:50],s.count(a)); return s.replace(a,b)
h=rep(h,"const VER='2026-11-26.1';","const VER='2026-11-27.1';")
h=rep(h,"sn17:1,sn18:1,st:D.st","sn17:1,sn18:1,sn19:1,st:D.st")
h=rep(h,"if(!S.sn18){snap('قبل إصدار 2026-11-26.1');S.sn18=1;save()}","if(!S.sn18){snap('قبل إصدار 2026-11-26.1');S.sn18=1;save()}\nif(!S.sn19){snap('قبل إصدار 2026-11-27.1');S.sn19=1;save()}")
h=rep(h,".xql{font-size:12px;color:var(--mu);margin:6px 0}",".xql{font-size:12px;color:var(--mu);margin:6px 0}.xq.nx{flex:0 0 auto;order:0;font-size:0;color:inherit}.hd .badge{white-space:nowrap;flex:none}.hd b{min-width:0;overflow:hidden;text-overflow:ellipsis}")
g=rep(g,"versionCode 13","versionCode 14"); g=rep(g,"versionName '1.8.0'","versionName '1.8.1'")
for m in re.finditer(r'<script[^>]*>(.*?)</script>',h,re.S):
    open('/tmp/_s.js','w',encoding='utf-8').write(m.group(1))
    import subprocess; r=subprocess.run(['node','--check','/tmp/_s.js']); assert r.returncode==0,'node --check فشل'
open(H,'w',encoding='utf-8').write(h); open(G,'w',encoding='utf-8').write(g); print('تم')
