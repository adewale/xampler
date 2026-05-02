export const onRequestGet: PagesFunction = async ({ request }) => {
  // Pages Functions use file-based routing. This file maps to /api/hello.
  const name = new URL(request.url).searchParams.get("name") ?? "Python";
  return Response.json({ message: `Hello, ${name}, from Pages Functions` });
};
