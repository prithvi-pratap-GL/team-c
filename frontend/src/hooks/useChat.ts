import { FormEvent, useState } from "react";
import { api, ChatFilters, RetrievalMode } from "../api/client";
import { Message } from "../components/MessageBubble";

export function useChat(token: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState<ChatFilters>({});
  const [retrievalMode, setRetrievalMode] = useState<RetrievalMode>("hybrid");
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event?: FormEvent) {
    event?.preventDefault();
    const trimmed = query.trim();
    if (!trimmed || loading) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      text: trimmed,
    };
    setMessages((current) => [...current, userMessage]);
    setQuery("");
    setError("");
    setLoading(true);

    try {
      const response = await api.chat(token, {
        query: trimmed,
        filters,
        retrieval_mode: retrievalMode,
        session_id: sessionId,
      });
      setSessionId(response.session_id);
      setMessages((current) => [
        ...current,
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
    } finally {
      setLoading(false);
    }
  }

  return {
    messages,
    query,
    filters,
    retrievalMode,
    loading,
    error,
    setQuery,
    setFilters,
    setRetrievalMode,
    submit,
  };
}
