import { useEffect, useState } from "react";
import { api } from "./lib/api";

type Room = { id: number; name: string; scenario: string };

export default function App() {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [name, setName] = useState("");
  const [scenario, setScenario] = useState("freeplay");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setErr(null);
    try {
      const data = await api<Room[]>("/rooms");
      setRooms(data);
    } catch (e: any) {
      setErr(e.message ?? String(e));
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function createRoom() {
    if (!name.trim()) return;
    setLoading(true);
    setErr(null);
    try {
      const room = await api<Room>("/rooms", {
        method: "POST",
        body: JSON.stringify({ name, scenario }),
      });
      setRooms((r) => [room, ...r]);
      setName("");
    } catch (e: any) {
      setErr(e.message ?? String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 720, margin: "2rem auto", padding: "0 1rem" }}>
      <h1>Multi-Agent Sandbox — Rooms</h1>

      <div style={{ margin: "1rem 0", padding: "1rem", border: "1px solid #ddd", borderRadius: 8 }}>
        <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
          <input
            placeholder="Room name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            style={{ flex: 1, padding: 8 }}
          />
          <select value={scenario} onChange={(e) => setScenario(e.target.value)} style={{ padding: 8 }}>
            <option value="freeplay">freeplay</option>
            <option value="debate">debate</option>
            <option value="planning">planning</option>
          </select>
          <button onClick={createRoom} disabled={loading || !name.trim()} style={{ padding: "8px 12px" }}>
            {loading ? "Creating..." : "Create"}
          </button>
        </div>
        {err && <div style={{ color: "crimson" }}>{err}</div>}
      </div>

      <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 8 }}>
        {rooms.map((r) => (
          <li key={r.id} style={{ border: "1px solid #eee", borderRadius: 8, padding: 12 }}>
            <div style={{ fontWeight: 600 }}>{r.name}</div>
            <div style={{ color: "#666" }}>{r.scenario}</div>
          </li>
        ))}
        {rooms.length === 0 && <li style={{ color: "#666" }}>No rooms yet.</li>}
      </ul>
    </div>
  );
}
