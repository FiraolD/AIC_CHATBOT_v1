import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Car,
  Heart,
  Home,
  Plane,
  Stethoscope,
  ArrowLeft,
  ArrowRight,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { chatAPI } from '../../services/api';

const PRODUCTS = [
  { id: 'motor', name: 'Motor', icon: Car, color: 'bg-blue-50 text-blue-700 border-blue-200' },
  { id: 'life', name: 'Life', icon: Heart, color: 'bg-rose-50 text-rose-700 border-rose-200' },
  { id: 'health', name: 'Health', icon: Stethoscope, color: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  { id: 'property', name: 'Property', icon: Home, color: 'bg-amber-50 text-amber-700 border-amber-200' },
  { id: 'travel', name: 'Travel', icon: Plane, color: 'bg-violet-50 text-violet-700 border-violet-200' },
];

/**
 * Full-page conversational quote flow.
 *
 * Flow:
 *   1. Product selection (chips)
 *   2. Questions asked one at a time (chat-like)
 *   3. Quote summary card
 */
const QuotePage = ({ onBack }) => {
  const [step, setStep] = useState('select'); // select | questions | loading | quote | error
  const [flow, setFlow] = useState(null);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [quote, setQuote] = useState(null);
  const [error, setError] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const scrollRef = useRef(null);
  const quoteRef = useRef(null);

  // Auto-scroll chat during questions
  useEffect(() => {
    if (step !== 'quote') {
      scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
    }
  }, [chatHistory, step]);

  // Scroll quote summary into view when it appears
  useEffect(() => {
    if (step === 'quote' && quoteRef.current) {
      setTimeout(() => {
        quoteRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    }
  }, [step]);

  const selectProduct = useCallback(async (productId) => {
    try {
      setError(null);
      setStep('loading');
      const flowData = await chatAPI.quote.start(productId);
      setFlow(flowData);
      setStep('questions');
      setChatHistory([
        {
          role: 'bot',
          text: `Great choice! Let me ask you a few questions about ${flowData.name}.`,
        },
        { role: 'bot', text: flowData.questions[0].text, questionId: flowData.questions[0].id },
      ]);
    } catch (err) {
      setError('Could not load the quote form. Please try again.');
      setStep('error');
    }
  }, []);

  const answerQuestion = useCallback(
    async (questionId, answer) => {
      const newAnswers = { ...answers, [questionId]: answer };
      setAnswers(newAnswers);

      const nextIndex = questionIndex + 1;
      const nextQuestion = flow.questions[nextIndex];

      setChatHistory((prev) => [
        ...prev,
        { role: 'user', text: answer },
      ]);

      if (nextQuestion) {
        setQuestionIndex(nextIndex);
        setChatHistory((prev) => [
          ...prev,
          { role: 'bot', text: nextQuestion.text, questionId: nextQuestion.id },
        ]);
      } else {
        setStep('loading');
        try {
          const result = await chatAPI.quote.calculate(flow.flow_id, newAnswers);
          setQuote(result);
          setChatHistory((prev) => [
            ...prev,
            { role: 'bot', text: 'Here is your quick quote!' },
          ]);
          setStep('quote');
        } catch (err) {
          setError('Could not calculate your quote. Please try again.');
          setStep('error');
        }
      }
    },
    [answers, flow, questionIndex]
  );

  const goBack = useCallback(() => {
    if (step === 'quote' || step === 'error') {
      setStep('questions');
      setQuestionIndex(flow.questions.length - 1);
      setChatHistory((prev) => prev.slice(0, -1));
      return;
    }
    if (step === 'questions') {
      if (questionIndex > 0) {
        setQuestionIndex(questionIndex - 1);
        setChatHistory((prev) => prev.slice(0, -2));
      } else {
        setStep('select');
        setChatHistory([]);
      }
    }
  }, [step, flow, questionIndex]);

  return (
    <div className="flex h-full flex-col bg-slate-50">
      {/* Sticky header */}
      <div className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 flex-shrink-0">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-awash-600 to-awash-900">
            <ShieldCheck className="h-4 w-4 text-white" aria-hidden="true" />
          </div>
          <h2 className="text-sm font-semibold text-slate-900">Get a Quick Quote</h2>
        </div>
        <button
          type="button"
          onClick={onBack}
          aria-label="Back to chat"
          className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-awash-500"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          <span className="hidden sm:inline">Back to chat</span>
        </button>
      </div>

      {/* Scrollable content */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-6">
        {step === 'select' && (
          <div className="mx-auto flex max-w-2xl flex-col items-center gap-6 py-8 animate-fade-in">
            <Sparkles className="h-12 w-12 text-awash-500" aria-hidden="true" />
            <h3 className="text-xl font-semibold text-slate-900 sm:text-2xl">
              What would you like to insure?
            </h3>
            <p className="max-w-md text-center text-sm leading-relaxed text-slate-500">
              Choose a product below to get a quick indicative quote. We'll ask you a few simple questions and calculate your premium.
            </p>
            <div className="grid w-full grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
              {PRODUCTS.map((product) => {
                const Icon = product.icon;
                return (
                  <button
                    key={product.id}
                    type="button"
                    onClick={() => selectProduct(product.id)}
                    className={`flex flex-col items-center gap-3 rounded-2xl border px-4 py-6 text-sm font-medium transition hover:-translate-y-0.5 hover:shadow-card active:scale-[0.97] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-awash-500 ${product.color}`}
                  >
                    <Icon className="h-10 w-10" aria-hidden="true" />
                    <span className="text-base">{product.name}</span>
                    <span className="text-xs opacity-70">Insurance</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {(step === 'questions' || step === 'loading' || step === 'quote' || step === 'error') && (
          <div className="mx-auto max-w-2xl space-y-3">
            {chatHistory.map((msg, i) => (
              <div
                key={i}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-message-in`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${
                    msg.role === 'user'
                      ? 'rounded-tr-sm bg-awash-700 text-white'
                      : 'rounded-tl-sm border border-slate-200 bg-white text-slate-700 shadow-soft'
                  }`}
                >
                  {msg.text}
                </div>
              </div>
            ))}

            {step === 'loading' && (
              <div className="flex justify-start animate-message-in">
                <div className="rounded-2xl rounded-tl-sm border border-slate-200 bg-white px-4 py-3.5 shadow-soft">
                  <div className="flex gap-1.5">
                    {[0, 1, 2].map((i) => (
                      <span
                        key={i}
                        className="h-1.5 w-1.5 animate-dot-bounce rounded-full bg-awash-600"
                        style={{ animationDelay: `${i * 0.15}s` }}
                      />
                    ))}
                  </div>
                </div>
              </div>
            )}

            {step === 'questions' && (
              <QuestionInput
                question={flow.questions[questionIndex]}
                onAnswer={(answer) =>
                  answerQuestion(flow.questions[questionIndex].id, answer)
                }
              />
            )}

            {step === 'quote' && quote && (
              <div ref={quoteRef}>
                <QuoteSummary quote={quote} onBack={onBack} />
              </div>
            )}

            {step === 'error' && (
              <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Bottom navigation */}
      {step !== 'select' && step !== 'quote' && (
        <div className="border-t border-slate-200 bg-white px-4 py-3 flex-shrink-0">
          <div className="mx-auto flex max-w-2xl items-center justify-between">
            <button
              type="button"
              onClick={goBack}
              disabled={step === 'loading'}
              className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900 disabled:opacity-40 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-awash-500"
            >
              <ArrowLeft className="h-4 w-4" aria-hidden="true" />
              Back
            </button>
            <p className="text-xs text-slate-400">
              {step === 'questions' && flow
                ? `Question ${questionIndex + 1} of ${flow.questions.length}`
                : ''}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

/** Renders chip-based or text input for a question. */
const QuestionInput = ({ question, onAnswer }) => {
  const [textValue, setTextValue] = useState('');

  if (question.type === 'choice' && question.options?.length) {
    return (
      <div className="flex flex-wrap gap-2 pt-2 animate-message-in">
        {question.options.map((option) => (
          <button
            key={option}
            type="button"
            onClick={() => onAnswer(option)}
            className="rounded-full border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-600 shadow-soft transition hover:-translate-y-0.5 hover:border-awash-300 hover:text-awash-700 hover:shadow-card active:scale-[0.97] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-awash-500"
          >
            {option}
          </button>
        ))}
      </div>
    );
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        const trimmed = textValue.trim();
        if (trimmed) {
          onAnswer(trimmed);
          setTextValue('');
        }
      }}
      className="flex items-center gap-2 pt-2 animate-message-in"
    >
      <input
        type="text"
        value={textValue}
        onChange={(e) => setTextValue(e.target.value)}
        placeholder="Type your answer..."
        className="flex-1 rounded-xl border border-slate-300 px-3 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 focus:border-awash-400 focus:outline-none focus:ring-2 focus:ring-awash-100"
      />
      <button
        type="submit"
        disabled={!textValue.trim()}
        className="flex h-10 w-10 items-center justify-center rounded-xl bg-awash-700 text-white transition hover:bg-awash-800 active:scale-95 disabled:cursor-not-allowed disabled:bg-slate-300"
      >
        <ArrowRight className="h-4 w-4" aria-hidden="true" />
      </button>
    </form>
  );
};

/** Displays the final quote summary. */
const QuoteSummary = ({ quote, onBack }) => {
  const isTravel = quote.product_name === 'Travel Insurance';

  return (
    <div className="mt-3 rounded-2xl border border-awash-200 bg-gradient-to-br from-awash-50 to-white p-5 animate-message-in shadow-card">
      <div className="mb-3 flex items-center gap-2">
        <Sparkles className="h-2 w-2 text-awash-600" aria-hidden="true" />
        <h3 className="text-base font-semibold text-slate-900">Your Quote</h3>
      </div>

      <div className="mb-4 space-y-1.5 text-sm text-slate-600">
        {Object.entries(quote.answers).map(([key, value]) => (
          <div key={key} className="flex justify-between gap-4">
            <span className="capitalize text-slate-500">
              {key.replace(/_/g, ' ')}:
            </span>
            <span className="font-medium text-slate-700 text-right">{value}</span>
          </div>
        ))}
      </div>

      <div className="border-t border-awash-100 pt-4">
        {isTravel ? (
          <div className="text-center">
            <p className="text-xs text-slate-500">Total Premium</p>
            <p className="text-3xl font-bold text-awash-700">
              ETB {quote.premium_annual.toLocaleString()}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4 text-center">
            <div className="rounded-xl bg-white p-3 shadow-soft">
              <p className="text-xs text-slate-500">Monthly</p>
              <p className="text-2xl font-bold text-awash-700">
                ETB {quote.premium_monthly.toLocaleString()}
              </p>
            </div>
            <div className="rounded-xl bg-white p-3 shadow-soft">
              <p className="text-xs text-slate-500">Annual</p>
              <p className="text-2xl font-bold text-awash-700">
                ETB {quote.premium_annual.toLocaleString()}
              </p>
            </div>
          </div>
        )}
      </div>

      <p className="mt-4 text-center text-xs text-slate-400">
        This is an indicative quote. Final premium may vary based on underwriting assessment.
      </p>

      <div className="mt-4 flex flex-col gap-2 sm:flex-row">
        <a
          href="/contact-us"
          className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-awash-700 px-4 py-3 text-sm font-medium text-white transition hover:bg-awash-800 active:scale-[0.97]"
        >
          Contact us to proceed
        </a>
        <button
          type="button"
          onClick={onBack}
          className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-600 transition hover:bg-slate-50 active:scale-[0.97]"
        >
          Get another quote
        </button>
      </div>
    </div>
  );
};

export default QuotePage;
