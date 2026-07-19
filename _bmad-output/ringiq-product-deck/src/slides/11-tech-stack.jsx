import React from 'react';
import { motion } from 'framer-motion';
import {
  ArrowRight,
  Braces,
  CheckCircle2,
  Cloud,
  Database,
  Fingerprint,
  Layers3,
  RadioTower,
  Server,
  ShieldCheck,
  TimerReset,
  Workflow,
} from 'lucide-react';

const reveal = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0 },
};

const voiceServices = [
  'Vobiz · SIP',
  'Deepgram Flux · STT',
  'Groq · llama-3.3-70b-versatile',
  'Sarvam Bulbul v3 · TTS',
];

export default function TechStackSlide() {
  return (
    <div className="slide-page">
      <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        <div className="absolute -left-36 -top-40 h-[32rem] w-[32rem] rounded-full bg-primary-500/20 blur-[120px]" />
        <div className="absolute -right-28 top-8 h-[30rem] w-[30rem] rounded-full bg-accent-500/10 blur-[125px]" />
        <div className="absolute bottom-0 left-[38%] h-44 w-[34rem] rounded-full bg-primary-400/10 blur-[100px]" />
        <div className="absolute inset-x-0 top-[47%] h-px bg-gradient-to-r from-transparent via-border-subtle to-transparent" />
      </div>

      <motion.header
        className="relative z-10 mb-5 shrink-0"
        initial="hidden"
        animate="show"
        transition={{ staggerChildren: 0.08 }}
      >
        <motion.div variants={reveal} className="mb-2.5 flex items-center gap-3">
          <span className="font-body text-xs font-semibold tracking-[0.2em] text-primary-300">
            DEPLOYMENT MAP
          </span>
          <span className="h-px w-14 bg-gradient-to-r from-primary-400/60 to-transparent" />
        </motion.div>
        <motion.div variants={reveal} className="flex items-end justify-between gap-8">
          <div>
            <h1 className="font-display text-[3.05rem] font-semibold leading-none tracking-[-0.04em] text-text-primary">
              The stack behind <span className="text-primary-300">RingIQ</span>
            </h1>
            <p className="mt-2.5 font-body text-base text-text-secondary">
              Product workflows, durable execution, and real-time voice—kept in distinct lanes.
            </p>
          </div>
          <div className="mb-0.5 flex shrink-0 items-center gap-2 rounded-full border border-border-default bg-bg-card/65 px-3 py-2 font-body text-xs text-text-secondary backdrop-blur-md">
            <Fingerprint className="h-4 w-4 text-primary-300" />
            Clerk auth + organizations at the identity edge
          </div>
        </motion.div>
      </motion.header>

      <div className="slide-content relative z-10 flex min-h-0 flex-col gap-3.5">
        <motion.section
          className="grid grid-cols-[0.9fr_auto_1.05fr_auto_1.12fr] items-stretch gap-2.5"
          initial="hidden"
          animate="show"
          transition={{ staggerChildren: 0.09, delayChildren: 0.15 }}
          aria-label="Product and data deployment lanes"
        >
          <motion.article variants={reveal} className="glass rounded-2xl border border-border-default/70 p-4">
            <div className="flex items-center justify-between">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-primary-300/30 bg-primary-500/10">
                <Braces className="h-[1.125rem] w-[1.125rem] text-primary-200" />
              </div>
              <span className="font-body text-[0.65rem] font-semibold tracking-[0.16em] text-text-muted">EXPERIENCE</span>
            </div>
            <h2 className="mt-3 font-display text-lg font-semibold text-text-primary">Next.js + TypeScript</h2>
            <p className="mt-1 font-body text-sm leading-relaxed text-text-secondary">
              Tenant workspace and platform console, targeted for deployment on Vercel.
            </p>
            <div className="mt-3 flex items-center gap-2 font-body text-xs font-medium text-primary-200">
              <Cloud className="h-3.5 w-3.5" /> Vercel · intended web target
            </div>
          </motion.article>

          <motion.div variants={reveal} className="flex items-center justify-center">
            <ArrowRight className="h-5 w-5 text-primary-300" />
          </motion.div>

          <motion.article variants={reveal} className="rounded-2xl border border-primary-300/30 bg-primary-500/10 p-4 backdrop-blur-xl">
            <div className="flex items-center justify-between">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-primary-300/30 bg-bg-base/60">
                <Server className="h-[1.125rem] w-[1.125rem] text-primary-200" />
              </div>
              <span className="font-body text-[0.65rem] font-semibold tracking-[0.16em] text-primary-300">PRODUCT API</span>
            </div>
            <h2 className="mt-3 font-display text-lg font-semibold text-text-primary">FastAPI + Python</h2>
            <p className="mt-1 font-body text-sm leading-relaxed text-text-secondary">
              Product policy, tenant authorization, and campaign / call coordination on Heroku.
            </p>
            <div className="mt-3 flex items-center gap-2 font-body text-xs font-medium text-primary-200">
              <ShieldCheck className="h-3.5 w-3.5" /> Server-enforced tenant boundary
            </div>
          </motion.article>

          <motion.div variants={reveal} className="flex items-center justify-center">
            <ArrowRight className="h-5 w-5 text-primary-300" />
          </motion.div>

          <motion.article variants={reveal} className="glass rounded-2xl border border-border-default/70 p-4">
            <div className="flex items-center justify-between">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-primary-300/30 bg-primary-500/10">
                <Database className="h-[1.125rem] w-[1.125rem] text-primary-200" />
              </div>
              <span className="font-body text-[0.65rem] font-semibold tracking-[0.16em] text-text-muted">DATA + ASYNC</span>
            </div>
            <h2 className="mt-3 font-display text-lg font-semibold text-text-primary">Heroku Postgres</h2>
            <div className="mt-2 grid grid-cols-2 gap-2 font-body text-xs leading-relaxed text-text-secondary">
              <div className="rounded-lg border border-border-subtle bg-bg-base/45 px-2.5 py-2">
                <span className="font-semibold text-text-primary">pgvector</span><br />tenant-scoped RAG
              </div>
              <div className="rounded-lg border border-border-subtle bg-bg-base/45 px-2.5 py-2">
                <span className="font-semibold text-text-primary">Durable jobs</span><br />Postgres outbox
              </div>
            </div>
            <p className="mt-2.5 font-body text-xs leading-relaxed text-text-muted">
              Leased claiming · bounded retries · idempotent handlers
            </p>
          </motion.article>
        </motion.section>

        <motion.section
          className="grid min-h-0 flex-1 grid-cols-[1.35fr_0.65fr] gap-3.5"
          initial="hidden"
          animate="show"
          transition={{ staggerChildren: 0.1, delayChildren: 0.45 }}
          aria-label="Real-time voice and deployment status"
        >
          <motion.article variants={reveal} className="relative overflow-hidden rounded-2xl border border-primary-300/30 bg-bg-card/70 p-4 backdrop-blur-xl">
            <div className="absolute inset-y-0 left-0 w-1 bg-primary-300" />
            <div className="flex items-center justify-between gap-5">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-primary-300/30 bg-primary-500/15">
                  <RadioTower className="h-5 w-5 text-primary-200" />
                </div>
                <div>
                  <span className="font-body text-[0.65rem] font-semibold tracking-[0.16em] text-primary-300">REAL-TIME VOICE</span>
                  <h2 className="font-display text-xl font-semibold text-text-primary">LiveKit Cloud + Python voice worker</h2>
                </div>
              </div>
              <span className="rounded-full border border-border-default bg-bg-base/50 px-3 py-1.5 font-body text-xs text-text-secondary">
                Worker hosted on Heroku
              </span>
            </div>

            <div className="mt-3.5 grid grid-cols-[auto_1fr] items-center gap-4">
              <div className="flex items-center gap-2 rounded-xl border border-border-subtle bg-bg-base/45 px-3 py-2.5">
                <Workflow className="h-4 w-4 text-primary-300" />
                <div>
                  <p className="font-display text-sm font-semibold text-text-primary">Media + session lane</p>
                  <p className="font-body text-xs text-text-muted">LiveKit orchestrates the call room</p>
                </div>
              </div>
              <div className="grid grid-cols-4 gap-2">
                {voiceServices.map((service, index) => (
                  <motion.div
                    key={service}
                    className="flex min-h-[3.5rem] items-center rounded-lg border border-border-subtle bg-bg-elevated/55 px-2.5 font-body text-xs font-medium leading-snug text-text-secondary"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.63 + index * 0.08 }}
                  >
                    {service}
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.article>

          <motion.aside variants={reveal} className="glass rounded-2xl border border-border-default/70 p-4">
            <div className="flex items-center gap-2.5">
              <Layers3 className="h-4 w-4 text-primary-300" />
              <h2 className="font-display text-base font-semibold text-text-primary">Deployment status</h2>
            </div>
            <div className="mt-3 space-y-2">
              <div className="flex items-start gap-2 rounded-lg border border-border-subtle bg-bg-base/45 px-3 py-2.5">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-primary-300" />
                <p className="font-body text-xs leading-relaxed text-text-secondary">
                  Staging backend, jobs worker, and voice worker are deployed on Heroku.
                </p>
              </div>
              <div className="flex items-start gap-2 rounded-lg border border-border-subtle bg-bg-base/45 px-3 py-2.5">
                <TimerReset className="mt-0.5 h-4 w-4 shrink-0 text-text-muted" />
                <p className="font-body text-xs leading-relaxed text-text-secondary">
                  Vercel is the intended frontend target; deployment is not verified by repo artifacts.
                </p>
              </div>
            </div>
          </motion.aside>
        </motion.section>
      </div>
    </div>
  );
}
