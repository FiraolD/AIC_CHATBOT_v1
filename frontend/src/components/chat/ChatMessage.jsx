import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Shield,
  User,
  Copy,
  Check,
  ThumbsUp,
  ThumbsDown,
  ChevronDown,
  FileText,
} from 'lucide-react';

/** Collapsible list of retrieval citations under a bot answer. */
const SourcesSection = ({ sources }) => {
  const [open, setOpen] = useState(false);
  if (!sources?.length) return null;

  return (
    <div className="mt-3 border-t border-slate-100 pt-2">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        aria-expanded={open}
        className="flex items-center gap-1.5 text-xs font-medium text-awash-700 transition hover:text-awash-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-awash-500 rounded"
      >
        <FileText className="h-3.5 w-3.5" aria-hidden="true" />
        {sources.length} {sources.length === 1 ? 'source' : 'sources'}
        <ChevronDown
          className={`h-3.5 w-3.5 transition-transform ${open ? 'rotate-180' : ''}`}
          aria-hidden="true"
        />
      </button>
      {/* Always mounted so the expand/collapse transition runs both ways.
          max-height is animated instead of grid-template-rows for cross-
          browser reliability. */}
      <div
        className={`overflow-hidden transition-all duration-300 ease-out ${
          open ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <ul className="space-y-1.5 pt-2">
          {sources.map((source, index) => (
            <li
              key={index}
              className="rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600"
            >
              <p className="line-clamp-3 leading-relaxed">{source.text}</p>
              <p className="mt-1 flex items-center gap-2 text-[10px] text-slate-400">
                <span className="font-medium text-slate-500">{source.source}</span>
                {typeof source.score === 'number' &&
                  source.score >= 0 &&
                  source.score <= 1 && (
                    <span>relevance {Math.round(source.score * 100)}%</span>
                  )}
              </p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

/** Thumbs up/down feedback, sent once per message. */
const FeedbackButtons = ({ message, onFeedback }) => {
  if (message.streaming) return null;
  const voted = message.feedback != null;

  return (
    <div className="flex items-center gap-0.5">
      {voted ? (
        <span className="px-1 text-xs text-slate-400">Thanks for your feedback</span>
      ) : (
        <>
          <button
            type="button"
            aria-label="Good answer"
            onClick={() => onFeedback(message.id, 5)}
            className="rounded p-1 text-slate-400 transition hover:bg-slate-100 hover:text-emerald-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-awash-500"
          >
            <ThumbsUp className="h-3.5 w-3.5" aria-hidden="true" />
          </button>
          <button
            type="button"
            aria-label="Poor answer"
            onClick={() => onFeedback(message.id, 1)}
            className="rounded p-1 text-slate-400 transition hover:bg-slate-100 hover:text-red-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-awash-500"
          >
            <ThumbsDown className="h-3.5 w-3.5" aria-hidden="true" />
          </button>
        </>
      )}
    </div>
  );
};

const ChatMessage = ({ message, onFeedback }) => {
  const isBot = message.role === 'bot';
  const [copied, setCopied] = useState(false);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard unavailable; ignore */
    }
  };

  const time = message.timestamp.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });

  if (!isBot) {
    return (
      <div className="flex animate-message-in justify-end gap-3">
        <div className="max-w-[85%] sm:max-w-[75%]">
          <div className="rounded-2xl rounded-tr-sm bg-awash-700 px-4 py-2.5 text-white shadow-soft">
            <p className="whitespace-pre-line text-[0.925rem] leading-relaxed">
              {message.content}
            </p>
          </div>
          <p className="mt-1 pr-1 text-right text-[10px] text-slate-400">{time}</p>
        </div>
        <div className="mt-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-slate-200">
          <User className="h-4 w-4 text-slate-500" aria-hidden="true" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex animate-message-in gap-3">
      <div className="mt-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-awash-600 to-awash-900 shadow-soft">
        <Shield className="h-4 w-4 text-white" aria-hidden="true" />
      </div>
      <div className="max-w-[85%] sm:max-w-[75%] min-w-0 flex-1">
        <div className="rounded-2xl rounded-tl-sm border border-slate-200 bg-white px-4 py-3 shadow-soft">
          {message.content ? (
            <div className={`prose-chat ${message.streaming ? 'stream-caret' : ''}`}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          ) : null}

          {message.partial && (
            <p className="mt-2 text-xs italic text-amber-600">
              The reply was cut short — please try again.
            </p>
          )}

          <SourcesSection sources={message.sources} />

          <div className="mt-2 flex items-center justify-between gap-2">
            <span className="text-[10px] text-slate-400">{time}</span>
            <div className="flex items-center gap-1">
              {!message.streaming && message.content && (
                <button
                  type="button"
                  onClick={copyToClipboard}
                  aria-label="Copy answer to clipboard"
                  className="flex items-center gap-1 rounded p-1 text-xs text-slate-400 transition hover:bg-slate-100 hover:text-slate-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-awash-500"
                >
                  {copied ? (
                    <Check className="h-3.5 w-3.5 text-emerald-600" aria-hidden="true" />
                  ) : (
                    <Copy className="h-3.5 w-3.5" aria-hidden="true" />
                  )}
                </button>
              )}
              <FeedbackButtons message={message} onFeedback={onFeedback} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
