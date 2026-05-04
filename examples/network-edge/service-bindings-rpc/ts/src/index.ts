export default {
  async fetch(request: Request, env: { PYTHON_RPC: { highlight_code(code: string): Promise<string> } }) {
    // Literate note: the TypeScript Worker does not know how highlighting works.
    // It only knows there is a Python service binding with a typed RPC method.
    const url = new URL(request.url);
    const code = url.searchParams.get("code") ?? "print('hello from Python RPC')";
    const highlighted = await env.PYTHON_RPC.highlight_code(code);
    const page = `<!doctype html>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Service Binding RPC · Xampler</title>
<style>
body{font:16px/1.55 system-ui;max-width:980px;margin:2rem auto;padding:0 1rem;color:#17202a}header{border-bottom:1px solid #d0d7de;margin-bottom:1rem}textarea{width:100%;min-height:8rem;font:14px/1.45 ui-monospace,monospace}button{font:inherit;padding:.5rem .8rem;border:1px solid #2563eb;border-radius:.5rem;background:#2563eb;color:white;cursor:pointer}.card{border:1px solid #d0d7de;border-radius:.75rem;padding:1rem;background:#f8fafc}.highlight{overflow:auto}.highlight pre{padding:1rem;border-radius:.75rem;background:#0d1117;color:#e6edf3}
</style>
<header><h1>Service Binding RPC</h1><p>A TypeScript Worker calls a Python Worker RPC method to highlight Python code.</p></header>
<section class=card><form><textarea name=code>${escapeHtml(code)}</textarea><p><button>Highlight through Python RPC</button></p></form></section>
<section class=card><h2>Highlighted result</h2>${highlighted}</section>`;
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
