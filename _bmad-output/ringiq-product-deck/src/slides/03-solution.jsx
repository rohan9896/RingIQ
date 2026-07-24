import React from 'react';
import { motion } from 'framer-motion';
import {
  ArrowRight,
  Building2,
  Database,
  FileUp,
  Fingerprint,
  Languages,
  PhoneCall,
  Rocket,
  ShieldCheck,
  Sparkles,
  Target,
  UserRoundCheck,
} from 'lucide-react';

const journey = [
  {
    number: '01',
    label: 'Prepare',
    icon: Building2,
    lines: ['Organization profile', 'Private knowledge base'],
    detailIcon: Database,
  },
  {
    number: '02',
    label: 'Import',
    icon: FileUp,
    lines: ['Validate a lead CSV', 'Or add one lead'],
    detailIcon: Fingerprint,
  },
  {
    number: '03',
    label: 'Launch',
    icon: Rocket,
    lines: ['Create a campaign', 'Or choose Call now'],
    detailIcon: PhoneCall,
  },
  {
    number: '04',
    label: 'Converse',
    icon: Languages,
    lines: ['Tenant-grounded AI', 'Hindi · English · Hinglish'],
    detailIcon: Sparkles,
  },
  {
    number: '05',
    label: 'Prioritize',
    icon: Target,
    lines: ['Outcome + callback + evidence', 'Clear human follow-up'],
    detailIcon: UserRoundCheck,
    endState: true,
  },
];

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.12, delayChildren: 0.18 } },
};

const item = {
  hidden: { opacity: 0, y: 22, scale: 0.97 },
  show: { opacity: 1, y: 0, scale: 1 },
};

export default function SolutionSlide() {
  return (
    <div className="slide-page relative bg-bg-base text-text-primary" data-slide="03-solution">
      <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        <div className="absolute -left-36 top-10 h-[30rem] w-[30rem] rounded-full bg-primary-500/15 blur-[115px]" />
        <div className="absolute -right-40 -top-24 h-[36rem] w-[36rem] rounded-full bg-accent-500/15 blur-[125px]" />
        <div className="absolute bottom-0 left-[42%] h-44 w-[38rem] rounded-full bg-primary-400/10 blur-[95px]" />
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
        className="relative z-10 mb-8 shrink-0"
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55, ease: 'easeOut' }}
      >
        <div className="mb-4 flex items-center gap-3">
          <span className="font-body text-xs font-semibold tracking-[0.22em] text-primary-300">THE COMPLETE JOURNEY</span>
          <span className="h-px w-20 bg-gradient-to-r from-primary-400/60 to-transparent" />
        </div>
        <h1 className="mobile-title max-w-5xl font-display text-[3.35rem] font-semibold leading-[1.02] tracking-[-0.04em] text-text-primary">
          One system, from raw lead to{' '}
          <span className="text-primary-300">clear next action</span>
        </h1>
        <p className="mobile-subtitle mt-3 max-w-3xl font-body text-lg leading-relaxed text-text-secondary">
          A continuous operating loop for setting context, reaching prospects, and focusing sales attention.
        </p>
      </motion.header>

      <div className="slide-content relative z-10 flex min-h-0 flex-col justify-center">
        <motion.div
          className="mobile-flow relative grid grid-cols-[repeat(4,minmax(0,1fr))_1.14fr] items-stretch gap-5"
          variants={container}
          initial="hidden"
          animate="show"
        >
          <div className="mobile-hide absolute left-[8%] right-[9%] top-[3.55rem] h-px bg-gradient-to-r from-primary-500/20 via-primary-300/70 to-primary-300/30" />

          {journey.map(({ number, label, icon: Icon, lines, detailIcon: DetailIcon, endState }, index) => (
            <motion.article
              key={label}
              variants={item}
              transition={{ duration: 0.48, ease: 'easeOut' }}
              className={`mobile-card relative flex min-w-0 flex-col rounded-2xl border backdrop-blur-xl ${
                endState
                  ? 'border-primary-300/45 bg-primary-500/15 shadow-2xl'
                  : 'border-border-default/70 bg-bg-card/65'
              }`}
            >
              {endState && (
                <div className="absolute inset-x-4 -top-4 flex justify-center">
                  <span className="rounded-full border border-primary-300/40 bg-bg-base px-3 py-1 font-body text-[0.62rem] font-semibold tracking-[0.16em] text-primary-200">
                    INTENDED COMPLETE-PRODUCT EXPERIENCE
                  </span>
                </div>
              )}

              <div className="flex items-center justify-between border-b border-border-subtle/80 px-4 py-4">
                <span className="font-body text-xs font-semibold tracking-[0.18em] text-text-muted">{number}</span>
                <motion.div
                  className={`relative z-10 flex h-10 w-10 items-center justify-center rounded-full border ${
                    endState
                      ? 'border-primary-300/50 bg-primary-500/25'
                      : 'border-primary-400/30 bg-bg-base/80'
                  }`}
                  whileHover={{ scale: 1.08 }}
                >
                  <Icon className="h-5 w-5 text-primary-200" strokeWidth={1.8} />
                </motion.div>
              </div>

              <div className="flex flex-1 flex-col px-4 pb-5 pt-4">
                <h2 className="font-display text-[1.45rem] font-semibold tracking-[-0.02em] text-text-primary">{label}</h2>
                <div className="mt-4 space-y-2.5">
                  {lines.map((line, lineIndex) => (
                    <div key={line} className="flex items-start gap-2.5 font-body text-sm leading-snug text-text-secondary">
                      <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${lineIndex === 0 ? 'bg-primary-300' : 'bg-border-default'}`} />
                      <span>{line}</span>
                    </div>
                  ))}
                </div>
                <div className="mt-auto pt-6">
                  <div className="flex items-center gap-2 rounded-lg border border-border-subtle bg-bg-base/55 px-3 py-2 font-body text-[0.69rem] font-semibold tracking-[0.1em] text-text-muted">
                    <DetailIcon className="h-3.5 w-3.5 text-primary-300" />
                    {endState ? 'TARGET WORKFLOW' : 'CONNECTED STEP'}
                  </div>
                </div>
              </div>

              {index < journey.length - 1 && (
                <motion.div
                  className="mobile-flow-connector absolute -right-4 top-[3.05rem] z-20 flex h-8 w-8 items-center justify-center rounded-full border border-primary-400/30 bg-bg-base"
                  initial={{ opacity: 0, scale: 0.6 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.5 + index * 0.12, duration: 0.3 }}
                >
                  <ArrowRight className="h-4 w-4 text-primary-300" />
                </motion.div>
              )}
            </motion.article>
          ))}
        </motion.div>

        <motion.div
          className="mobile-card mobile-status mt-7 flex items-center justify-between gap-6 rounded-xl border border-border-default/60 bg-bg-card/50 px-5 py-3.5 backdrop-blur-md"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.85, duration: 0.45 }}
        >
          <div className="mobile-status flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-500/15">
              <ShieldCheck className="h-5 w-5 text-primary-300" />
            </div>
            <div>
              <p className="font-display text-sm font-semibold text-text-primary">Multi-tenant and private by design</p>
              <p className="font-body text-xs text-text-muted">Each organization&apos;s profile, knowledge, leads, and call context stay logically isolated.</p>
            </div>
          </div>
          <div className="mobile-wrap shrink-0 rounded-full border border-border-default/70 px-3 py-1.5 font-body text-[0.65rem] font-semibold tracking-[0.15em] text-text-secondary">
            CONTEXT FOLLOWS THE LEAD
          </div>
        </motion.div>
      </div>
    </div>
  );
}
