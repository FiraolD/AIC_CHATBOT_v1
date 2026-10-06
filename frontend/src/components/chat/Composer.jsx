import React, { useEffect, useRef, useState } from 'react';
import { Send, Square } from 'lucide-react';

const MAX_LENGTH = 4000; // must match backend max_message_length
const COUNTER_THRESHOLD = 3500;

/**
 * Auto-growing message input: Enter sends, Shift+Enter inserts a newline.
 * While the assistant is streaming the send button turns into "stop
 * generating"; typing is still allowed so the next question can be drafted.
 */
const Composer = ({ onSend, onStop, disabled }) => {
  const [value, setValue] = useState('');
  const textareaRef = useRef(null);

  // Grow with content up to ~6 lines
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 144)}px`;
  }, [value]);

  const submit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue('');
    requestAnimationFrame(() => textareaRef.current?.focus());
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  };

  const overLimit = value.length > MAX_LENGTH;
  const showCounter = value.length >= COUNTER_THRESHOLD;

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        submit();
      }}
      className="border-t border-slate-200 bg-white"
    >
      <div className="mx-auto max-w-3xl px-4 py-3">
        <div
          className={`flex items-end gap-2 rounded-2xl border bg-white px-3 py-2 shadow-soft transition focus-within:border-awash-400 focus-within:ring-2 focus-within:ring-awash-100 ${
            overLimit ? 'border-red-300' : 'border-slate-300'
          }`}
        >
          <textarea
            ref={textareaRef}
            rows={1}
            value={value}
            onChange={(event) => setValue(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              disabled ? 'Smart AI is responding...' : 'Ask about policies, claims, premiums...'
            }
            aria-label="Message"
            className="max-h-36 flex-1 resize-none bg-transparent py-1.5 text-[0.925rem] leading-relaxed text-slate-800 placeholder:text-slate-400 focus:outline-none"
          />
          {disabled ? (
            <button
              type="button"
              onClick={onStop}
              aria-label="Stop generating"
              className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-slate-800 text-white shadow-soft transition hover:bg-slate-700 active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-500 focus-visible:ring-offset-1 sm:h-9 sm:w-9"
            >
              <Square className="h-3.5 w-3.5 fill-current" aria-hidden="true" />
            </button>
          ) : (
            <button
              type="submit"
              disabled={!value.trim() || overLimit}
              aria-label="Send message"
              className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-awash-700 text-white shadow-soft transition hover:bg-awash-800 active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-awash-500 focus-visible:ring-offset-1 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:active:scale-100 sm:h-9 sm:w-9"
            >
              <Send className="h-4 w-4" aria-hidden="true" />
            </button>
          )}
        </div>
        <div className="mt-1 flex items-center justify-between px-1">
          <p className="text-[10px] text-slate-400">
            Enter to send · Shift+Enter for a new line
          </p>
          {showCounter && (
            <p
              className={`text-[10px] ${overLimit ? 'font-medium text-red-500' : 'text-slate-400'}`}
              aria-live="polite"
            >
              {value.length.toLocaleString()}/{MAX_LENGTH.toLocaleString()}
            </p>
          )}
        </div>
      </div>
    </form>
  );
};

export default Composer;
