import React from 'react';
import { motion } from 'framer-motion';
import {
  ArrowRight,
  Clock3,
  Focus,
  ListRestart,
  PhoneCall,
  PhoneMissed,
  Sparkles,
  UsersRound,
} from 'lucide-react';

const reveal = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
};

const flow = [
  {
    icon: UsersRound,
    eyebrow: 'INPUT',
    title: 'High lead volume',
    detail: 'Demand arrives continuously',
  },
  {
    icon: PhoneCall,
    eyebrow: 'BOTTLENECK',
    title: 'Manual first calls',
    detail: 'Every lead enters the same queue',
    emphasis: true,
  },
  {
    icon: Focus,
    eyebrow: 'OUTCOME',
    title: 'Lost sales focus',
    detail: 'Attention fragments before follow-up',
  },
];

const painPoints = [
  { icon: Clock3, label: 'Slow speed-to-lead' },
  { icon: PhoneMissed, label: 'Time lost to unanswered and low-intent calls' },
  { icon: ListRestart, label: 'Inconsistent explanations and manual disposition updates' },
];

export default function ProblemSlide() {
  return (
    <div className="slide-page relative bg-bg-base text-text-primary">
      <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        <div className="absolute -left-40 top-1/4 h-[30rem] w-[30rem] rounded-full bg-primary-500/20 blur-[120px]" />
        <div className="absolute -right-32 -top-36 h-[34rem] w-[34rem] rounded-full bg-accent-500/10 blur-[130px]" />
        <div className="absolute bottom-0 left-[42%] h-48 w-[34rem] rounded-full bg-primary-400/10 blur-[100px]" />
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
        initial="hidden"
        animate="show"
        transition={{ staggerChildren: 0.1 }}
      >
        <motion.div variants={reveal} transition={{ duration: 0.4 }} className="mb-4 flex items-center gap-3">
          <span className="font-body text-xs font-semibold tracking-[0.2em] text-primary-300">THE BEFORE-STATE</span>
          <span className="h-px w-20 bg-gradient-to-r from-primary-400/60 to-transparent" />
        </motion.div>
        <motion.h1
          variants={reveal}
          transition={{ duration: 0.55 }}
          className="font-display text-[3.8rem] font-semibold leading-[0.95] tracking-[-0.045em] text-text-primary"
        >
          The first-touch <span className="text-primary-300">bottleneck</span>
        </motion.h1>
        <motion.p
          variants={reveal}
          transition={{ duration: 0.5 }}
          className="mt-4 font-body text-xl text-text-secondary"
        >
          Lead volume grows faster than the team&apos;s ability to respond.
        </motion.p>
      </motion.header>

      <div className="slide-content relative z-10 grid grid-cols-[1.65fr_0.85fr] grid-rows-[1fr_auto] gap-5">
        <motion.section
          className="glass relative flex min-w-0 flex-col justify-between overflow-hidden rounded-2xl p-6"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.18, duration: 0.6 }}
          aria-label="Lead handling bottleneck flow"
        >
          <div className="absolute left-1/3 top-0 h-full w-1/3 bg-primary-500/10 blur-3xl" aria-hidden="true" />
          <div className="relative flex items-center justify-between">
            <p className="font-body text-xs font-semibold tracking-[0.18em] text-text-muted">WHERE CAPACITY BREAKS</p>
            <div className="flex items-center gap-2 font-body text-xs text-text-muted">
              <span className="h-1.5 w-1.5 rounded-full bg-primary-300" />
              FIRST-CONTACT WORKFLOW
            </div>
          </div>

          <div className="relative mt-5 grid flex-1 grid-cols-[1fr_auto_1fr_auto_1fr] items-center gap-3">
            {flow.map(({ icon: Icon, eyebrow, title, detail, emphasis }, index) => (
              <React.Fragment key={title}>
                <motion.div
                  className={`relative flex min-h-48 flex-col rounded-2xl border p-5 backdrop-blur-md ${
                    emphasis
                      ? 'border-primary-300/40 bg-primary-500/20 shadow-2xl'
                      : 'border-border-default/70 bg-bg-card/60'
                  }`}
                  initial={{ opacity: 0, scale: 0.94 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.34 + index * 0.16, duration: 0.5, ease: 'easeOut' }}
                >
                  {emphasis && (
                    <motion.div
                      className="absolute inset-0 rounded-2xl border border-primary-300/30"
                      animate={{ opacity: [0.25, 0.8, 0.25] }}
                      transition={{ duration: 2.4, repeat: Infinity, ease: 'easeInOut' }}
                    />
                  )}
                  <div className={`relative mb-auto flex h-11 w-11 items-center justify-center rounded-xl ${
                    emphasis ? 'bg-primary-500/25' : 'bg-bg-elevated/80'
                  }`}>
                    <Icon className="h-5 w-5 text-primary-200" strokeWidth={1.8} />
                  </div>
                  <p className="relative mt-5 font-body text-[0.65rem] font-semibold tracking-[0.18em] text-primary-300">{eyebrow}</p>
                  <h2 className="relative mt-2 font-display text-[1.35rem] font-semibold leading-tight tracking-[-0.02em] text-text-primary">{title}</h2>
                  <p className="relative mt-2 font-body text-sm leading-snug text-text-muted">{detail}</p>
                </motion.div>

                {index < flow.length - 1 && (
                  <motion.div
                    className="relative flex w-8 items-center justify-center"
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5 + index * 0.18, duration: 0.4 }}
                    aria-hidden="true"
                  >
                    <span className="absolute h-px w-8 bg-gradient-to-r from-border-default to-primary-300/70" />
                    <motion.span
                      className="absolute h-1.5 w-1.5 rounded-full bg-primary-300"
                      animate={{ x: [-12, 12], opacity: [0, 1, 0] }}
                      transition={{ duration: 1.7, delay: index * 0.35, repeat: Infinity, ease: 'easeInOut' }}
                    />
                    <ArrowRight className="absolute -right-1 h-4 w-4 text-primary-300" />
                  </motion.div>
                )}
              </React.Fragment>
            ))}
          </div>
        </motion.section>

        <motion.aside
          className="glass flex flex-col rounded-2xl p-6"
          initial="hidden"
          animate="show"
          transition={{ delayChildren: 0.35, staggerChildren: 0.12 }}
          aria-label="Operational pain points"
        >
          <motion.div variants={reveal} className="mb-4 flex items-center justify-between">
            <div>
              <p className="font-body text-xs font-semibold tracking-[0.18em] text-primary-300">THE COST</p>
              <h2 className="mt-2 font-display text-2xl font-semibold tracking-[-0.025em] text-text-primary">Repetitive work compounds</h2>
            </div>
          </motion.div>

          <div className="flex flex-1 flex-col justify-center gap-3">
            {painPoints.map(({ icon: Icon, label }, index) => (
              <motion.div
                key={label}
                variants={reveal}
                transition={{ duration: 0.45 }}
                className="group flex items-start gap-3 rounded-xl border border-border-subtle bg-bg-base/45 p-3.5"
              >
                <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary-500/20">
                  <Icon className="h-4 w-4 text-primary-200" strokeWidth={1.8} />
                </div>
                <div className="min-w-0">
                  <span className="font-body text-[0.65rem] font-semibold tracking-[0.16em] text-text-muted">0{index + 1}</span>
                  <p className="mt-1 font-body text-sm font-medium leading-snug text-text-secondary">{label}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.aside>

        <motion.section
          className="col-span-2 flex items-center justify-between gap-8 rounded-2xl border border-primary-300/30 bg-primary-500/20 px-6 py-4 backdrop-blur-xl"
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.72, duration: 0.55 }}
          aria-label="Product opportunity"
        >
          <div className="flex min-w-0 items-center gap-4">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-primary-300/30 bg-primary-500/20">
              <Sparkles className="h-5 w-5 text-primary-200" />
            </div>
            <div>
              <p className="font-body text-xs font-semibold tracking-[0.18em] text-primary-300">PRODUCT OPPORTUNITY</p>
              <p className="mt-1.5 font-display text-lg font-medium leading-snug text-text-primary">
                Automate the repetitive first-contact layer while keeping people on high-value follow-up.
              </p>
            </div>
          </div>
          <motion.div
            className="hidden shrink-0 items-center gap-2 rounded-full border border-primary-300/30 bg-bg-base/45 px-4 py-2 font-body text-xs font-semibold tracking-[0.12em] text-primary-200 lg:flex"
            animate={{ x: [0, 4, 0] }}
            transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
          >
            RESTORE SALES FOCUS
            <ArrowRight className="h-4 w-4" />
          </motion.div>
        </motion.section>
      </div>
    </div>
  );
}
