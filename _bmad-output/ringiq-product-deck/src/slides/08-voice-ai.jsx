import React from 'react';
import { motion } from 'framer-motion';
import {
  Activity,
  ArrowRight,
  AudioLines,
  BookOpenCheck,
  BrainCircuit,
  CheckCircle2,
  Clock3,
  Languages,
  Network,
  PhoneCall,
  RadioTower,
  ScrollText,
  Sparkles,
  UserRound,
  Volume2,
} from 'lucide-react';

const pipeline = [
  { icon: RadioTower, label: 'Vobiz over SIP', detail: 'Call transport' },
  { icon: Network, label: 'LiveKit session', detail: 'Real-time media' },
  { icon: AudioLines, label: 'Deepgram Flux STT', detail: 'Speech → text' },
  { icon: BrainCircuit, label: 'Tenant context + Groq LLM', detail: 'Grounded reasoning' },
  { icon: Volume2, label: 'Sarvam Bulbul v3', detail: 'Text → speech' },
  { icon: UserRound, label: 'Lead', detail: 'Natural response' },
];

const capabilities = [
  { icon: Languages, title: 'Hindi · English · Hinglish', detail: 'A single call can feel naturally mixed.' },
  { icon: UserRound, title: 'Lead-aware opening', detail: 'Name and optional attributes enter context.' },
  { icon: BookOpenCheck, title: 'Tenant-safe answers', detail: 'The active private KB grounds each turn.' },
];

const waveform = [40, 72, 52, 88, 64, 100, 58, 82, 46, 92, 66, 38, 74, 54, 86];

const rise = {
  hidden: { opacity: 0, y: 18 },
  show: { opacity: 1, y: 0 },
};

export default function VoiceAiSlide() {
  return (
    <div className="slide-page relative bg-bg-base text-text-primary">
      <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        <div className="absolute -left-36 top-8 h-[30rem] w-[30rem] rounded-full bg-primary-500/16 blur-[115px]" />
        <div className="absolute -right-32 -top-20 h-[34rem] w-[34rem] rounded-full bg-accent-500/14 blur-[125px]" />
        <div className="absolute bottom-0 left-[36%] h-52 w-[38rem] rounded-full bg-primary-400/10 blur-[105px]" />
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
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55, ease: 'easeOut' }}
      >
        <div className="mb-4 flex items-center gap-3">
          <span className="font-body text-xs font-semibold tracking-[0.22em] text-primary-300">LIVE VOICE EXPERIENCE</span>
          <span className="h-px w-20 bg-gradient-to-r from-primary-400/60 to-transparent" />
        </div>
        <h1 className="max-w-[68rem] font-display text-[3.3rem] font-semibold leading-[1.02] tracking-[-0.04em] text-text-primary">
          A natural conversation,{' '}
          <span className="text-primary-300">grounded at every turn</span>
        </h1>
        <p className="mt-3 font-body text-lg text-text-secondary">
          RingIQ carries voice, context, and response through one observable real-time loop.
        </p>
      </motion.header>

      <div className="slide-content relative z-10 flex min-h-0 flex-col justify-center">
        <motion.section
          className="relative"
          initial="hidden"
          animate="show"
          transition={{ staggerChildren: 0.1, delayChildren: 0.12 }}
          aria-label="Live voice processing pipeline"
        >
          <div className="mb-3 flex items-center justify-between">
            <p className="font-body text-xs font-semibold tracking-[0.18em] text-text-muted">THE SIGNAL PATH</p>
            <p className="font-body text-[0.68rem] text-text-muted">Listen → understand in context → respond</p>
          </div>
          <div className="grid grid-cols-[0.86fr_0.86fr_1.08fr_1.3fr_1.15fr_0.78fr] gap-3">
            {pipeline.map(({ icon: Icon, label, detail }, index) => (
              <motion.div
                key={label}
                variants={rise}
                transition={{ duration: 0.42, ease: 'easeOut' }}
                className={`relative flex min-w-0 items-center gap-3 rounded-xl border px-3.5 py-3 backdrop-blur-md ${
                  index === 3
                    ? 'border-primary-300/40 bg-primary-500/15'
                    : 'border-border-default/65 bg-bg-card/60'
                }`}
              >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-primary-400/25 bg-bg-base/65">
                  <Icon className="h-4 w-4 text-primary-300" />
                </div>
                <div className="min-w-0">
                  <p className="truncate font-display text-xs font-semibold text-text-primary">{label}</p>
                  <p className="mt-0.5 truncate font-body text-[0.62rem] text-text-muted">{detail}</p>
                </div>
                {index < pipeline.length - 1 && (
                  <div className="absolute -right-2.5 top-1/2 z-20 flex h-5 w-5 -translate-y-1/2 items-center justify-center rounded-full border border-primary-400/30 bg-bg-base">
                    <ArrowRight className="h-3 w-3 text-primary-300" />
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </motion.section>

        <div className="mt-6 grid grid-cols-[1fr_0.72fr_1fr] items-center gap-8">
          <motion.section
            className="space-y-2.5"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.48, duration: 0.5 }}
          >
            <p className="mb-3 font-body text-xs font-semibold tracking-[0.18em] text-text-muted">EXPERIENCE CAPABILITIES</p>
            {capabilities.map(({ icon: Icon, title, detail }) => (
              <div key={title} className="flex items-center gap-3 rounded-xl border border-border-default/60 bg-bg-card/55 px-3.5 py-2.5 backdrop-blur-md">
                <Icon className="h-4 w-4 shrink-0 text-primary-300" />
                <div className="min-w-0">
                  <p className="font-display text-sm font-semibold text-text-primary">{title}</p>
                  <p className="mt-0.5 font-body text-[0.67rem] text-text-muted">{detail}</p>
                </div>
              </div>
            ))}
          </motion.section>

          <motion.section
            className="relative flex items-center justify-center"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.38, duration: 0.7, ease: 'easeOut' }}
            aria-label="Active RingIQ voice call"
          >
            <div className="relative h-60 w-60">
              <motion.div
                className="absolute inset-0 rounded-full border border-primary-400/25"
                animate={{ rotate: 360 }}
                transition={{ duration: 24, repeat: Infinity, ease: 'linear' }}
              >
                <span className="absolute left-[14%] top-[18%] h-2 w-2 rounded-full bg-primary-300" />
                <span className="absolute bottom-[13%] right-[18%] h-1.5 w-1.5 rounded-full bg-accent-300" />
              </motion.div>
              <motion.div
                className="absolute inset-5 rounded-full border border-dashed border-border-default/70"
                animate={{ rotate: -360 }}
                transition={{ duration: 18, repeat: Infinity, ease: 'linear' }}
              />
              <div className="absolute inset-10 flex flex-col items-center justify-center rounded-full border border-primary-300/35 bg-bg-card/80 shadow-2xl backdrop-blur-xl">
                <motion.div
                  className="flex h-16 w-16 items-center justify-center rounded-full border border-primary-300/40 bg-primary-500/20"
                  animate={{ boxShadow: ['0 0 0 0 currentColor', '0 0 0 15px transparent'] }}
                  transition={{ duration: 2.2, repeat: Infinity, ease: 'easeOut' }}
                >
                  <PhoneCall className="h-7 w-7 text-primary-200" strokeWidth={1.7} />
                </motion.div>
                <p className="mt-3 font-body text-[0.6rem] font-semibold tracking-[0.18em] text-primary-300">LIVE · GROUNDED</p>
                <div className="mt-2 flex h-5 items-center gap-0.5">
                  {waveform.map((height, index) => (
                    <motion.span
                      key={index}
                      className="w-0.5 rounded-full bg-primary-300"
                      animate={{ height: [`${Math.max(20, height - 28)}%`, `${height}%`, `${Math.max(24, height - 16)}%`] }}
                      transition={{ duration: 0.7 + (index % 4) * 0.12, repeat: Infinity, repeatType: 'mirror', ease: 'easeInOut' }}
                    />
                  ))}
                </div>
              </div>
            </div>
          </motion.section>

          <motion.section
            className="rounded-2xl border border-border-default/65 bg-bg-card/60 p-4 backdrop-blur-xl"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.52, duration: 0.5 }}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="font-body text-[0.62rem] font-semibold tracking-[0.17em] text-primary-300">OBSERVABLE BY DESIGN</p>
                <h2 className="mt-1 font-display text-lg font-semibold text-text-primary">Every turn leaves a trace</h2>
              </div>
              <Activity className="h-5 w-5 text-primary-300" />
            </div>
            <div className="mt-4 space-y-2.5">
              <div className="flex items-center justify-between rounded-xl border border-border-subtle bg-bg-base/55 px-3.5 py-3">
                <div className="flex items-center gap-2 font-body text-sm text-text-secondary">
                  <ScrollText className="h-4 w-4 text-primary-300" />
                  Pipeline events
                </div>
                <span className="rounded-full bg-primary-500/15 px-2 py-1 font-body text-[0.6rem] font-semibold tracking-[0.1em] text-primary-200">LOGGED</span>
              </div>
              <div className="flex items-center justify-between rounded-xl border border-border-subtle bg-bg-base/55 px-3.5 py-3">
                <div className="flex items-center gap-2 font-body text-sm text-text-secondary">
                  <Clock3 className="h-4 w-4 text-primary-300" />
                  Turn latency
                </div>
                <span className="rounded-full bg-primary-500/15 px-2 py-1 font-body text-[0.6rem] font-semibold tracking-[0.1em] text-primary-200">TIMED</span>
              </div>
            </div>
            <div className="mt-3 flex items-center gap-2 border-t border-border-subtle pt-3 font-body text-[0.67rem] text-text-muted">
              <Sparkles className="h-3.5 w-3.5 text-primary-300" />
              Debug the system without exposing another tenant.
            </div>
          </motion.section>
        </div>

        <motion.div
          className="mt-6 grid grid-cols-[0.92fr_1.08fr] overflow-hidden rounded-xl border border-border-default/65 bg-bg-card/50 backdrop-blur-md"
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.9, duration: 0.45 }}
        >
          <div className="flex items-center gap-3 border-r border-border-subtle px-4 py-3">
            <CheckCircle2 className="h-5 w-5 shrink-0 text-primary-300" />
            <div>
              <p className="font-body text-[0.58rem] font-semibold tracking-[0.16em] text-primary-300">WORKING IN PRODUCTION</p>
              <p className="mt-0.5 font-display text-sm font-semibold text-text-primary">Tenant-grounded calls with the active KB context</p>
            </div>
          </div>
          <div className="flex items-center gap-3 px-4 py-3">
            <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-dashed border-primary-400/50">
              <span className="h-1.5 w-1.5 rounded-full bg-primary-300" />
            </div>
            <div>
              <p className="font-body text-[0.58rem] font-semibold tracking-[0.16em] text-text-muted">NEXT LAYER</p>
              <p className="mt-0.5 font-body text-xs text-text-secondary">Structured qualification capture, callback time, and terminal outcome policy</p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
