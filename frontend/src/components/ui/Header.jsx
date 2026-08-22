import React, { useEffect, useState } from 'react';
import { Shield, Edit, Phone, Sparkles } from 'lucide-react';
import { chatAPI } from '../../services/api';
import config from '../../config';

const STATUS_LABELS = {
  checking: { text: 'Connecting...', dot: 'bg-slate-400' },
  online: { text: 'Online', dot: 'bg-emerald-500' },
  offline: { text: 'Service unavailable', dot: 'bg-red-500' },
};

/**
 * Slim sticky header: brand, assistant status, new conversation and hotline.
 * Status comes from one /health/ready call on mount plus a 60s poll.
 */
const Header = ({ onNewConversation, hasMessages, onNavigate, currentView }) => {
  const [status, setStatus] = useState('checking');

  useEffect(() => {
    let active = true;

    const check = async () => {
      try {
        const ready = await chatAPI.readiness();
        if (active) setStatus(ready.status === 'ready' ? 'online' : 'offline');
      } catch {
        if (active) setStatus('offline');
      }
    };

    check();
    const timer = setInterval(check, 60000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, []);

  const { text, dot } = STATUS_LABELS[status];

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-3xl items-center justify-between gap-3 px-4">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-awash-600 to-awash-900 shadow-soft">
            <Shield className="h-5 w-5 text-white" aria-hidden="true" />
          </div>
          <div className="min-w-0">
            <h1 className="truncate text-sm font-semibold text-slate-900">
              Awash Insurance
            </h1>
            <p className="flex items-center gap-1.5 text-xs text-slate-500">
              <span
                className={`h-1.5 w-1.5 rounded-full ${dot} ${status === 'online' ? 'animate-pulse' : ''}`}
                aria-hidden="true"
              />
              <span className="truncate">AwashAI Assistant · {text}</span>
            </p>
          </div>
        </div>

        <div className="flex flex-shrink-0 items-center gap-1">
          <button
            type="button"
            onClick={() => onNavigate?.('quote')}
            disabled={currentView === 'quote'}
            className="flex items-center gap-1.5 rounded-lg bg-awash-700 px-3 py-2 text-sm font-medium text-white transition hover:bg-awash-800 active:scale-[0.97] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-awash-500 focus-visible:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Sparkles className="h-4 w-4" aria-hidden="true" />
            <span className="hidden sm:inline">Get a Quote</span>
          </button>
          {hasMessages && (
            <button
              type="button"
              onClick={onNewConversation}
              aria-label="Start a new conversation"
              className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-awash-500"
            >
              <Edit className="h-4 w-4" aria-hidden="true" />
              <span className="hidden sm:inline">New conversation</span>
            </button>
          )}
          <a
            href={`tel:${config.support.phone.replace(/[^+\d]/g, '')}`}
            aria-label={`Call support at ${config.support.phone}`}
            className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium text-awash-700 transition hover:bg-awash-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-awash-500"
          >
            <Phone className="h-4 w-4" aria-hidden="true" />
            <span className="hidden md:inline">{config.support.phone}</span>
          </a>
        </div>
      </div>
    </header>
  );
};

export default Header;
