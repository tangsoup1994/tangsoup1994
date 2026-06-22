#!/usr/bin/env python3
"""从 notes/*.md 生成自包含的 index.html（双击即开，离线可用）。

用法：python3 build.py
笔记更新后重跑一次即可。只用标准库，无第三方依赖。
"""
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))

TEMPLATE = r"""<!doctype html>
<html lang="zh" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>托业错题本 · 查看器</title>
<script>(function(){try{var t=localStorage.getItem('toeic-theme')||((window.matchMedia&&matchMedia('(prefers-color-scheme:dark)').matches)?'dark':'light');document.documentElement.setAttribute('data-theme',t);}catch(e){}})();</script>
<style>
 :root{
   --paper:#f7f9fc; --surface:#ffffff; --surface-2:#eef2fa;
   --ink:#18233f; --ink-soft:#566087; --ink-faint:#8b93ab;
   --line:#e1e7f2; --line-soft:#eef1f8;
   --brand:#2d4f91; --brand-deep:#21407a; --brand-soft:#e6edfa;
   --gold:#bd8224;
   --correct:#1f8a5b; --correct-soft:#e2f2ea; --correct-line:#bfe0cd;
   --mark:#ffe29a; --mark-ink:#4a3a06;
   --shadow:0 1px 2px rgba(24,35,63,.04),0 4px 16px rgba(24,35,63,.05);
   --font-display:Georgia,"Times New Roman","Songti SC","Source Han Serif SC","Noto Serif CJK SC",STSong,SimSun,serif;
   --font-body:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
   --font-mono:"SF Mono","Cascadia Code","JetBrains Mono",Consolas,"Liberation Mono",monospace;
 }
 [data-theme="dark"]{
   --paper:#0e1525; --surface:#161f33; --surface-2:#1d2840;
   --ink:#e8edf8; --ink-soft:#a6b0c9; --ink-faint:#6e7796;
   --line:#283250; --line-soft:#222c47;
   --brand:#7aa0e8; --brand-deep:#9bb8f0; --brand-soft:#1f2d4c;
   --gold:#dcab5e;
   --correct:#52c08c; --correct-soft:#16301f; --correct-line:#2c5640;
   --mark:#6a5722; --mark-ink:#ffe7a8;
   --shadow:0 1px 2px rgba(0,0,0,.2),0 6px 20px rgba(0,0,0,.28);
 }
 *{box-sizing:border-box;}
 html,body{margin:0;height:100%;}
 body{font-family:var(--font-body);color:var(--ink);background:var(--paper);line-height:1.8;font-size:15.5px;-webkit-font-smoothing:antialiased;}
 .wrap{display:flex;min-height:100vh;}

 /* sidebar */
 aside{width:264px;flex:0 0 264px;background:var(--surface-2);border-right:1px solid var(--line);position:sticky;top:0;height:100vh;display:flex;flex-direction:column;padding:22px 16px;}
 .brand{display:flex;align-items:center;gap:10px;padding:0 6px 4px;}
 .brand .tick{width:6px;height:26px;border-radius:3px;background:var(--gold);flex:0 0 auto;}
 .brand .t1{font-family:var(--font-display);font-weight:700;font-size:18px;letter-spacing:.01em;line-height:1.1;}
 .brand .t2{font-size:11px;color:var(--ink-faint);letter-spacing:.16em;text-transform:uppercase;margin-top:2px;}
 #search{width:100%;margin:16px 0 14px;padding:9px 12px;border:1px solid var(--line);border-radius:9px;font-size:14px;background:var(--surface);color:var(--ink);font-family:inherit;transition:border-color .15s,box-shadow .15s;}
 #search::placeholder{color:var(--ink-faint);}
 #search:focus{outline:none;border-color:var(--brand);box-shadow:0 0 0 3px var(--brand-soft);}
 #nav{display:flex;flex-direction:column;gap:3px;flex:1;overflow:auto;margin:0 -4px;padding:0 4px;}
 .nav-item{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:9px;color:var(--ink-soft);text-decoration:none;cursor:pointer;border:1px solid transparent;transition:background .14s,color .14s;}
 .nav-item:hover{background:var(--brand-soft);color:var(--ink);}
 .nav-item.active{background:var(--surface);color:var(--brand-deep);border-color:var(--line);font-weight:600;box-shadow:var(--shadow);}
 .nav-num{font-family:var(--font-mono);font-size:11px;color:var(--ink-faint);min-width:18px;text-align:center;}
 .nav-item.active .nav-num{color:var(--gold);}
 .nav-name{font-size:14px;flex:1;}
 .badge{background:var(--brand);color:#fff;font-size:11px;border-radius:999px;padding:1px 8px;font-weight:600;font-family:var(--font-mono);}
 .foot{padding-top:12px;margin-top:8px;border-top:1px solid var(--line);}
 #theme{width:100%;padding:8px;border:1px solid var(--line);border-radius:9px;background:var(--surface);color:var(--ink-soft);font-family:inherit;font-size:13px;cursor:pointer;transition:background .14s,color .14s;}
 #theme:hover{background:var(--brand-soft);color:var(--ink);}
 #theme:focus-visible{outline:2px solid var(--brand);outline-offset:2px;}

 /* main */
 main{flex:1;min-width:0;padding:46px 56px 90px;}
 .content{max-width:760px;margin:0 auto;animation:rise .16s ease;}
 @keyframes rise{from{opacity:0;transform:translateY(6px);}to{opacity:1;transform:none;}}

 .content h1{font-family:var(--font-display);font-size:30px;font-weight:700;line-height:1.2;margin:0 0 6px;letter-spacing:.01em;}
 .content h1::after{content:"";display:block;width:46px;height:3px;border-radius:2px;background:var(--gold);margin-top:14px;}

 .entry{background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--brand);border-radius:14px;padding:22px 26px;margin:18px 0;box-shadow:var(--shadow);}
 .entry h2{font-family:var(--font-display);font-size:19px;font-weight:600;color:var(--brand-deep);margin:0 0 14px;line-height:1.35;}
 .entry > :last-child{margin-bottom:0;}
 .content h3{font-size:16px;font-weight:600;margin:1.3em 0 .4em;}

 .content p{margin:.62em 0;}
 .content > p{color:var(--ink-soft);margin:.4em 0 1.15em;}
 .content ul{margin:.5em 0;padding-left:1.3em;list-style:none;}
 .content li{margin:.34em 0;position:relative;}
 .content li::before{content:"";position:absolute;left:-1.05em;top:.72em;width:5px;height:5px;border-radius:50%;background:var(--gold);}
 .content strong{font-weight:600;color:var(--ink);}

 .content code{font-family:var(--font-mono);font-size:.85em;background:var(--surface-2);color:var(--brand-deep);padding:.12em .42em;border-radius:5px;border:1px solid var(--line);}

 blockquote{margin:.9em 0;padding:.85em 1.1em;background:var(--surface-2);border-left:3px solid var(--brand);border-radius:0 10px 10px 0;color:var(--ink);font-size:.97em;}
 [data-theme="dark"] blockquote{background:var(--paper);}

 p.answer{display:inline-block;margin:.85em 0;padding:.32em .9em;background:var(--correct-soft);color:var(--correct);border:1px solid var(--correct-line);border-radius:999px;font-size:.93rem;line-height:1.4;}
 p.answer::before{content:"✓";font-weight:700;margin-right:.45em;}
 p.answer strong{color:var(--correct);}

 /* tri-line / booktabs table */
 table{border-collapse:collapse;width:100%;margin:1.1em 0;font-size:14px;}
 thead th{text-align:left;font-weight:600;color:var(--ink-soft);font-size:12.5px;letter-spacing:.02em;padding:6px 14px 9px;border-bottom:2px solid var(--brand);white-space:nowrap;}
 tbody td{padding:10px 14px;border-bottom:1px solid var(--line-soft);vertical-align:top;}
 tbody tr:last-child td{border-bottom:none;}
 tbody tr:hover td{background:var(--surface-2);}
 td code{white-space:nowrap;}

 mark{background:var(--mark);color:var(--mark-ink);padding:0 2px;border-radius:3px;}
 a{color:var(--brand);text-decoration:none;border-bottom:1px solid var(--brand-soft);}
 a:hover{border-bottom-color:var(--brand);}
 .empty{color:var(--ink-faint);padding:2em 0;}
 :focus-visible{outline:2px solid var(--brand);outline-offset:2px;border-radius:4px;}

 @media (max-width:820px){
   .wrap{flex-direction:column;}
   aside{width:auto;flex:none;height:auto;position:static;border-right:none;border-bottom:1px solid var(--line);padding:16px;}
   #nav{flex-direction:row;flex-wrap:nowrap;overflow-x:auto;margin:0;padding:2px;flex:none;}
   .nav-item{white-space:nowrap;}
   .nav-name{flex:none;}
   .foot{display:none;}
   main{padding:30px 22px 60px;}
   .content h1{font-size:25px;}
 }
 @media (prefers-reduced-motion:reduce){
   *{animation:none!important;transition:none!important;}
 }
</style>
</head>
<body>
<div class="wrap">
 <aside>
   <div class="brand"><span class="tick"></span><span><span class="t1">托业错题本</span><span class="t2">TOEIC Review</span></span></div>
   <input id="search" type="search" placeholder="跨笔记搜索…" autocomplete="off" aria-label="搜索笔记">
   <nav id="nav"></nav>
   <div class="foot"><button id="theme" type="button">🌙 深色</button></div>
 </aside>
 <main><div class="content" id="content"></div></main>
</div>
<script>
const NOTES = __NOTES_DATA__;

function escapeHtml(s){
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
function inline(s){
  s = escapeHtml(s);
  s = s.replace(/`([^`]+)`/g, function(m,c){ return '<code>'+c+'</code>'; });
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  return s;
}
function splitRow(line){
  var s = line.trim();
  if(s.charAt(0)==='|') s = s.slice(1);
  if(s.charAt(s.length-1)==='|') s = s.slice(0,-1);
  return s.split('|').map(function(c){ return c.trim(); });
}
function isTableSep(l){ return /^\s*\|?[\s:|-]+\|?\s*$/.test(l) && l.indexOf('-')>=0; }
function renderMarkdown(md){
  md = md.replace(/<!--[\s\S]*?-->/g, '');
  var lines = md.split(/\r?\n/);
  var out = [];
  var inEntry = false;
  var i = 0;
  function closeEntry(){ if(inEntry){ out.push('</section>'); inEntry=false; } }
  while(i < lines.length){
    var line = lines[i];
    if(line.trim()===''){ i++; continue; }
    var h = /^(#{1,6})\s+(.*)$/.exec(line);
    if(h){
      var lvl=h[1].length, txt=inline(h[2].trim());
      if(lvl===1){ closeEntry(); out.push('<h1>'+txt+'</h1>'); }
      else if(lvl===2){ closeEntry(); out.push('<section class="entry"><h2>'+txt+'</h2>'); inEntry=true; }
      else { out.push('<h'+lvl+'>'+txt+'</h'+lvl+'>'); }
      i++; continue;
    }
    if(line.indexOf('|')>=0 && i+1<lines.length && isTableSep(lines[i+1])){
      var header = splitRow(line);
      i += 2;
      var rows = [];
      while(i<lines.length && lines[i].indexOf('|')>=0 && lines[i].trim()!==''){ rows.push(splitRow(lines[i])); i++; }
      var t = '<table><thead><tr>';
      header.forEach(function(c){ t += '<th>'+inline(c)+'</th>'; });
      t += '</tr></thead><tbody>';
      rows.forEach(function(r){
        t += '<tr>';
        for(var k=0;k<header.length;k++){ t += '<td>'+inline(r[k]!==undefined?r[k]:'')+'</td>'; }
        t += '</tr>';
      });
      t += '</tbody></table>';
      out.push(t);
      continue;
    }
    if(/^\s*>\s?/.test(line)){
      var bq = [];
      while(i<lines.length && /^\s*>\s?/.test(lines[i])){ bq.push(inline(lines[i].replace(/^\s*>\s?/,''))); i++; }
      out.push('<blockquote>'+bq.join('<br>')+'</blockquote>');
      continue;
    }
    if(/^\s*[-*]\s+/.test(line)){
      var items=[];
      while(i<lines.length && /^\s*[-*]\s+/.test(lines[i])){ items.push('<li>'+inline(lines[i].replace(/^\s*[-*]\s+/,''))+'</li>'); i++; }
      out.push('<ul>'+items.join('')+'</ul>');
      continue;
    }
    var para=[];
    while(i<lines.length && lines[i].trim()!=='' &&
          !/^(#{1,6})\s+/.test(lines[i]) &&
          !/^\s*[-*]\s+/.test(lines[i]) &&
          !/^\s*>\s?/.test(lines[i]) &&
          !(lines[i].indexOf('|')>=0 && i+1<lines.length && isTableSep(lines[i+1]))){
      para.push(lines[i]); i++;
    }
    var raw = para.join(' ');
    var cls = /^\s*\*\*答案\*\*/.test(raw) ? ' class="answer"' : '';
    out.push('<p'+cls+'>'+inline(raw)+'</p>');
  }
  closeEntry();
  return out.join('\n');
}

var app = { idx:0, q:'' };
var navEl = document.getElementById('nav');
var contentEl = document.getElementById('content');
var searchEl = document.getElementById('search');
var themeBtn = document.getElementById('theme');
var root = document.documentElement;

function countOcc(text,q){
  if(!q) return 0;
  var t=text.toLowerCase(), s=q.toLowerCase(), n=0, p=0;
  while((p=t.indexOf(s,p))>=0){ n++; p+=s.length; }
  return n;
}
function navParts(label){
  var m=/^(\d+)\s+(.*)$/.exec(label);
  return m ? {num:m[1], name:m[2]} : {num:'', name:label};
}
function buildNav(){
  navEl.innerHTML='';
  NOTES.forEach(function(n,k){
    if(app.q && countOcc(n.md,app.q)===0) return;
    var p=navParts(n.label);
    var a=document.createElement('a');
    a.className='nav-item'+(k===app.idx?' active':'');
    a.innerHTML='<span class="nav-num">'+escapeHtml(p.num)+'</span><span class="nav-name">'+escapeHtml(p.name)+'</span>'+
      (app.q?'<span class="badge">'+countOcc(n.md,app.q)+'</span>':'');
    a.onclick=function(){ openNote(k); };
    navEl.appendChild(a);
  });
}
function highlight(rootEl,q){
  var walker=document.createTreeWalker(rootEl, NodeFilter.SHOW_TEXT, null);
  var nodes=[], node;
  while(node=walker.nextNode()) nodes.push(node);
  var ql=q.toLowerCase();
  nodes.forEach(function(tn){
    var txt=tn.nodeValue, low=txt.toLowerCase(), idx=low.indexOf(ql);
    if(idx<0) return;
    var frag=document.createDocumentFragment(), last=0;
    while(idx>=0){
      frag.appendChild(document.createTextNode(txt.slice(last,idx)));
      var mk=document.createElement('mark'); mk.textContent=txt.slice(idx,idx+q.length);
      frag.appendChild(mk);
      last=idx+q.length;
      idx=low.indexOf(ql,last);
    }
    frag.appendChild(document.createTextNode(txt.slice(last)));
    tn.parentNode.replaceChild(frag,tn);
  });
}
function openNote(k){
  app.idx=k;
  contentEl.innerHTML=renderMarkdown(NOTES[k].md);
  contentEl.style.animation='none'; void contentEl.offsetWidth; contentEl.style.animation='';
  if(app.q){ highlight(contentEl,app.q); var m=contentEl.querySelector('mark'); if(m) m.scrollIntoView({block:'center'}); }
  buildNav();
}
searchEl.addEventListener('input', function(){
  app.q=searchEl.value.trim();
  if(app.q){
    var first=-1;
    for(var k=0;k<NOTES.length;k++){ if(countOcc(NOTES[k].md,app.q)>0){ first=k; break; } }
    if(first<0){ buildNav(); contentEl.innerHTML='<p class="empty">没有找到 “'+escapeHtml(app.q)+'”</p>'; return; }
    if(countOcc(NOTES[app.idx].md,app.q)===0) app.idx=first;
  }
  openNote(app.idx);
});
function setTheme(t){
  root.setAttribute('data-theme',t);
  try{ localStorage.setItem('toeic-theme',t); }catch(e){}
  themeBtn.textContent = t==='dark' ? '☀ 浅色' : '🌙 深色';
}
themeBtn.onclick=function(){ setTheme(root.getAttribute('data-theme')==='dark'?'light':'dark'); };
setTheme(root.getAttribute('data-theme')||'light');
if(NOTES.length) openNote(0);
</script>
</body>
</html>
"""

def main():
    files = sorted(glob.glob(os.path.join(ROOT, "notes", "*.md")))
    notes = []
    for f in files:
        name = os.path.basename(f)
        label = re.sub(r"\.md$", "", name).replace("_", " ")
        with open(f, encoding="utf-8") as fh:
            notes.append({"name": name, "label": label, "md": fh.read()})
    data = json.dumps(notes, ensure_ascii=False).replace("<", "\\u003c")
    html = TEMPLATE.replace("__NOTES_DATA__", data)
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(html)
    print("index.html generated from %d notes" % len(notes))

if __name__ == "__main__":
    main()
