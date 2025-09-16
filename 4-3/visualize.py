# visualize.py  —  단일 파일 실시간 시각화 (SSE, 표준 라이브러리만)
# 사용법:
#   python visualize.py your_script.py [arg1 arg2 ...]
# 실행되면 브라우저가 자동으로 열리고,
# 우측 페이지에서 한-스텝 / 정지 / 속도(ms) 제어 가능.
# 기본 속도는 "아주 느리게" 1500ms/줄로 설정함.

import sys, os, json, time, threading, traceback, runpy, argparse, queue, webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

# ===== 실행/스텝 상태 =====
class State:
    def __init__(self):
        self.stepping   = False
        self.delay      = 5.0    # seconds (기본 5000ms = 아주 느리게)
        self.max_lines  = 20000
        self.line_count = 0
        self.step_event = threading.Event()
        self.stop_flag  = False
        self.pause_mode = False
        self.pending_steps = 0

STATE = State()
TARGET_PATH = None
# 각 SSE 연결마다 전용 큐
SUBS_LOCK = threading.Lock()
SUBS = []  # list[queue.Queue[str]]

def _broadcast(obj):
    """모든 구독자에게 이벤트 전송"""
    try:
        data = json.dumps(obj, ensure_ascii=False)
    except Exception as e:
        data = json.dumps({"type":"error","error":f"encode error: {e}"}, ensure_ascii=False)
    with SUBS_LOCK:
        dead = []
        for q in SUBS:
            try:
                q.put_nowait(data)
            except Exception:
                dead.append(q)
        for d in dead:
            if d in SUBS:
                SUBS.remove(d)

def _locals_slim(frame, limit=120):
    out={}
    try:
        for i,(k,v) in enumerate(list(frame.f_locals.items())):
            if i>=limit: break
            if str(k).startswith("__"): continue
            try:
                s=repr(v)
                if len(s)>180: s=s[:179]+"…"
            except Exception as e:
                s=f"<repr error: {e}>"
            out[str(k)]=s
    except Exception as e:
        out["_err"]=f"locals error: {e}"
    return out

def _frame_matches_target(frame):
    if frame is None or TARGET_PATH is None:
        return False
    try:
        return os.path.abspath(frame.f_code.co_filename) == TARGET_PATH
    except Exception:
        return False

def _stack_list(frame, limit=48):
    st = []
    f = frame
    try:
        while f and len(st) < limit:
            if _frame_matches_target(f):
                st.append(f.f_code.co_name or "<module>")
            f = f.f_back
    except Exception:
        pass
    return list(reversed(st))

def make_trace():
    """sys.settrace 훅: call/return/line + locals diff + 스텝/딜레이"""
    last_locals = None
    def _trace(frame, event, arg):
        nonlocal last_locals
        if STATE.stop_flag:
            raise SystemExit("stopped")

        if not _frame_matches_target(frame):
            return _trace

        if event in ("call","return","line"):
            name = frame.f_code.co_name or "<module>"
            stack = _stack_list(frame)

            if event == "call":
                _broadcast({"type":"call","func":name,"stack":stack})

            elif event == "return":
                _broadcast({"type":"return","func":name,"stack":stack})

            elif event == "line":
                STATE.line_count += 1
                if STATE.line_count > STATE.max_lines:
                    _broadcast({"type":"halt"})
                    raise SystemExit("line limit")

                ln  = int(frame.f_lineno) if frame and frame.f_lineno else 0
                cur = _locals_slim(frame)

                if last_locals is None:
                    diffs = list(cur.keys())
                else:
                    diffs = [k for k,v in cur.items()
                             if (k not in last_locals) or (last_locals.get(k)!=v)]
                last_locals = cur

                _broadcast({
                    "type":"trace",
                    "line":ln,
                    "locals":cur,
                    "stack":stack,
                    "var_changed":diffs,
                    "func":name
                })

                if STATE.delay > 0 and not STATE.pause_mode:
                    time.sleep(STATE.delay)
                if STATE.pause_mode:
                    if STATE.pending_steps > 0:
                        STATE.pending_steps -= 1
                        if STATE.pending_steps == 0:
                            _broadcast({"type":"paused"})
                            STATE.step_event.clear()
                            STATE.step_event.wait()
                    else:
                        _broadcast({"type":"paused"})
                        STATE.step_event.clear()
                        STATE.step_event.wait()
        return _trace
    return _trace

def run_user(path, argv):
    """사용자 스크립트 실행(별도 스레드)"""
    global TARGET_PATH
    STATE.line_count = 0
    TARGET_PATH = os.path.abspath(path)
    STATE.pause_mode = False
    STATE.pending_steps = 0
    STATE.stop_flag = False
    STATE.step_event.set()
    script_msg = {"type":"script", "path": path}
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as fh:
            script_msg["source"] = fh.read()
    except Exception as exc:
        script_msg["error"] = str(exc)
    _broadcast(script_msg)
    tracer = make_trace()
    sys.settrace(tracer)
    threading.settrace(tracer)  # 새 스레드 추적
    g = {"__name__":"__main__", "__file__":path}
    sys.argv = [path] + argv
    try:
        runpy.run_path(path, run_name="__main__")  # 원본 그대로 실행
    except SystemExit:
        pass
    except Exception:
        _broadcast({"type":"error","error":traceback.format_exc()})
    finally:
        sys.settrace(None); threading.settrace(None)
        _broadcast({"type":"done"})     # 실행 종료 알림

# ====== HTTP(SSE) ======
HTML = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8"/>
<title>Python 실시간 시각화</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<style>
:root{color-scheme:dark}
*{box-sizing:border-box;margin:0;padding:0}
body{margin:0;font-family:"Segoe UI",system-ui,-apple-system,BlinkMacSystemFont,"Noto Sans KR",sans-serif;background:#0b0f17;color:#d7defc;height:100vh;display:grid;grid-template-rows:64px 1fr}
header{display:flex;align-items:center;justify-content:space-between;padding:0 24px;background:rgba(10,15,28,0.85);backdrop-filter:blur(14px);border-bottom:1px solid #1f2734}
header .branding{display:flex;align-items:center;gap:12px;color:#9bb1ff;font-weight:600;letter-spacing:0.04em}
header .branding span.mark{display:flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:9px;background:linear-gradient(135deg,#243b6b,#3a5dab);color:#f8fafc;font-size:12px}
header .branding span.label{font-size:13px;color:#cdd6f8;letter-spacing:0.02em}
header .controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
button{cursor:pointer;border:none;border-radius:10px;padding:8px 16px;font-size:13px;font-weight:600;letter-spacing:0.02em;background:linear-gradient(135deg,#1f2a44,#23345c);color:#e2e8f0;border:1px solid #2f3e62;transition:transform .1s ease,box-shadow .2s ease,background .2s ease}
button:hover{background:linear-gradient(135deg,#26355a,#2e4473);box-shadow:0 10px 25px rgba(17,24,39,0.45)}
button:active{transform:scale(.97)}
button.attn{animation:pulse 1.2s ease-in-out infinite alternate;background:linear-gradient(135deg,#2f3f65,#3e58a0)}
button.active{box-shadow:0 0 0 2px rgba(96,165,250,0.6)}
@keyframes pulse{to{box-shadow:0 0 0 6px rgba(59,130,246,0)}}
label{display:flex;align-items:center;gap:8px;font-size:12px;color:#9da9d9;background:rgba(30,41,68,0.6);padding:6px 12px;border-radius:999px;border:1px solid rgba(148,163,184,0.18)}
input[type="number"]{background:transparent;border:none;color:#e2e8f0;font-size:12px;width:90px;text-align:right}
input[type="number"]:focus{outline:none}
.stateTag{display:flex;align-items:center;gap:8px;font-size:13px;padding:6px 14px;border-radius:999px;border:1px solid rgba(148,163,184,0.22);background:rgba(148,163,184,0.16);color:#cbd5f5}
.stateTag.run{border-color:rgba(74,222,128,0.45);background:rgba(74,222,128,0.12);color:#bbf7d0}
.stateTag.stop{border-color:rgba(248,113,113,0.45);background:rgba(248,113,113,0.12);color:#fecaca}
.stateTag.wait{border-color:rgba(148,163,184,0.32);background:rgba(148,163,184,0.14);color:#cbd5f5}
.stateDot{width:8px;height:8px;border-radius:50%;background:#94a3b8}
.stateTag.run .stateDot{background:#4ade80}
.stateTag.stop .stateDot{background:#f87171}
main{display:grid;grid-template-columns:minmax(440px,55%) minmax(480px,1fr);gap:20px;padding:20px 24px 24px 24px;height:100%;min-height:0}
#leftPane{display:flex;flex-direction:column;min-height:0}
#rightPane{display:flex;flex-direction:column;gap:18px;min-height:0}
.panel{background:#111b2b;border:1px solid #1b2439;border-radius:16px;padding:18px;display:flex;flex-direction:column;gap:14px;box-shadow:0 24px 45px rgba(0,6,26,0.4)}
.panelTitle{font-size:13px;font-weight:700;letter-spacing:0.08em;color:#f8fafc;text-transform:uppercase}
.panelSub{font-size:12px;color:#8fa0c9;margin-top:4px}
.panelHead{display:flex;align-items:flex-start;justify-content:space-between;gap:14px}
.pill{font-size:12px;padding:4px 10px;border-radius:999px;border:1px solid rgba(148,163,184,0.2);color:#cbd5f5;background:rgba(148,163,184,0.16)}
.panelBody{font-family:"Fira Code",Consolas,"Courier New",monospace;font-size:12.5px;line-height:1.6;color:#cfd9ff;background:#0f172a;border:1px solid #1b2439;border-radius:12px;padding:12px 14px;white-space:pre-wrap;overflow:auto;max-height:260px}
.panelBody::-webkit-scrollbar,#code::-webkit-scrollbar{width:10px}
.panelBody::-webkit-scrollbar-thumb,#code::-webkit-scrollbar-thumb{background:#1f2f4d;border-radius:10px}
.panelBody::-webkit-scrollbar-track,#code::-webkit-scrollbar-track{background:transparent}
#diagramPanel{flex:1;min-height:0}
#graph{width:100%;height:100%;min-height:420px;background:#0d1526;border:1px solid #1b2439;border-radius:14px}
#graph text{font-size:11px;fill:#d4ddff}
.nodeCircle{fill:#152746;stroke:#385d9b;stroke-width:1.2}
.nodeFunc{fill:#12305b}
.nodeVar{fill:#1a2f52}
.nodeActive{stroke:#93c5fd;stroke-width:2.2}
.edge{stroke:rgba(148,163,184,0.28);stroke-width:1.2}
.pulse{fill:#60a5fa;opacity:0}
.codePanel{flex:1;min-height:0}
#code{flex:1;background:#0f172a;border:1px solid #1b2439;border-radius:14px;padding:12px 0;overflow:auto;font-family:"Fira Code",Consolas,"Courier New",monospace;font-size:13px;color:#d4ddff}
.codeLine{display:flex;align-items:flex-start;gap:16px;padding:0 20px;position:relative;scroll-margin:180px}
.codeLine::after{content:"";position:absolute;left:12px;right:12px;bottom:-1px;height:1px;background:rgba(30,41,59,0.55)}
.codeLine:last-child::after{display:none}
.codeNo{width:48px;text-align:right;color:#526180;flex-shrink:0}
.codeText{white-space:pre;color:#cbd5ff}
.codeLine.active{background:linear-gradient(90deg,rgba(59,130,246,0.18),rgba(59,130,246,0))}
.codeLine.active .codeNo{color:#93c5fd}
.codeBadge{margin-left:auto;background:rgba(99,102,241,0.18);border:1px solid rgba(99,102,241,0.38);color:#c7d2ff;border-radius:999px;font-size:11px;padding:2px 10px}
.codeBadge + .codeBadge{margin-left:6px}
.emptyMessage{padding:20px 24px;color:#94a3b8;font-size:13px}
#errBox{border-color:#f97316;background:rgba(251,191,36,0.12);color:#fde68a}
#err{font-family:"Fira Code",Consolas,monospace;font-size:12.5px;white-space:pre-wrap}
@media (max-width:1320px){main{grid-template-columns:1fr;overflow:auto}#diagramPanel{min-height:360px}#rightPane{min-height:auto}}
</style>
</head>
<body>
<header>
  <div class="branding"><span class="mark">Δ</span><span class="label">덕현이가 말아주는 코드</span></div>
  <div class="controls">
    <button id="back">◀ 이전</button>
    <button id="forward">다음 ▶</button>
    <button id="pause">일시정지</button>
    <label>속도(ms)<input id="delay" type="number" value="5000"></label>
    <div id="stateTag" class="stateTag wait"><span id="stateDot" class="stateDot"></span><span id="state" class="stateText">연결 대기</span></div>
  </div>
</header>
<main>
  <section id="leftPane">
    <div class="panel" id="diagramPanel">
      <div class="panelHead">
        <div>
          <div class="panelTitle">Execution Diagram</div>
          <div class="panelSub">함수와 변수 사이의 흐름</div>
        </div>
        <span id="lineInfo" class="pill">라인 -</span>
      </div>
      <svg id="graph" viewBox="0 0 960 720" preserveAspectRatio="xMidYMid meet"></svg>
    </div>
  </section>
  <section id="rightPane">
    <div class="panel codePanel">
      <div class="panelHead">
        <div>
          <div class="panelTitle">Source Trace</div>
          <div id="scriptPath" class="panelSub"></div>
        </div>
      </div>
      <div id="code"><div class="emptyMessage">브라우저 연결을 기다리는 중…</div></div>
    </div>
    <div class="panel" id="stackPanel">
      <div class="panelHead">
        <div>
          <div class="panelTitle">Call Stack</div>
          <div class="panelSub">최신 프레임이 맨 아래</div>
        </div>
      </div>
      <pre id="stack" class="panelBody"></pre>
    </div>
    <div class="panel" id="varsPanel">
      <div class="panelHead">
        <div>
          <div class="panelTitle">Local Variables</div>
          <div class="panelSub">변경된 항목은 ★ 표시</div>
        </div>
      </div>
      <pre id="vars" class="panelBody"></pre>
    </div>
    <div class="panel" id="errBox" style="display:none">
      <div class="panelHead">
        <div class="panelTitle">Runtime Error</div>
      </div>
      <pre id="err"></pre>
    </div>
  </section>
</main>
<script>
const backBtn=document.getElementById('back');
const forwardBtn=document.getElementById('forward');
const pauseBtn=document.getElementById('pause');
const delayIn=document.getElementById('delay');
const stateEl=document.getElementById('state');
const stateTag=document.getElementById('stateTag');
const stateDot=document.getElementById('stateDot');
const graph=document.getElementById('graph');
const stackEl=document.getElementById('stack');
const varsEl=document.getElementById('vars');
const errBox=document.getElementById('errBox');
const errEl=document.getElementById('err');
const lineInfo=document.getElementById('lineInfo');
const codeView=document.getElementById('code');
const scriptPathEl=document.getElementById('scriptPath');
const LINE_BREAK='\\n';

let G={nodes:new Map(),edges:new Map()};
let svg={gEdges:null,gPulses:null,gNodes:null};
let layoutOrder={func:0,var:0};
let activeFuncId=null;
let PULSE_DUR=5000;
let codeLineMap=new Map();
let activeLineEl=null;
let badgeLineEl=null;
let isPaused=false;
let followLive=true;
let eventLog=[];
let currentIndex=-1;

function setPauseUi(active){
  isPaused=!!active;
  pauseBtn.textContent=active?'재생':'일시정지';
  if(active){ pauseBtn.classList.add('active'); }
  else{ pauseBtn.classList.remove('active'); }
}

function setState(text,cls){
  stateEl.textContent=text;
  stateTag.className='stateTag '+cls;
  if(cls==='run'){ stateDot.style.background='#4ade80'; }
  else if(cls==='stop'){ stateDot.style.background='#f87171'; }
  else{ stateDot.style.background='#94a3b8'; }
}

function showError(msg){ errEl.textContent=msg; errBox.style.display='block'; }
function clearError(){ errEl.textContent=''; errBox.style.display='none'; }

function resetSVG(){
  while(graph.firstChild) graph.removeChild(graph.firstChild);
  const ns='http://www.w3.org/2000/svg';
  svg.gEdges=document.createElementNS(ns,'g');
  svg.gPulses=document.createElementNS(ns,'g');
  svg.gNodes=document.createElementNS(ns,'g');
  graph.appendChild(svg.gEdges);
  graph.appendChild(svg.gPulses);
  graph.appendChild(svg.gNodes);
}
function resetGraph(){
  G={nodes:new Map(),edges:new Map()};
  layoutOrder={func:0,var:0};
  activeFuncId=null;
  resetSVG();
}
function ensureNode(id,kind,label){
  if(!G.nodes.has(id)){
    const FUNC_PER_COL=6;
    const VAR_PER_COL=9;
    let node;
    if(kind==='func'){
      const idx=layoutOrder.func++;
      const col=Math.floor(idx/FUNC_PER_COL);
      const row=idx%FUNC_PER_COL;
      node={id,kind,label,x:240+col*150,y:140+row*110,active:false,index:idx};
    } else {
      const idx=layoutOrder.var++;
      const col=Math.floor(idx/VAR_PER_COL);
      const row=idx%VAR_PER_COL;
      node={id,kind,label,x:540+col*160,y:100+row*80,active:false,index:idx};
    }
    G.nodes.set(id,node);
  }
  const n=G.nodes.get(id);
  n.label=label;
  return n;
}
function drawAllNodes(){
  const ns='http://www.w3.org/2000/svg';
  svg.gNodes.innerHTML='';
  for(const n of G.nodes.values()){
    const g=document.createElementNS(ns,'g');
    const c=document.createElementNS(ns,'circle');
    c.setAttribute('cx',n.x);c.setAttribute('cy',n.y);
    c.setAttribute('r',n.kind==='func'?'28':'18');
    let cls='nodeCircle '+(n.kind==='func'?'nodeFunc':'nodeVar');
    if(n.active) cls+=' nodeActive';
    c.setAttribute('class',cls);
    const t=document.createElementNS(ns,'text');
    t.setAttribute('x',n.x);t.setAttribute('y',n.y+4);
    t.setAttribute('text-anchor','middle');
    t.textContent=n.label;
    g.appendChild(c);g.appendChild(t);
    svg.gNodes.appendChild(g);
  }
}
function ensureEdge(a,b,type){
  const k=a+'>'+b+':'+type;
  if(!G.edges.has(k)){
    const ns='http://www.w3.org/2000/svg';
    const e={a,b,type};
    const na=G.nodes.get(a), nb=G.nodes.get(b);
    if(!na||!nb) return;
    const ln=document.createElementNS(ns,'line');
    ln.setAttribute('x1',na.x);ln.setAttribute('y1',na.y);
    ln.setAttribute('x2',nb.x);ln.setAttribute('y2',nb.y);
    ln.setAttribute('class','edge');
    e._line=ln;svg.gEdges.appendChild(ln);
    const p=document.createElementNS(ns,'circle');
    p.setAttribute('r','5');p.setAttribute('class','pulse');
    e._pulse=p;svg.gPulses.appendChild(p);
    G.edges.set(k,e);
  }
  return G.edges.get(k);
}
function updateEdges(){
  for(const e of G.edges.values()){
    const na=G.nodes.get(e.a), nb=G.nodes.get(e.b);
    if(!na||!nb||!e._line) continue;
    e._line.setAttribute('x1',na.x);e._line.setAttribute('y1',na.y);
    e._line.setAttribute('x2',nb.x);e._line.setAttribute('y2',nb.y);
  }
}
function pulseEdge(e){
  const na=G.nodes.get(e.a), nb=G.nodes.get(e.b);
  if(!na||!nb||!e._pulse) return;
  e._pulse.style.opacity='1';
  const start=performance.now(),dur=Math.max(PULSE_DUR,800);
  (function loop(){
    const t=Math.min(1,(performance.now()-start)/dur);
    const x=na.x+(nb.x-na.x)*t,y=na.y+(nb.y-na.y)*t;
    e._pulse.setAttribute('cx',x);e._pulse.setAttribute('cy',y);
    if(t<1) requestAnimationFrame(loop); else e._pulse.style.opacity='0';
  })();
}
function setActiveFunction(id){
  if(activeFuncId && G.nodes.has(activeFuncId)){
    G.nodes.get(activeFuncId).active=false;
  }
  if(id && G.nodes.has(id)){
    G.nodes.get(id).active=true;
    activeFuncId=id;
  } else {
    activeFuncId=null;
  }
  drawAllNodes();
  updateEdges();
}
function renderStack(stack){
  if(!stack||!stack.length){ stackEl.textContent=''; return; }
  const rows=stack.map((s,i)=>(i===stack.length-1?'➤ ':'   ')+s);
  stackEl.textContent=rows.join(LINE_BREAK);
}
function renderVars(locals,changed){
  if(!locals){ varsEl.textContent=''; return; }
  const highlight=new Set(changed||[]);
  const rows=Object.entries(locals).slice(0,120).map(([k,v])=>(highlight.has(k)?'★ ':'  ')+k+': '+v);
  varsEl.textContent=rows.join(LINE_BREAK);
}
function renderSource(source){
  codeView.innerHTML='';
  codeLineMap=new Map();
  activeLineEl=null;
  badgeLineEl=null;
  if(!source){
    const empty=document.createElement('div');
    empty.className='emptyMessage';
    empty.textContent='소스를 불러오지 못했습니다.';
    codeView.appendChild(empty);
    return;
  }
  const lines=source.replace(/\r?\n/g,'\n').split('\n');
  const frag=document.createDocumentFragment();
  lines.forEach((line,idx)=>{
    const row=document.createElement('div');
    row.className='codeLine';
    const no=document.createElement('span');
    no.className='codeNo';
    no.textContent=String(idx+1).padStart(4,' ');
    const text=document.createElement('span');
    text.className='codeText';
    text.textContent=line.replace(/	/g,'    ');
    row.dataset.line=idx+1;
    row.appendChild(no);
    row.appendChild(text);
    frag.appendChild(row);
    codeLineMap.set(idx+1,row);
  });
  codeView.appendChild(frag);
}
function clearActiveLine(){
  if(activeLineEl){
    activeLineEl.classList.remove('active');
    activeLineEl=null;
  }
  if(badgeLineEl){
    badgeLineEl.querySelectorAll('.codeBadge').forEach(b=>b.remove());
    badgeLineEl=null;
  }
}
function highlightLine(ln,locals,changed,options){
  const replay=options&&options.replay;
  const row=codeLineMap.get(ln);
  if(!row) return;
  if(activeLineEl && activeLineEl!==row){
    activeLineEl.classList.remove('active');
    if(activeLineEl===badgeLineEl){
      activeLineEl.querySelectorAll('.codeBadge').forEach(b=>b.remove());
      badgeLineEl=null;
    }
  }
  row.classList.add('active');
  activeLineEl=row;
  lineInfo.textContent='라인 '+ln;
  row.querySelectorAll('.codeBadge').forEach(b=>b.remove());
  if(changed && locals){
    const badgeLimit=3;
    let appended=0;
    changed.forEach(k=>{
      if(appended>=badgeLimit) return;
      const value=locals[k];
      if(value===undefined) return;
      const badge=document.createElement('span');
      badge.className='codeBadge';
      badge.textContent=`${k} = ${value}`;
      row.appendChild(badge);
      appended+=1;
    });
    if(appended>0) badgeLineEl=row;
  }
  row.scrollIntoView({block:'center',behavior:replay?'instant':'smooth'});
}

function resetForNewRun(){
  eventLog=[];
  currentIndex=-1;
  followLive=true;
  setPauseUi(false);
  resetGraph();
  renderStack([]);
  varsEl.textContent='';
  clearActiveLine();
  lineInfo.textContent='라인 -';
  clearError();
  codeView.innerHTML='<div class=\"emptyMessage\">실행 중인 스크립트를 기다리는 중…</div>';
  scriptPathEl.textContent='';
}

function processEvent(m,{replay=false}={}){
  if(m.type==='call'){
    const caller=(m.stack||[]).slice(-2,-1)[0]||'<module>';
    const a='f:'+caller,b='f:'+m.func;
    ensureNode(a,'func',caller);
    ensureNode(b,'func',m.func);
    drawAllNodes();
    updateEdges();
    const e=ensureEdge(a,b,'call');
    if(e && !replay) pulseEdge(e);
    setActiveFunction(b);
    renderStack(m.stack);
    return;
  }
  if(m.type==='return'){
    const current=(m.stack||[]).slice(-1)[0]||'<module>';
    setActiveFunction('f:'+current);
    renderStack(m.stack);
    return;
  }
  if(m.type==='trace'){
    renderVars(m.locals,m.var_changed);
    renderStack(m.stack);
    const fname=m.func||'<module>';
    const funcId='f:'+fname;
    ensureNode(funcId,'func',fname);
    drawAllNodes();
    updateEdges();
    setActiveFunction(funcId);
    (m.var_changed||[]).forEach(k=>{
      const id='v:'+k;
      ensureNode(id,'var',k);
      drawAllNodes();
      updateEdges();
      const e=ensureEdge(funcId,id,'write');
      if(e && !replay) pulseEdge(e);
    });
    if(m.line){
      highlightLine(m.line,m.locals,m.var_changed,{replay});
    }
    return;
  }
}

function replayTo(index){
  if(eventLog.length===0){
    resetGraph();
    renderStack([]);
    varsEl.textContent='';
    clearActiveLine();
    lineInfo.textContent='라인 -';
    currentIndex=-1;
    return;
  }
  index=Math.max(0,Math.min(index,eventLog.length-1));
  resetGraph();
  renderStack([]);
  varsEl.textContent='';
  clearActiveLine();
  lineInfo.textContent='라인 -';
  for(let i=0;i<=index;i++){
    processEvent(eventLog[i],{replay:true});
  }
  currentIndex=index;
}

let es=null;
function connect(){
  es=new EventSource('/events');
  setState('연결 시도중…','wait');

  es.onopen=()=>{ setState('연결됨 · 대기','wait'); clearError(); };
  es.onerror=()=>{ setState('연결 오류(자동 재시도)','wait'); };

  es.onmessage=(ev)=>{
    if(!ev.data) return;
    const m=JSON.parse(ev.data);

    if(m.type==='hello'){
      resetForNewRun();
      return;
    }
    if(m.type==='script'){
      scriptPathEl.textContent=m.path||'';
      renderSource(m.source||'');
      if(m.error){
        const warn=document.createElement('div');
        warn.className='emptyMessage';
        warn.textContent='소스 로딩 오류: '+m.error;
        codeView.appendChild(warn);
      }
      return;
    }
    if(m.type==='pause-state'){
      setPauseUi(!!m.active);
      if(m.active){
        followLive=false;
        setState('일시정지','wait');
      } else {
        setState('실행중','run');
        followLive=true;
        if(eventLog.length){
          replayTo(eventLog.length-1);
          currentIndex=eventLog.length-1;
        }
      }
      return;
    }
    if(m.type==='paused'){
      setPauseUi(true);
      followLive=false;
      setState('일시정지','wait');
      return;
    }
    if(m.type==='error'){
      showError(m.error);
      setState('에러','stop');
      setPauseUi(false);
      return;
    }
    if(m.type==='halt'){
      showError('[HALT] 라인 한도 도달');
      setState('정지됨','stop');
      setPauseUi(false);
      return;
    }
    if(m.type==='done'){
      setState('정지됨','stop');
      setPauseUi(false);
      followLive=true;
      return;
    }

    if(m.type==='call' || m.type==='return' || m.type==='trace'){
      eventLog.push(m);
      if(followLive){
        processEvent(m,{replay:false});
        currentIndex=eventLog.length-1;
      }
      if(m.type==='trace'){
        setState('실행중','run');
      }
    }
  };
}

function post(path,body){
  return fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body||{})});
}
backBtn.onclick=()=>{
  if(eventLog.length===0) return;
  post('/ctrl',{type:'pause-on'});
  followLive=false;
  const target=currentIndex<=0?eventLog.length-1:currentIndex-1;
  replayTo(target);
};
forwardBtn.onclick=()=>{
  if(eventLog.length===0) return;
  post('/ctrl',{type:'pause-on'});
  followLive=false;
  const target=currentIndex<0?0:Math.min(eventLog.length-1,currentIndex+1);
  replayTo(target);
};
pauseBtn.onclick=()=>{
  post('/ctrl',{type:'pause-toggle'});
};
delayIn.onchange=()=>{
  const ms=Number(delayIn.value)||0;
  PULSE_DUR=Math.max(ms,800);
  post('/ctrl',{type:'set-delay',ms});
};

resetSVG();
connect();
</script>
</body></html>
"""

class Handler(BaseHTTPRequestHandler):
    def _set_headers(self, code=200, content_type='text/html; charset=utf-8', extra=None):
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Cache-Control', 'no-cache')
        if extra:
            for k,v in (extra or {}).items():
                self.send_header(k,v)
        self.end_headers()

    def log_message(self, fmt, *args):
        # 조용히
        pass

    def do_GET(self):
        if self.path == '/' or self.path.startswith('/index'):
            self._set_headers()
            self.wfile.write(HTML.encode('utf-8'))
            return

        if self.path.startswith('/events'):
            self._set_headers(200, 'text/event-stream', {'Connection':'keep-alive'})
            # 구독 등록
            q = queue.Queue()
            with SUBS_LOCK:
                SUBS.append(q)
            # hello 전송
            self.wfile.write(b'data: {"type":"hello"}\n\n')
            self.wfile.flush()
            try:
                while True:
                    msg = q.get()  # blocking
                    out = f"data: {msg}\n\n".encode('utf-8')
                    self.wfile.write(out)
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                with SUBS_LOCK:
                    if q in SUBS: SUBS.remove(q)
            return

        # 404
        self._set_headers(404, 'text/plain; charset=utf-8')
        self.wfile.write(b'Not Found')

    def do_POST(self):
        if not self.path.startswith('/ctrl'):
            self._set_headers(404, 'text/plain; charset=utf-8')
            self.wfile.write(b'Not Found')
            return

        try:
            ln = int(self.headers.get('Content-Length','0'))
            data = self.rfile.read(ln) if ln>0 else b'{}'
            m = json.loads(data.decode('utf-8'))
        except Exception:
            self._set_headers(400, 'text/plain; charset=utf-8')
            self.wfile.write(b'Bad JSON')
            return

        t = m.get('type')
        if t == 'set-delay':
            ms = int(m.get('ms') or 0)
            STATE.delay = max(0, ms)/1000.0
        elif t == 'pause-toggle':
            STATE.pause_mode = not STATE.pause_mode
            if not STATE.pause_mode:
                STATE.pending_steps = 0
                STATE.step_event.set()
            _broadcast({"type":"pause-state","active":STATE.pause_mode})
        elif t == 'pause-on':
            if not STATE.pause_mode:
                STATE.pause_mode = True
                STATE.pending_steps = 0
                _broadcast({"type":"pause-state","active":True})
        elif t == 'step-once':
            count = int(m.get('count') or 1)
            STATE.pause_mode = True
            STATE.pending_steps += max(1, count)
            STATE.step_event.set()
            _broadcast({"type":"pause-state","active":True})
        elif t == 'stop':
            STATE.stop_flag = True
            STATE.step_event.set()

        self._set_headers(204, 'text/plain; charset=utf-8')

def wait_for_client(timeout=15):
    """브라우저가 /events 구독할 때까지 대기 (최대 timeout초)"""
    t0 = time.time()
    while time.time() - t0 < timeout:
        with SUBS_LOCK:
            if SUBS:
                return True
        time.sleep(0.05)
    return False

def serve_and_run(path, argv):
    # 서버 시작 (임의 포트)
    httpd = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    host, port = httpd.server_address
    url = f'http://{host}:{port}/'
    print(f'[visualize] open  {url}')
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    # 브라우저 오픈
    webbrowser.open(url)

    # ✨ 브라우저(SSE) 연결을 기다렸다가 실행 시작
    if not wait_for_client(timeout=30):
        print('[visualize] 경고: 30초 내 브라우저 연결 없음 → 실행을 강행합니다.')

    # 사용자 코드 실행 스레드
    t = threading.Thread(target=run_user, args=(path, argv), daemon=True)
    t.start()

    try:
        while t.is_alive():
            time.sleep(0.05)
    finally:
        httpd.shutdown()

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('script', help='실행할 파이썬 파일 경로')
    ap.add_argument('script_args', nargs=argparse.REMAINDER)
    return ap.parse_args()

if __name__ == '__main__':
    args = parse_args()
    # 초기 상태
    STATE.stepping  = False
    STATE.delay     = 5.0    # ✨ 기본 5000ms/줄 (아주 느리게)
    STATE.max_lines = 20000
    STATE.stop_flag = False
    STATE.step_event.set()
    serve_and_run(os.path.abspath(args.script), args.script_args or [])
