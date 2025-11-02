import { useEffect, useState } from "react";
import { api, API_BASE } from "./lib/api";
import type { Room, Agent, Message } from "./types";

function RoomsView({ onOpen }: { onOpen: (room: Room) => void }) {
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
    <div style={{ maxWidth: 800, margin: "2rem auto", padding: "0 1rem" }}>
      <h1>Rooms</h1>

      <div
        style={{
          margin: "1rem 0",
          padding: "1rem",
          border: "1px solid #ddd",
          borderRadius: 8,
        }}
      >
        <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
          <input
            placeholder="Room name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            style={{ flex: 1, padding: 8 }}
          />
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <label>Scenario:</label>
          <select
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
            style={{ padding: 8 }}
          >
            <option value="freeplay">freeplay</option>
            <option value="debate">debate</option>
            <option value="planning">planning</option>
          </select>
          <button
            onClick={createRoom}
            disabled={loading || !name.trim()}
            style={{ padding: "8px 12px" }}
          >
            {loading ? "Creating..." : "Create"}
          </button>
        </div>
        {err && <div style={{ color: "crimson", marginTop: 8 }}>{err}</div>}
      </div>

      <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 8 }}>
        {rooms.map((r) => (
          <li
            key={r.id}
            onClick={() => onOpen(r)}
            style={{
              border: "1px solid #eee",
              borderRadius: 8,
              padding: 12,
              cursor: "pointer",
            }}
            title="Open room"
          >
            <div style={{ fontWeight: 600 }}>{r.name}</div>
            <div style={{ color: "#666" }}>{r.scenario}</div>
          </li>
        ))}
        {rooms.length === 0 && <li style={{ color: "#666" }}>No rooms yet.</li>}
      </ul>
    </div>
  );
}

function RoomView({ room, onBack }: { room: Room; onBack: () => void }) {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draftAgent, setDraftAgent] = useState<
    Pick<Agent, "name" | "role" | "goal">
  >({
    name: "",
    role: "",
    goal: "",
  });
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [live, setLive] = useState(true); // ⬅️ new

  async function refresh() {
    setErr(null);
    try {
      const [a, m] = await Promise.all([
        api<Agent[]>(`/agents/${room.id}`),
        api<Message[]>(`/messages/${room.id}`),
      ]);
      setAgents(a);
      setMessages(m);
    } catch (e: any) {
      setErr(e.message ?? String(e));
    }
  }

  useEffect(() => {
    // Initial load when entering the room
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [room.id]);

  // Polling loop for live updates
  useEffect(() => {
    if (!live) return;

    let stopped = false;

    async function poll() {
      try {
        const m = await api<Message[]>(`/messages/${room.id}`);
        if (!stopped) setMessages(m);
      } catch {
        // ignore transient network errors while polling
      }
    }

    // poll immediately, then at an interval
    poll();
    const id = setInterval(poll, 1500);

    return () => {
      stopped = true;
      clearInterval(id);
    };
  }, [room.id, live]);

  async function addAgent() {
    if (!draftAgent.name.trim() || !draftAgent.role.trim()) return;
    setLoading(true);
    setErr(null);
    try {
      const payload = { ...draftAgent, room_id: room.id };
      const agent = await api<Agent>("/agents", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setAgents((prev) => [...prev, agent]);
      setDraftAgent({ name: "", role: "", goal: "" });
    } catch (e: any) {
      setErr(e.message ?? String(e));
    } finally {
      setLoading(false);
    }
  }

  async function simulateTurn() {
    setLoading(true);
    setErr(null);
    try {
      await api<Message>(`/simulate/turn/${room.id}`, { method: "POST" });
      // no need to call refresh(); the poller will pick it up within ~1.5s
    } catch (e: any) {
      setErr(e.message ?? String(e));
    } finally {
      setLoading(false);
    }
  }

  async function judgeTurn() {
    setLoading(true);
    setErr(null);
    try {
      await api<Message>(`/simulate/judge/${room.id}`, { method: "POST" });
      // Poller will pick it up automatically
    } catch (e: any) {
      setErr(e.message ?? String(e));
    } finally {
      setLoading(false);
    }
  }

  async function exportMarkdown() {
    try {
      const res = await fetch(`${API_BASE}/rooms/${room.id}/export.md`, {
        method: "GET",
      });
      if (!res.ok) throw new Error(await res.text());
      const text = await res.text();
      const blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const safeName = `${room.name.replace(/\s+/g, "_")}_transcript.md`;
      a.download = safeName;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      alert(e.message ?? String(e));
    }
  }

  return (
    <div style={{ maxWidth: 1000, margin: "2rem auto", padding: "0 1rem" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          marginBottom: 12,
        }}
      >
        <button onClick={onBack} style={{ padding: "6px 10px" }}>
          ← Back
        </button>
        <h2 style={{ margin: 0 }}>{room.name}</h2>
        <span style={{ color: "#666" }}>({room.scenario})</span>
        <div
          style={{
            marginLeft: "auto",
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <label>Live</label>
          <input
            type="checkbox"
            checked={live}
            onChange={(e) => setLive(e.target.checked)}
            title="Toggle live polling"
          />
          <button onClick={exportMarkdown} style={{ padding: "6px 10px" }}>
            Export Markdown
          </button>
        </div>
      </div>

      <div
        style={{
          border: "1px solid #ddd",
          borderRadius: 8,
          padding: 12,
          marginBottom: 16,
        }}
      >
        <h3 style={{ marginTop: 0 }}>Agents</h3>
        <div
          style={{
            display: "grid",
            gap: 8,
            gridTemplateColumns: "repeat(3, 1fr)",
            marginBottom: 8,
          }}
        >
          <input
            placeholder="Name"
            value={draftAgent.name}
            onChange={(e) =>
              setDraftAgent((s) => ({ ...s, name: e.target.value }))
            }
            style={{ padding: 8 }}
          />
          <input
            placeholder="Role"
            value={draftAgent.role}
            onChange={(e) =>
              setDraftAgent((s) => ({ ...s, role: e.target.value }))
            }
            style={{ padding: 8 }}
          />
          <input
            placeholder="Goal"
            value={draftAgent.goal}
            onChange={(e) =>
              setDraftAgent((s) => ({ ...s, goal: e.target.value }))
            }
            style={{ padding: 8 }}
          />
        </div>
        <button
          onClick={addAgent}
          disabled={loading || !draftAgent.name || !draftAgent.role}
          style={{ padding: "8px 12px" }}
        >
          Add Agent
        </button>
        <div style={{ marginTop: 8, color: "#666" }}>
          {agents.length
            ? `Agents: ${agents.map((a) => a.name).join(", ")}`
            : "No agents yet."}
        </div>
      </div>

      <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12 }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 8,
          }}
        >
          <h3 style={{ margin: 0 }}>Conversation</h3>
          <button
            onClick={simulateTurn}
            disabled={loading || agents.length === 0}
            style={{ padding: "8px 12px" }}
          >
            {loading ? "Working..." : "Simulate Turn"}
          </button>
          <button
            onClick={judgeTurn}
            disabled={loading || messages.length === 0}
            style={{ padding: "8px 12px" }}
          >
            Judge
          </button>
        </div>
        <div
          style={{
            border: "1px solid #eee",
            borderRadius: 6,
            padding: 8,
            height: 420,
            overflow: "auto",
          }}
        >
          {messages.map((m) => (
            <div key={m.id} style={{ marginBottom: 8, fontSize: 14 }}>
              <strong style={{ marginRight: 8 }}>
                {agents.find((a) => a.id === m.agent_id)?.name ?? "System"}
              </strong>
              <span style={{ whiteSpace: "pre-wrap" }}>{m.content}</span>
            </div>
          ))}
          {messages.length === 0 && (
            <div style={{ color: "#666" }}>No messages yet.</div>
          )}
        </div>
      </div>

      {err && <div style={{ color: "crimson", marginTop: 12 }}>{err}</div>}
    </div>
  );
}

export default function App() {
  const [open, setOpen] = useState<Room | null>(null);
  return open ? (
    <RoomView room={open} onBack={() => setOpen(null)} />
  ) : (
    <RoomsView onOpen={setOpen} />
  );
}
