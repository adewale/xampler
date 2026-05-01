export default {
  async fetch(request: Request, env: { PYTHON_RPC: { highlight_code(code: string): Promise<string> } }) {
    // Literate note: the TypeScript Worker does not know how highlighting works.
    // It only knows there is a Python service binding with a typed RPC method.
    const url = new URL(request.url);
    const code = url.searchParams.get("code") ?? "print('hello from Python RPC')";
    const html = await env.PYTHON_RPC.highlight_code(code);
    return new Response(html, { headers: { "content-type": "text/html; charset=utf-8" } });
  },
};
