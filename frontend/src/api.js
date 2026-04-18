// api.js — centralised HTTP client

const BASE = '/api'

export async function fetchChargers() {
  const res = await fetch(`${BASE}/chargers`)
  return res.json()
}

export async function fetchAlerts() {
  const res = await fetch(`${BASE}/alerts`)
  return res.json()
}
