export type Room = { id: number; name: string; scenario: string };
export type Agent = { id: number; room_id: number; name: string; role: string; goal: string; };
export type Message = { id: number; room_id: number; agent_id: number | null; content: string; created_at: string };
