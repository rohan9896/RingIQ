import React from 'react';
import { motion } from 'framer-motion';
import {
  ArrowRight,
  AudioLines,
  BookOpenCheck,
  BrainCircuit,
  BriefcaseBusiness,
  CheckCircle2,
  CloudCog,
  Database,
  Fingerprint,
  HardDrive,
  Layers3,
  LockKeyhole,
  MessageSquareText,
  Network,
  PhoneCall,
  RadioTower,
  RefreshCw,
  Search,
  ShieldCheck,
  UserRound,
  Volume2,
  Workflow,
} from 'lucide-react';

const rise = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0 },
};

const controlNodes = [
  { icon: BriefcaseBusiness, title: 'Next.js workspace', note: 'Tenant product surface' },
  { icon: CloudCog, title: 'FastAPI core API', note: 'AuthZ · mutations · state' },
  { icon: Database, title: 'PostgreSQL', note: 'KB · campaigns · leads' },
  { icon: Workflow, title: 'Jobs + outbox', note: 'Background dispatch' },
];

const knowledgeNodes = [
  { icon: MessageSquareText, title: 'Q&A + profile', note: 'Approved source' },
  { icon: BookOpenCheck, title: 'Published KB v17', note: 'Immutable version' },
  { icon: Search, title: 'pgvector', note: 'Tenant chunks · target' },
  { icon: LockKeyhole, title: 'Pinned retrieval', note: 'tenant_7f · kb_v17' },
];

const voiceNodes = [
  { icon: RefreshCw, title: 'Worker claim', note: 'Leased + idempotent' },
  { icon: Network, title: 'LiveKit + Vobiz', note: 'Session · SIP' },
  { icon: AudioLines, title: 'Deepgram STT', note: 'Streaming speech' },
  { icon: BrainCircuit, title: 'Context + Groq', note: 'Grounded response' },
  { icon: Volume2, title: 'Sarvam TTS', note: 'Streaming voice' },
  { icon: UserRound, title: 'Lead', note: 'Natural dialogue' },
];

const invariants = [
  {
    icon: ShieldCheck,
    title: 'Isolation',
    text: 'tenant_id on every owned row · scoped queries + tenant-aware FKs · PostgreSQL RLS direction',
  },
  {
    icon: Workflow,
    title: 'Jobs',
    text: 'Atomic state + outbox · leases · idempotency · bounded retry + dead-letter · one active attempt',
  },
  {
    icon: HardDrive,
    title: 'Artifacts',
    text: 'Facts + transcripts in Postgres · recordings in private tenant-prefixed object storage · short-lived access',
  },
  {
    icon: RadioTower,
    title: 'Reliability + traces',
    text: 'Provider timeouts · graceful failure · latency events · tenant/campaign/lead/attempt correlation',
  },
];

function FlowNode({ icon: Icon, title, note, highlighted = false, compact = false }) {
  return (
    <div
      className={`relative flex min-w-0 items-center gap-2 rounded-lg border px-2.5 py-2 backdrop-blur-md mobile-card ${
        highlighted
          ? 'border-primary-300/45 bg-primary-500/15'
          : 'border-border-default/65 bg-bg-card/60'
      }`}
    >
      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-primary-400/25 bg-bg-base/65">
        <Icon className="h-3.5 w-3.5 text-primary-300" />
      </div>
      <div className="min-w-0">
        <p className={`${compact ? 'text-[0.66rem]' : 'text-xs'} truncate font-display font-semibold text-text-primary mobile-wrap`}>
          {title}
        </p>
        <p className="mt-0.5 truncate font-body text-[0.55rem] text-text-muted mobile-wrap">{note}</p>
      </div>
    </div>
  );
}

function Connector() {
  return (
    <div className="flex items-center justify-center mobile-flow-connector">
      <span className="h-px flex-1 bg-gradient-to-r from-primary-400/25 to-primary-300/60" />
      <ArrowRight className="h-3.5 w-3.5 shrink-0 text-primary-300" />
    </div>
  );
}

export default function ArchitectureSlide() {
  return (
    <div className="slide-page relative bg-bg-base text-text-primary" data-slide="12-architecture">
      <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        <div className="absolute -left-40 -top-36 h-[32rem] w-[32rem] rounded-full bg-primary-500/18 blur-[120px]" />
        <div className="absolute -right-36 top-2 h-[30rem] w-[30rem] rounded-full bg-accent-500/12 blur-[125px]" />
        <div className="absolute bottom-0 left-[32%] h-48 w-[40rem] rounded-full bg-primary-400/10 blur-[100px]" />
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
        className="relative z-10 mb-3 shrink-0"
        initial="hidden"
        animate="show"
        transition={{ staggerChildren: 0.08 }}
      >
        <motion.div variants={rise} className="mb-2 flex items-center gap-3 mobile-chip-row">
          <span className="font-body text-xs font-semibold tracking-[0.2em] text-primary-300">
            TECHNICAL ARCHITECTURE
          </span>
          <span className="h-px w-16 bg-gradient-to-r from-primary-400/60 to-transparent" />
          <span className="rounded-full border border-primary-300/30 bg-primary-500/10 px-2.5 py-1 font-body text-[0.6rem] font-semibold tracking-[0.12em] text-primary-200 mobile-wrap">
            B2B · MULTI-TENANT · REAL-TIME
          </span>
        </motion.div>
        <motion.h1
          variants={rise}
          className="font-display text-[2.75rem] font-semibold leading-[1.03] tracking-[-0.04em] text-text-primary mobile-title"
        >
          Multi-tenant RAG meets a <span className="text-primary-300">real-time voice pipeline</span>
        </motion.h1>
        <motion.p variants={rise} className="mt-2 font-body text-base text-text-secondary mobile-subtitle">
          One tenant context travels end to end; live media never waits on persistence.
        </motion.p>
      </motion.header>

      <div className="slide-content relative z-10 flex min-h-0 flex-col justify-center gap-2.5">
        <motion.div
          className="grid grid-cols-[7.5rem_1fr] overflow-hidden rounded-xl border border-border-default/70 bg-bg-card/55 backdrop-blur-xl mobile-stack mobile-card"
          initial="hidden"
          animate="show"
          transition={{ staggerChildren: 0.06, delayChildren: 0.12 }}
        >
          <div className="flex flex-col justify-between border-r border-border-subtle bg-bg-base/45 px-3 py-3 mobile-stack">
            <div>
              <Layers3 className="h-4 w-4 text-primary-300" />
              <p className="mt-2 font-body text-[0.62rem] font-semibold tracking-[0.16em] text-primary-300">CONTROL PLANE</p>
            </div>
            <span className="font-body text-[0.54rem] leading-snug text-text-muted">Product truth + dispatch</span>
          </div>
          <div className="grid grid-cols-[1fr_2rem_1fr_2rem_1fr_2rem_1fr] items-center gap-1.5 p-2.5 mobile-flow">
            {controlNodes.map((node, index) => (
              <React.Fragment key={node.title}>
                <motion.div variants={rise}>
                  <FlowNode {...node} highlighted={index === 1} />
                </motion.div>
                {index < controlNodes.length - 1 && <Connector />}
              </React.Fragment>
            ))}
          </div>
        </motion.div>

        <motion.div
          className="grid grid-cols-[7.5rem_1fr] overflow-hidden rounded-xl border border-primary-300/25 bg-primary-500/10 backdrop-blur-xl mobile-stack mobile-card"
          initial="hidden"
          animate="show"
          transition={{ staggerChildren: 0.06, delayChildren: 0.28 }}
        >
          <div className="flex flex-col justify-between border-r border-primary-300/20 bg-bg-base/40 px-3 py-3 mobile-stack">
            <div>
              <BookOpenCheck className="h-4 w-4 text-primary-300" />
              <p className="mt-2 font-body text-[0.62rem] font-semibold tracking-[0.16em] text-primary-300">KNOWLEDGE PLANE</p>
            </div>
            <span className="font-body text-[0.54rem] leading-snug text-text-muted">Approved context only</span>
          </div>
          <div className="relative p-2.5">
            <div className="grid grid-cols-[1fr_2rem_1fr_2rem_1fr_2rem_1fr] items-center gap-1.5 mobile-flow">
              {knowledgeNodes.map((node, index) => (
                <React.Fragment key={node.title}>
                  <motion.div variants={rise}>
                    <FlowNode {...node} highlighted={index === 3} />
                  </motion.div>
                  {index < knowledgeNodes.length - 1 && <Connector />}
                </React.Fragment>
              ))}
            </div>
            <div className="mt-1.5 flex items-center justify-between px-1 font-body text-[0.55rem] text-text-muted mobile-stack">
              <span className="mobile-wrap">Production: each call already loads pinned tenant KB context</span>
              <span className="flex items-center gap-1 text-primary-200 mobile-wrap">
                <Fingerprint className="h-3 w-3" />
                Per turn: tenant_7f only · approved kb_v17
              </span>
            </div>
          </div>
        </motion.div>

        <motion.div
          className="grid grid-cols-[7.5rem_1fr] overflow-hidden rounded-xl border border-border-default/70 bg-bg-card/55 backdrop-blur-xl mobile-stack mobile-card"
          initial="hidden"
          animate="show"
          transition={{ staggerChildren: 0.05, delayChildren: 0.44 }}
        >
          <div className="flex flex-col justify-between border-r border-border-subtle bg-bg-base/45 px-3 py-3 mobile-stack">
            <div>
              <PhoneCall className="h-4 w-4 text-primary-300" />
              <p className="mt-2 font-body text-[0.62rem] font-semibold tracking-[0.16em] text-primary-300">REAL-TIME VOICE</p>
            </div>
            <span className="font-body text-[0.54rem] leading-snug text-text-muted">Media path stays hot</span>
          </div>
          <div className="p-2.5">
            <div className="grid grid-cols-[1fr_1.25rem_1fr_1.25rem_1fr_1.25rem_1.12fr_1.25rem_1fr_1.25rem_0.78fr] items-center gap-1 mobile-flow">
              {voiceNodes.map((node, index) => (
                <React.Fragment key={node.title}>
                  <motion.div variants={rise}>
                    <FlowNode {...node} compact highlighted={index === 3} />
                  </motion.div>
                  {index < voiceNodes.length - 1 && <Connector />}
                </React.Fragment>
              ))}
            </div>
            <div className="mt-1.5 flex items-center justify-between px-1 font-body text-[0.55rem] text-text-muted mobile-stack">
              <span className="flex items-center gap-1.5 mobile-wrap"><Fingerprint className="h-3 w-3 text-primary-300" /> tenant_7f · campaign_82 · lead_204 · attempt_9</span>
              <span className="flex items-center gap-1.5 mobile-wrap"><CheckCircle2 className="h-3 w-3 text-primary-300" /> Idempotent events + result → core, asynchronous to media</span>
            </div>
          </div>
        </motion.div>

        <motion.section
          className="grid grid-cols-4 overflow-hidden rounded-xl border border-primary-300/25 bg-primary-500/10 backdrop-blur-xl mobile-single-grid"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.72, duration: 0.45 }}
          aria-label="Architecture invariants"
        >
          {invariants.map(({ icon: Icon, title, text }, index) => (
            <div key={title} className={`px-3 py-2.5 mobile-card ${index > 0 ? 'border-l border-border-subtle' : ''}`}>
              <div className="flex items-center gap-2">
                <Icon className="h-3.5 w-3.5 shrink-0 text-primary-300" />
                <p className="font-display text-[0.68rem] font-semibold text-text-primary">{title}</p>
              </div>
              <p className="mt-1 font-body text-[0.54rem] leading-[1.35] text-text-muted mobile-wrap">{text}</p>
            </div>
          ))}
        </motion.section>
      </div>
    </div>
  );
}
