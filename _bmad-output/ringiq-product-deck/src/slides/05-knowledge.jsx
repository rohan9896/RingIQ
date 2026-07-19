import React from 'react';
import { motion } from 'framer-motion';
import {
  ArrowRight,
  BookOpenCheck,
  Building2,
  CheckCircle2,
  CircleHelp,
  FileText,
  History,
  Layers3,
  Lightbulb,
  ListChecks,
  LockKeyhole,
  MessageSquareText,
  Pin,
  ShieldCheck,
  Sparkles,
  UserRound,
} from 'lucide-react';

const inputs = [
  { icon: Building2, title: 'Business profile', detail: 'Identity, offer, positioning' },
  { icon: ListChecks, title: 'Structured Q&A', detail: 'Category-specific answers' },
  { icon: FileText, title: 'Supporting notes', detail: 'Only approved call guidance' },
];

const contextLayers = [
  { icon: BookOpenCheck, label: 'Tenant context', detail: 'Pinned knowledge version' },
  { icon: UserRound, label: 'Lead attributes', detail: 'Known prospect details' },
  { icon: MessageSquareText, label: 'Conversation state', detail: 'What has been said now' },
];

const guardrails = [
  { icon: CheckCircle2, title: 'Complete before publish', detail: 'Required answers block publication.' },
  { icon: CircleHelp, title: 'Unknown stays unknown', detail: 'Missing information is never invented.' },
  { icon: LockKeyhole, title: 'Workspace isolation', detail: 'Tenant data never crosses workspaces.' },
];

const rise = {
  hidden: { opacity: 0, y: 18 },
  show: { opacity: 1, y: 0 },
};

export default function KnowledgeSlide() {
  return (
    <div className="slide-page relative bg-bg-base text-text-primary">
      <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        <div className="absolute -left-40 -top-24 h-[34rem] w-[34rem] rounded-full bg-primary-500/18 blur-[120px]" />
        <div className="absolute -right-32 top-[18%] h-[31rem] w-[31rem] rounded-full bg-accent-500/14 blur-[120px]" />
        <div className="absolute bottom-0 left-[38%] h-48 w-[35rem] rounded-full bg-primary-400/10 blur-[100px]" />
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
        className="relative z-10 mb-7 shrink-0"
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55, ease: 'easeOut' }}
      >
        <div className="mb-4 flex items-center gap-3">
          <span className="font-body text-xs font-semibold tracking-[0.22em] text-primary-300">KNOWLEDGE SYSTEM</span>
          <span className="h-px w-20 bg-gradient-to-r from-primary-400/60 to-transparent" />
        </div>
        <h1 className="max-w-[71rem] font-display text-[3.3rem] font-semibold leading-[1.02] tracking-[-0.04em] text-text-primary">
          Private knowledge becomes the agent&apos;s{' '}
          <span className="text-primary-300">operating context</span>
        </h1>
        <p className="mt-3 font-body text-lg text-text-secondary">
          Curated tenant truth is published once, then pinned into the production call that needs it.
        </p>
      </motion.header>

      <div className="slide-content relative z-10 flex min-h-0 flex-col justify-center">
        <motion.div
          className="grid grid-cols-[0.88fr_0.58fr_1.12fr] items-stretch gap-7"
          initial="hidden"
          animate="show"
          transition={{ staggerChildren: 0.13, delayChildren: 0.12 }}
        >
          <motion.section variants={rise} transition={{ duration: 0.48 }} className="flex min-w-0 flex-col">
            <div className="mb-3 flex items-center justify-between">
              <p className="font-body text-xs font-semibold tracking-[0.18em] text-text-muted">TENANT INPUTS</p>
              <span className="rounded-full border border-border-default/70 bg-bg-card/60 px-2.5 py-1 font-body text-[0.62rem] tracking-[0.12em] text-text-secondary">PRIVATE</span>
            </div>
            <div className="space-y-3">
              {inputs.map(({ icon: Icon, title, detail }, index) => (
                <motion.div
                  key={title}
                  className="group relative flex items-center gap-4 rounded-xl border border-border-default/70 bg-bg-card/65 px-4 py-3.5 backdrop-blur-md"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.25 + index * 0.1, duration: 0.42 }}
                  whileHover={{ x: 4 }}
                >
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-primary-400/25 bg-primary-500/12">
                    <Icon className="h-5 w-5 text-primary-200" strokeWidth={1.8} />
                  </div>
                  <div className="min-w-0">
                    <p className="font-display text-base font-semibold text-text-primary">{title}</p>
                    <p className="mt-0.5 truncate font-body text-xs text-text-muted">{detail}</p>
                  </div>
                  <ArrowRight className="ml-auto h-4 w-4 shrink-0 text-primary-300/70" />
                </motion.div>
              ))}
            </div>
          </motion.section>

          <motion.section
            variants={rise}
            transition={{ duration: 0.55, delay: 0.12 }}
            className="relative flex min-w-0 items-center justify-center"
            aria-label="Publish and pin active knowledge base"
          >
            <div className="absolute inset-x-0 top-1/2 h-px bg-gradient-to-r from-primary-400/20 via-primary-300/70 to-primary-400/20" />
            <motion.div
              className="relative z-10 w-full rounded-2xl border border-primary-300/40 bg-bg-card/80 p-5 text-center shadow-2xl backdrop-blur-xl"
              animate={{ boxShadow: ['0 0 0 0 currentColor', '0 0 0 12px transparent'] }}
              transition={{ duration: 2.5, repeat: Infinity, ease: 'easeOut' }}
            >
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full border border-primary-300/40 bg-primary-500/20">
                <BookOpenCheck className="h-7 w-7 text-primary-200" strokeWidth={1.7} />
              </div>
              <p className="mt-4 font-body text-[0.62rem] font-semibold tracking-[0.17em] text-primary-300">ACTIVE KNOWLEDGE BASE</p>
              <h2 className="mt-1.5 font-display text-xl font-semibold text-text-primary">Publish + pin</h2>
              <div className="mt-4 space-y-2">
                <div className="flex items-center justify-center gap-2 rounded-lg border border-border-subtle bg-bg-base/60 px-3 py-2 font-body text-xs text-text-secondary">
                  <History className="h-3.5 w-3.5 text-primary-300" />
                  Versioned source of truth
                </div>
                <div className="flex items-center justify-center gap-2 rounded-lg border border-primary-400/25 bg-primary-500/10 px-3 py-2 font-body text-xs text-primary-200">
                  <Pin className="h-3.5 w-3.5" />
                  Pinned to this call
                </div>
              </div>
            </motion.div>
          </motion.section>

          <motion.section variants={rise} transition={{ duration: 0.55, delay: 0.22 }} className="min-w-0">
            <div className="mb-3 flex items-center justify-between">
              <p className="font-body text-xs font-semibold tracking-[0.18em] text-text-muted">SAFE CONVERSATION CONTEXT</p>
              <div className="flex items-center gap-1.5 font-body text-[0.62rem] font-semibold tracking-[0.12em] text-primary-300">
                <span className="h-1.5 w-1.5 rounded-full bg-primary-300" />
                CALL-BOUND
              </div>
            </div>
            <div className="relative overflow-hidden rounded-2xl border border-primary-300/35 bg-bg-card/70 p-5 backdrop-blur-xl">
              <div className="absolute -right-14 -top-14 h-40 w-40 rounded-full bg-primary-500/15 blur-3xl" />
              <div className="relative flex items-start justify-between gap-5">
                <div>
                  <p className="font-body text-[0.65rem] font-semibold tracking-[0.16em] text-primary-300">AGENT INSTRUCTIONS</p>
                  <h2 className="mt-1.5 font-display text-[1.55rem] font-semibold leading-tight text-text-primary">One grounded prompt context</h2>
                </div>
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-primary-300/35 bg-primary-500/15">
                  <Layers3 className="h-5 w-5 text-primary-200" />
                </div>
              </div>

              <div className="relative mt-5 space-y-2.5">
                {contextLayers.map(({ icon: Icon, label, detail }, index) => (
                  <motion.div
                    key={label}
                    className="flex items-center gap-3 rounded-xl border border-border-subtle bg-bg-base/55 px-3.5 py-2.5"
                    initial={{ opacity: 0, x: 18 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.55 + index * 0.1, duration: 0.38 }}
                  >
                    <Icon className="h-4 w-4 shrink-0 text-primary-300" />
                    <div className="min-w-0 flex-1">
                      <p className="font-display text-sm font-semibold text-text-primary">{label}</p>
                      <p className="font-body text-[0.68rem] text-text-muted">{detail}</p>
                    </div>
                    <span className="h-1.5 w-1.5 rounded-full bg-primary-300" />
                  </motion.div>
                ))}
              </div>

              <div className="relative mt-4 flex items-center gap-2 border-t border-border-subtle pt-3 font-body text-xs text-text-secondary">
                <Sparkles className="h-4 w-4 text-primary-300" />
                Context is assembled for the live conversation—without cross-tenant mixing.
              </div>
            </div>
          </motion.section>
        </motion.div>

        <motion.div
          className="mt-6 grid grid-cols-[1fr_1fr_1fr_0.92fr] gap-3"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.82, duration: 0.48 }}
        >
          {guardrails.map(({ icon: Icon, title, detail }) => (
            <div key={title} className="flex min-w-0 items-start gap-3 rounded-xl border border-border-default/60 bg-bg-card/50 px-3.5 py-3 backdrop-blur-md">
              <Icon className="mt-0.5 h-4 w-4 shrink-0 text-primary-300" />
              <div className="min-w-0">
                <p className="font-display text-xs font-semibold text-text-primary">{title}</p>
                <p className="mt-1 font-body text-[0.66rem] leading-snug text-text-muted">{detail}</p>
              </div>
            </div>
          ))}
          <div className="flex min-w-0 items-start gap-3 rounded-xl border border-dashed border-primary-400/35 bg-primary-500/10 px-3.5 py-3">
            <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-primary-300" />
            <div className="min-w-0">
              <p className="font-body text-[0.58rem] font-semibold tracking-[0.14em] text-primary-300">FUTURE LOOP</p>
              <p className="mt-1 font-body text-[0.66rem] leading-snug text-text-secondary">Unanswered questions surface as knowledge gaps for continuous improvement.</p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
