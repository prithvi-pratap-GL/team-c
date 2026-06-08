import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { api, ChatFilters, ChatMessage, ChatSession, RetrievalMode } from "../api/client";
import { Message } from "../components/MessageBubble";

function parseMeta(metaJson?: string | null) {
  if (!metaJson) return null;
  try { return JSON.parse(metaJson); } catch { return null; }
}

function dbMessagesToUI(dbMsgs: ChatMessage[], sessionId: number): Message[] {
  const messages: Message[] = [];
  for (let i = 0; i < dbMsgs.length; i++) {
    const m = dbMsgs[i];
    if (m.role === "user") {
      messages.push({ id: String(m.id), role: "user", text: m.content });
    } else {
      const meta = parseMeta(m.meta_json);
      const prevUser = dbMsgs.slice(0, i).reverse().find(x => x.role === "user");
      messages.push({
        id: String(m.id),
        role: "assistant",
        text: m.content,
        query: prevUser?.content,
        response: meta
          ? {
              answer: m.content,
              sources: meta.sources ?? [],
              retrieval_mode_used: meta.retrieval_mode_used ?? "hybrid",
              confidence: meta.confidence ?? "low",
              session_id: String(sessionId),
            }
          : undefined,
      });
    }
  }
  return messages;
}

interface UseChatOptions {
  token: string;
  activeSession: ChatSession | null;
  onSessionTitleChange?: (sessionId: number, newTitle: string) => void;
}

export function useChat({ token, activeSession, onSessionTitleChange }: UseChatOptions) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState<ChatFilters>({});
  const [retrievalMode, setRetrievalMode] = useState<RetrievalMode>("hybrid");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Track which session's history is loaded
  const loadedSessionRef = useRef<number | null>(null);

  // Load history whenever active session changes
  useEffect(() => {
    if (!activeSession) {
      setMessages([]);
      loadedSessionRef.current = null;
      return;
    }
    if (loadedSessionRef.current === activeSession.id) return;

    loadedSessionRef.current = activeSession.id;
    setLoadingHistory(true);
    setMessages([]);

    api.getMessages(token, activeSession.id)
      .then(dbMsgs => {
        setMessages(dbMessagesToUI(dbMsgs, activeSession.id));
      })
      .catch(() => setError("Failed to load conversation history"))
      .finally(() => setLoadingHistory(false));
  }, [activeSession, token]);

  const submit = useCallback(async (event?: FormEvent) => {
    event?.preventDefault();
    const trimmed = query.trim();
    if (!trimmed || loading || !activeSession) return;

    const tempId = crypto.randomUUID();
    setMessages(cur => [...cur, { id: tempId, role: "user", text: trimmed }]);
    setQuery("");
    setError("");
    setLoading(true);

    try {
      const response = await api.sendMessage(token, activeSession.id, {
        query: trimmed,
        filters,
        retrieval_mode: retrievalMode,
      });

      // Notify parent if title changed (backend auto-titles on first msg)
      // We re-fetch session list to get updated title
      onSessionTitleChange?.(activeSession.id, response.session_id);

      setMessages(cur => [
        ...cur,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          text: response.answer,
          query: trimmed,
          response,
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Chat request failed");
      // Remove the optimistic user message on error
      setMessages(cur => cur.filter(m => m.id !== tempId));
    } finally {
      setLoading(false);
    }
  }, [query, loading, activeSession, token, filters, retrievalMode, onSessionTitleChange]);

  return {
    messages,
    query,
    filters,
    retrievalMode,
    loading,
    loadingHistory,
    error,
    setQuery,
    setFilters,
    setRetrievalMode,
    submit,
  };
}
