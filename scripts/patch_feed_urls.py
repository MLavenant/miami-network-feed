from pathlib import Path

dash = Path(r"C:\Users\MatthiasLavenant\Downloads\today-dashboard (5).html")
text = dash.read_text(encoding="utf-8")

old_const = 'const NETWORK_FEED_URL = "https://mlavenant.github.io/miami-network-feed/events.json";\nconst NETWORK_FEED_TIMEOUT_MS = 10000;'
new_const = '''const NETWORK_FEED_URLS = [
  "https://mlavenant.github.io/miami-network-feed/events.json",
  "https://cdn.jsdelivr.net/gh/MLavenant/miami-network-feed@main/docs/events.json"
];
const NETWORK_FEED_URL = NETWORK_FEED_URLS[0];
const NETWORK_FEED_TIMEOUT_MS = 10000;'''
if old_const not in text:
    raise SystemExit("const block not found")
text = text.replace(old_const, new_const, 1)

old_load = '''async function loadNetworkFeed(force){
  const btn = document.getElementById('netRefreshBtn');
  if(btn) btn.disabled = true;
  setNetStatus('Fetching Miami event feed…');

  const cachedRaw = localStorage.getItem(NETWORK_CACHE_KEY);
  let cached = null;
  if(cachedRaw){
    try{ cached = JSON.parse(cachedRaw); }catch(e){ cached = null; }
  }

  const controller = new AbortController();
  const timer = setTimeout(()=>controller.abort(), NETWORK_FEED_TIMEOUT_MS);
  try{
    const res = await fetch(NETWORK_FEED_URL + (force ? `?t=${Date.now()}` : ''), {
      signal: controller.signal,
      cache: force ? 'no-store' : 'default'
    });
    clearTimeout(timer);
    if(!res.ok) throw new Error('HTTP '+res.status);
    const data = await res.json();
    if(!data || !Array.isArray(data.events)) throw new Error('Invalid feed shape');
    networkFeed = data;
    networkFeedMeta = { stale:false, error:null, loadedAt:new Date().toISOString() };
    localStorage.setItem(NETWORK_CACHE_KEY, JSON.stringify({ savedAt: networkFeedMeta.loadedAt, feed:data }));
    const gen = data.generated_at ? new Date(data.generated_at).toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}) : '—';
    setNetStatus(`Live · ${data.event_count||data.events.length} signals · updated ${gen}`);
    renderNetworkList();
  }catch(err){
    clearTimeout(timer);
    if(cached && cached.feed){
      networkFeed = cached.feed;
      networkFeedMeta = { stale:true, error:String(err.message||err), loadedAt:cached.savedAt };
      const gen = cached.feed.generated_at ? new Date(cached.feed.generated_at).toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}) : 'cache';
      setNetStatus(`Offline / stale cache · showing ${cached.feed.event_count||cached.feed.events.length} events from ${gen}`, 'stale');
      renderNetworkList();
    }else if(typeof NETWORK_BOOTSTRAP !== 'undefined' && NETWORK_BOOTSTRAP && Array.isArray(NETWORK_BOOTSTRAP.events)){
      networkFeed = NETWORK_BOOTSTRAP;
      networkFeedMeta = { stale:true, error:String(err.message||err), loadedAt:null };
      setNetStatus('Using built-in bootstrap feed (live GitHub Pages feed not reachable yet).', 'stale');
      renderNetworkList();
    }else{
      networkFeed = { events:[], event_count:0 };
      networkFeedMeta = { stale:true, error:String(err.message||err), loadedAt:null };
      setNetStatus('Could not load feed yet. Deploy miami-network-feed to GitHub Pages, or check your connection.', 'err');
      renderNetworkList();
    }
  }finally{
    if(btn) btn.disabled = false;
  }
}'''

new_load = '''async function loadNetworkFeed(force){
  const btn = document.getElementById('netRefreshBtn');
  if(btn) btn.disabled = true;
  setNetStatus('Fetching Miami event feed…');

  const cachedRaw = localStorage.getItem(NETWORK_CACHE_KEY);
  let cached = null;
  if(cachedRaw){
    try{ cached = JSON.parse(cachedRaw); }catch(e){ cached = null; }
  }

  let lastErr = null;
  let data = null;
  for(const base of NETWORK_FEED_URLS){
    const controller = new AbortController();
    const timer = setTimeout(()=>controller.abort(), NETWORK_FEED_TIMEOUT_MS);
    try{
      const res = await fetch(base + (force ? `?t=${Date.now()}` : ''), {
        signal: controller.signal,
        cache: force ? 'no-store' : 'default'
      });
      clearTimeout(timer);
      if(!res.ok) throw new Error('HTTP '+res.status);
      const parsed = await res.json();
      if(!parsed || !Array.isArray(parsed.events)) throw new Error('Invalid feed shape');
      data = parsed;
      break;
    }catch(err){
      clearTimeout(timer);
      lastErr = err;
    }
  }

  if(data){
    networkFeed = data;
    networkFeedMeta = { stale:false, error:null, loadedAt:new Date().toISOString() };
    localStorage.setItem(NETWORK_CACHE_KEY, JSON.stringify({ savedAt: networkFeedMeta.loadedAt, feed:data }));
    const gen = data.generated_at ? new Date(data.generated_at).toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}) : '—';
    setNetStatus(`Live · ${data.event_count||data.events.length} signals · updated ${gen}`);
    renderNetworkList();
  }else if(cached && cached.feed){
    networkFeed = cached.feed;
    networkFeedMeta = { stale:true, error:String(lastErr && (lastErr.message||lastErr)), loadedAt:cached.savedAt };
    const gen = cached.feed.generated_at ? new Date(cached.feed.generated_at).toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}) : 'cache';
    setNetStatus(`Offline / stale cache · showing ${cached.feed.event_count||cached.feed.events.length} events from ${gen}`, 'stale');
    renderNetworkList();
  }else if(typeof NETWORK_BOOTSTRAP !== 'undefined' && NETWORK_BOOTSTRAP && Array.isArray(NETWORK_BOOTSTRAP.events)){
    networkFeed = NETWORK_BOOTSTRAP;
    networkFeedMeta = { stale:true, error:String(lastErr && (lastErr.message||lastErr)), loadedAt:null };
    setNetStatus('Using built-in bootstrap feed (live feed not reachable yet).', 'stale');
    renderNetworkList();
  }else{
    networkFeed = { events:[], event_count:0 };
    networkFeedMeta = { stale:true, error:String(lastErr && (lastErr.message||lastErr)), loadedAt:null };
    setNetStatus('Could not load feed yet. Check connection or open after GitHub Pages finishes deploying.', 'err');
    renderNetworkList();
  }
  if(btn) btn.disabled = false;
}'''

if old_load not in text:
    raise SystemExit("loadNetworkFeed block not found")
text = text.replace(old_load, new_load, 1)
dash.write_text(text, encoding="utf-8")
print("patched feed urls + loader")
