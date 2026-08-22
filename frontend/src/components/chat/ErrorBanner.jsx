import React, { useEffect, useState } from 'react';
import { AlertTriangle, Clock, WifiOff, X } from 'lucide-react';
import config from '../../config';

/**
 * Dismissible inline banner above the composer. Variants:
 * rate-limit (with live retry countdown), unavailable, unauthorized, network.
 */
const ErrorBanner = ({ error, rateLimitUntil, onDismiss }) => {
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    if (error?.type !== 'rate-limit') return undefined;
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [error?.type]);

  if (!error) return null;

  const retrySeconds = rateLimitUntil
    ? Math.max(0, Math.ceil((rateLimitUntil - now) / 1000))
    : 0;

  const variants = {
    'rate-limit': {
      icon: Clock,
      classes: 'border-amber-200 bg-amber-50 text-amber-800',
      title: 'You are sending messages too quickly',
      body:
        retrySeconds > 0
          ? `Please wait about ${retrySeconds}s before sending another message.`
          : 'You can send another message now.',
    },
    unavailable: {
      icon: AlertTriangle,
      classes: 'border-red-200 bg-red-50 text-red-700',
      title: 'The assistant is temporarily unavailable',
      body: `Please try again in a moment, or call our support team at ${config.support.phone}.`,
    },
    unauthorized: {
      icon: AlertTriangle,
      classes: 'border-red-200 bg-red-50 text-red-700',
      title: 'Access denied',
      body: 'This chat is not configured correctly. Please contact support.',
    },
    network: {
      icon: WifiOff,
      classes: 'border-slate-200 bg-slate-50 text-slate-600',
      title: 'Connection issue',
      body: 'Check your internet connection and try again.',
    },
  };

  const variant = variants[error.type] || variants.network;
  const Icon = variant.icon;

  return (
    <div className="mx-auto max-w-3xl px-4 pb-2">
      <div
        role="alert"
        className={`flex items-start gap-2.5 rounded-xl border px-3.5 py-2.5 text-sm shadow-soft ${variant.classes}`}
      >
        <Icon className="mt-0.5 h-4 w-4 flex-shrink-0" aria-hidden="true" />
        <div className="min-w-0 flex-1">
          <p className="font-medium">{variant.title}</p>
          <p className="mt-0.5 text-xs opacity-90">{variant.body}</p>
        </div>
        <button
          type="button"
          onClick={onDismiss}
          aria-label="Dismiss message"
          className="rounded p-1 opacity-60 transition hover:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-current"
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
};

export default ErrorBanner;
