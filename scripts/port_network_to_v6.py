"""Port Network tab from today-dashboard (5).html into (6).html."""
from __future__ import annotations

import re
from pathlib import Path

SRC = Path(r"C:\Users\MatthiasLavenant\Downloads\today-dashboard (5).html")
DST = Path(r"C:\Users\MatthiasLavenant\Downloads\today-dashboard (6).html")

src = SRC.read_text(encoding="utf-8")
dst = DST.read_text(encoding="utf-8")

if 'id="panel-network"' in dst:
    raise SystemExit("Network already present in (6)")

# --- CSS: replace tabbar block through footnote with v5 version (includes net styles) ---
css_pat = re.compile(
    r"  \.tabbar\{.*?  \.footnote\{margin-top:24px;font-size:10\.5px;color:var\(--paper-dim\);font-family:'JetBrains Mono',monospace;text-align:center;opacity:0\.7;\}",
    re.S,
)
css_src = css_pat.search(src)
css_dst = css_pat.search(dst)
if not css_src or not css_dst:
    raise SystemExit("CSS tabbar/footnote block not found")
dst = dst[: css_dst.start()] + css_src.group(0) + dst[css_dst.end() :]

# --- HTML panel ---
panel_pat = re.compile(
    r"  <!-- ============ NETWORK PANEL ============ -->.*?  </div>\n\n</div>",
    re.S,
)
panel = panel_pat.search(src)
if not panel:
    raise SystemExit("Network panel not found in source")
# In dest, health panel ends then </div> closes wrap
health_end = '    <div class="footnote">HEATMAP, PROGRESS &amp; CARDIO ARE BUILT FROM YOUR SAVED LOGS</div>\n  </div>\n\n</div>'
if health_end not in dst:
    raise SystemExit("Health panel end not found")
# Insert network panel before closing wrap
insert = (
    '    <div class="footnote">HEATMAP, PROGRESS &amp; CARDIO ARE BUILT FROM YOUR SAVED LOGS</div>\n'
    "  </div>\n\n"
    + panel.group(0)  # includes NETWORK panel + closing </div>
)
dst = dst.replace(health_end, insert, 1)

# --- Tab button ---
tab_pat = re.compile(
    r'  <button class="tab-btn" data-tab="network" onclick="goTab\(\'network\'\)">.*?</button>\n',
    re.S,
)
tab = tab_pat.search(src)
if not tab:
    raise SystemExit("Network tab button not found")
health_tab_end = (
    '  <button class="tab-btn" data-tab="health" onclick="goTab(\'health\')">\n'
    '    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="5" r="2.5"/><path d="M12 9v6M8 12h8M9 22l1.5-7M15 22l-1.5-7"/></svg>\n'
    "    Health\n"
    "  </button>\n"
    "</div>"
)
if health_tab_end not in dst:
    raise SystemExit("Health tab end not found")
dst = dst.replace(
    health_tab_end,
    health_tab_end.replace("</div>", tab.group(0) + "</div>", 1),
    1,
)

# --- Storage keys + feed constants (from LOG_KEY through NETWORK_FEED_TIMEOUT) ---
# In src, after RETIRE_KEY come network keys and bootstrap. Extract from NETWORK_CACHE_KEY through TIMEOUT.
keys_pat = re.compile(
    r'const NETWORK_CACHE_KEY = "command_dashboard_network_feed_v1";.*?const NETWORK_FEED_TIMEOUT_MS = 10000;',
    re.S,
)
keys = keys_pat.search(src)
if not keys:
    raise SystemExit("Network keys/bootstrap not found")
retire_line = 'const RETIRE_KEY = "command_dashboard_retire_v1";'
if retire_line not in dst:
    raise SystemExit("RETIRE_KEY not found")
dst = dst.replace(retire_line, retire_line + "\n" + keys.group(0), 1)

# --- JS network module + init ---
js_pat = re.compile(
    r"/\* =========================================================================\n"
    r"   NETWORK TAB — Miami luxury / hospitality event intelligence\n"
    r"   ========================================================================= \*/.*?initNetworkTab\(\);\n",
    re.S,
)
js = js_pat.search(src)
if not js:
    raise SystemExit("Network JS block not found")

old_init = """/* ---------------- INITIAL RENDER ---------------- */
renderDay();
renderFinance();
renderHealthTab();
if(savedIcs){
  // auto-attempt reconnect on load
  document.getElementById('icsConnectBtn').click();
}"""

# js.group may include trailing initNetworkTab();\n from src INITIAL RENDER.
js_body = js.group(0)
if js_body.endswith("initNetworkTab();\n"):
    js_body = js_body[: -len("initNetworkTab();\n")]

new_init = (
    js_body
    + """/* ---------------- INITIAL RENDER ---------------- */
renderDay();
renderFinance();
renderHealthTab();
initNetworkTab();
if(savedIcs){
  // auto-attempt reconnect on load
  document.getElementById('icsConnectBtn').click();
}"""
)

if old_init not in dst:
    raise SystemExit("INITIAL RENDER block not found")
dst = dst.replace(old_init, new_init, 1)

DST.write_text(dst, encoding="utf-8")

# Verify
checks = {
    "panel": 'id="panel-network"' in dst,
    "tab": "goTab('network')" in dst,
    "bootstrap": "NETWORK_BOOTSTRAP" in dst,
    "init": "initNetworkTab()" in dst,
    "css": ".net-card{" in dst,
    "tabs": dst.count('class="tab-btn'),
}
print(checks)
print("kb", round(DST.stat().st_size / 1024, 1))
if not all(checks[k] for k in ("panel", "tab", "bootstrap", "init", "css")):
    raise SystemExit("verification failed")
if checks["tabs"] < 6:
    raise SystemExit("expected 6 tabs")
print("OK")
