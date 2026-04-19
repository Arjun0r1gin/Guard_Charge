import { useEffect, useState } from "react"

const WS_URL  = "wss://localhost:8000/detection/ws"
const API_URL = "https://localhost:8000"

const STATUS_CONFIG = {
  VERIFIED:        { color: "#16a34a", bg: "#dcfce7", border: "#86efac", signal: "🟢  CHARGING AUTHORIZED",           btn: true  },
  SUSPICIOUS:      { color: "#ca8a04", bg: "#fef9c3", border: "#fde047", signal: "🟡  WARNING — PROCEED WITH CAUTION", btn: true  },
  LIKELY_ROGUE:    { color: "#ea580c", bg: "#ffedd5", border: "#fdba74", signal: "🟠  CHARGING BLOCKED",               btn: false },
  CONFIRMED_ROGUE: { color: "#dc2626", bg: "#fee2e2", border: "#fca5a5", signal: "🔴  HARD BLOCK — DO NOT CHARGE",     btn: false },
}

export default function App() {
  const [detection, setDetection] = useState(null)
  const [chargers, setChargers]   = useState([])
  const [charging, setCharging]   = useState(false)
  const [connected, setConnected] = useState(false)
  const [waiting, setWaiting]     = useState(true)

  useEffect(() => {
    fetch(`${API_URL}/chargers/`)
      .then(r => r.json())
      .then(setChargers)
      .catch(() => {})
  }, [])

  useEffect(() => {
    let ws
    let timer

    function connect() {
      ws = new WebSocket(WS_URL)

      ws.onopen = () => setConnected(true)

      ws.onclose = () => {
        setConnected(false)
        timer = setTimeout(connect, 2000)
      }

      ws.onerror = () => ws.close()

      ws.onmessage = (e) => {
        const data = JSON.parse(e.data)
        if (data.event === "trust_score_update") {
          setDetection(data)
          setCharging(false)
          setWaiting(false)
        }
      }
    }

    connect()
    return () => { clearTimeout(timer); ws?.close() }
  }, [])

  function handleReset() {
    setDetection(null)
    setCharging(false)
    setWaiting(true)
  }

  const cfg     = detection ? STATUS_CONFIG[detection.status] ?? STATUS_CONFIG.CONFIRMED_ROGUE : null
  const charger = detection ? chargers.find(c => c.id === detection.charger_id) : null

  return (
    <div style={{
      minHeight: "100vh",
      background: "#0f172a",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      padding: "32px 16px",
      fontFamily: "Arial, sans-serif",
    }}>

      {/* Header */}
      <div style={{ textAlign: "center", marginBottom: "32px" }}>
        <h1 style={{ color: "#f1f5f9", fontSize: "2rem", margin: 0 }}>⚡ GuardCharge</h1>
        <p style={{ color: "#94a3b8", margin: "6px 0 12px" }}>
          EV Charging Security Dashboard
        </p>
        <div style={{
          display: "inline-flex", gap: "8px", alignItems: "center",
          padding: "4px 14px", borderRadius: "999px",
          background: connected ? "#166534" : "#7f1d1d",
          color: connected ? "#86efac" : "#fca5a5",
          fontSize: "0.8rem",
        }}>
          <div style={{
            width: "6px", height: "6px", borderRadius: "50%",
            background: connected ? "#86efac" : "#fca5a5",
          }}/>
          {connected ? "🔒 Secure — Backend connected" : "Reconnecting..."}
        </div>
      </div>

      <div style={{ width: "100%", maxWidth: "520px" }}>

        {/* Waiting for USB */}
        {waiting && (
          <div style={{
            background: "#1e293b",
            borderRadius: "16px",
            padding: "48px 32px",
            textAlign: "center",
          }}>
            <div style={{ fontSize: "3rem", marginBottom: "16px" }}>🔌</div>
            <h2 style={{ color: "#f1f5f9", marginBottom: "8px" }}>
              Waiting for charger...
            </h2>
            <p style={{ color: "#94a3b8", marginBottom: "24px", fontSize: "0.9rem" }}>
              Insert USB device to begin security verification
            </p>
            <div style={{
              display: "flex", flexDirection: "column", gap: "10px",
              textAlign: "left",
            }}>
              {[
                { n: "1st", label: "Tata Power Koramangala", expected: "VERIFIED",        color: "#16a34a" },
                { n: "2nd", label: "Ather Grid HSR Layout",  expected: "SUSPICIOUS",      color: "#ca8a04" },
                { n: "3rd", label: "ChargeZone MG Road",     expected: "CONFIRMED ROGUE", color: "#dc2626" },
              ].map(p => (
                <div key={p.n} style={{
                  background: "#0f172a",
                  borderRadius: "8px",
                  padding: "10px 14px",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}>
                  <div>
                    <span style={{ color: "#64748b", fontSize: "0.75rem" }}>{p.n} plug-in  </span>
                    <span style={{ color: "#cbd5e1", fontSize: "0.85rem" }}>{p.label}</span>
                  </div>
                  <span style={{ color: p.color, fontSize: "0.75rem", fontWeight: "bold" }}>
                    {p.expected}
                  </span>
                </div>
              ))}
            </div>

            {/* TLS badge */}
            <div style={{
              marginTop: "24px",
              padding: "8px 14px",
              background: "#0f172a",
              borderRadius: "8px",
              fontSize: "0.75rem",
              color: "#64748b",
            }}>
              🔒 All communications secured via TLS (WSS + HTTPS)
            </div>
          </div>
        )}

        {/* Detection result */}
        {detection && cfg && (
          <div style={{
            background: "#1e293b",
            borderRadius: "16px",
            padding: "28px",
            border: `2px solid ${cfg.border}`,
          }}>

            {/* Signal banner */}
            <div style={{
              background: cfg.bg,
              borderRadius: "10px",
              padding: "14px",
              textAlign: "center",
              marginBottom: "24px",
            }}>
              <div style={{ fontSize: "1.3rem", fontWeight: "bold", color: cfg.color }}>
                {cfg.signal}
              </div>
            </div>

            {/* Charger info */}
            {charger && (
              <div style={{ marginBottom: "18px" }}>
                <div style={{ color: "#64748b", fontSize: "0.75rem", marginBottom: "4px" }}>
                  CHARGER DETECTED
                </div>
                <div style={{ color: "#f1f5f9", fontSize: "1rem", fontWeight: "bold" }}>
                  {charger.name}
                </div>
                <div style={{ color: "#94a3b8", fontSize: "0.85rem" }}>
                  {charger.operator}
                </div>
              </div>
            )}

            {/* Trust score */}
            <div style={{ marginBottom: "18px" }}>
              <div style={{ color: "#64748b", fontSize: "0.75rem", marginBottom: "8px" }}>
                TRUST SCORE
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                <div style={{
                  fontSize: "2.8rem", fontWeight: "bold",
                  color: cfg.color, lineHeight: 1, minWidth: "64px",
                }}>
                  {detection.score}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{
                    height: "10px", background: "#334155",
                    borderRadius: "5px", overflow: "hidden",
                  }}>
                    <div style={{
                      height: "100%",
                      width: `${detection.score}%`,
                      background: cfg.color,
                      borderRadius: "5px",
                      transition: "width 0.8s ease",
                    }}/>
                  </div>
                  <div style={{ color: "#64748b", fontSize: "0.72rem", marginTop: "4px" }}>
                    out of 100
                  </div>
                </div>
              </div>
            </div>

            {/* Status + Action */}
            <div style={{
              display: "grid", gridTemplateColumns: "1fr 1fr",
              gap: "10px", marginBottom: "18px",
            }}>
              <div style={{ background: "#0f172a", borderRadius: "8px", padding: "12px" }}>
                <div style={{ color: "#64748b", fontSize: "0.72rem", marginBottom: "4px" }}>STATUS</div>
                <div style={{ color: cfg.color, fontWeight: "bold", fontSize: "0.88rem" }}>
                  {detection.status}
                </div>
              </div>
              <div style={{ background: "#0f172a", borderRadius: "8px", padding: "12px" }}>
                <div style={{ color: "#64748b", fontSize: "0.72rem", marginBottom: "4px" }}>ACTION</div>
                <div style={{ color: "#f1f5f9", fontWeight: "bold", fontSize: "0.88rem" }}>
                  {detection.action}
                </div>
              </div>
            </div>

            {/* Layer badges */}
            <div style={{
              display: "grid", gridTemplateColumns: "1fr 1fr",
              gap: "10px", marginBottom: "18px",
            }}>
              <div style={{
                background: detection.hard_blocked ? "#7f1d1d" : "#166534",
                borderRadius: "8px", padding: "10px 12px",
              }}>
                <div style={{ color: "#64748b", fontSize: "0.72rem", marginBottom: "4px" }}>LAYER 1</div>
                <div style={{
                  fontWeight: "bold", fontSize: "0.82rem",
                  color: detection.hard_blocked ? "#fca5a5" : "#86efac",
                }}>
                  {detection.hard_blocked ? "✗ CERT MISMATCH" : "✓ CERT VALID"}
                </div>
              </div>
              <div style={{
                background: (!detection.hard_blocked && detection.score < 100) ? "#7c2d12" : "#166534",
                borderRadius: "8px", padding: "10px 12px",
              }}>
                <div style={{ color: "#64748b", fontSize: "0.72rem", marginBottom: "4px" }}>LAYER 2</div>
                <div style={{
                  fontWeight: "bold", fontSize: "0.82rem",
                  color: (!detection.hard_blocked && detection.score < 100) ? "#fdba74" : "#86efac",
                }}>
                  {detection.hard_blocked
                    ? "— SKIPPED"
                    : detection.score === 100
                    ? "✓ BEHAVIOUR NORMAL"
                    : "⚠ ANOMALY DETECTED"}
                </div>
              </div>
            </div>

            {/* Explanation */}
            <div style={{
              background: "#0f172a", borderRadius: "8px",
              padding: "14px", marginBottom: "20px",
            }}>
              <div style={{ color: "#64748b", fontSize: "0.72rem", marginBottom: "8px" }}>
                DETECTION ENGINE EXPLANATION
              </div>
              {detection.explanation.split("\n").map((line, i) => (
                <div key={i} style={{ color: "#cbd5e1", fontSize: "0.82rem", lineHeight: "1.7" }}>
                  {line}
                </div>
              ))}
            </div>

            {/* TLS badge */}
            <div style={{
              marginBottom: "16px",
              padding: "8px 12px",
              background: "#0f172a",
              borderRadius: "8px",
              fontSize: "0.72rem",
              color: "#64748b",
              textAlign: "center",
            }}>
              🔒 Verified over TLS — WSS + HTTPS
            </div>

            {/* Charging button */}
            {charging ? (
              <div style={{
                padding: "16px", background: "#166534",
                borderRadius: "10px", textAlign: "center",
                color: "#86efac", fontWeight: "bold",
                fontSize: "1rem", marginBottom: "12px",
              }}>
                ⚡ Charging in progress...
              </div>
            ) : cfg.btn ? (
              <button
                onClick={() => setCharging(true)}
                style={{
                  width: "100%", padding: "15px",
                  background: "#16a34a", color: "white",
                  border: "none", borderRadius: "10px",
                  fontSize: "1rem", fontWeight: "bold",
                  cursor: "pointer", marginBottom: "12px",
                }}
              >
                ▶ Start Charging
              </button>
            ) : (
              <button disabled style={{
                width: "100%", padding: "15px",
                background: "#7f1d1d", color: "#fca5a5",
                border: "none", borderRadius: "10px",
                fontSize: "1rem", fontWeight: "bold",
                cursor: "not-allowed", marginBottom: "12px",
              }}>
                🚫 Charging Blocked — Rogue Station Detected
              </button>
            )}

            {/* Reset */}
            <button
              onClick={handleReset}
              style={{
                width: "100%", padding: "10px",
                background: "transparent", color: "#64748b",
                border: "1px solid #334155", borderRadius: "8px",
                fontSize: "0.85rem", cursor: "pointer",
              }}
            >
              ↩ Disconnect & Reset
            </button>
          </div>
        )}

        {/* Charger list */}
        {chargers.length > 0 && (
          <div style={{ marginTop: "28px" }}>
            <div style={{ color: "#475569", fontSize: "0.75rem", marginBottom: "10px" }}>
              REGISTERED CHARGERS
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
              {chargers.map(c => {
                const isActive = detection?.charger_id === c.id
                return (
                  <div key={c.id} style={{
                    background: "#1e293b", borderRadius: "8px",
                    padding: "10px 14px",
                    border: isActive ? `1px solid ${cfg?.border}` : "1px solid #334155",
                  }}>
                    <div style={{
                      color: isActive ? "#f1f5f9" : "#94a3b8",
                      fontSize: "0.82rem",
                      fontWeight: isActive ? "bold" : "normal",
                    }}>
                      {c.name}
                    </div>
                    <div style={{ color: "#475569", fontSize: "0.72rem" }}>
                      Score: {c.trust_score} — {c.status}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}