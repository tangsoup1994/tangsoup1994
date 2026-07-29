#!/usr/bin/env python3
"""从 notes/*.md 生成自包含的 offline.html（双击即开，离线可用）。

在线版 index.html 是手维护的静态文件，运行时直接 fetch 各 md 文件，不由本脚本生成；
新增/删除/改名笔记文件时，手动更新 index.html 顶部的 NOTE_FILES 清单即可。

用法：python3 build.py
只用标准库，无第三方依赖。
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
<meta name="theme-color" content="#f7f9fc">
<title>托业试题集 · 查看器</title>
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
 body{font-family:var(--font-body);color:var(--ink);background:var(--paper);line-height:1.8;font-size:15.5px;-webkit-font-smoothing:antialiased;-webkit-text-size-adjust:100%;text-size-adjust:100%;-webkit-tap-highlight-color:transparent;overflow-wrap:break-word;}
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
 .question-entry{scroll-margin-top:64px;}
 .question-entry blockquote{margin-bottom:12px;}
 .answer-toggle{display:flex;align-items:center;justify-content:center;gap:9px;width:100%;min-height:42px;padding:9px 14px;border:1px solid var(--line);border-radius:8px;background:var(--surface-2);color:var(--brand-deep);font-family:inherit;font-size:14px;font-weight:600;cursor:pointer;transition:background .14s,border-color .14s,color .14s;}
 .answer-toggle:hover{background:var(--brand-soft);border-color:var(--brand);}
 .answer-toggle:focus-visible{outline:2px solid var(--brand);outline-offset:2px;}
 .answer-toggle .chevron{width:8px;height:8px;border-right:2px solid currentColor;border-bottom:2px solid currentColor;transform:rotate(45deg) translate(-1px,-1px);transition:transform .16s;flex:0 0 auto;}
 .answer-toggle[aria-expanded="true"] .chevron{transform:rotate(225deg) translate(-1px,-1px);}
 .entry-details{padding-top:4px;}
 .question-options{margin:.8em 0;padding:.75em 1.1em;background:var(--surface-2);border-left:3px solid var(--gold);border-radius:0 8px 8px 0;line-height:1.9;}
 [data-theme="dark"] .question-options{background:var(--paper);}
 .added-date{margin:-6px 0 10px;color:var(--ink-faint);font-family:var(--font-mono);font-size:12px;}
 .added-date strong{color:inherit;font-weight:500;}
 .date-bar{position:sticky;top:0;z-index:5;display:flex;align-items:center;gap:12px;margin:12px 0 20px;padding:9px 0;background:var(--paper);border-bottom:1px solid var(--line);}
 .date-bar-label{flex:0 0 auto;color:var(--ink-faint);font-size:12px;font-weight:600;}
 .date-list{display:flex;gap:5px;min-width:0;overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch;}
 .date-list::-webkit-scrollbar{display:none;}
 .date-jump{display:flex;align-items:center;gap:7px;min-height:34px;padding:6px 10px;border:0;border-bottom:2px solid transparent;background:transparent;color:var(--ink-soft);font-family:var(--font-mono);font-size:12px;white-space:nowrap;cursor:pointer;}
 .date-jump:hover{color:var(--brand-deep);background:var(--brand-soft);}
 .date-jump.active{color:var(--brand-deep);border-bottom-color:var(--gold);font-weight:700;}
 .date-jump:focus-visible{outline:2px solid var(--brand);outline-offset:-2px;}
 .date-count{display:inline-flex;align-items:center;justify-content:center;min-width:22px;height:20px;padding:0 5px;border-radius:10px;background:var(--surface-2);color:var(--ink-faint);font-size:10px;}
 .date-jump.active .date-count{background:var(--brand-soft);color:var(--brand-deep);}
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
   aside{width:auto;flex:none;height:auto;position:relative;border-right:none;border-bottom:1px solid var(--line);padding:16px 16px 12px;}
   .brand{padding-right:92px;}
   #search{font-size:16px;margin:14px 0 12px;}
   #nav{flex-direction:row;flex-wrap:nowrap;overflow-x:auto;-webkit-overflow-scrolling:touch;margin:0;padding:2px 0 4px;flex:none;gap:6px;scrollbar-width:none;}
   #nav::-webkit-scrollbar{display:none;}
   .nav-item{white-space:nowrap;padding:9px 13px;}
   .nav-name{flex:none;}
   .foot{display:block;position:absolute;top:12px;right:14px;margin:0;padding:0;border-top:none;}
   #theme{width:auto;padding:7px 12px;}
   main{padding:26px 18px 60px;}
   .content h1{font-size:24px;}
   .entry{padding:18px 16px;}
   table{display:block;overflow-x:auto;-webkit-overflow-scrolling:touch;}
   thead th{white-space:normal;}
   td code{white-space:normal;}
 }
 @media (prefers-reduced-motion:reduce){
   *{animation:none!important;transition:none!important;}
 }
</style>
</head>
<body>
<div class="wrap">
 <aside>
   <div class="brand"><span class="tick"></span><span><span class="t1">托业试题集</span><span class="t2">TOEIC Practice</span></span></div>
   <input id="search" type="search" placeholder="跨笔记搜索…" autocomplete="off" aria-label="搜索笔记">
   <nav id="nav"></nav>
   <div class="foot"><button id="theme" type="button">🌙 深色</button></div>
 </aside>
 <main><div class="content" id="content"></div></main>
</div>
<script>
var NOTES = __NOTES_DECL__;

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
    var cls = /^\s*\*\*答案\*\*/.test(raw) ? ' class="answer"' :
              (/^\s*\*\*添加日期\*\*/.test(raw) ? ' class="added-date"' : '');
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
  var act=navEl.querySelector('.nav-item.active');
  if(act && navEl.scrollWidth>navEl.clientWidth+4){
    navEl.scrollLeft=act.offsetLeft-(navEl.clientWidth-act.offsetWidth)/2;
  }
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
function setQuestionExpanded(entry,expanded){
  var details=entry.querySelector('.entry-details');
  var button=entry.querySelector('.answer-toggle');
  if(!details || !button) return;
  details.hidden=!expanded;
  button.setAttribute('aria-expanded',expanded?'true':'false');
  button.querySelector('.toggle-label').textContent=expanded?'收起解析':'显示解析';
}
function setupDateBar(entries){
  var groups={};
  var dates=[];
  entries.forEach(function(entry){
    var dateEl=entry.querySelector('.added-date');
    if(!dateEl) return;
    var match=/\d{4}-\d{2}-\d{2}/.exec(dateEl.textContent);
    if(!match) return;
    var date=match[0];
    entry.dataset.addedDate=date;
    if(!groups[date]){ groups[date]=[]; dates.push(date); }
    groups[date].push(entry);
  });
  if(!dates.length) return;

  var bar=document.createElement('div');
  bar.className='date-bar';
  bar.setAttribute('aria-label','按添加日期定位试题');
  var label=document.createElement('span');
  label.className='date-bar-label';
  label.textContent='日期';
  var list=document.createElement('div');
  list.className='date-list';
  list.setAttribute('role','navigation');
  list.setAttribute('aria-label','试题添加日期');

  dates.forEach(function(date,index){
    var button=document.createElement('button');
    button.type='button';
    button.className='date-jump'+(index===0?' active':'');
    button.title=date+' · '+groups[date].length+' 题';
    button.innerHTML='<span>'+escapeHtml(date.slice(5))+'</span><span class="date-count">'+groups[date].length+'题</span>';
    button.onclick=function(){
      list.querySelectorAll('.date-jump').forEach(function(item){ item.classList.remove('active'); });
      button.classList.add('active');
      groups[date][0].scrollIntoView({behavior:'smooth',block:'start'});
    };
    list.appendChild(button);
  });

  bar.appendChild(label);
  bar.appendChild(list);
  contentEl.insertBefore(bar,entries[0]);
}
function setupQuestionEntries(){
  var entries=contentEl.querySelectorAll('.entry');
  entries.forEach(function(entry){
    var quote=entry.querySelector('blockquote');
    if(!quote) return;
    var optionBreak=quote.querySelector('br');
    if(!optionBreak) return;

    var options=document.createElement('div');
    options.className='question-options';
    var optionNode=optionBreak.nextSibling;
    while(optionNode){
      var nextOption=optionNode.nextSibling;
      options.appendChild(optionNode);
      optionNode=nextOption;
    }
    optionBreak.remove();

    var details=document.createElement('div');
    details.className='entry-details';
    var detailNode=quote.nextSibling;
    while(detailNode){
      var nextDetail=detailNode.nextSibling;
      details.appendChild(detailNode);
      detailNode=nextDetail;
    }

    var button=document.createElement('button');
    button.type='button';
    button.className='answer-toggle';
    button.innerHTML='<span class="toggle-label">显示解析</span><span class="chevron" aria-hidden="true"></span>';
    button.onclick=function(){ setQuestionExpanded(entry,button.getAttribute('aria-expanded')!=='true'); };

    entry.classList.add('question-entry');
    entry.appendChild(options);
    entry.appendChild(button);
    entry.appendChild(details);
    setQuestionExpanded(entry,false);
  });
  setupDateBar(entries);
}
function openNote(k){
  app.idx=k;
  contentEl.innerHTML=renderMarkdown(NOTES[k].md);
  if(NOTES[k].name==='01_试题集.md') setupQuestionEntries();
  contentEl.style.animation='none'; void contentEl.offsetWidth; contentEl.style.animation='';
  if(app.q){
    highlight(contentEl,app.q);
    contentEl.querySelectorAll('.entry-details mark').forEach(function(mark){
      var entry=mark.closest('.question-entry');
      if(entry) setQuestionExpanded(entry,true);
    });
    var m=contentEl.querySelector('mark'); if(m) m.scrollIntoView({block:'center'});
  }
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
  var mc=document.querySelector('meta[name="theme-color"]');
  if(mc) mc.setAttribute('content', t==='dark' ? '#0e1525' : '#f7f9fc');
}
themeBtn.onclick=function(){ setTheme(root.getAttribute('data-theme')==='dark'?'light':'dark'); };
setTheme(root.getAttribute('data-theme')||'light');
__BOOTSTRAP__
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
    offline = (TEMPLATE
               .replace("__NOTES_DECL__", data)
               .replace("__BOOTSTRAP__", "if(NOTES.length) openNote(0);"))
    with open(os.path.join(ROOT, "offline.html"), "w", encoding="utf-8") as fh:
        fh.write(offline)
    print("offline.html generated from %d notes" % len(notes))

if __name__ == "__main__":
    main()
