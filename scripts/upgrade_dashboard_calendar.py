"""Upgrade both dashboard copies to the curated Network calendar UI."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(r"C:\Users\MatthiasLavenant\Downloads")
FEED = ROOT / "miami-network-feed" / "docs" / "events.json"
TARGETS = [
    ROOT / "today-dashboard-with-network.html",
    ROOT / "today-dashboard (6).html",
]

CSS = r"""  .net-status{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--paper-dim);margin:-6px 0 14px;}
  .net-status.stale{color:var(--amber);}
  .net-status.err{color:var(--clay);}
  .net-intro{font-size:12.5px;color:var(--paper-dim);line-height:1.55;margin:-8px 0 15px;max-width:760px;}
  .net-filters{display:flex;flex-direction:column;gap:9px;margin-bottom:15px;}
  .net-filter-row{display:flex;gap:7px;overflow-x:auto;padding-bottom:2px;scrollbar-width:none;}
  .net-filter-row::-webkit-scrollbar{display:none;}
  .net-chip{font-family:'JetBrains Mono',monospace;font-size:10.5px;padding:7px 11px;border-radius:20px;border:1px solid var(--line);color:var(--paper-dim);white-space:nowrap;cursor:pointer;background:var(--bg-card);}
  .net-chip.active{background:var(--amber);color:var(--bg);border-color:var(--amber);}
  .net-chip.ghost.active{background:var(--violet);border-color:var(--violet);color:var(--bg);}
  .net-toolbar{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:12px;flex-wrap:wrap;}
  .net-count{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--paper-dim);}
  .net-refresh{background:var(--bg-card);border:1px solid var(--line);color:var(--paper);border-radius:7px;font-size:11px;font-family:'JetBrains Mono',monospace;padding:7px 12px;cursor:pointer;}
  .net-refresh:disabled{opacity:0.5;cursor:not-allowed;}
  .net-calendar{background:var(--bg-card);border:1px solid var(--line);border-radius:12px;padding:14px;margin-bottom:16px;}
  .net-cal-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:12px;}
  .net-cal-title{font-family:'Archivo Narrow',sans-serif;font-size:20px;font-weight:700;}
  .net-cal-nav{display:flex;gap:6px;}
  .net-cal-nav button{width:32px;height:30px;border:1px solid var(--line);border-radius:7px;background:var(--bg-raised);color:var(--paper);cursor:pointer;font-size:16px;}
  .net-cal-weekdays,.net-cal-grid{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:5px;}
  .net-cal-weekdays{margin-bottom:5px;}
  .net-cal-weekdays span{text-align:center;font-family:'JetBrains Mono',monospace;font-size:9px;color:var(--paper-dim);text-transform:uppercase;}
  .net-cal-cell{min-height:82px;border:1px solid var(--line);border-radius:7px;background:var(--bg-raised);padding:6px;cursor:pointer;overflow:hidden;text-align:left;color:var(--paper);}
  .net-cal-cell.blank{visibility:hidden;pointer-events:none;}
  .net-cal-cell.today{border-color:var(--amber-dim);}
  .net-cal-cell.selected{background:#2a241e;border-color:var(--amber);}
  .net-cal-day{display:flex;justify-content:space-between;align-items:center;font-family:'JetBrains Mono',monospace;font-size:10px;margin-bottom:5px;}
  .net-cal-count{color:var(--amber);font-size:9px;}
  .net-cal-mini{display:block;font-size:9px;line-height:1.25;padding:3px 4px;margin-top:3px;border-left:3px solid var(--paper-dim);background:rgba(255,255,255,.025);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
  .net-cal-mini.hospitality{border-color:var(--amber);}
  .net-cal-mini.sports{border-color:var(--blue);}
  .net-cal-mini.real_estate{border-color:var(--sage);}
  .net-cal-mini.culinary{border-color:var(--clay);}
  .net-cal-mini.art_fashion{border-color:var(--violet);}
  .net-cal-more{font-family:'JetBrains Mono',monospace;font-size:8.5px;color:var(--paper-dim);margin-top:3px;}
  .net-day-head{display:flex;justify-content:space-between;align-items:end;gap:10px;margin:4px 0 11px;}
  .net-day-title{font-family:'Archivo Narrow',sans-serif;font-size:20px;font-weight:700;}
  .net-day-sub{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--paper-dim);text-align:right;}
  .net-list{display:flex;flex-direction:column;gap:10px;}
  .net-card{background:var(--bg-card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;}
  .net-card.saved{border-color:var(--amber-dim);}
  .net-card-top{display:flex;justify-content:space-between;gap:10px;align-items:flex-start;margin-bottom:7px;}
  .net-when{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--amber);line-height:1.4;}
  .net-score{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--paper-dim);white-space:nowrap;}
  .net-source{display:inline-flex;align-items:center;gap:5px;font-family:'JetBrains Mono',monospace;font-size:9.5px;color:var(--amber);text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;}
  .net-source::before{content:'';width:5px;height:5px;border-radius:50%;background:var(--amber);}
  .net-title{font-size:15px;font-weight:600;line-height:1.35;margin-bottom:5px;}
  .net-title a:hover{color:var(--amber);}
  .net-meta{font-size:11.5px;color:var(--paper-dim);line-height:1.5;margin-bottom:8px;}
  .net-why{font-size:12px;color:var(--paper);line-height:1.5;margin-bottom:9px;}
  .net-access-tip{background:var(--bg-raised);border-left:3px solid var(--violet);border-radius:0 7px 7px 0;padding:9px 10px;margin:9px 0;font-size:11.5px;line-height:1.5;color:var(--paper-dim);}
  .net-access-tip b{display:block;color:var(--paper);font-size:10px;text-transform:uppercase;letter-spacing:.6px;margin-bottom:3px;}
  .net-tags{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:11px;}
  .net-tag{font-family:'JetBrains Mono',monospace;font-size:9px;text-transform:uppercase;letter-spacing:.35px;padding:3px 7px;border-radius:5px;background:var(--bg-raised);border:1px solid var(--line);color:var(--paper-dim);}
  .net-tag.access{color:var(--violet);border-color:#4a3d5c;}
  .net-tag.industry{color:var(--sage);}
  .net-actions{display:flex;gap:7px;flex-wrap:wrap;}
  .net-btn{background:var(--bg-raised);border:1px solid var(--line);color:var(--paper);border-radius:7px;font-size:11px;font-weight:500;padding:7px 10px;cursor:pointer;}
  .net-btn.primary{background:var(--amber);border-color:var(--amber);color:var(--bg);font-weight:600;}
  .net-btn.active-save{border-color:var(--amber);color:var(--amber);}
  .net-trail{margin-top:11px;padding-top:9px;border-top:1px solid var(--line);font-size:11px;color:var(--paper-dim);line-height:1.55;display:none;}
  .net-trail.open{display:block;}
  .net-trail b{color:var(--paper);font-weight:500;}
  .net-empty{text-align:center;padding:25px 12px;color:var(--paper-dim);font-size:13px;line-height:1.6;background:var(--bg-card);border:1px solid var(--line);border-radius:10px;}
  .net-directory{margin-top:22px;}
  .net-directory-title{font-family:'Archivo Narrow',sans-serif;font-size:20px;font-weight:700;margin-bottom:5px;}
  .net-directory-sub{font-size:11.5px;color:var(--paper-dim);line-height:1.5;margin-bottom:11px;}
  .net-directory-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;}
  .net-club{background:var(--bg-card);border:1px solid var(--line);border-radius:9px;padding:12px;}
  .net-club-name{font-size:13px;font-weight:600;margin-bottom:3px;}
  .net-club-type{font-family:'JetBrains Mono',monospace;font-size:9px;color:var(--violet);text-transform:uppercase;margin-bottom:7px;}
  .net-club-tip{font-size:11px;color:var(--paper-dim);line-height:1.45;margin-bottom:9px;}
  @media(max-width:620px){
    .net-calendar{padding:10px;}
    .net-cal-weekdays,.net-cal-grid{gap:3px;}
    .net-cal-cell{min-height:55px;padding:4px;}
    .net-cal-mini{height:4px;padding:0;font-size:0;border-left:0;border-radius:2px;background:var(--paper-dim);}
    .net-cal-mini.hospitality{background:var(--amber);}
    .net-cal-mini.sports{background:var(--blue);}
    .net-cal-mini.real_estate{background:var(--sage);}
    .net-cal-mini.culinary{background:var(--clay);}
    .net-cal-mini.art_fashion{background:var(--violet);}
    .net-directory-grid{grid-template-columns:1fr;}
  }"""

PANEL = r"""  <!-- ============ NETWORK PANEL ============ -->
  <div class="panel" id="panel-network">
    <div class="section-title">Network</div>
    <div class="net-intro">A selective calendar for Miami hospitality, sports, real estate, culinary, and art/fashion rooms worth entering.</div>
    <div class="net-status" id="netStatus">Loading Miami event feed…</div>

    <div class="net-filters">
      <div class="net-filter-row" id="netCatFilters">
        <button type="button" class="net-chip ghost active" data-cat="all">All industries</button>
        <button type="button" class="net-chip ghost" data-cat="hospitality">Hospitality</button>
        <button type="button" class="net-chip ghost" data-cat="sports">Sports</button>
        <button type="button" class="net-chip ghost" data-cat="real_estate">Real Estate</button>
        <button type="button" class="net-chip ghost" data-cat="culinary">Culinary</button>
        <button type="button" class="net-chip ghost" data-cat="art_fashion">Art / Fashion</button>
        <button type="button" class="net-chip ghost" data-cat="saved">Saved</button>
      </div>
      <div class="net-filter-row" id="netAccessFilters">
        <button type="button" class="net-chip active" data-access="all">Any access</button>
        <button type="button" class="net-chip" data-access="invitation-only">Invitation</button>
        <button type="button" class="net-chip" data-access="members">Members</button>
        <button type="button" class="net-chip" data-access="registration">RSVP</button>
        <button type="button" class="net-chip" data-access="public">Public</button>
      </div>
    </div>

    <div class="net-toolbar">
      <div class="net-count" id="netCount">—</div>
      <div>
        <button type="button" class="net-refresh" id="netSignalsBtn">Early signals</button>
        <button type="button" class="net-refresh" id="netRefreshBtn">Refresh sources</button>
      </div>
    </div>

    <div class="net-calendar">
      <div class="net-cal-head">
        <div class="net-cal-title" id="netCalTitle">—</div>
        <div class="net-cal-nav">
          <button type="button" id="netCalPrev" aria-label="Previous month">‹</button>
          <button type="button" id="netCalToday" aria-label="Current month">●</button>
          <button type="button" id="netCalNext" aria-label="Next month">›</button>
        </div>
      </div>
      <div class="net-cal-weekdays"><span>Sun</span><span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span></div>
      <div class="net-cal-grid" id="netCalGrid"></div>
    </div>

    <div class="net-day-head">
      <div class="net-day-title" id="netDayTitle">Select a date</div>
      <div class="net-day-sub" id="netDaySub">—</div>
    </div>
    <div class="net-list" id="netList"></div>

    <div class="net-directory" id="netDirectory">
      <div class="net-directory-title">Private club access</div>
      <div class="net-directory-sub">These calendars are not public. Use only the official membership and concierge routes below.</div>
      <div class="net-directory-grid" id="netDirectoryGrid"></div>
    </div>

    <div class="footnote">CURATED OFFICIAL SOURCES · GENERIC COMMUNITY EVENTS EXCLUDED · SAVE/DISMISS STAYS IN THIS BROWSER</div>
  </div>"""

JS = r"""/* =========================================================================
   NETWORK TAB — curated Miami industry calendar
   ========================================================================= */
let networkFeed = null;
let networkFeedMeta = { stale:false, error:null, loadedAt:null };
let networkCat = 'all';
let networkAccess = 'all';
let networkSelectedDay = '';
let networkCalendarMonth = null;
let networkSignalsMode = false;
let networkSaved = (()=>{ try{ return JSON.parse(localStorage.getItem(NETWORK_SAVED_KEY)) || {}; }catch(e){ return {}; } })();
let networkDismissed = (()=>{ try{ return JSON.parse(localStorage.getItem(NETWORK_DISMISSED_KEY)) || {}; }catch(e){ return {}; } })();

function saveNetworkPrefs(){
  localStorage.setItem(NETWORK_SAVED_KEY, JSON.stringify(networkSaved));
  localStorage.setItem(NETWORK_DISMISSED_KEY, JSON.stringify(networkDismissed));
}

function miamiNow(){
  return new Date(new Date().toLocaleString('en-US', { timeZone:'America/New_York' }));
}

function parseEventStart(ev){
  if(!ev || !ev.starts_at) return null;
  const d = new Date(ev.starts_at);
  return isNaN(d.getTime()) ? null : d;
}

function miamiLocalDate(d){
  return new Date(d.toLocaleString('en-US', { timeZone:'America/New_York' }));
}

function dayKeyFromDate(d){
  const local = miamiLocalDate(d);
  return `${local.getFullYear()}-${pad(local.getMonth()+1)}-${pad(local.getDate())}`;
}

function eventDayKey(ev){
  const d = parseEventStart(ev);
  return d ? dayKeyFromDate(d) : '';
}

function dateFromDayKey(key){
  const parts = String(key||'').split('-').map(Number);
  return parts.length===3 ? new Date(parts[0],parts[1]-1,parts[2],12,0,0) : miamiNow();
}

function formatEventWhen(ev){
  const d = parseEventStart(ev);
  if(!d) return 'Date TBA · early signal';
  const local = miamiLocalDate(d);
  if(ev.all_day) return 'All day';
  let h=local.getHours(), m=pad(local.getMinutes()), ap=h>=12?'PM':'AM';
  h=h%12; if(!h) h=12;
  return `${h}:${m} ${ap}`;
}

function leadLabel(ev){
  if(ev.lead_hours == null) return '';
  const h=Number(ev.lead_hours);
  if(h<0) return 'Late signal';
  if(h<24) return `Lead ${h}h`;
  return `Lead ${Math.round(h/24)}d`;
}

function eventIndustry(ev){
  if(ev.industry) return ev.industry;
  const cats=ev.categories||[];
  if(cats.includes('real_estate')) return 'real_estate';
  if(cats.includes('culinary')) return 'culinary';
  if(cats.includes('sports') || ev.source_id==='wr_chess') return 'sports';
  if(cats.includes('art') || cats.includes('fashion')) return 'art_fashion';
  return 'hospitality';
}

function industryLabel(industry){
  return ({hospitality:'Hospitality',sports:'Sports',real_estate:'Real Estate',culinary:'Culinary',art_fashion:'Art / Fashion'})[industry] || 'Hospitality';
}

function filteredNetworkEvents(){
  const events=(networkFeed&&networkFeed.events)||[];
  return events.filter(ev=>{
    if(networkDismissed[ev.id] && networkCat!=='saved') return false;
    if(networkCat==='saved' && !networkSaved[ev.id]) return false;
    if(networkCat!=='all' && networkCat!=='saved' && eventIndustry(ev)!==networkCat) return false;
    if(networkAccess!=='all' && ev.access!==networkAccess) return false;
    return true;
  }).sort((a,b)=>{
    if(!!networkSaved[a.id]!==!!networkSaved[b.id]) return networkSaved[a.id]?-1:1;
    const ad=parseEventStart(a), bd=parseEventStart(b);
    if(ad&&bd&&ad.getTime()!==bd.getTime()) return ad-bd;
    if(ad&&!bd) return -1;
    if(!ad&&bd) return 1;
    return (b.score||0)-(a.score||0);
  });
}

function buildDayMap(rows){
  const map=new Map();
  rows.forEach(ev=>{
    const key=eventDayKey(ev);
    if(!key) return;
    if(!map.has(key)) map.set(key,[]);
    map.get(key).push(ev);
  });
  map.forEach(list=>list.sort((a,b)=>{
    const at=parseEventStart(a), bt=parseEventStart(b);
    return (at?at.getTime():0)-(bt?bt.getTime():0) || (b.score||0)-(a.score||0);
  }));
  return map;
}

function ensureCalendarSelection(rows){
  if(networkSignalsMode){
    networkSelectedDay='';
    if(!networkCalendarMonth){ const n=miamiNow(); networkCalendarMonth=new Date(n.getFullYear(),n.getMonth(),1); }
    return;
  }
  const dated=rows.filter(ev=>parseEventStart(ev));
  if(!dated.length){
    networkSelectedDay='';
    if(!networkCalendarMonth){ const n=miamiNow(); networkCalendarMonth=new Date(n.getFullYear(),n.getMonth(),1); }
    return;
  }
  const keys=new Set(dated.map(eventDayKey));
  if(!networkSelectedDay || !keys.has(networkSelectedDay)){
    const todayKey=dayKeyFromDate(miamiNow());
    const next=dated.find(ev=>eventDayKey(ev)>=todayKey) || dated[0];
    networkSelectedDay=eventDayKey(next);
  }
  const selected=dateFromDayKey(networkSelectedDay);
  if(!networkCalendarMonth) networkCalendarMonth=new Date(selected.getFullYear(),selected.getMonth(),1);
}

function renderNetworkCalendar(rows){
  ensureCalendarSelection(rows);
  const map=buildDayMap(rows);
  const month=networkCalendarMonth || new Date(miamiNow().getFullYear(),miamiNow().getMonth(),1);
  const year=month.getFullYear(), monthIndex=month.getMonth();
  document.getElementById('netCalTitle').textContent=month.toLocaleDateString('en-US',{month:'long',year:'numeric'});
  const firstDow=new Date(year,monthIndex,1).getDay();
  const daysInMonth=new Date(year,monthIndex+1,0).getDate();
  const todayKey=dayKeyFromDate(miamiNow());
  const cells=[];
  for(let i=0;i<firstDow;i++) cells.push('<button type="button" class="net-cal-cell blank" tabindex="-1"></button>');
  for(let day=1;day<=daysInMonth;day++){
    const key=`${year}-${pad(monthIndex+1)}-${pad(day)}`;
    const events=map.get(key)||[];
    const minis=events.slice(0,3).map(ev=>`<span class="net-cal-mini ${esc(eventIndustry(ev))}">${esc(ev.title)}</span>`).join('');
    const more=events.length>3?`<div class="net-cal-more">+${events.length-3} more</div>`:'';
    const classes=['net-cal-cell'];
    if(key===todayKey) classes.push('today');
    if(key===networkSelectedDay) classes.push('selected');
    cells.push(`<button type="button" class="${classes.join(' ')}" data-day="${key}" aria-label="${day}, ${events.length} events">
      <span class="net-cal-day"><span>${day}</span>${events.length?`<span class="net-cal-count">${events.length}</span>`:''}</span>${minis}${more}
    </button>`);
  }
  document.getElementById('netCalGrid').innerHTML=cells.join('');
}

function defaultAccessTip(ev){
  if(ev.access==='invitation-only') return 'No public RSVP. Follow the official organizer and request a member, host, concierge or PR introduction.';
  if(ev.access==='members') return 'Use the official membership or concierge channel.';
  if(ev.access==='press') return 'Request accreditation from the official press contact before the deadline.';
  if(ev.access==='registration') return 'RSVP on the official page early; registration may close before the event.';
  return 'Check the official event page and reserve early if booking is available.';
}

function renderEventCard(ev){
  const saved=!!networkSaved[ev.id];
  const industry=eventIndustry(ev);
  const venueBits=[ev.venue,ev.neighborhood||ev.city].filter(Boolean).join(' · ');
  const href=ev.rsvp_url||ev.url||ev.source_url||'#';
  const contactUrl=ev.contact_url||'';
  const contactEmail=ev.contact_email||'';
  const contactAction=contactEmail
    ? `<a class="net-btn" href="mailto:${esc(contactEmail)}">Email contact</a>`
    : (contactUrl && contactUrl!==href ? `<a class="net-btn" href="${esc(contactUrl)}" target="_blank" rel="noopener">Access route</a>` : '');
  const tags=[
    `<span class="net-tag access">${esc(ev.access||'public')}</span>`,
    `<span class="net-tag industry">${esc(industryLabel(industry))}</span>`,
    ev.confidence!=null?`<span class="net-tag">${Math.round(ev.confidence*100)}% confidence</span>`:'',
    leadLabel(ev)?`<span class="net-tag">${esc(leadLabel(ev))}</span>`:''
  ].filter(Boolean).join('');
  const trail=(ev.source_trail||[]).map(t=>{
    const when=t.seen_at?new Date(t.seen_at).toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}):'';
    return `<div>• <b>${esc(t.source_name||t.source_id)}</b>${when?` · first seen ${esc(when)}`:''}${t.url?` · <a href="${esc(t.url)}" target="_blank" rel="noopener">source</a>`:''}</div>`;
  }).join('')||`<div>• <b>${esc(ev.source_name||'Official source')}</b></div>`;
  return `<article class="net-card${saved?' saved':''}" data-id="${esc(ev.id)}">
    <div class="net-card-top"><div class="net-when">${esc(formatEventWhen(ev))}</div><div class="net-score">Signal ${esc(String(ev.score??'—'))}</div></div>
    <div class="net-source">${esc(ev.source_name||'Official source')}</div>
    <div class="net-title"><a href="${esc(href)}" target="_blank" rel="noopener">${esc(ev.title)}</a></div>
    <div class="net-meta">${esc(venueBits||'Miami')}</div>
    <div class="net-why">${esc(ev.why_it_matters||ev.summary||'')}</div>
    <div class="net-access-tip"><b>How to get in</b>${esc(ev.access_tip||defaultAccessTip(ev))}</div>
    <div class="net-tags">${tags}</div>
    <div class="net-actions">
      <a class="net-btn primary" href="${esc(href)}" target="_blank" rel="noopener">${ev.access==='registration'?'RSVP / Details':'Official details'}</a>
      ${contactAction}
      <button type="button" class="net-btn${saved?' active-save':''}" data-act="save">${saved?'Saved':'Save'}</button>
      <button type="button" class="net-btn" data-act="trail">Source trail</button>
      <button type="button" class="net-btn" data-act="dismiss">Dismiss</button>
    </div>
    <div class="net-trail" data-trail>${trail}</div>
  </article>`;
}

function renderNetworkAgenda(rows){
  const list=document.getElementById('netList');
  const tba=rows.filter(ev=>!parseEventStart(ev));
  const selected=rows.filter(ev=>eventDayKey(ev)===networkSelectedDay);
  const dayDate=dateFromDayKey(networkSelectedDay);
  const title=networkSignalsMode?'Early signals':(networkSelectedDay?dayDate.toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric'}):'Select a date');
  document.getElementById('netDayTitle').textContent=title;
  document.getElementById('netDaySub').textContent=!networkSignalsMode&&networkSelectedDay
    ? `${selected.length} curated option${selected.length===1?'':'s'}`
    : `${tba.length} date-TBA signal${tba.length===1?'':'s'}`;
  let shown=networkSignalsMode?tba:selected;
  if(!shown.length){
    list.innerHTML='<div class="net-empty">No top-tier events match this date and filter. Try another industry, month, or access level.</div>';
  }else{
    list.innerHTML=shown.slice(0,16).map(renderEventCard).join('');
  }
}

function renderAccessDirectory(){
  const grid=document.getElementById('netDirectoryGrid');
  const rows=(networkFeed&&networkFeed.access_directory)||[];
  if(!rows.length){ document.getElementById('netDirectory').style.display='none'; return; }
  document.getElementById('netDirectory').style.display='';
  grid.innerHTML=rows.map(club=>`<div class="net-club">
    <div class="net-club-name">${esc(club.name)}</div>
    <div class="net-club-type">${esc(club.type||'Private membership')}</div>
    <div class="net-club-tip">${esc(club.tip||'Use the official membership route.')}</div>
    <a class="net-btn" href="${esc(club.apply_url||club.url)}" target="_blank" rel="noopener">Official access route</a>
  </div>`).join('');
}

function renderNetworkView(){
  const rows=filteredNetworkEvents();
  const signalCount=rows.filter(ev=>!parseEventStart(ev)).length;
  document.getElementById('netCount').textContent=`${rows.length} curated event${rows.length===1?'':'s'} · generic listings removed`;
  const signalBtn=document.getElementById('netSignalsBtn');
  signalBtn.textContent=`Early signals (${signalCount})`;
  signalBtn.classList.toggle('active-save',networkSignalsMode);
  renderNetworkCalendar(rows);
  renderNetworkAgenda(rows);
  renderAccessDirectory();
}

function setNetStatus(text,kind){
  const el=document.getElementById('netStatus');
  el.textContent=text;
  el.className='net-status'+(kind?' '+kind:'');
}

function esc(s){
  return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

async function loadNetworkFeed(force){
  const btn=document.getElementById('netRefreshBtn');
  if(btn) btn.disabled=true;
  setNetStatus('Fetching curated Miami sources…');
  const cachedRaw=localStorage.getItem(NETWORK_CACHE_KEY);
  let cached=null;
  if(cachedRaw){ try{ cached=JSON.parse(cachedRaw); }catch(e){ cached=null; } }
  let lastErr=null,data=null;
  for(const base of NETWORK_FEED_URLS){
    const controller=new AbortController();
    const timer=setTimeout(()=>controller.abort(),NETWORK_FEED_TIMEOUT_MS);
    try{
      const res=await fetch(base+(force?`?t=${Date.now()}`:''),{signal:controller.signal,cache:force?'no-store':'default'});
      clearTimeout(timer);
      if(!res.ok) throw new Error('HTTP '+res.status);
      const parsed=await res.json();
      if(!parsed||!Array.isArray(parsed.events)) throw new Error('Invalid feed shape');
      data=parsed; break;
    }catch(err){ clearTimeout(timer); lastErr=err; }
  }
  if(data){
    networkFeed=data;
    networkFeedMeta={stale:false,error:null,loadedAt:new Date().toISOString()};
    localStorage.setItem(NETWORK_CACHE_KEY,JSON.stringify({savedAt:networkFeedMeta.loadedAt,feed:data}));
    const gen=data.generated_at?new Date(data.generated_at).toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}):'—';
    setNetStatus(`Live · ${data.event_count||data.events.length} curated events · updated ${gen}`);
  }else if(cached&&cached.feed&&Array.isArray(cached.feed.events)){
    networkFeed=cached.feed;
    networkFeedMeta={stale:true,error:String(lastErr&&(lastErr.message||lastErr)),loadedAt:cached.savedAt};
    setNetStatus('Offline · showing the last saved calendar','stale');
  }else{
    networkFeed=NETWORK_BOOTSTRAP;
    networkFeedMeta={stale:true,error:String(lastErr&&(lastErr.message||lastErr)),loadedAt:null};
    setNetStatus('Using the built-in curated calendar while live sources reconnect','stale');
  }
  networkSelectedDay='';
  networkCalendarMonth=null;
  renderNetworkView();
  if(btn) btn.disabled=false;
}

function initNetworkTab(){
  const catRow=document.getElementById('netCatFilters');
  const accessRow=document.getElementById('netAccessFilters');
  catRow.addEventListener('click',e=>{
    const chip=e.target.closest('[data-cat]'); if(!chip) return;
    networkCat=chip.dataset.cat;
    catRow.querySelectorAll('.net-chip').forEach(c=>c.classList.toggle('active',c===chip));
    networkSignalsMode=false; networkSelectedDay=''; networkCalendarMonth=null; renderNetworkView();
  });
  accessRow.addEventListener('click',e=>{
    const chip=e.target.closest('[data-access]'); if(!chip) return;
    networkAccess=chip.dataset.access;
    accessRow.querySelectorAll('.net-chip').forEach(c=>c.classList.toggle('active',c===chip));
    networkSignalsMode=false; networkSelectedDay=''; networkCalendarMonth=null; renderNetworkView();
  });
  document.getElementById('netCalGrid').addEventListener('click',e=>{
    const cell=e.target.closest('[data-day]'); if(!cell) return;
    networkSignalsMode=false; networkSelectedDay=cell.dataset.day; renderNetworkView();
  });
  document.getElementById('netCalPrev').addEventListener('click',()=>{
    networkCalendarMonth=new Date(networkCalendarMonth.getFullYear(),networkCalendarMonth.getMonth()-1,1); renderNetworkView();
  });
  document.getElementById('netCalNext').addEventListener('click',()=>{
    networkCalendarMonth=new Date(networkCalendarMonth.getFullYear(),networkCalendarMonth.getMonth()+1,1); renderNetworkView();
  });
  document.getElementById('netCalToday').addEventListener('click',()=>{
    const now=miamiNow(); networkSignalsMode=false; networkCalendarMonth=new Date(now.getFullYear(),now.getMonth(),1); networkSelectedDay=dayKeyFromDate(now); renderNetworkView();
  });
  document.getElementById('netSignalsBtn').addEventListener('click',()=>{
    networkSignalsMode=true; networkSelectedDay=''; renderNetworkView();
  });
  document.getElementById('netRefreshBtn').addEventListener('click',()=>loadNetworkFeed(true));
  document.getElementById('netList').addEventListener('click',e=>{
    const btn=e.target.closest('[data-act]'); if(!btn) return;
    const card=btn.closest('.net-card'); if(!card) return;
    const id=card.dataset.id,act=btn.dataset.act;
    if(act==='save'){
      if(networkSaved[id]) delete networkSaved[id]; else networkSaved[id]=Date.now();
      saveNetworkPrefs(); renderNetworkView();
    }else if(act==='dismiss'){
      networkDismissed[id]=Date.now(); delete networkSaved[id]; saveNetworkPrefs(); renderNetworkView();
    }else if(act==='trail'){
      const trail=card.querySelector('[data-trail]'); if(trail) trail.classList.toggle('open');
    }
  });
  loadNetworkFeed(false);
}

"""


def minified_bootstrap() -> str:
    data = json.loads(FEED.read_text(encoding="utf-8"))
    dated = [e for e in data["events"] if e.get("starts_at")][:24]
    tba = [e for e in data["events"] if not e.get("starts_at")][:6]
    bootstrap = {
        "generated_at": data["generated_at"],
        "timezone": data["timezone"],
        "version": 1,
        "event_count": len(dated) + len(tba),
        "industries": data.get("industries", []),
        "access_directory": data.get("access_directory", []),
        "events": dated + tba,
        "bootstrap": True,
    }
    return json.dumps(bootstrap, ensure_ascii=False, separators=(",", ":"))


def upgrade(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    text, n = re.subn(
        r"  \.net-status\{.*?  \.net-empty\{.*?\}\n",
        CSS + "\n",
        text,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise RuntimeError(f"{path.name}: Network CSS block not found")

    text, n = re.subn(
        r"  <!-- ============ NETWORK PANEL ============ -->.*?  </div>\n\n</div>\n\n<div class=\"region-modal-backdrop\"",
        PANEL + "\n\n</div>\n\n<div class=\"region-modal-backdrop\"",
        text,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise RuntimeError(f"{path.name}: Network panel not found")

    bootstrap = minified_bootstrap()
    text, n = re.subn(
        r"const NETWORK_BOOTSTRAP = .*?;\nconst NETWORK_FEED_URLS",
        f"const NETWORK_BOOTSTRAP = {bootstrap};\nconst NETWORK_FEED_URLS",
        text,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise RuntimeError(f"{path.name}: bootstrap constant not found")

    text, n = re.subn(
        r"/\* =========================================================================\n   NETWORK TAB .*?(?=/\* ---------------- INITIAL RENDER ---------------- \*/)",
        JS,
        text,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise RuntimeError(f"{path.name}: Network JS block not found")

    path.write_text(text, encoding="utf-8")
    print(path.name, path.stat().st_size)


for target in TARGETS:
    upgrade(target)
