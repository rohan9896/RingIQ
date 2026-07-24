import React from 'react';
import { motion } from 'framer-motion';
import {
  ArrowRight,
  BadgeCheck,
  Building2,
  Database,
  Fingerprint,
  KeyRound,
  LockKeyhole,
  Network,
  Route,
  ShieldCheck,
  UserCog,
  Workflow,
} from 'lucide-react';

const reveal = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0 },
};

const identityFlow = [
  {
    icon: Fingerprint,
    eyebrow: '01 · CLERK EDGE',
    title: 'Identity',
    points: ['Custom sign-in / sign-up', 'Session + token verification', 'Canonical user identity'],
  },
  {
    icon: Building2,
    eyebrow: '02 · ORG CONTEXT',
    title: 'Workspace',
    points: ['Create or select workspace', 'Activate organization', 'Membership + role context'],
  },
  {
    icon: Network,
    eyebrow: '03 · RINGIQ CORE',
    title: 'Tenant mapping',
    points: ['User · Tenant · Membership', 'Idempotent internal mapping', 'Resolve TenantContext'],
  },
  {
    icon: LockKeyhole,
    eyebrow: '04 · PRODUCT DATA',
    title: 'Authorization',
    points: ['Scope every product query', 'Tenant-aware jobs + retrieval', 'Claims alone never authorize data'],
  },
];

const tenantResources = ['Leads + KB', 'Campaigns + jobs', 'Calls + artifacts'];

function FlowCard({ icon: Icon, eyebrow, title, points, highlighted }) {
  return (
    <motion.article
      variants={reveal}
      className={`relative min-w-0 rounded-xl border p-3.5 backdrop-blur-xl mobile-card mobile-wrap ${
        highlighted
          ? 'border-primary-300/45 bg-primary-500/15'
          : 'border-border-default/70 bg-bg-card/60'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-primary-300/30 bg-bg-base/60">
          <Icon className="h-4 w-4 text-primary-300" />
        </div>
        <span className="font-body text-[0.58rem] font-semibold tracking-[0.13em] text-primary-300">
          {eyebrow}
        </span>
      </div>
      <h2 className="mt-2.5 font-display text-base font-semibold text-text-primary">{title}</h2>
      <div className="mt-2 space-y-1.5">
        {points.map((point) => (
          <div key={point} className="flex items-start gap-1.5 font-body text-[0.68rem] leading-snug text-text-secondary">
            <BadgeCheck className="mt-0.5 h-3 w-3 shrink-0 text-primary-300" />
            <span>{point}</span>
          </div>
        ))}
      </div>
    </motion.article>
  );
}

function Connector() {
  return (
    <motion.div variants={reveal} className="flex items-center justify-center mobile-flow-connector" aria-hidden="true">
      <span className="h-px flex-1 bg-gradient-to-r from-primary-400/25 to-primary-300/70" />
      <ArrowRight className="h-4 w-4 shrink-0 text-primary-300" />
    </motion.div>
  );
}

export default function ClerkIdentitySlide() {
  return (
    <div className="slide-page relative bg-bg-base text-text-primary" data-slide="13-clerk-identity">
      <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        <div className="absolute -left-36 -top-40 h-[32rem] w-[32rem] rounded-full bg-primary-500/20 blur-[120px]" />
        <div className="absolute -right-32 top-4 h-[30rem] w-[30rem] rounded-full bg-accent-500/12 blur-[125px]" />
        <div className="absolute bottom-0 left-[34%] h-48 w-[38rem] rounded-full bg-primary-400/10 blur-[100px]" />
        <div className="absolute inset-0 opacity-20">
          {Array.from({ length: 13 }).map((_, index) => (
            <div
              key={`identity-grid-${index}`}
              className="absolute inset-y-0 w-px bg-border-subtle"
              style={{ left: `${index * 8.33}%` }}
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
        <motion.div variants={reveal} className="mb-2 flex items-center gap-3 mobile-chip-row">
          <span className="font-body text-xs font-semibold tracking-[0.2em] text-primary-300">
            IDENTITY + TENANT CONTROL
          </span>
          <span className="h-px w-14 bg-gradient-to-r from-primary-400/60 to-transparent" />
          <span className="rounded-full border border-primary-300/30 bg-primary-500/10 px-2.5 py-1 font-body text-[0.6rem] font-semibold tracking-[0.12em] text-primary-200 mobile-wrap">
            CLERK × RINGIQ
          </span>
        </motion.div>
        <motion.h1
          variants={reveal}
          className="font-display text-[2.75rem] font-semibold leading-[1.03] tracking-[-0.04em] text-text-primary mobile-title"
        >
          Clerk handles identity. <span className="text-primary-300">RingIQ enforces tenancy.</span>
        </motion.h1>
        <motion.p variants={reveal} className="mt-2 font-body text-base text-text-secondary mobile-subtitle">
          Authentication starts at the edge; product authorization stays inside the platform.
        </motion.p>
      </motion.header>

      <div className="slide-content relative z-10 flex min-h-0 flex-col justify-center gap-2.5">
        <motion.section
          className="rounded-2xl border border-border-default/70 bg-bg-card/45 p-2.5 backdrop-blur-xl"
          initial="hidden"
          animate="show"
          transition={{ staggerChildren: 0.065, delayChildren: 0.12 }}
          aria-label="Identity to tenant data authorization flow"
        >
          <div className="grid grid-cols-[1fr_1.8rem_1fr_1.8rem_1fr_1.8rem_1.08fr] items-stretch gap-1.5 mobile-flow">
            {identityFlow.map((stage, index) => (
              <React.Fragment key={stage.title}>
                <FlowCard {...stage} highlighted={index === 2 || index === 3} />
                {index < identityFlow.length - 1 && <Connector />}
              </React.Fragment>
            ))}
          </div>
          <motion.div variants={reveal} className="mt-2 grid grid-cols-[auto_1fr] items-center gap-3 rounded-lg border border-primary-300/25 bg-primary-500/10 px-3 py-2 mobile-stack mobile-card">
            <div className="flex items-center gap-2 font-body text-[0.64rem] font-semibold tracking-[0.12em] text-primary-200">
              <ShieldCheck className="h-3.5 w-3.5" />
              ACTIVE ORG REQUIRED
            </div>
            <div className="grid grid-cols-3 gap-2 mobile-compact-grid">
              {tenantResources.map((resource) => (
                <span key={resource} className="rounded-md border border-border-subtle bg-bg-base/45 px-2 py-1 text-center font-body text-[0.62rem] text-text-secondary mobile-wrap">
                  {resource}
                </span>
              ))}
            </div>
          </motion.div>
        </motion.section>

        <motion.section
          className="grid grid-cols-[0.84fr_1.16fr] gap-2.5 mobile-stack"
          initial="hidden"
          animate="show"
          transition={{ staggerChildren: 0.1, delayChildren: 0.45 }}
          aria-label="Platform administration realm and delivery status"
        >
          <motion.article variants={reveal} className="rounded-xl border border-border-default/70 bg-bg-card/60 p-3.5 backdrop-blur-xl mobile-card">
            <div className="flex items-start gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-primary-300/30 bg-primary-500/10">
                <UserCog className="h-[1.125rem] w-[1.125rem] text-primary-300" />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-2 mobile-chip-row">
                  <h2 className="font-display text-base font-semibold text-text-primary">Separate platform realm</h2>
                  <span className="rounded-full border border-border-default bg-bg-base/50 px-2 py-0.5 font-body text-[0.55rem] font-semibold tracking-[0.1em] text-text-muted mobile-wrap">INTERNAL</span>
                </div>
                <p className="mt-1 font-body text-[0.68rem] leading-snug text-text-secondary">
                  Dedicated, organizationless Clerk accounts cannot also be tenant identities.
                </p>
              </div>
            </div>
            <div className="mt-2.5 grid grid-cols-3 gap-1.5 mobile-compact-grid">
              {['platform_super_admin', 'operations', 'template_manager'].map((role) => (
                <div key={role} className="flex items-center justify-center gap-1 rounded-lg border border-border-subtle bg-bg-base/45 px-1.5 py-2 font-body text-[0.58rem] text-text-secondary">
                  <KeyRound className="h-3 w-3 shrink-0 text-primary-300" />
                  <span className="truncate mobile-wrap">{role}</span>
                </div>
              ))}
            </div>
            <p className="mt-2 flex items-center gap-1.5 font-body text-[0.61rem] text-text-muted">
              <Route className="h-3 w-3 text-primary-300" /> Backend role checks protect platform routes.
            </p>
          </motion.article>

          <motion.article variants={reveal} className="overflow-hidden rounded-xl border border-primary-300/25 bg-primary-500/10 backdrop-blur-xl mobile-card">
            <div className="grid grid-cols-2 mobile-stack">
              <div className="p-3.5">
                <div className="flex items-center gap-2">
                  <BadgeCheck className="h-4 w-4 text-primary-300" />
                  <h2 className="font-body text-[0.66rem] font-semibold tracking-[0.15em] text-primary-200">CURRENT</h2>
                </div>
                <p className="mt-2 font-body text-[0.67rem] leading-[1.45] text-text-secondary">
                  Custom auth · workspace setup + org selection · separate realms · role-aware backend contexts · tenant provisioning
                </p>
              </div>
              <div className="border-l border-border-subtle bg-bg-card/35 p-3.5">
                <div className="flex items-center gap-2">
                  <Workflow className="h-4 w-4 text-text-muted" />
                  <h2 className="font-body text-[0.66rem] font-semibold tracking-[0.15em] text-text-secondary">NEXT</h2>
                </div>
                <p className="mt-2 font-body text-[0.67rem] leading-[1.45] text-text-secondary">
                  Invitations + removal · org edit / suspend / lifecycle · platform-user admin · webhook sync + audit trail
                </p>
                <p className="mt-1.5 flex items-center gap-1 font-body text-[0.56rem] text-text-muted">
                  <Database className="h-3 w-3" /> Idempotent Clerk webhook sync is architecture direction.
                </p>
              </div>
            </div>
          </motion.article>
        </motion.section>
      </div>
    </div>
  );
}
