export default {
  async fetch(request: Request, env: { PYTHON_RPC: { highlight_code(code: string): Promise<string> } }) {
    // Literate note: the TypeScript Worker does not know how highlighting works.
    // It only knows there is a Python service binding with a typed RPC method.
    const url = new URL(request.url);
    const code = url.searchParams.get("code") ?? `from dataclasses import dataclass

@dataclass
class Track:
    title: str
    plays: int

tracks = [Track("Monty on the Run", 128), Track("Cybernoid", 64)]
for track in tracks:
    print(f"{track.title}: {track.plays} plays")`;
    const highlighted = await env.PYTHON_RPC.highlight_code(code);
    const page = `<!doctype html>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Service Binding RPC · Xampler</title>
<style>
*{box-sizing:border-box}body{font:16px/1.55 system-ui,-apple-system,Segoe UI,sans-serif;max-width:1120px;margin:0 auto;padding:2rem 1rem;color:#17202a;background:linear-gradient(180deg,#f8fafc,#fff 20rem)}h1{font-size:clamp(2.1rem,5vw,3.2rem);line-height:1.04;margin:.1rem 0 .75rem;letter-spacing:-.04em}h2{font-size:1.05rem;margin:0 0 .45rem}.eyebrow{font-size:.78rem;text-transform:uppercase;letter-spacing:.08em;color:#64748b;font-weight:800}.hero{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:1.5rem;align-items:end;border-bottom:1px solid #d0d7de;padding-bottom:1.3rem;margin-bottom:1.4rem}.lede{font-size:1.1rem;color:#334155;max-width:72ch}.card,.panel,.step{border:1px solid #d0d7de;border-radius:16px;background:rgba(255,255,255,.9);box-shadow:0 8px 24px rgba(15,23,42,.05)}.card,.step{padding:1rem}.layout{display:grid;grid-template-columns:360px minmax(0,1fr);gap:1.4rem;align-items:start}.steps{position:sticky;top:1rem;display:grid;gap:1rem}.num{display:inline-grid;place-items:center;width:1.65rem;height:1.65rem;border-radius:999px;background:#2563eb;color:white;font-weight:800;font-size:.85rem;margin-right:.45rem}.muted{color:#64748b}textarea{width:100%;min-height:12rem;font:14px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace;border:1px solid #cbd5e1;border-radius:12px;padding:.75rem;resize:vertical}button{font:inherit;padding:.55rem .8rem;border:1px solid #2563eb;border-radius:10px;background:#2563eb;color:white;cursor:pointer;font-weight:650}.button-row{display:flex;gap:.6rem;flex-wrap:wrap;margin-top:.8rem}.panel{overflow:hidden}.panel-head{display:flex;justify-content:space-between;gap:1rem;align-items:center;padding:1rem;border-bottom:1px solid #e2e8f0;background:#f8fafc}.badge{display:inline-flex;border-radius:999px;background:#dcfce7;color:#14532d;padding:.2rem .55rem;font-size:.86rem;font-weight:700}.highlight{overflow:auto;padding:1rem}.highlight pre{margin:0;padding:1rem;border-radius:12px;background:#0d1117;color:#e6edf3;overflow:auto}.flow{display:grid;grid-template-columns:1fr auto 1fr auto 1fr;gap:.5rem;align-items:center;margin-top:1rem}.node{border:1px solid #bfdbfe;background:#eff6ff;color:#1e3a8a;border-radius:12px;padding:.65rem;text-align:center;font-weight:700}.arrow{color:#64748b;text-align:center}@media(max-width:860px){body{padding:1rem}.hero,.layout{display:block}.steps{position:static;margin-bottom:1rem}.flow{grid-template-columns:1fr}.arrow{display:none}}
</style>
<header class=hero><div><p class=eyebrow>Network edge example</p><h1>Service Binding RPC</h1><p class=lede>A TypeScript Worker calls a Python Worker through a typed service binding. The TypeScript edge app owns the route and UI; the Python service owns code highlighting.</p><div class=flow><div class=node>Browser</div><div class=arrow>→</div><div class=node>TypeScript Worker</div><div class=arrow>→</div><div class=node>Python RPC</div></div></div><aside class=card><strong>What this proves</strong><p class=muted>Cross-language Worker composition without HTTP public hops between internal services.</p></aside></header>
<main class=layout><aside class=steps><section class=step><h2><span class=num>1</span>Edit Python code</h2><p class=muted>The form submits to the TypeScript Worker. The TS Worker never implements highlighting.</p><form id=form><textarea name=code>${escapeHtml(code)}</textarea><div class=button-row><button>Highlight through Python RPC</button></div></form></section><section class=step><h2><span class=num>2</span>Boundary</h2><p class=muted>The binding exposes <code>highlight_code(code: string): Promise&lt;string&gt;</code>. The Python Worker returns highlighted HTML.</p></section></aside><section class=panel><div class=panel-head><div><h2>Highlighted result</h2><p class=muted>Rendered by the Python Worker, framed by the TypeScript app.</p></div><span class=badge>PYTHON_RPC connected locally</span></div><div class=highlight>${highlighted}</div></section></main>`;
    return new Response(page, { headers: { "content-type": "text/html; charset=utf-8" } });
  },
};

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#39;",
  })[char] ?? char);
}
