// A thin wrapper around the Sourdough HTTP API (see sourdough/interface/server.py).

export async function api(path, body) {
  const options = body == null ? undefined : {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }
  const res = await fetch(path, options)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || res.statusText)
  return data
}
