// Every call to the server goes through here.
export async function getJson(address, options) {
  const response = await fetch(address, options)
  if (!response.ok) throw new Error(`The server answered ${response.status}`)
  return response.json()
}
