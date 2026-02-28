#!/usr/bin/env python3
"""
PolyEdge — Polymarket Top Trader Copy Tool
==========================================
Run:   python3 start_polyedge.py
Open:  http://localhost:8765
Stop:  Ctrl+C

Requires Python 3.6+ (no extra packages needed)
"""

import http.server
import urllib.request
import urllib.parse
import urllib.error
import ssl
import json
import threading
import webbrowser
import sys
import os

PORT = 8765

# Exact Polymarket API paths the JS will request
# JS calls: GET /api/v1/leaderboard?...
#           GET /api/positions?...
# Proxy maps: /api/* → https://data-api.polymarket.com/*
POLYMARKET_BASE = "https://data-api.polymarket.com"

# ─── Embedded HTML/CSS/JS app ────────────────────────────────────────────────
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PolyEdge — Copy the Top 1%</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
:root{--bg:#04060a;--surface:#090e16;--panel:#0d1520;--border:#131f30;--border2:#1c2d42;--accent:#00e5b5;--adim:rgba(0,229,181,.08);--aglow:rgba(0,229,181,.2);--red:#ff4d6d;--yellow:#f59e0b;--text:#e2eaf4;--muted:#4a6080;--muted2:#2a3d55;}
*{margin:0;padding:0;box-sizing:border-box;}
body{background:var(--bg);color:var(--text);font-family:'Space Mono',monospace;min-height:100vh;}
body::before{content:'';position:fixed;inset:0;background-image:linear-gradient(rgba(0,229,181,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(0,229,181,.025) 1px,transparent 1px);background-size:48px 48px;pointer-events:none;z-index:0;}
.app{display:flex;min-height:100vh;position:relative;z-index:1;}
.sidebar{width:360px;flex-shrink:0;background:var(--surface);border-right:1px solid var(--border);display:flex;flex-direction:column;position:sticky;top:0;height:100vh;overflow:hidden;}
.sh{padding:20px 18px 14px;border-bottom:1px solid var(--border);}
.logo{font-family:'Syne',sans-serif;font-size:22px;font-weight:800;letter-spacing:-.5px;margin-bottom:3px;}
.logo em{color:var(--accent);font-style:normal;}
.tagline{font-size:10px;color:var(--muted);letter-spacing:2px;text-transform:uppercase;}
.badge{display:inline-flex;align-items:center;gap:6px;margin-top:8px;font-size:10px;color:var(--accent);background:var(--adim);border:1px solid var(--aglow);border-radius:3px;padding:3px 9px;}
.dot{width:6px;height:6px;background:var(--accent);border-radius:50%;animation:blink 2s infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
.filters{padding:12px 14px;border-bottom:1px solid var(--border);display:flex;flex-direction:column;gap:9px;}
.fr{display:flex;align-items:center;gap:8px;flex-wrap:wrap;}
.fl{font-size:10px;color:var(--muted);letter-spacing:1px;text-transform:uppercase;width:50px;flex-shrink:0;}
.btns{display:flex;gap:4px;flex-wrap:wrap;}
.btn{background:var(--panel);border:1px solid var(--border2);color:var(--muted);font-family:'Space Mono',monospace;font-size:10px;padding:5px 10px;cursor:pointer;border-radius:3px;transition:all .12s;white-space:nowrap;}
.btn:hover{color:var(--text);border-color:var(--muted);}
.btn.active{background:var(--adim);border-color:var(--accent);color:var(--accent);}
.trader-list{flex:1;overflow-y:auto;padding:4px 0;}
.trader-list::-webkit-scrollbar{width:4px;}
.trader-list::-webkit-scrollbar-thumb{background:var(--border2);border-radius:2px;}
.ti{display:flex;align-items:center;gap:10px;padding:10px 14px;cursor:pointer;border-left:3px solid transparent;transition:all .12s;border-bottom:1px solid rgba(19,31,48,.5);}
.ti:hover{background:rgba(0,229,181,.03);border-left-color:var(--border2);}
.ti.active{background:var(--adim);border-left-color:var(--accent);}
.tr{font-size:11px;font-weight:700;color:var(--muted);width:24px;text-align:right;flex-shrink:0;}
.rg{color:#f59e0b;}.rs{color:#94a3b8;}.rb{color:#b45309;}
.ava{width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,#1a2535,#0d1520);border:1px solid var(--border2);display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:var(--accent);flex-shrink:0;overflow:hidden;}
.ava img{width:100%;height:100%;object-fit:cover;}
.td{flex:1;min-width:0;}
.tn{font-family:'Syne',sans-serif;font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.ts{font-size:10px;color:var(--muted);margin-top:2px;}
.pb{font-family:'Syne',sans-serif;font-size:12px;font-weight:700;text-align:right;flex-shrink:0;}
.pp{color:var(--accent);}.pn{color:var(--red);}
.main{flex:1;display:flex;flex-direction:column;min-width:0;}
.mh{padding:20px 26px 16px;border-bottom:1px solid var(--border);background:var(--surface);position:sticky;top:0;z-index:10;}
.mt{font-family:'Syne',sans-serif;font-size:18px;font-weight:700;margin-bottom:4px;display:flex;align-items:center;gap:10px;}
.ld{width:7px;height:7px;background:var(--accent);border-radius:50%;flex-shrink:0;animation:blink 2s infinite;}
.ms{font-size:11px;color:var(--muted);}
.stats-bar{display:flex;border-bottom:1px solid var(--border);background:var(--surface);}
.stat{flex:1;padding:12px 16px;border-right:1px solid var(--border);text-align:center;}
.stat:last-child{border-right:none;}
.sv{font-family:'Syne',sans-serif;font-size:17px;font-weight:700;color:var(--accent);}
.sl{font-size:9px;color:var(--muted);letter-spacing:1.5px;text-transform:uppercase;margin-top:3px;}
.pa{flex:1;padding:22px 26px;overflow-y:auto;}
.pa::-webkit-scrollbar{width:4px;}
.pa::-webkit-scrollbar-thumb{background:var(--border2);border-radius:2px;}
.empty{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;min-height:300px;gap:14px;color:var(--muted);text-align:center;}
.ei{font-size:48px;opacity:.3;}
.et{font-family:'Syne',sans-serif;font-size:15px;font-weight:600;}
.es{font-size:11px;line-height:1.8;max-width:300px;}
.sw{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;min-height:200px;}
.spin{width:32px;height:32px;border:3px solid var(--border2);border-top-color:var(--accent);border-radius:50%;animation:spin .9s linear infinite;}
@keyframes spin{to{transform:rotate(360deg)}}
.spt{font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);}
.sps{font-size:10px;color:var(--muted2);}
.err{background:rgba(255,77,109,.07);border:1px solid rgba(255,77,109,.2);border-radius:6px;padding:13px 16px;font-size:11px;color:var(--red);margin-bottom:16px;line-height:1.8;}
.ph{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;flex-wrap:wrap;gap:10px;}
.pt{font-family:'Syne',sans-serif;font-size:15px;font-weight:700;}
.cbadge{background:var(--adim);border:1px solid var(--aglow);color:var(--accent);font-size:10px;padding:4px 12px;border-radius:20px;margin-left:10px;}
.sbs{display:flex;gap:5px;}
.sb{background:var(--panel);border:1px solid var(--border2);color:var(--muted);font-family:'Space Mono',monospace;font-size:10px;padding:5px 10px;cursor:pointer;border-radius:3px;transition:all .12s;}
.sb:hover{color:var(--text);}
.sb.active{color:var(--accent);border-color:var(--accent);background:var(--adim);}
.bet-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:12px;}
.bc{background:var(--panel);border:1px solid var(--border2);border-radius:8px;overflow:hidden;transition:all .15s;cursor:pointer;}
.bc:hover{border-color:var(--aglow);box-shadow:0 0 20px rgba(0,229,181,.06);transform:translateY(-1px);}
.bct{padding:13px 15px 11px;border-bottom:1px solid var(--border);position:relative;}
.bct::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;}
.bc.yes .bct::before{background:var(--accent);}
.bc.no .bct::before{background:var(--red);}
.micon{width:26px;height:26px;border-radius:5px;object-fit:cover;float:right;margin-left:8px;background:var(--border2);}
.btitle{font-size:12px;line-height:1.5;color:var(--text);margin-bottom:9px;padding-right:34px;}
.bmr{display:flex;align-items:center;gap:7px;flex-wrap:wrap;}
.op{font-family:'Syne',sans-serif;font-size:10px;font-weight:700;padding:3px 9px;border-radius:3px;letter-spacing:.5px;text-transform:uppercase;}
.op.yes{background:rgba(0,229,181,.12);color:var(--accent);border:1px solid rgba(0,229,181,.2);}
.op.no{background:rgba(255,77,109,.12);color:var(--red);border:1px solid rgba(255,77,109,.2);}
.edt{font-size:10px;color:var(--muted);}
.pbar{height:3px;background:var(--border2);border-radius:2px;margin-top:8px;overflow:hidden;}
.pfill{height:100%;border-radius:2px;}
.bc.yes .pfill{background:var(--accent);}
.bc.no .pfill{background:var(--red);}
.bcb{padding:11px 15px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;}
.bsv{font-family:'Syne',sans-serif;font-size:14px;font-weight:700;}
.bsv.g{color:var(--accent);}.bsv.r{color:var(--red);}.bsv.y{color:var(--yellow);}
.bsl{font-size:9px;color:var(--muted);letter-spacing:1px;text-transform:uppercase;margin-top:2px;}
.ca{padding:0 15px 13px;}
.cl{display:flex;align-items:center;justify-content:center;gap:7px;background:var(--adim);border:1px solid var(--aglow);border-radius:5px;color:var(--accent);font-family:'Space Mono',monospace;font-size:10px;padding:8px;letter-spacing:1px;text-transform:uppercase;transition:all .12s;cursor:pointer;}
.cl:hover{background:rgba(0,229,181,.15);}
.no-bets{text-align:center;padding:36px 20px;color:var(--muted);font-size:11px;line-height:2;background:var(--panel);border:1px solid var(--border2);border-radius:8px;}
@media(max-width:900px){.app{flex-direction:column;}.sidebar{width:100%;height:auto;position:relative;}.trader-list{max-height:250px;}.stats-bar{flex-wrap:wrap;}.bet-grid{grid-template-columns:1fr;}}
</style>
</head>
<body>
<div class="app">
  <aside class="sidebar">
    <div class="sh">
      <div class="logo">Poly<em>Edge</em></div>
      <div class="tagline">Top 1% Trader Intelligence</div>
      <div class="badge"><div class="dot"></div>Live proxy active</div>
    </div>
    <div class="filters">
      <div class="fr">
        <span class="fl">Period</span>
        <div class="btns" id="periodBtns">
          <button class="btn active" data-v="ALL">All time</button>
          <button class="btn" data-v="MONTH">30d</button>
          <button class="btn" data-v="WEEK">7d</button>
          <button class="btn" data-v="DAY">24h</button>
        </div>
      </div>
      <div class="fr">
        <span class="fl">Market</span>
        <div class="btns" id="catBtns">
          <button class="btn active" data-v="OVERALL">All</button>
          <button class="btn" data-v="POLITICS">Politics</button>
          <button class="btn" data-v="SPORTS">Sports</button>
          <button class="btn" data-v="CRYPTO">Crypto</button>
          <button class="btn" data-v="ECONOMICS">Econ</button>
        </div>
      </div>
    </div>
    <div class="trader-list" id="traderList">
      <div class="sw"><div class="spin"></div><div class="spt">Loading…</div></div>
    </div>
  </aside>

  <main class="main">
    <div class="mh">
      <div class="mt"><div class="ld"></div><span id="mainTitle">Select a trader</span></div>
      <div class="ms" id="mainSub">← Pick a top earner to see their live open bets you can copy</div>
    </div>
    <div class="stats-bar" id="statsBar" style="display:none">
      <div class="stat"><div class="sv" id="sOpen">—</div><div class="sl">Open Bets</div></div>
      <div class="stat"><div class="sv" id="sDep">—</div><div class="sl">Capital In</div></div>
      <div class="stat"><div class="sv" id="sPnl">—</div><div class="sl">Unrealized PnL</div></div>
      <div class="stat"><div class="sv" id="sPrice">—</div><div class="sl">Avg Price</div></div>
    </div>
    <div class="pa" id="posArea">
      <div class="empty">
        <div class="ei">🎯</div>
        <div class="et">Ready to Copy Trades</div>
        <div class="es">Select any top trader on the left to instantly see every open bet they hold — only unresolved markets you can still enter.</div>
      </div>
    </div>
  </main>
</div>

<script>
const API = '';  // same origin, no prefix needed
let period='ALL', cat='OVERALL', traders=[], selIdx=null, sortMode='VALUE', cache={};

function $f(n){
  if(n==null)return'—';
  const a=Math.abs(n),s=n<0?'-':'';
  if(a>=1e6)return s+'$'+(a/1e6).toFixed(2)+'M';
  if(a>=1e3)return s+'$'+(a/1e3).toFixed(1)+'K';
  return s+'$'+a.toFixed(0);
}

async function get(path){
  const r = await fetch('/proxy' + path);
  if(!r.ok){
    const body = await r.text().catch(()=>'');
    throw new Error('HTTP '+r.status+(body?' — '+body.slice(0,120):''));
  }
  return r.json();
}

async function loadBoard(){
  document.getElementById('traderList').innerHTML=`<div class="sw"><div class="spin"></div><div class="spt">Fetching top 100…</div></div>`;
  try{
    const [a,b] = await Promise.all([
      get(`/v1/leaderboard?limit=50&offset=0&orderBy=PNL&timePeriod=${period}&category=${cat}`),
      get(`/v1/leaderboard?limit=50&offset=50&orderBy=PNL&timePeriod=${period}&category=${cat}`)
    ]);
    traders=[...(Array.isArray(a)?a:[]),...(Array.isArray(b)?b:[])].filter(t=>t.pnl>0);
    renderList();
  }catch(e){
    document.getElementById('traderList').innerHTML=`
      <div style="padding:18px;font-size:11px;color:var(--red);line-height:2;text-align:center">
        ⚠ ${e.message}<br>
        <button class="btn active" onclick="loadBoard()" style="margin-top:8px">↺ Retry</button>
      </div>`;
  }
}

function renderList(){
  if(!traders.length){
    document.getElementById('traderList').innerHTML=`<div style="padding:24px;text-align:center;font-size:11px;color:var(--muted)">No traders found.</div>`;
    return;
  }
  document.getElementById('traderList').innerHTML=traders.map((t,i)=>{
    const name=t.userName||(t.proxyWallet?t.proxyWallet.slice(0,6)+'…'+t.proxyWallet.slice(-4):'?');
    const init=name.slice(0,2).toUpperCase();
    const rc=i===0?'rg':i===1?'rs':i===2?'rb':'';
    const pc=t.pnl>=0?'pp':'pn';
    return`<div class="ti${i===selIdx?' active':''}" onclick="selTrader(${i})">
      <div class="tr ${rc}">${i===0?'👑':'#'+(i+1)}</div>
      <div class="ava">${t.profileImage?`<img src="${t.profileImage}" onerror="this.parentNode.textContent='${init}'">`:`${init}`}</div>
      <div class="td">
        <div class="tn">${name}${t.verifiedBadge?' ✓':''}</div>
        <div class="ts">${t.xUsername?'@'+t.xUsername:(t.proxyWallet||'').slice(0,18)+'…'}</div>
      </div>
      <div class="pb ${pc}">${t.pnl>=0?'+':''}${$f(t.pnl)}</div>
    </div>`;
  }).join('');
}

async function selTrader(i){
  selIdx=i; renderList();
  const t=traders[i];
  const name=t.userName||(t.proxyWallet?.slice(0,10)+'…');
  document.getElementById('mainTitle').textContent=name+(t.verifiedBadge?' ✓':'');
  document.getElementById('mainSub').textContent='Fetching open bets…';
  document.getElementById('statsBar').style.display='none';
  if(cache[t.proxyWallet]){renderPositions(cache[t.proxyWallet],t,i);return;}
  document.getElementById('posArea').innerHTML=`<div class="sw"><div class="spin"></div><div class="spt">Loading positions</div><div class="sps">Filtering to unresolved markets only…</div></div>`;
  try{
    const data=await get(`/positions?user=${t.proxyWallet}&sizeThreshold=1&redeemable=false&limit=100&sortBy=CURRENT&sortDirection=DESC`);
    const pos=(Array.isArray(data)?data:[]).filter(p=>p.size>0&&(p.currentValue||0)>0&&!p.redeemable);
    cache[t.proxyWallet]=pos;
    renderPositions(pos,t,i);
  }catch(e){
    document.getElementById('posArea').innerHTML=`<div class="err">⚠ ${e.message}</div><div class="empty" style="min-height:160px"><div class="ei">🔄</div><div class="et">Click trader to retry</div></div>`;
    document.getElementById('mainSub').textContent='Error — click to retry';
  }
}

function renderPositions(pos,trader,idx){
  document.getElementById('mainSub').textContent=`#${idx+1} · ${$f(trader.pnl)} all-time profit · ${pos.length} open bet${pos.length!==1?'s':''}`;
  if(!pos.length){
    document.getElementById('statsBar').style.display='none';
    document.getElementById('posArea').innerHTML=`<div class="no-bets">🔍 No active open bets for this trader right now.<br>They may have closed all positions or only hold resolved markets.</div>`;
    return;
  }
  const totVal=pos.reduce((s,p)=>s+(p.currentValue||0),0);
  const unrealPnl=totVal-pos.reduce((s,p)=>s+(p.initialValue||0),0);
  const avgPrice=pos.reduce((s,p)=>s+(p.curPrice||0),0)/pos.length;
  document.getElementById('sOpen').textContent=pos.length;
  document.getElementById('sDep').textContent=$f(totVal);
  document.getElementById('sPnl').textContent=(unrealPnl>=0?'+':'')+$f(unrealPnl);
  document.getElementById('sPnl').style.color=unrealPnl>=0?'var(--accent)':'var(--red)';
  document.getElementById('sPrice').textContent=(avgPrice*100).toFixed(0)+'¢';
  document.getElementById('statsBar').style.display='flex';
  let sorted=[...pos];
  if(sortMode==='VALUE') sorted.sort((a,b)=>(b.currentValue||0)-(a.currentValue||0));
  else if(sortMode==='CONF') sorted.sort((a,b)=>Math.abs(b.curPrice-.5)-Math.abs(a.curPrice-.5));
  else sorted.sort((a,b)=>new Date(a.endDate||0)-new Date(b.endDate||0));
  const cards=sorted.map(p=>{
    const isYes=(p.outcome||'').toLowerCase()==='yes'||p.outcomeIndex===0;
    const cls=isYes?'yes':'no';
    const pp=Math.round((p.curPrice||0)*100);
    const cashPnl=p.cashPnl!=null?p.cashPnl:((p.currentValue||0)-(p.initialValue||0));
    let edt='—';
    if(p.endDate){
      const d=new Date(p.endDate),now=new Date(),diff=d-now,days=Math.floor(diff/864e5);
      if(diff<0)edt='⚠ Resolving soon';
      else if(days===0)edt='⏰ Ends today';
      else if(days===1)edt='📅 Tomorrow';
      else edt=`📅 ${days}d left`;
    }
    const url=p.eventSlug?`https://polymarket.com/event/${p.eventSlug}`:p.slug?`https://polymarket.com/event/${p.slug}`:`https://polymarket.com`;
    return`<div class="bc ${cls}" onclick="window.open('${url}','_blank')">
      <div class="bct">
        ${p.icon?`<img class="micon" src="${p.icon}" onerror="this.style.display='none'" alt="">`:''}
        <div class="btitle">${p.title||'Unknown Market'}</div>
        <div class="bmr">
          <span class="op ${cls}">${isYes?'✓ YES':'✗ NO'}</span>
          <span class="edt">${edt}</span>
        </div>
        <div class="pbar"><div class="pfill" style="width:${pp}%"></div></div>
      </div>
      <div class="bcb">
        <div><div class="bsv y">${$f(p.currentValue)}</div><div class="bsl">Position value</div></div>
        <div><div class="bsv">${pp}¢</div><div class="bsl">Market price</div></div>
        <div><div class="bsv ${cashPnl>=0?'g':'r'}">${cashPnl>=0?'+':''}${$f(cashPnl)}</div><div class="bsl">Unrealized</div></div>
      </div>
      <div class="ca">
        <div class="cl" onclick="event.stopPropagation();window.open('${url}','_blank')">
          📋 Open on Polymarket &amp; Copy This Bet →
        </div>
      </div>
    </div>`;
  }).join('');
  document.getElementById('posArea').innerHTML=`
    <div class="ph">
      <div><span class="pt">Open Active Bets</span><span class="cbadge">${pos.length} positions</span></div>
      <div class="sbs">
        <button class="sb${sortMode==='VALUE'?' active':''}" onclick="resort('VALUE')">By Value</button>
        <button class="sb${sortMode==='CONF'?' active':''}" onclick="resort('CONF')">By Confidence</button>
        <button class="sb${sortMode==='DATE'?' active':''}" onclick="resort('DATE')">By End Date</button>
      </div>
    </div>
    <div class="bet-grid">${cards}</div>`;
}

function resort(m){sortMode=m;if(selIdx!=null){const t=traders[selIdx];if(cache[t.proxyWallet])renderPositions(cache[t.proxyWallet],t,selIdx);}}

function resetMain(){
  selIdx=null;cache={};
  document.getElementById('mainTitle').textContent='Select a trader';
  document.getElementById('mainSub').textContent='← Pick a top earner to see their live open bets';
  document.getElementById('statsBar').style.display='none';
  document.getElementById('posArea').innerHTML=`<div class="empty"><div class="ei">🎯</div><div class="et">Ready to Copy Trades</div><div class="es">Click any trader on the left to reveal their open bets — only unresolved markets you can still enter.</div></div>`;
}

document.getElementById('periodBtns').addEventListener('click',e=>{
  const b=e.target.closest('.btn');if(!b)return;
  document.querySelectorAll('#periodBtns .btn').forEach(x=>x.classList.remove('active'));
  b.classList.add('active');period=b.dataset.v;resetMain();loadBoard();
});
document.getElementById('catBtns').addEventListener('click',e=>{
  const b=e.target.closest('.btn');if(!b)return;
  document.querySelectorAll('#catBtns .btn').forEach(x=>x.classList.remove('active'));
  b.classList.add('active');cat=b.dataset.v;resetMain();loadBoard();
});

loadBoard();
</script>
</body>
</html>"""


# ─── Proxy server ─────────────────────────────────────────────────────────────
class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # Print clean logs to terminal
        status = args[1] if len(args) > 1 else '?'
        path = args[0].split(' ')[1] if args else '?'
        color = '\033[92m' if str(status).startswith('2') else '\033[91m'
        print(f"  {color}{status}\033[0m  {path}")

    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # ── Serve HTML app ──
        if path in ('/', '/index.html', ''):
            body = HTML.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(body)
            return

        # ── Proxy /proxy/* → Polymarket ──
        if path.startswith('/proxy/') or path.startswith('/proxy?'):
            # Strip /proxy prefix, keep everything after
            poly_path = path[6:]  # '/proxy/v1/...' → '/v1/...'
            if parsed.query:
                poly_path += '?' + parsed.query

            target_url = POLYMARKET_BASE + poly_path
            print(f"  → {target_url}")

            try:
                # Create SSL context that works on all platforms
                ctx = ssl.create_default_context()
                try:
                    ctx.load_default_certs()
                except Exception:
                    pass

                req = urllib.request.Request(
                    target_url,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'application/json, */*',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Origin': 'https://polymarket.com',
                        'Referer': 'https://polymarket.com/',
                    }
                )

                with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
                    body = resp.read()
                    content_type = resp.headers.get('Content-Type', 'application/json')

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(body)

            except urllib.error.HTTPError as e:
                body = json.dumps({'error': f'Polymarket returned {e.code}: {e.reason}'}).encode()
                self.send_response(502)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(body)
                print(f"  ✗ Polymarket HTTP error: {e.code} {e.reason}")

            except urllib.error.URLError as e:
                msg = str(e.reason)
                body = json.dumps({'error': f'Cannot reach Polymarket: {msg}'}).encode()
                self.send_response(502)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(body)
                print(f"  ✗ URL error: {msg}")

            except Exception as e:
                body = json.dumps({'error': str(e)}).encode()
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(body)
                print(f"  ✗ Exception: {e}")
            return

        # ── 404 for anything else ──
        self.send_response(404)
        self.end_headers()


def main():
    print('\n\033[92m' + '─'*45)
    print('  PolyEdge — Polymarket Copy Tool')
    print('─'*45 + '\033[0m')
    print(f'  App  →  http://localhost:{PORT}')
    print(f'  Stop →  Ctrl+C')
    print('─'*45 + '\n')

    try:
        server = http.server.ThreadingHTTPServer(('localhost', PORT), Handler)
    except AttributeError:
        # Python < 3.7 fallback
        server = http.server.HTTPServer(('localhost', PORT), Handler)

    def open_browser():
        import time; time.sleep(0.6)
        webbrowser.open(f'http://localhost:{PORT}')

    threading.Thread(target=open_browser, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n\033[93m  Stopped.\033[0m\n')
        server.server_close()


if __name__ == '__main__':
    main()
