import React from 'react';
import { motion } from 'framer-motion';
import {
  AlertCircle,
  ArrowRight,
  CalendarClock,
  CheckCircle2,
  ChevronRight,
  CircleDot,
  FileText,
  Filter,
  Flame,
  History,
  Lightbulb,
  ListChecks,
  MessageSquareText,
  Mic2,
  PhoneCall,
  Search,
  Snowflake,
  Sparkles,
  Tag,
  UserRoundX,
  Volume2,
} from 'lucide-react';

const reveal = {
  hidden: { opacity: 0, y: 18 },
  show: { opacity: 1, y: 0 },
};

const outcomes = [
  { label: 'Hot', icon: Flame, emphasis: true },
  { label: 'Warm', icon: Sparkles, emphasis: true },
  { label: 'Cold', icon: Snowflake },
  { label: 'Callback requested', icon: CalendarClock },
  { label: 'Not interested', icon: UserRoundX },
  { label: 'Unanswered', icon: PhoneCall },
  { label: 'Invalid number', icon: AlertCircle },
  { label: 'Needs review', icon: CircleDot },
];

const queue = [
  { status: 'HOT', reason: 'Budget and timeline aligned', evidence: 'Summary + facts', icon: Flame },
  { status: 'WARM', reason: 'Needs a project comparison', evidence: 'Transcript evidence', icon: Sparkles },
  { status: 'CALLBACK', reason: 'Asked to continue later', evidence: 'Date + time captured', icon: CalendarClock },
];

const waveform = [36, 62, 48, 82, 56, 92, 66, 42, 74, 52, 86, 60, 38, 70, 46, 78, 54, 34];

export default function IntelligenceSlide() {
  return (
    <div className="slide-page relative bg-bg-base text-text-primary" data-slide="09-intelligence">
      <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        <div className="absolute -left-36 -top-44 h-[34rem] w-[34rem] rounded-full bg-primary-500/20 blur-[125px]" />
        <div className="absolute -right-32 top-16 h-[32rem] w-[32rem] rounded-full bg-accent-500/10 blur-[130px]" />
        <div className="absolute bottom-0 left-[38%] h-52 w-[38rem] rounded-full bg-primary-400/10 blur-[105px]" />
        <div className="absolute inset-0 opacity-20">
          {Array.from({ length: 13 }).map((_, index) => (
            <div
              key={`v-${index}`}
              className="absolute inset-y-0 w-px bg-border-subtle"
              style={{ left: `${index * 8.33}%` }}
            />
          ))}
          {Array.from({ length: 8 }).map((_, index) => (
            <div
              key={`h-${index}`}
              className="absolute inset-x-0 h-px bg-border-subtle"
              style={{ top: `${index * 14.28}%` }}
            />
          ))}
        </div>
      </div>

      <motion.header
        className="relative z-10 mb-5 shrink-0"
        initial="hidden"
        animate="show"
        transition={{ staggerChildren: 0.1 }}
      >
        <motion.div variants={reveal} transition={{ duration: 0.4 }} className="mb-3 flex items-center gap-3">
          <span className="inline-flex items-center gap-2 rounded-full border border-primary-300/30 bg-primary-500/15 px-3 py-1.5 font-body text-xs font-semibold tracking-[0.18em] text-primary-200">
            <Sparkles className="h-3.5 w-3.5" /> COMPLETE-PRODUCT OUTCOME
          </span>
          <span className="h-px w-20 bg-gradient-to-r from-primary-400/60 to-transparent" />
        </motion.div>
        <motion.h1
          variants={reveal}
          transition={{ duration: 0.55 }}
          className="mobile-title font-display text-[3.35rem] font-semibold leading-[0.98] tracking-[-0.045em] text-text-primary"
        >
          Every conversation becomes a <span className="text-primary-300">decision record</span>
        </motion.h1>
      </motion.header>

      <div className="mobile-stack slide-content relative z-10 grid grid-rows-[1fr_auto] gap-4">
        <div className="mobile-stack grid min-h-0 grid-cols-[1.18fr_0.74fr_1.08fr] gap-4">
          <motion.section
            className="mobile-card glass relative flex min-w-0 flex-col overflow-hidden rounded-2xl p-4"
            initial={{ opacity: 0, x: -22 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.16, duration: 0.6, ease: 'easeOut' }}
            aria-label="Evidence captured from a conversation"
          >
            <div className="absolute -left-16 bottom-10 h-48 w-48 rounded-full bg-primary-500/10 blur-3xl" aria-hidden="true" />
            <div className="relative flex items-center justify-between">
              <div>
                <p className="font-body text-xs font-semibold tracking-[0.18em] text-primary-300">01 · EVIDENCE</p>
                <h2 className="mt-1 font-display text-xl font-semibold tracking-[-0.02em] text-text-primary">The complete call record</h2>
              </div>
              <Volume2 className="h-5 w-5 text-primary-200" />
            </div>

            <div className="relative mt-3 rounded-xl border border-primary-300/30 bg-bg-base/50 p-3">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-500/20">
                    <PhoneCall className="h-4 w-4 text-primary-200" />
                  </div>
                  <div>
                    <p className="font-body text-sm font-semibold text-text-primary">Call attempt</p>
                    <p className="font-body text-xs text-text-muted">Outbound · connected · agent version</p>
                  </div>
                </div>
                <span className="rounded-full border border-primary-300/30 bg-primary-500/15 px-2.5 py-1 font-body text-[0.65rem] font-semibold tracking-[0.12em] text-primary-200">METADATA</span>
              </div>
              <div className="mt-3 flex h-9 items-center gap-1 rounded-lg border border-border-subtle bg-bg-card/50 px-3">
                <Mic2 className="mr-2 h-4 w-4 shrink-0 text-primary-200" />
                {waveform.map((height, index) => (
                  <motion.span
                    key={index}
                    className="w-1 rounded-full bg-primary-300"
                    initial={{ height: '18%' }}
                    animate={{ height: [`${Math.max(18, height - 22)}%`, `${height}%`, `${Math.max(20, height - 14)}%`] }}
                    transition={{ duration: 0.8 + (index % 4) * 0.1, repeat: Infinity, repeatType: 'mirror', ease: 'easeInOut' }}
                  />
                ))}
                <span className="ml-auto font-body text-xs text-text-muted">Recording</span>
              </div>
            </div>

            <div className="mobile-compact-grid relative mt-3 grid grid-cols-2 gap-2.5">
              <div className="rounded-xl border border-border-subtle bg-bg-base/45 p-3">
                <div className="flex items-center gap-2 font-body text-xs font-semibold tracking-[0.12em] text-text-muted">
                  <MessageSquareText className="h-4 w-4 text-primary-200" /> TRANSCRIPT
                </div>
                <p className="mt-2 font-body text-xs leading-relaxed text-text-secondary">Searchable exchange with speaker turns and source evidence.</p>
              </div>
              <div className="rounded-xl border border-border-subtle bg-bg-base/45 p-3">
                <div className="flex items-center gap-2 font-body text-xs font-semibold tracking-[0.12em] text-text-muted">
                  <FileText className="h-4 w-4 text-primary-200" /> SUMMARY
                </div>
                <p className="mt-2 font-body text-xs leading-relaxed text-text-secondary">Concise intent, objections, and agreed next step.</p>
              </div>
            </div>

            <div className="relative mt-2.5 space-y-2">
              <div className="flex items-center justify-between rounded-lg border border-border-subtle bg-bg-card/50 px-3 py-2">
                <span className="flex items-center gap-2 font-body text-xs text-text-secondary"><ListChecks className="h-4 w-4 text-primary-200" /> Qualification facts</span>
                <span className="font-body text-xs text-text-muted">Captured as fields</span>
              </div>
              <div className="flex items-center justify-between rounded-lg border border-border-subtle bg-bg-card/50 px-3 py-2">
                <span className="flex items-center gap-2 font-body text-xs text-text-secondary"><CalendarClock className="h-4 w-4 text-primary-200" /> Callback date + time</span>
                <span className="font-body text-xs text-text-muted">When requested</span>
              </div>
              <div className="flex items-center justify-between rounded-lg border border-border-subtle bg-bg-card/50 px-3 py-2">
                <span className="flex items-center gap-2 font-body text-xs text-text-secondary"><Lightbulb className="h-4 w-4 text-primary-200" /> Knowledge gaps</span>
                <span className="font-body text-xs text-text-muted">Flagged for review</span>
              </div>
            </div>
          </motion.section>

          <motion.section
            className="mobile-card glass relative flex min-w-0 flex-col overflow-hidden rounded-2xl p-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.28, duration: 0.6 }}
            aria-label="AI decision outcomes"
          >
            <div className="relative">
              <p className="font-body text-xs font-semibold tracking-[0.18em] text-primary-300">02 · DECISION</p>
              <h2 className="mt-1 font-display text-xl font-semibold tracking-[-0.02em] text-text-primary">One explicit outcome</h2>
              <p className="mt-1 font-body text-xs leading-relaxed text-text-muted">Evidence remains attached to every classification.</p>
            </div>

            <div className="mobile-compact-grid relative mt-3 grid flex-1 grid-cols-2 content-center gap-2.5">
              {outcomes.map(({ label, icon: Icon, emphasis }, index) => (
                <motion.div
                  key={label}
                  className={`flex min-h-16 min-w-0 flex-col justify-between rounded-xl border p-2.5 ${
                    emphasis
                      ? 'border-primary-300/40 bg-primary-500/20'
                      : 'border-border-subtle bg-bg-base/45'
                  }`}
                  initial={{ opacity: 0, scale: 0.94 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.38 + index * 0.06, duration: 0.35 }}
                >
                  <Icon className="h-4 w-4 text-primary-200" />
                  <span className="mt-2 font-body text-xs font-medium leading-tight text-text-secondary">{label}</span>
                </motion.div>
              ))}
            </div>

            <motion.div
              className="relative mt-3 flex items-center gap-2 rounded-xl border border-primary-300/30 bg-primary-500/15 px-3 py-2.5"
              animate={{ opacity: [0.75, 1, 0.75] }}
              transition={{ duration: 2.4, repeat: Infinity, ease: 'easeInOut' }}
            >
              <Tag className="h-4 w-4 text-primary-200" />
              <span className="font-body text-xs font-semibold text-primary-200">Structured, filterable, auditable</span>
            </motion.div>
          </motion.section>

          <motion.section
            className="mobile-card glass relative flex min-w-0 flex-col overflow-hidden rounded-2xl p-4"
            initial={{ opacity: 0, x: 22 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.36, duration: 0.6, ease: 'easeOut' }}
            aria-label="Sales follow-up queue"
          >
            <div className="absolute -right-12 bottom-10 h-44 w-44 rounded-full bg-accent-500/10 blur-3xl" aria-hidden="true" />
            <div className="relative flex items-start justify-between gap-3">
              <div>
                <p className="font-body text-xs font-semibold tracking-[0.18em] text-primary-300">03 · ACTION</p>
                <h2 className="mt-1 font-display text-xl font-semibold tracking-[-0.02em] text-text-primary">Follow-up queue</h2>
              </div>
              <ChevronRight className="h-5 w-5 text-primary-200" />
            </div>

            <div className="relative mt-3 flex items-center gap-2">
              <div className="flex min-w-0 flex-1 items-center gap-2 rounded-lg border border-border-default/70 bg-bg-base/50 px-3 py-2">
                <Search className="h-3.5 w-3.5 text-text-muted" />
                <span className="mobile-wrap truncate font-body text-xs text-text-muted">Search lead details…</span>
              </div>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-border-default/70 bg-bg-base/50">
                <Filter className="h-3.5 w-3.5 text-primary-200" />
              </div>
            </div>

            <div className="relative mt-3 space-y-2.5">
              {queue.map(({ status, reason, evidence, icon: Icon }, index) => (
                <motion.div
                  key={status}
                  className="rounded-xl border border-border-subtle bg-bg-base/45 p-3"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.52 + index * 0.1, duration: 0.4 }}
                >
                  <div className="flex items-start gap-3">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary-500/20">
                      <Icon className="h-4 w-4 text-primary-200" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-body text-[0.65rem] font-semibold tracking-[0.14em] text-primary-300">{status}</span>
                        <span className="font-body text-[0.65rem] text-text-muted">{evidence}</span>
                      </div>
                      <p className="mt-1 font-body text-sm font-medium leading-snug text-text-secondary">{reason}</p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>

            <div className="mobile-compact-grid relative mt-3 grid grid-cols-2 gap-2.5">
              <div className="rounded-xl border border-border-subtle bg-bg-card/50 p-3">
                <p className="font-body text-xs font-semibold text-text-secondary">Lead detail</p>
                <p className="mt-1 font-body text-xs text-text-muted">Conversation evidence in context</p>
              </div>
              <div className="rounded-xl border border-border-subtle bg-bg-card/50 p-3">
                <p className="font-body text-xs font-semibold text-text-secondary">Smart filters</p>
                <p className="mt-1 font-body text-xs text-text-muted">Outcome, callback, campaign</p>
              </div>
            </div>
          </motion.section>
        </div>

        <motion.section
          className="mobile-stack mobile-status flex items-center justify-between gap-5 rounded-2xl border border-primary-300/30 bg-primary-500/15 px-5 py-3 backdrop-blur-xl"
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.78, duration: 0.5 }}
          aria-label="Product delivery status"
        >
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-primary-300/30 bg-bg-base/45">
              <CheckCircle2 className="h-5 w-5 text-primary-200" />
            </div>
            <div>
              <p className="font-body text-[0.65rem] font-semibold tracking-[0.16em] text-primary-300">OPERATIONAL TODAY</p>
              <p className="mt-0.5 font-body text-sm text-text-secondary">Call activity exists today.</p>
            </div>
          </div>
          <ArrowRight className="mobile-flow-connector h-5 w-5 shrink-0 text-primary-300" />
          <div className="flex min-w-0 flex-[1.5] items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-primary-300/30 bg-bg-base/45">
              <History className="h-5 w-5 text-primary-200" />
            </div>
            <div>
              <p className="font-body text-[0.65rem] font-semibold tracking-[0.16em] text-primary-300">NEXT DELIVERY LAYER</p>
              <p className="mt-0.5 font-body text-sm leading-snug text-text-secondary">Persisted artifacts · AI classification · callback capture · follow-up queue</p>
            </div>
          </div>
        </motion.section>
      </div>
    </div>
  );
}
