import React from 'react';
import { motion } from 'framer-motion';
import {
  Archive,
  ArrowRight,
  Check,
  CheckCircle2,
  Download,
  FileSpreadsheet,
  History,
  ListFilter,
  Megaphone,
  Pencil,
  Phone,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  UserPlus,
  XCircle,
} from 'lucide-react';

const reveal = {
  hidden: { opacity: 0, y: 18 },
  show: { opacity: 1, y: 0 },
};

const importSteps = [
  { label: 'Map columns', icon: SlidersHorizontal },
  { label: 'Validate', icon: ShieldCheck },
  { label: 'Import', icon: FileSpreadsheet },
];

const workspaceActions = [
  { label: 'Edit', icon: Pencil },
  { label: 'Archive', icon: Archive },
  { label: 'Enroll', icon: Megaphone },
  { label: 'Call history', icon: History },
];

export default function LeadsSlide() {
  return (
    <div className="slide-page relative bg-bg-base text-text-primary">
      <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        <div className="absolute -left-36 -top-40 h-[32rem] w-[32rem] rounded-full bg-primary-500/20 blur-[120px]" />
        <div className="absolute -right-28 top-1/4 h-[30rem] w-[30rem] rounded-full bg-accent-500/10 blur-[125px]" />
        <div className="absolute bottom-0 left-[38%] h-48 w-[36rem] rounded-full bg-primary-400/10 blur-[100px]" />
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
        <motion.div variants={reveal} transition={{ duration: 0.4 }} className="mb-3 flex items-center gap-3">
          <span className="font-body text-xs font-semibold tracking-[0.2em] text-primary-300">LEAD OPERATIONS</span>
          <span className="h-px w-20 bg-gradient-to-r from-primary-400/60 to-transparent" />
        </motion.div>
        <motion.h1
          variants={reveal}
          transition={{ duration: 0.55 }}
          className="font-display text-[3.45rem] font-semibold leading-[0.98] tracking-[-0.045em] text-text-primary"
        >
          Clean lead data in. <span className="text-primary-300">Actionable context out.</span>
        </motion.h1>
        <motion.p
          variants={reveal}
          transition={{ duration: 0.5 }}
          className="mt-3 font-body text-lg text-text-secondary"
        >
          Structure every record before it reaches a campaign—or the agent representing your business.
        </motion.p>
      </motion.header>

      <div className="slide-content relative z-10 grid grid-cols-2 gap-5">
        <motion.section
          className="glass relative flex min-w-0 flex-col overflow-hidden rounded-2xl p-5"
          initial={{ opacity: 0, x: -24 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.18, duration: 0.65, ease: 'easeOut' }}
          aria-label="CSV lead import pipeline"
        >
          <div className="absolute -left-12 top-1/3 h-48 w-48 rounded-full bg-primary-500/10 blur-3xl" aria-hidden="true" />
          <div className="relative flex items-start justify-between gap-4">
            <div>
              <p className="font-body text-xs font-semibold tracking-[0.18em] text-primary-300">CSV IMPORT</p>
              <h2 className="mt-1.5 font-display text-2xl font-semibold tracking-[-0.025em] text-text-primary">A guided path to clean records</h2>
            </div>
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-primary-300/30 bg-primary-500/20">
              <FileSpreadsheet className="h-5 w-5 text-primary-200" />
            </div>
          </div>

          <div className="relative mt-4 grid grid-cols-[1fr_auto_1fr_auto_1fr] items-center gap-2">
            {importSteps.map(({ label, icon: Icon }, index) => (
              <React.Fragment key={label}>
                <motion.div
                  className={`flex min-w-0 items-center justify-center gap-2 rounded-xl border px-3 py-3 ${
                    index === 1
                      ? 'border-primary-300/40 bg-primary-500/20'
                      : 'border-border-default/70 bg-bg-base/50'
                  }`}
                  initial={{ opacity: 0, scale: 0.94 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.34 + index * 0.12, duration: 0.4 }}
                >
                  <Icon className="h-4 w-4 shrink-0 text-primary-200" />
                  <span className="truncate font-body text-xs font-semibold text-text-secondary">{label}</span>
                </motion.div>
                {index < importSteps.length - 1 && <ArrowRight className="h-4 w-4 text-primary-300" />}
              </React.Fragment>
            ))}
          </div>

          <div className="relative mt-4 grid grid-cols-[1fr_0.92fr] gap-3">
            <div className="rounded-xl border border-border-subtle bg-bg-base/45 p-4">
              <div className="mb-3 flex items-center justify-between">
                <p className="font-body text-xs font-semibold tracking-[0.14em] text-text-muted">FIELD MAP</p>
                <span className="flex items-center gap-1 font-body text-xs text-primary-300">
                  <Check className="h-3.5 w-3.5" /> Required mapped
                </span>
              </div>
              <div className="space-y-2">
                {['Name', 'Email', 'Phone'].map((field) => (
                  <div key={field} className="flex items-center justify-between rounded-lg border border-border-subtle bg-bg-card/55 px-3 py-2">
                    <span className="font-body text-sm text-text-secondary">{field}</span>
                    <span className="rounded-md bg-primary-500/20 px-2 py-1 font-body text-[0.65rem] font-semibold tracking-[0.1em] text-primary-200">MANDATORY</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-xl border border-border-subtle bg-bg-base/45 p-4">
              <p className="font-body text-xs font-semibold tracking-[0.14em] text-text-muted">OPTIONAL CONTEXT</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {['Project', 'Budget', 'Locality', 'Property type'].map((field) => (
                  <span key={field} className="rounded-lg border border-border-default/70 bg-bg-card/60 px-2.5 py-2 font-body text-xs text-text-secondary">
                    {field}
                  </span>
                ))}
              </div>
              <p className="mt-3 font-body text-xs leading-relaxed text-text-muted">Real-estate attributes travel with the lead into every agent interaction.</p>
            </div>
          </div>

          <motion.div
            className="relative mt-3 rounded-xl border border-primary-300/30 bg-primary-500/15 p-3.5"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7, duration: 0.45 }}
          >
            <div className="flex items-center justify-between gap-4">
              <div className="flex min-w-0 items-start gap-3">
                <XCircle className="mt-0.5 h-5 w-5 shrink-0 text-primary-200" />
                <div>
                  <p className="font-body text-sm font-semibold text-text-primary">2 rows need attention</p>
                  <p className="mt-1 font-body text-xs leading-snug text-text-secondary">Duplicate detected · phone must match Indian or E.164 format</p>
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-2 rounded-lg border border-primary-300/30 bg-bg-base/45 px-3 py-2 font-body text-xs font-semibold text-primary-200">
                <Download className="h-4 w-4" /> Error report
              </div>
            </div>
            <div className="mt-2.5 flex items-center gap-2 border-t border-border-subtle pt-2.5 font-body text-xs text-primary-200">
              <CheckCircle2 className="h-4 w-4" /> Invalid rows are explained—never silently discarded.
            </div>
          </motion.div>
        </motion.section>

        <motion.section
          className="glass relative flex min-w-0 flex-col overflow-hidden rounded-2xl p-5"
          initial={{ opacity: 0, x: 24 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.26, duration: 0.65, ease: 'easeOut' }}
          aria-label="Lead management workspace"
        >
          <div className="absolute -right-12 bottom-8 h-52 w-52 rounded-full bg-accent-500/10 blur-3xl" aria-hidden="true" />
          <div className="relative flex items-start justify-between gap-4">
            <div>
              <p className="font-body text-xs font-semibold tracking-[0.18em] text-primary-300">LEAD WORKSPACE</p>
              <h2 className="mt-1.5 font-display text-2xl font-semibold tracking-[-0.025em] text-text-primary">One record, every next action</h2>
            </div>
            <div className="flex items-center gap-2 rounded-lg border border-primary-300/30 bg-primary-500/20 px-3 py-2 font-body text-xs font-semibold text-primary-200">
              <UserPlus className="h-4 w-4" /> New lead
            </div>
          </div>

          <div className="relative mt-4 flex items-center gap-2">
            <div className="flex min-w-0 flex-1 items-center gap-2 rounded-xl border border-border-default/70 bg-bg-base/50 px-3 py-2.5">
              <Search className="h-4 w-4 shrink-0 text-text-muted" />
              <span className="truncate font-body text-sm text-text-muted">Search leads, phone, email…</span>
            </div>
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-border-default/70 bg-bg-base/50">
              <ListFilter className="h-4 w-4 text-primary-200" />
            </div>
          </div>

          <motion.div
            className="relative mt-4 overflow-hidden rounded-2xl border border-primary-300/30 bg-bg-card/60"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.5 }}
          >
            <div className="flex items-center justify-between border-b border-border-subtle bg-primary-500/10 px-4 py-3">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full border border-primary-300/30 bg-primary-500/20 font-display text-sm font-semibold text-primary-200">DL</div>
                <div>
                  <p className="font-body text-sm font-semibold text-text-primary">Demo Lead 014</p>
                  <p className="mt-0.5 font-body text-xs text-text-muted">demo014@example.invalid · +91 98••• ••210</p>
                </div>
              </div>
              <span className="rounded-full border border-primary-300/30 bg-primary-500/20 px-2.5 py-1 font-body text-[0.65rem] font-semibold tracking-[0.1em] text-primary-200">READY</span>
            </div>

            <div className="grid grid-cols-2 gap-4 p-4">
              <div>
                <p className="font-body text-xs font-semibold tracking-[0.14em] text-text-muted">AGENT CONTEXT</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {['2–3 BHK', 'West zone', 'Site visit'].map((tag) => (
                    <span key={tag} className="rounded-lg border border-border-default/70 bg-bg-base/50 px-2.5 py-1.5 font-body text-xs text-text-secondary">{tag}</span>
                  ))}
                </div>
              </div>
              <div>
                <p className="font-body text-xs font-semibold tracking-[0.14em] text-text-muted">CAMPAIGN</p>
                <div className="mt-2 rounded-lg border border-border-default/70 bg-bg-base/50 px-3 py-2">
                  <p className="font-body text-sm font-medium text-text-secondary">Qualification queue</p>
                  <p className="mt-1 font-body text-xs text-text-muted">Enrollment ready</p>
                </div>
              </div>
            </div>
          </motion.div>

          <div className="relative mt-3 grid grid-cols-4 gap-2">
            {workspaceActions.map(({ label, icon: Icon }, index) => (
              <motion.div
                key={label}
                className="flex min-w-0 flex-col items-center gap-2 rounded-xl border border-border-subtle bg-bg-base/45 px-2 py-3 text-center"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.62 + index * 0.08, duration: 0.35 }}
              >
                <Icon className="h-4 w-4 text-primary-200" />
                <span className="truncate font-body text-xs font-medium text-text-secondary">{label}</span>
              </motion.div>
            ))}
          </div>

          <div className="relative mt-3 flex items-center justify-between rounded-xl border border-border-subtle bg-bg-base/45 px-4 py-3">
            <div className="flex items-center gap-3">
              <Phone className="h-4 w-4 text-primary-200" />
              <div>
                <p className="font-body text-sm font-medium text-text-secondary">Call context stays attached</p>
                <p className="mt-0.5 font-body text-xs text-text-muted">Optional attributes pass directly into the agent.</p>
              </div>
            </div>
            <ArrowRight className="h-4 w-4 shrink-0 text-primary-300" />
          </div>
        </motion.section>
      </div>
    </div>
  );
}
