import React from 'react';
import { Shield } from 'lucide-react';

/** Animated three-dot indicator shown while waiting for the first token. */
const TypingIndicator = () => (
  <div className="flex animate-message-in gap-3">
    <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-awash-600 to-awash-900 shadow-soft">
      <Shield className="h-4 w-4 text-white" aria-hidden="true" />
    </div>
    <div
      className="flex items-center gap-1.5 rounded-2xl rounded-tl-sm border border-slate-200 bg-white px-4 py-3.5 shadow-soft"
      role="status"
      aria-label="Assistant is typing"
    >
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-1.5 w-1.5 animate-dot-bounce rounded-full bg-awash-600"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  </div>
);

export default TypingIndicator;
