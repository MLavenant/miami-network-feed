from pathlib import Path

p = Path(r"C:\Users\MatthiasLavenant\Downloads\today-dashboard (5).html")
t = p.read_text(encoding="utf-8")
print("panel", 'id="panel-network"' in t)
print("tab", "goTab('network')" in t)
print("bootstrap", "NETWORK_BOOTSTRAP" in t)
print("init", "initNetworkTab()" in t)
print("tabs", t.count('class="tab-btn'))
print("kb", round(p.stat().st_size / 1024, 1))
