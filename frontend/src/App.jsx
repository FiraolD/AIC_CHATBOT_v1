import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Shield, ArrowDown } from 'lucide-react';
import { useChat } from './hooks/useChat';
import Header from './components/ui/Header';
import Footer from './components/ui/Footer';
import ChatMessage from './components/chat/ChatMessage';
import Composer from './components/chat/Composer';
import QuickReplies from './components/chat/QuickReplies';
import TypingIndicator from './components/chat/TypingIndicator';
import ErrorBanner from './components/chat/ErrorBanner';
import QuotePage from './components/quote/QuotePage';

/** Welcome hero shown before the first message of a conversation. */
const WelcomeState = ({ onSuggestion }) => (
  <div className="flex flex-1 animate-fade-in flex-col items-center justify-center gap-6 px-4 py-12 text-center">
    <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-awash-600 to-awash-900 shadow-card">
      <Shield className="h-8 w-8 text-white" aria-hidden="true" />
    </div>
    <div className="max-w-md">
      <h2 className="text-xl font-semibold text-slate-900 sm:text-2xl">
        How can we help you today?
      </h2>
      <p className="mt-2 text-sm leading-relaxed text-slate-500">
        Ask about insurance products, coverage details, claims and premiums.
        For urgent claims, call our 24/7 hotline from the header.
      </p>
    </div>
    <QuickReplies onSelect={onSuggestion} />
  </div>
);

/** Distance from the bottom (px) that still counts as "pinned to latest". */
const STICKY_SCROLL_THRESHOLD = 80;

function App() {
  const [view, setView] = useState('chat'); // chat | quote
  const {
    messages,
    isStreaming,
    error,
    rateLimitUntil,
    send,
    stopStreaming,
    newConversation,
    dismissError,
    submitFeedback,
  } = useChat();

  const scrollRef = useRef(null);
  const bottomRef = useRef(null);
  // Tracks whether the user is pinned to the bottom; refs avoid re-renders
  const atBottomRef = useRef(true);
  const [showJumpButton, setShowJumpButton] = useState(false);

  const lastMessage = messages[messages.length - 1];
  const waitingForFirstToken =
    isStreaming && lastMessage?.role === 'bot' && !lastMessage.content;

  // Follow the conversation only while the user is near the bottom, or when
  // they just sent a message themselves.
  useEffect(() => {
    if (atBottomRef.current || lastMessage?.role === 'user') {
      bottomRef.current?.scrollIntoView({
        behavior: isStreaming ? 'auto' : 'smooth',
        block: 'end',
      });
    }
  }, [messages, isStreaming, lastMessage?.role]);

  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
    const atBottom = distance < STICKY_SCROLL_THRESHOLD;
    atBottomRef.current = atBottom;
    setShowJumpButton(!atBottom);
  }, []);

  const jumpToLatest = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, []);

  return (
    <div className="flex h-full flex-col bg-slate-50">
      <Header
        onNewConversation={newConversation}
        hasMessages={messages.length > 0}
        onNavigate={setView}
        currentView={view}
      />

      {view === 'quote' ? (
        <QuotePage onBack={() => setView('chat')} />
      ) : (
        <>
          <div className="relative min-h-0 flex-1">
            <main
              ref={scrollRef}
              onScroll={handleScroll}
              className="chat-scroll h-full overflow-y-auto"
              aria-live="polite"
            >
              <div className="mx-auto flex min-h-full max-w-3xl flex-col px-4 py-6">
                {messages.length === 0 ? (
                  <WelcomeState onSuggestion={send} />
                ) : (
                  <div className="space-y-5">
                    {messages.map((message) => {
                      // The typing indicator covers an empty streaming bot bubble
                      if (message.role === 'bot' && message.streaming && !message.content) {
                        return null;
                      }
                      return (
                        <ChatMessage
                          key={message.id}
                          message={message}
                          onFeedback={submitFeedback}
                        />
                      );
                    })}
                    {waitingForFirstToken && <TypingIndicator />}
                    <div ref={bottomRef} />
                  </div>
                )}
              </div>
            </main>

            {showJumpButton && messages.length > 0 && (
              <button
                type="button"
                onClick={jumpToLatest}
                aria-label="Jump to the latest message"
                className="absolute bottom-4 left-1/2 z-30 flex h-9 w-9 -translate-x-1/2 animate-pop-in items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 shadow-card transition hover:text-awash-700 active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-awash-500"
              >
                <ArrowDown className="h-4 w-4" aria-hidden="true" />
              </button>
            )}
          </div>

          <ErrorBanner
            error={error}
            rateLimitUntil={rateLimitUntil}
            onDismiss={dismissError}
          />
          <Composer onSend={send} onStop={stopStreaming} disabled={isStreaming} />
        </>
      )}

      <Footer />
    </div>
  );
}

export default App;
