import { useCallback, useEffect, useRef, useState } from 'react';
import { chatAPI, ApiError } from '../services/api';

const SESSION_KEY = 'awash_chat_session_id';

let messageCounter = 0;
const nextId = () => `msg-${Date.now()}-${++messageCounter}`;

/** Map an ApiError into a UI-facing error descriptor. */
function classifyError(error) {
  if (error instanceof ApiError && error.isRateLimited) {
    return {
      type: 'rate-limit',
      retryAfter: error.retryAfter || 60,
      detail: error.detail,
    };
  }
  if (error instanceof ApiError && error.isUnavailable) {
    return { type: 'unavailable', detail: error.detail };
  }
  if (error instanceof ApiError && error.status === 403) {
    return { type: 'unauthorized', detail: error.detail };
  }
  return { type: 'network', detail: error?.detail || error?.message };
}

/**
 * Chat state: messages, streaming, session memory and feedback.
 * The session id lives in sessionStorage so a refresh keeps the
 * conversation, while a new tab starts fresh.
 */
export function useChat() {
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState(null);
  const [rateLimitUntil, setRateLimitUntil] = useState(null);
  const [sessionId, setSessionId] = useState(
    () => sessionStorage.getItem(SESSION_KEY) || null
  );
  const sessionIdRef = useRef(sessionId);
  const abortRef = useRef(null);

  useEffect(() => {
    sessionIdRef.current = sessionId;
    if (sessionId) sessionStorage.setItem(SESSION_KEY, sessionId);
  }, [sessionId]);

  const patchMessage = useCallback((id, patch) => {
    setMessages((prev) =>
      prev.map((msg) => (msg.id === id ? { ...msg, ...patch } : msg))
    );
  }, []);

  const send = useCallback(
    async (text) => {
      const trimmed = text.trim();
      if (!trimmed || isStreaming) return;

      setError(null);

      const userMessage = {
        id: nextId(),
        role: 'user',
        content: trimmed,
        timestamp: new Date(),
      };
      const botMessage = {
        id: nextId(),
        role: 'bot',
        content: '',
        timestamp: new Date(),
        sources: [],
        streaming: true,
        receivedTokens: false,
      };

      setMessages((prev) => [...prev, userMessage, botMessage]);
      setIsStreaming(true);

      const controller = new AbortController();
      abortRef.current = controller;

      await chatAPI.stream(
        trimmed,
        sessionIdRef.current,
        {
        onStart: (sid) => {
          if (sid) setSessionId(sid);
        },
        onSources: (sources) => {
          patchMessage(botMessage.id, { sources });
        },
        onToken: (token) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === botMessage.id
                ? {
                    ...msg,
                    content: msg.content + token,
                    receivedTokens: true,
                  }
                : msg
            )
          );
        },
        onEnd: () => {
          patchMessage(botMessage.id, { streaming: false });
        },
        onError: (apiError) => {
          const classified = classifyError(apiError);
          if (classified.type === 'rate-limit') {
            setRateLimitUntil(Date.now() + classified.retryAfter * 1000);
          }
          // If tokens already streamed, keep the partial answer with a note;
          // otherwise surface the error banner and drop the empty bubble.
          setMessages((prev) =>
            prev.flatMap((msg) => {
              if (msg.id !== botMessage.id) return [msg];
              if (msg.receivedTokens) {
                return [{ ...msg, streaming: false, partial: true }];
              }
              return [];
            })
          );
          setError(classified);
        },
        onAbort: () => {
          // User stopped generation: keep any streamed text, drop empty bubbles
          setMessages((prev) =>
            prev.flatMap((msg) => {
              if (msg.id !== botMessage.id) return [msg];
              if (msg.receivedTokens) {
                return [{ ...msg, streaming: false }];
              }
              return [];
            })
          );
        },
        },
        { signal: controller.signal }
      );

      abortRef.current = null;
      setIsStreaming(false);
    },
    [isStreaming, patchMessage]
  );

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const newConversation = useCallback(() => {
    setMessages([]);
    setError(null);
    setSessionId(null);
    sessionStorage.removeItem(SESSION_KEY);
  }, []);

  const dismissError = useCallback(() => setError(null), []);

  const submitFeedback = useCallback(
    async (messageId, rating) => {
      // Optimistic mark; revert silently if the request fails
      patchMessage(messageId, { feedback: rating });
      try {
        await chatAPI.feedback({ sessionId: sessionIdRef.current, rating });
      } catch {
        patchMessage(messageId, { feedback: null });
      }
    },
    [patchMessage]
  );

  return {
    messages,
    sessionId,
    isStreaming,
    error,
    rateLimitUntil,
    send,
    stopStreaming,
    newConversation,
    dismissError,
    submitFeedback,
  };
}

export default useChat;
