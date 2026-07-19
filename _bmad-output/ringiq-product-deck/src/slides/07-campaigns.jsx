import React from 'react';
import { motion } from 'framer-motion';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  CircleDashed,
  Database,
  ListChecks,
  Pause,
  PhoneOutgoing,
  Play,
  RefreshCcw,
  ShieldCheck,
  Users,
  XCircle,
} from 'lucide-react';

const reveal = {
  hidden: { opacity: 0, y: 18 },
  show: { opacity: 1, y: 0 },
};

const lifecycle = [
  { label: 'Draft', icon: CircleDashed },
  { label: 'Ready', icon: ShieldCheck },
  { label: 'Running', icon: Play, active: true },
  { label: 'Paused / Resumed', icon: Pause },
  { label: 'Completed / Cancelled', icon: CheckCircle2, terminal: true },
];

const operationGroups = [
  {
    icon: Users,
    title: 'Start with eligible leads',
    detail: 'Readiness confirms an active knowledge base and complete business profile.',
  },
  {
    icon: RefreshCcw,
    title: 'Retry unanswered calls—safely',
    detail: 'One initial attempt, then up to 3 retries. A connected or terminal outcome stops the sequence.',
  },
  {
    icon: PhoneOutgoing,
    title: 'Keep “Call now” immediate',
    detail: 'Single-lead calls skip the retry loop, while campaign work remains durable in PostgreSQL.',
  },
];

const totals = [
  { value: '1,284', label: 'Total leads' },
  { value: '946', label: 'Attempts' },
  { value: '612', label: 'Connected' },
  { value: '03', label: 'Operational errors', warning: true },
];

export default function CampaignsSlide() {
  return (
    <div className="slide-page relative bg-bg-base text-text-primary">
      <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        <div className="absolute -left-36 -top-28 h-[32rem] w-[32rem] rounded-full bg-primary-500/20 blur-[120px]" />
        <div className="absolute -right-32 top-20 h-[30rem] w-[30rem] rounded-full bg-accent-500/10 blur-[125px]" />
        <div className="absolute bottom-0 left-1/3 h-48 w-[34rem] rounded-full bg-primary-400/10 blur-[100px]" />
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
        className="relative z-10 mb-6 shrink-0"
        initial="hidden"
        animate="show"
        transition={{ staggerChildren: 0.1 }}
      >
        <motion.div variants={reveal} className="mb-3 flex items-center gap-3">
          <span className="font-body text-xs font-semibold tracking-[0.2em] text-primary-300">
            CAMPAIGN OPERATIONS
          </span>
          <span className="h-px w-14 bg-gradient-to-r from-primary-400/60 to-transparent" />
        </motion.div>
        <motion.h1
          variants={reveal}
          transition={{ duration: 0.5 }}
          className="font-display text-[3.15rem] font-semibold leading-[1.02] tracking-[-0.04em] text-text-primary"
        >
          Campaign control without <span className="text-primary-300">operational guesswork</span>
        </motion.h1>
      </motion.header>

      <div className="slide-content relative z-10 flex flex-col gap-5">
        <motion.section
          className="glass relative overflow-hidden rounded-2xl border border-border-default/70 px-6 py-5"
          initial="hidden"
          animate="show"
          transition={{ staggerChildren: 0.09, delayChildren: 0.15 }}
          aria-label="Campaign lifecycle control rail"
        >
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Activity className="h-[1.125rem] w-[1.125rem] text-primary-300" />
              <h2 className="font-display text-lg font-semibold text-text-primary">Lifecycle control rail</h2>
            </div>
            <span className="rounded-full border border-primary-400/25 bg-primary-500/10 px-3 py-1 font-body text-xs font-semibold tracking-[0.12em] text-primary-200">
              OPERATOR CONTROLLED
            </span>
          </div>

          <div className="relative grid grid-cols-5 gap-3">
            <div className="absolute left-[9%] right-[9%] top-5 h-px bg-border-default" />
            <motion.div
              className="absolute left-[9%] top-5 h-px bg-primary-300"
              initial={{ width: 0 }}
              animate={{ width: '41%' }}
              transition={{ duration: 1, delay: 0.35, ease: 'easeOut' }}
            />
            {lifecycle.map(({ label, icon: Icon, active, terminal }) => (
              <motion.div key={label} variants={reveal} className="relative flex min-w-0 flex-col items-center text-center">
                <motion.div
                  className={`relative z-10 flex h-10 w-10 items-center justify-center rounded-full border ${
                    active
                      ? 'border-primary-300/50 bg-primary-500/25 text-primary-200'
                      : 'border-border-default bg-bg-base text-text-muted'
                  }`}
                  animate={active ? { boxShadow: ['0 0 0 0 currentColor', '0 0 0 9px transparent'] } : undefined}
                  transition={active ? { duration: 2.2, repeat: Infinity, ease: 'easeOut' } : undefined}
                >
                  <Icon className="h-4 w-4" strokeWidth={1.9} />
                  {terminal && (
                    <span className="absolute -bottom-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full border border-border-default bg-bg-base">
                      <XCircle className="h-2.5 w-2.5 text-text-muted" />
                    </span>
                  )}
                </motion.div>
                <p className={`mt-2 font-display text-sm font-semibold ${active ? 'text-primary-200' : 'text-text-secondary'}`}>
                  {label}
                </p>
              </motion.div>
            ))}
          </div>
        </motion.section>

        <div className="grid min-h-0 flex-1 grid-cols-[1.3fr_0.7fr] gap-5">
          <motion.section
            className="glass rounded-2xl border border-border-default/70 p-5"
            initial="hidden"
            animate="show"
            transition={{ staggerChildren: 0.1, delayChildren: 0.3 }}
            aria-label="Campaign operating rules"
          >
            <motion.div variants={reveal} className="mb-3 flex items-center gap-2.5">
              <ListChecks className="h-5 w-5 text-primary-300" />
              <h2 className="font-display text-xl font-semibold tracking-[-0.02em] text-text-primary">
                Guardrails built into every launch
              </h2>
            </motion.div>

            <div className="grid grid-cols-3 gap-3">
              {operationGroups.map(({ icon: Icon, title, detail }) => (
                <motion.article
                  key={title}
                  variants={reveal}
                  transition={{ duration: 0.45 }}
                  className="rounded-xl border border-border-subtle bg-bg-card/55 p-4 backdrop-blur-md"
                  whileHover={{ y: -3 }}
                >
                  <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-primary-500/15">
                    <Icon className="h-[1.125rem] w-[1.125rem] text-primary-200" />
                  </div>
                  <h3 className="font-display text-base font-semibold leading-snug text-text-primary">{title}</h3>
                  <p className="mt-2 font-body text-sm leading-relaxed text-text-secondary">{detail}</p>
                </motion.article>
              ))}
            </div>

            <motion.div variants={reveal} className="mt-3 flex items-center gap-2 font-body text-xs text-text-muted">
              <Database className="h-3.5 w-3.5 text-primary-300" />
              <span>Durable PostgreSQL jobs preserve campaign progress through interruptions.</span>
            </motion.div>
          </motion.section>

          <motion.aside
            className="rounded-2xl border border-primary-300/25 bg-bg-card/70 p-5 backdrop-blur-xl"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.55, delay: 0.45 }}
            aria-label="Campaign monitoring summary"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-body text-xs font-semibold tracking-[0.16em] text-primary-300">MONITORING</p>
                <h2 className="mt-1 font-display text-xl font-semibold text-text-primary">Totals at a glance</h2>
              </div>
              <span className="mt-1 h-2.5 w-2.5 rounded-full bg-primary-300" />
            </div>

            <div className="mt-4 grid grid-cols-2 gap-2.5">
              {totals.map(({ value, label, warning }) => (
                <div
                  key={label}
                  className={`rounded-xl border p-3 ${
                    warning
                      ? 'border-accent-300/25 bg-accent-500/10'
                      : 'border-border-subtle bg-bg-base/50'
                  }`}
                >
                  <p className={`font-display text-xl font-semibold ${warning ? 'text-accent-200' : 'text-text-primary'}`}>
                    {value}
                  </p>
                  <p className="mt-0.5 font-body text-xs text-text-muted">{label}</p>
                </div>
              ))}
            </div>

            <div className="mt-3 flex items-start gap-2.5 rounded-xl border border-accent-300/20 bg-accent-500/10 p-3">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-accent-200" />
              <div>
                <p className="font-body text-xs font-semibold text-text-primary">Operational errors stay visible</p>
                <p className="mt-1 font-body text-xs leading-relaxed text-text-muted">
                  Review failed attempts without losing campaign totals or control.
                </p>
              </div>
            </div>
          </motion.aside>
        </div>
      </div>
    </div>
  );
}
