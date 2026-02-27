import { useEffect, useMemo, useState } from "react";
import type { ReactEventHandler } from "react";
import "./App.css";

type Role = "user" | "assistant";

type ChatMessage = {
  message_id: string;
  role: Role;
  content: string;
  created_at: string;
};

type ChatSessionSummary = {
  session_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  last_message_preview: string | null;
};

type SessionListResponse = { sessions: ChatSessionSummary[] };
type SessionCreateResponse = { session: ChatSessionSummary };
type SessionMessagesResponse = { session: ChatSessionSummary; messages: ChatMessage[] };
type SessionMessageResponse = {
  session: ChatSessionSummary;
  user_message: ChatMessage;
  assistant_message: ChatMessage;
};

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `HTTP ${response.status}`);
  }

  return response.json() as Promise<T>;
}

function formatDate(value: string) {
  const d = new Date(value);
  return d.toLocaleString("ko-KR", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function App() {
  const [sessions, setSessions] = useState<ChatSessionSummary[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [messageInput, setMessageInput] = useState("");
  const [newTitle, setNewTitle] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activeSession = useMemo(
    () => sessions.find((s) => s.session_id === activeSessionId) ?? null,
    [sessions, activeSessionId],
  );

  async function loadSessions() {
    const data = await api<SessionListResponse>("/chat/sessions");
    setSessions(data.sessions);

    if (!activeSessionId && data.sessions.length > 0) {
      setActiveSessionId(data.sessions[0].session_id);
    }
  }

  async function loadMessages(sessionId: string) {
    const data = await api<SessionMessagesResponse>(`/chat/sessions/${sessionId}/messages`);
    setMessages(data.messages);

    setSessions((prev) => {
      const exists = prev.some((s) => s.session_id === data.session.session_id);
      if (exists) {
        return prev.map((s) => (s.session_id === data.session.session_id ? data.session : s));
      }
      return [data.session, ...prev];
    });
  }

  async function createSession(title?: string) {
    const data = await api<SessionCreateResponse>("/chat/sessions", {
      method: "POST",
      body: JSON.stringify({ title: title?.trim() || undefined }),
    });

    setSessions((prev) => [data.session, ...prev]);
    setActiveSessionId(data.session.session_id);
    setMessages([]);
    return data.session.session_id;
  }

  const onSubmitMessage: ReactEventHandler<HTMLFormElement> = async (e) => {
    e.preventDefault();
    const text = messageInput.trim();
    if (!text || sending) return;

    try {
      setSending(true);
      setError(null);

      let targetSessionId = activeSessionId;
      if (!targetSessionId) {
        targetSessionId = await createSession();
      }

      const data = await api<SessionMessageResponse>(`/chat/sessions/${targetSessionId}/messages`, {
        method: "POST",
        body: JSON.stringify({ message: text }),
      });

      setMessages((prev) => [...prev, data.user_message, data.assistant_message]);
      setSessions((prev) => {
        const others = prev.filter((s) => s.session_id !== data.session.session_id);
        return [data.session, ...others];
      });
      setMessageInput("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "메시지 전송에 실패했습니다.");
    } finally {
      setSending(false);
    }
  };

  async function onCreateSession() {
    try {
      setError(null);
      await createSession(newTitle);
      setNewTitle("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "세션 생성에 실패했습니다.");
    }
  }

  useEffect(() => {
    async function bootstrap() {
      try {
        setLoading(true);
        setError(null);
        const data = await api<SessionListResponse>("/chat/sessions");
        setSessions(data.sessions);
        if (data.sessions.length > 0) {
          const first = data.sessions[0].session_id;
          setActiveSessionId(first);
          const msgData = await api<SessionMessagesResponse>(`/chat/sessions/${first}/messages`);
          setMessages(msgData.messages);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "초기 로딩에 실패했습니다.");
      } finally {
        setLoading(false);
      }
    }

    void bootstrap();
  }, []);

  useEffect(() => {
    if (!activeSessionId) {
      setMessages([]);
      return;
    }

    void loadMessages(activeSessionId).catch((err: unknown) => {
      setError(err instanceof Error ? err.message : "세션 메시지 조회에 실패했습니다.");
    });
  }, [activeSessionId]);

  return (
    <div className="app-shell">
      <aside className="session-pane">
        <header className="pane-header">
          <h1>QMS Chat</h1>
          <p>세션 기반 대화</p>
        </header>

        <div className="session-create">
          <input
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder="새 세션 제목 (선택)"
            maxLength={50}
          />
          <button onClick={onCreateSession}>새 세션</button>
        </div>

        <button className="refresh-button" onClick={() => void loadSessions()}>
          목록 새로고침
        </button>

        <div className="session-list">
          {sessions.map((session) => (
            <button
              key={session.session_id}
              className={`session-item ${activeSessionId === session.session_id ? "active" : ""}`}
              onClick={() => setActiveSessionId(session.session_id)}
            >
              <strong>{session.title}</strong>
              <span>{session.last_message_preview || "메시지 없음"}</span>
              <time>{formatDate(session.updated_at)}</time>
            </button>
          ))}
          {!loading && sessions.length === 0 && <p className="empty">세션이 없습니다.</p>}
        </div>
      </aside>

      <main className="chat-pane">
        <header className="chat-header">
          <h2>{activeSession?.title || "세션을 선택하세요"}</h2>
          <p>오늘 범위: 대화형 UI + 세션 관리</p>
        </header>

        <section className="message-list">
          {messages.map((msg) => (
            <article key={msg.message_id} className={`bubble ${msg.role}`}>
              <p>{msg.content}</p>
              <time>{formatDate(msg.created_at)}</time>
            </article>
          ))}
          {!loading && messages.length === 0 && (
            <p className="empty-message">메시지를 보내 대화를 시작하세요.</p>
          )}
        </section>

        <form className="composer" onSubmit={onSubmitMessage}>
          <textarea
            value={messageInput}
            onChange={(e) => setMessageInput(e.target.value)}
            rows={3}
            placeholder="질문을 입력하세요"
          />
          <button type="submit" disabled={sending}>
            {sending ? "전송 중..." : "보내기"}
          </button>
        </form>

        {error && <p className="error">오류: {error}</p>}
      </main>
    </div>
  );
}

export default App;
