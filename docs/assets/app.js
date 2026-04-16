/* Global Market Orchestrator dashboard */

const INDEX_URL = "reports/index.json";
const REPORT_URL = (d) => `reports/${d}.json`;
const RISK_EMOJI = {"Risk-On":"🟢","Neutral":"🟡","Risk-Off":"🔴"};
const HEAT_CLS = {hot:"heat-hot",warm:"heat-warm",cool:"heat-cool",neutral:"heat-neutral","n/a":"heat-na"};

function $(s){return document.querySelector(s)}
function el(tag,a={},...ch){
  const e=document.createElement(tag);
  Object.entries(a).forEach(([k,v])=>{if(k==="class")e.className=v;else e.setAttribute(k,v)});
  ch.flat().forEach(c=>{if(c!=null)e.appendChild(typeof c==="string"?document.createTextNode(c):c)});
  return e;
}
async function loadJSON(u){const r=await fetch(u,{cache:"no-cache"});if(!r.ok)throw new Error(`${u}→${r.status}`);return r.json()}

/* ─── Dashboard ─── */
async function renderDashboard(){
  let index;
  try{index=await loadJSON(INDEX_URL)}catch(e){$("#hero-tagline").textContent="No reports yet.";return}
  if(!index||!index.length){$("#hero-tagline").textContent="No reports yet.";return}
  const latest=index[0];
  $("#hero-tagline").textContent=`Latest: ${latest.date}`;
  try{
    const r=await loadJSON(REPORT_URL(latest.date));
    renderPosture(r.cross_analysis);
    renderSignals(r.cross_analysis);
    renderMarketsGrid(r.agent_reports);
    renderHeatmap(r.cross_analysis.sector_heatmap);
    renderInsight(r.cross_analysis,r.narrative);
  }catch(e){console.warn(e)}
  renderHistory(index);
}

function renderPosture(ca){
  if(!ca)return;
  $("#posture-card").hidden=false;
  const em=RISK_EMOJI[ca.global_risk_posture]||"⚪";
  $("#posture-badge").textContent=`${em} ${ca.global_risk_posture}`;
  $("#flow-text").textContent=ca.capital_flow_direction||"";
}

function renderSignals(ca){
  if(!ca||!ca.cross_market_signals||!ca.cross_market_signals.length)return;
  $("#signals-card").hidden=false;
  const ul=$("#signals-list");ul.innerHTML="";
  ca.cross_market_signals.forEach(s=>{
    const mkts=s.markets_involved?` [${s.markets_involved.join(", ")}]`:"";
    ul.appendChild(el("li",{},s.signal+mkts));
  });
}

function renderMarketsGrid(agents){
  if(!agents||!agents.length)return;
  $("#markets-card").hidden=false;
  const grid=$("#markets-grid");grid.innerHTML="";
  agents.forEach(ar=>{
    const g=ar.top_gainers&&ar.top_gainers[0];
    const card=el("div",{class:"market-card"},
      el("div",{},
        el("span",{class:"emoji"},ar.agent_emoji||"")," ",
        el("span",{class:"label"},ar.agent_label||ar.agent_key),
        ar.is_stale?el("span",{class:"stale"}," ⏳stale"):null
      ),
      g?el("div",{},
        el("span",{class:"name-sub"},g.name||g.identifier)," ",
        el("span",{class:"pct"},`+${g.change_pct.toFixed(1)}%`)
      ):el("div",{class:"name-sub"},"no data"),
      ar.dashboard_url?el("div",{class:"link"},el("a",{href:ar.dashboard_url,target:"_blank"},"→ detail")):null
    );
    grid.appendChild(card);
  });
}

function renderHeatmap(heatmap){
  if(!heatmap||!heatmap.length)return;
  $("#heatmap-card").hidden=false;
  const t=$("#heatmap-table");t.innerHTML="";
  const keys=["crypto","kospi","sp500","nasdaq","dow30"];
  const labels=["Crypto","KOSPI","S&P500","NDQ100","Dow30"];
  const hdr=el("tr",{},el("th",{},"Sector"),...labels.map(l=>el("th",{},l)));
  t.appendChild(el("thead",{},hdr));
  const tbody=el("tbody");
  heatmap.forEach(row=>{
    const tr=el("tr",{},el("td",{},row.sector));
    keys.forEach(k=>{
      const v=row[k]||"n/a";
      tr.appendChild(el("td",{class:HEAT_CLS[v]||"heat-na"},v));
    });
    tbody.appendChild(tr);
  });
  t.appendChild(tbody);
}

function renderInsight(ca,narr){
  if(!ca)return;
  $("#insight-card").hidden=false;
  $("#insight-text").textContent=ca.global_insight||"";
  if(narr&&narr.positioning_advice){
    $("#positioning-text").textContent=narr.positioning_advice;
  }
}

function renderHistory(index){
  const ul=$("#history-list");ul.innerHTML="";
  index.forEach(e=>{
    const em=RISK_EMOJI[e.risk_posture]||"⚪";
    const a=el("a",{href:`report.html?date=${e.date}`},
      el("span",{class:"date"},e.date),
      el("span",{class:"badge"},em+" "+( e.risk_posture||"")),
      e.narrative_tagline||"report"
    );
    ul.appendChild(el("li",{},a));
  });
}

/* ─── Report page ─── */
async function renderReportPage(){
  const params=new URLSearchParams(window.location.search);
  let date=params.get("date");
  let index=[];
  try{index=await loadJSON(INDEX_URL)}catch(_){}
  if(!date&&index.length)date=index[0].date;
  if(!date){$("#report-title").textContent="No report";return}

  $("#report-title").textContent=`Global Report — ${date}`;
  document.title=`Global Report · ${date}`;

  let r;
  try{r=await loadJSON(REPORT_URL(date))}catch(e){
    $("#report-title").textContent=`Report ${date} not found`;return;
  }

  const ca=r.cross_analysis||{};
  const narr=r.narrative||{};

  // Posture
  renderPosture(ca);

  // Signals
  renderSignals(ca);

  // Divergences
  if(ca.divergences&&ca.divergences.length){
    const dc=$("#divergence-card");if(dc){dc.hidden=false;
    const ul=$("#divergence-list");ul.innerHTML="";
    ca.divergences.forEach(d=>ul.appendChild(el("li",{},d)));}
  }

  // Markets detail
  const md=$("#markets-detail");
  if(md&&r.agent_reports){md.innerHTML="";
    r.agent_reports.forEach(ar=>{
      const card=el("div",{class:"analysis"});
      card.appendChild(el("h3",{},`${ar.agent_emoji} ${ar.agent_label}`,
        ar.is_stale?el("span",{class:"stale"}," ⏳ stale"):null));
      if(ar.narrative&&ar.narrative.current_narrative)
        card.appendChild(el("p",{},ar.narrative.current_narrative));
      if(ar.top_gainers&&ar.top_gainers.length){
        const ul=el("ul");
        ar.top_gainers.forEach(g=>ul.appendChild(el("li",{},
          `${g.name} (${g.identifier}) +${g.change_pct.toFixed(1)}%`)));
        card.appendChild(ul);
      }
      if(ar.dashboard_url)
        card.appendChild(el("p",{},el("a",{href:ar.dashboard_url,target:"_blank"},"→ Full detail report")));
      md.appendChild(card);
    });
  }

  // Heatmap
  renderHeatmap(ca.sector_heatmap);

  // Narrative
  const nc=$("#narrative-card");
  if(nc&&(narr.macro_regime||narr.flow_summary)){
    nc.hidden=false;
    const mt=$("#macro-text");if(mt)mt.textContent=narr.macro_regime||"";
    const ft=$("#narr-flow-text");if(ft)ft.textContent=narr.flow_summary||"";
    const wt=$("#wow-text");if(wt)wt.textContent=narr.week_over_week||"";
    if(narr.theme_convergence&&narr.theme_convergence.length){
      const d=$("#convergence-div");if(d){d.hidden=false;
      const ul=$("#convergence-list");ul.innerHTML="";
      narr.theme_convergence.forEach(t=>ul.appendChild(el("li",{},t)));}
    }
    if(narr.theme_divergence&&narr.theme_divergence.length){
      const d=$("#divergence-theme-div");if(d){d.hidden=false;
      const ul=$("#divergence-theme-list");ul.innerHTML="";
      narr.theme_divergence.forEach(t=>ul.appendChild(el("li",{},t)));}
    }
    const pt=$("#positioning-text");if(pt)pt.textContent=narr.positioning_advice||"";
  }

  // Insight
  if(ca.global_insight){
    $("#insight-card").hidden=false;
    $("#insight-text").textContent=ca.global_insight;
  }

  // Nav
  const dates=index.map(e=>e.date);
  const idx=dates.indexOf(date);
  const pb=$("#prev-btn"),nb=$("#next-btn");
  const prev=idx>=0&&idx<dates.length-1?dates[idx+1]:null;
  const next=idx>0?dates[idx-1]:null;
  if(prev)pb.onclick=()=>{window.location.search=`?date=${prev}`};else pb.disabled=true;
  if(next)nb.onclick=()=>{window.location.search=`?date=${next}`};else nb.disabled=true;
}

window.renderReportPage=renderReportPage;
if(document.getElementById("history-list")&&!document.getElementById("markets-detail")){
  renderDashboard();
}
