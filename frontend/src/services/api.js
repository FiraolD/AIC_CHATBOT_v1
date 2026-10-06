import axios from 'axios';
import config from '../config';

/**
 * Normalized API error carrying the backend's typed contract:
 * {error_code, detail} plus the HTTP status and Retry-After (for 429).
 */
export class ApiError extends Error {
  constructor({ status, code, detail, retryAfter }) {
    super(detail || 'Request failed');
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.detail = detail;
    this.retryAfter = retryAfter; // seconds, only for 429
  }

  get isRateLimited() {
    return this.status === 429;
  }

  get isUnavailable() {
    return this.status === 503;
  }
}

const api = axios.create({
  baseURL: config.api.baseUrl,
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': config.api.key,
  },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status || 0;
    const body = error.response?.data;
    throw new ApiError({
      status,
      code: body?.error_code || (status === 0 ? 'NETWORK_ERROR' : 'UNKNOWN_ERROR'),
      detail: typeof body?.detail === 'string' ? body.detail : error.message,
      retryAfter: Number(error.response?.headers?.['retry-after']) || null,
    });
  }
);

/**
 * Parse a single SSE `data: {...}` line into a typed event object.
 * Returns null for keep-alives or malformed lines.
 */
function parseSseLine(line) {
  const trimmed = line.trim();
  if (!trimmed.startsWith('data:')) return null;
  try {
    return JSON.parse(trimmed.slice(5).trim());
  } catch {
    return null;
  }
}

export const chatAPI = {
  /** Non-streaming chat (fallback path). */
  send: async (message, sessionId = null) => {
    const response = await api.post('/chat', {
      message,
      ...(sessionId ? { session_id: sessionId } : {}),
    });
    return response.data; // {answer, session_id, sources}
  },

  /**
   * Streaming chat over SSE using fetch + ReadableStream (POST with headers,
   * which EventSource cannot do). Handlers:
   *   onStart(sessionId), onSources(sources), onToken(text),
   *   onEnd(), onError(ApiError | {message}), onAbort()
   * Pass options.signal (AbortSignal) to support "stop generating".
   */
  stream: async (message, sessionId, handlers = {}, { signal } = {}) => {
    const { onStart, onSources, onToken, onEnd, onError, onAbort } = handlers;

    let response;
    try {
      response = await fetch(`${config.api.baseUrl}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': config.api.key,
        },
        body: JSON.stringify({
          message,
          ...(sessionId ? { session_id: sessionId } : {}),
        }),
        signal,
      });
    } catch (error) {
      if (error?.name === 'AbortError') {
        onAbort?.();
        return;
      }
      onError?.(new ApiError({ status: 0, code: 'NETWORK_ERROR', detail: error.message }));
      return;
    }

    if (!response.ok || !response.body) {
      // Drain a JSON error body when the backend rejects before streaming
      let detail = `Request failed with status ${response.status}`;
      let code = response.status === 429 ? 'RATE_LIMIT_ERROR' : 'STREAM_ERROR';
      try {
        const body = await response.json();
        if (body?.detail && typeof body.detail === 'string') detail = body.detail;
        if (body?.error_code) code = body.error_code;
      } catch {
        /* not JSON; keep defaults */
      }
      onError?.(
        new ApiError({
          status: response.status,
          code,
          detail,
          retryAfter: Number(response.headers.get('Retry-After')) || null,
        })
      );
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let ended = false;
    let errored = false;

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? ''; // keep the trailing partial line

        for (const line of lines) {
          const event = parseSseLine(line);
          if (!event) continue;

          switch (event.type) {
            case 'start':
              onStart?.(event.session_id);
              break;
            case 'sources':
              onSources?.(event.sources || []);
              break;
            case 'token':
              onToken?.(event.content || '');
              break;
            case 'end':
              ended = true;
              onEnd?.();
              break;
            case 'error':
              errored = true;
              onError?.(
                new ApiError({
                  status: 503,
                  code: 'SERVICE_UNAVAILABLE',
                  detail: event.error || 'Service temporarily unavailable',
                })
              );
              break;
            default:
              break;
          }
        }
      }
      if (!ended && !errored) onEnd?.();
    } catch (error) {
      // User pressed "stop generating" mid-stream
      if (error?.name === 'AbortError') {
        onAbort?.();
        return;
      }
      onError?.(new ApiError({ status: 0, code: 'NETWORK_ERROR', detail: error.message }));
    }
  },

  /** Stored conversation history for a session. */
  history: async (sessionId) => {
    const response = await api.get(`/conversations/${sessionId}/history`);
    return response.data; // {session_id, messages}
  },

  /** Persist user feedback (rating 1-5). */
  feedback: async ({ sessionId, rating, comment }) => {
    const response = await api.post('/feedback', {
      ...(sessionId ? { session_id: sessionId } : {}),
      rating,
      ...(comment ? { comment } : {}),
    });
    return response.data;
  },

  /** Deep readiness probe used by the header status indicator. */
  readiness: async () => {
    const response = await api.get('/health/ready');
    return response.data; // {status, components, system}
  },

  /** Product catalog for suggestions. */
  insuranceTypes: async () => {
    const response = await api.get('/insurance-types');
    return response.data;
  },

  /** Quote engine: start a flow and calculate premiums. */
  quote: {
    start: async (flowId) => {
      const response = await api.post('/quote/start', { flow_id: flowId });
      return response.data;
    },
    calculate: async (flowId, answers) => {
      const response = await api.post('/quote/calculate', {
        flow_id: flowId,
        answers,
      });
      return response.data;
    },
  },
};

export default api;
