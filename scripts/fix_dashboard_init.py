from pathlib import Path

FILES = [
    Path(r"C:\Users\MatthiasLavenant\Downloads\today-dashboard (6).html"),
    Path(r"C:\Users\MatthiasLavenant\Downloads\today-dashboard-with-network.html"),
]

OLD_INIT = """/* ---------------- INITIAL RENDER ---------------- */
renderDay();
renderFinance();
renderHealthTab();
/* ---------------- INITIAL RENDER ---------------- */
renderDay();
renderFinance();
renderHealthTab();
initNetworkTab();
if(savedIcs){
  // auto-attempt reconnect on load
  document.getElementById('icsConnectBtn').click();
}"""

NEW_INIT = """/* ---------------- INITIAL RENDER ---------------- */
renderDay();
renderFinance();
renderHealthTab();
initNetworkTab();
if(savedIcs){
  // auto-attempt reconnect on load
  document.getElementById('icsConnectBtn').click();
}"""

OLD_RANGE = """  // Prefer tonight on evenings, otherwise 7 days
  const hour = miamiNow().getHours();
  if(hour < 16){
    networkRange = '7d';
    dateRow.querySelectorAll('.net-chip').forEach(c=>c.classList.toggle('active', c.dataset.range==='7d'));
  }
  loadNetworkFeed(false);"""

NEW_RANGE = """  networkRange = '7d';
  dateRow.querySelectorAll('.net-chip').forEach(c=>c.classList.toggle('active', c.dataset.range==='7d'));
  loadNetworkFeed(false);"""

OLD_CHIPS = """        <button type="button" class="net-chip active" data-range="tonight">Tonight</button>
        <button type="button" class="net-chip" data-range="tomorrow">Tomorrow</button>
        <button type="button" class="net-chip" data-range="7d">7 days</button>"""

NEW_CHIPS = """        <button type="button" class="net-chip" data-range="tonight">Tonight</button>
        <button type="button" class="net-chip" data-range="tomorrow">Tomorrow</button>
        <button type="button" class="net-chip active" data-range="7d">7 days</button>"""


def fix(path: Path) -> None:
    t = path.read_text(encoding="utf-8")
    changed = []
    if OLD_INIT in t:
        t = t.replace(OLD_INIT, NEW_INIT, 1)
        changed.append("duplicate-init")
    if "behavior:'instant'" in t:
        t = t.replace("behavior:'instant'", "behavior:'auto'")
        changed.append("scroll")
    if OLD_RANGE in t:
        t = t.replace(OLD_RANGE, NEW_RANGE, 1)
        changed.append("default-range-js")
    if OLD_CHIPS in t:
        t = t.replace(OLD_CHIPS, NEW_CHIPS, 1)
        changed.append("default-range-html")
    if "let networkRange = 'tonight';" in t:
        t = t.replace("let networkRange = 'tonight';", "let networkRange = '7d';")
        changed.append("networkRange-var")
    path.write_text(t, encoding="utf-8")
    print(path.name, changed or ["no-changes"], path.stat().st_size)


for f in FILES:
    fix(f)
