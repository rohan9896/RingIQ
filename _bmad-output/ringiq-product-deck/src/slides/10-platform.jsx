import React from 'react';
import { motion } from 'framer-motion';
import {
  ArrowRight,
  Database,
  Languages,
  Layers3,
  LockKeyhole,
  MonitorSmartphone,
  RadioTower,
  ShieldCheck,
  Sparkles,
  UserRoundCheck,
} from 'lucide-react';

const reveal = {
  hidden: { opacity: 0, y: 18 },
  show: { opacity: 1, y: 0 },
};

const layers = [
  {
    number: '01',
    icon: MonitorSmartphone,
    title: 'Experience',
    detail: 'Next.js tenant workspace + platform console',
  },
  {
    number: '02',
    icon: Database,
    title: 'Core SaaS',
    detail: 'FastAPI + PostgreSQL + background worker',
  },
  {
    number: '03',
    icon: RadioTower,
    title: 'Voice runtime',
    detail: 'LiveKit + Vobiz SIP + Deepgram + Groq + Sarvam',
  },
  {
    number: '04',
    icon: ShieldCheck,
    title: 'Trust boundary',
    detail: 'Clerk org context + backend tenant authorization + tenant-scoped leads, KB, and call data',
  },
];

const pillars = [
  { icon: LockKeyhole, label: 'Private tenant grounding' },
  { icon: Languages, label: 'India-ready multilingual voice' },
  { icon: UserRoundCheck, label: 'Evidence-driven human handoff' },
];

const roadmap = [
  {
    phase: 'Now',
    detail: 'Activation, KB, leads, campaign operations, tenant-grounded calls',
  },
  {
    phase: 'Next',
    detail: 'Qualification, artifacts, callback / follow-up, knowledge gaps',
  },
  {
    phase: 'Later',
    detail: 'Compliance workflows, CRM integrations, live transfer, billing',
  },
];

export default function PlatformSlide() {
  return (
    <div className="slide-page relative bg-bg-base text-text-primary" data-slide="10-platform">
      <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        <div className="absolute -left-40 -top-32 h-[34rem] w-[34rem] rounded-full bg-primary-500/20 blur-[125px]" />
        <div className="absolute -right-36 top-8 h-[32rem] w-[32rem] rounded-full bg-accent-500/10 blur-[130px]" />
        <div className="absolute bottom-0 left-1/3 h-52 w-[38rem] rounded-full bg-primary-400/10 blur-[105px]" />
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
            PLATFORM SPINE
          </span>
          <span className="h-px w-14 bg-gradient-to-r from-primary-400/60 to-transparent" />
        </motion.div>
        <motion.h1
          variants={reveal}
          transition={{ duration: 0.5 }}
          className="max-w-[76rem] font-display text-[3.05rem] font-semibold leading-[1.03] tracking-[-0.04em] text-text-primary mobile-title"
        >
          Built as a platform. Focused on one <span className="text-primary-300">decisive outcome.</span>
        </motion.h1>
      </motion.header>

      <div className="slide-content relative z-10 grid grid-cols-[0.96fr_1.04fr] gap-5 mobile-stack">
        <motion.section
          className="glass relative overflow-hidden rounded-2xl border border-border-default/70 p-5 mobile-card"
          initial="hidden"
          animate="show"
          transition={{ staggerChildren: 0.1, delayChildren: 0.15 }}
          aria-label="RingIQ platform architecture"
        >
          <motion.div variants={reveal} className="mb-4 flex items-center gap-2.5">
            <Layers3 className="h-5 w-5 text-primary-300" />
            <h2 className="font-display text-xl font-semibold tracking-[-0.02em] text-text-primary">
              One connected platform stack
            </h2>
          </motion.div>

          <div className="relative space-y-2.5">
            <div className="absolute bottom-6 left-5 top-6 w-px bg-border-default" />
            <motion.div
              className="absolute left-5 top-6 w-px bg-primary-300"
              initial={{ height: 0 }}
              animate={{ height: 'calc(100% - 3rem)' }}
              transition={{ duration: 1.1, delay: 0.4, ease: 'easeOut' }}
            />

            {layers.map(({ number, icon: Icon, title, detail }) => (
              <motion.article
                key={title}
                variants={reveal}
                transition={{ duration: 0.45 }}
                className="relative grid grid-cols-[2.5rem_1fr] items-center gap-3 rounded-xl border border-border-subtle bg-bg-card/55 px-3.5 py-3 backdrop-blur-md mobile-card"
                whileHover={{ x: 4 }}
              >
                <div className="relative z-10 flex h-10 w-10 items-center justify-center rounded-lg border border-primary-300/30 bg-bg-base">
                  <Icon className="h-[1.125rem] w-[1.125rem] text-primary-200" strokeWidth={1.8} />
                </div>
                <div className="min-w-0">
                  <div className="flex items-baseline gap-2.5">
                    <span className="font-display text-xs font-semibold tracking-[0.14em] text-primary-300">{number}</span>
                    <h3 className="font-display text-base font-semibold text-text-primary">{title}</h3>
                  </div>
                  <p className="mt-1 font-body text-sm leading-relaxed text-text-secondary mobile-wrap">{detail}</p>
                </div>
              </motion.article>
            ))}
          </div>
        </motion.section>

        <div className="flex min-w-0 flex-col gap-4 mobile-stack">
          <motion.section
            className="rounded-2xl border border-primary-300/25 bg-bg-card/70 p-5 backdrop-blur-xl mobile-card"
            initial="hidden"
            animate="show"
            transition={{ staggerChildren: 0.08, delayChildren: 0.3 }}
            aria-label="Product differentiation"
          >
            <motion.div variants={reveal} className="mb-3 flex items-center gap-2.5">
              <Sparkles className="h-[1.125rem] w-[1.125rem] text-primary-300" />
              <h2 className="font-display text-lg font-semibold text-text-primary">Three compounding advantages</h2>
            </motion.div>
            <div className="grid grid-cols-3 gap-2.5 mobile-compact-grid">
              {pillars.map(({ icon: Icon, label }) => (
                <motion.div
                  key={label}
                  variants={reveal}
                  className="rounded-xl border border-border-subtle bg-bg-base/50 p-3 mobile-card"
                  whileHover={{ y: -3 }}
                >
                  <Icon className="h-4 w-4 text-primary-300" />
                  <p className="mt-2 font-display text-sm font-semibold leading-snug text-text-primary">{label}</p>
                </motion.div>
              ))}
            </div>
          </motion.section>

          <motion.section
            className="glass rounded-2xl border border-border-default/70 p-5 mobile-card"
            initial="hidden"
            animate="show"
            transition={{ staggerChildren: 0.1, delayChildren: 0.45 }}
            aria-label="Product roadmap"
          >
            <motion.div variants={reveal} className="mb-3 flex items-center justify-between">
              <h2 className="font-display text-lg font-semibold text-text-primary">Now → Next → Later</h2>
              <span className="font-body text-xs font-semibold tracking-[0.13em] text-text-muted">ROADMAP</span>
            </motion.div>
            <div className="space-y-2.5 mobile-timeline">
              {roadmap.map(({ phase, detail }, index) => (
                <motion.div
                  key={phase}
                  variants={reveal}
                  className="grid grid-cols-[4.25rem_auto_1fr] items-center gap-2.5 rounded-xl border border-border-subtle bg-bg-card/50 px-3 py-2.5 mobile-card"
                >
                  <span className={`font-display text-sm font-semibold ${index === 0 ? 'text-primary-200' : 'text-text-secondary'}`}>
                    {phase}
                  </span>
                  <ArrowRight className="h-3.5 w-3.5 text-text-muted" />
                  <p className="font-body text-sm leading-relaxed text-text-secondary mobile-wrap">{detail}</p>
                </motion.div>
              ))}
            </div>
          </motion.section>

          <motion.div
            className="flex items-center justify-between gap-5 rounded-2xl border border-primary-300/30 bg-primary-500/10 px-5 py-4 mobile-stack mobile-card"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.75 }}
          >
            <p className="font-display text-xl font-semibold tracking-[-0.02em] text-text-primary">
              Automate first touch. <span className="text-primary-300">Concentrate human judgment.</span>
            </p>
            <ArrowRight className="h-5 w-5 shrink-0 text-primary-200" />
          </motion.div>
        </div>
      </div>
    </div>
  );
}
