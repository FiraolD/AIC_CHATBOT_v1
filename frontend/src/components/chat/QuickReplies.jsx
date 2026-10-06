import React from 'react';
import {
  ShieldCheck,
  FileText,
  ClipboardList,
  Calculator,
  HeartPulse,
} from 'lucide-react';

const suggestions = [
  {
    text: 'What types of insurance do you offer?',
    icon: ShieldCheck,
  },
  {
    text: 'How do I file a claim?',
    icon: FileText,
  },
  {
    text: 'What documents do I need for a motor insurance claim?',
    icon: ClipboardList,
  },
  {
    text: 'How is my premium calculated?',
    icon: Calculator,
  },
  {
    text: 'Does health insurance cover pre-existing conditions?',
    icon: HeartPulse,
  },
];

/** Suggestion chips shown in the welcome state to guide first-time users. */
const QuickReplies = ({ onSelect }) => (
  <div className="flex max-w-xl flex-wrap justify-center gap-2">
    {suggestions.map(({ text, icon: Icon }, index) => (
      <span
        key={text}
        style={{ animationDelay: `${0.1 + index * 0.06}s` }}
        className="animate-chip-in opacity-0"
      >
        <button
          type="button"
          onClick={() => onSelect(text)}
          className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3.5 py-2.5 text-xs text-slate-600 shadow-soft transition hover:-translate-y-0.5 hover:border-awash-300 hover:text-awash-700 hover:shadow-card active:scale-[0.97] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-awash-500 sm:text-sm"
        >
          <Icon className="h-4 w-4 flex-shrink-0 text-awash-500" aria-hidden="true" />
          {text}
        </button>
      </span>
    ))}
  </div>
);

export default QuickReplies;
