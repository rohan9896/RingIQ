import React from 'react';
import { motion } from 'framer-motion';
import {
  ArrowRight,
  BookOpenCheck,
  Building2,
  Check,
  CircleCheckBig,
  LayoutDashboard,
  PhoneCall,
  Tags,
  UserRoundPlus,
} from 'lucide-react';

const reveal = {
  hidden: { opacity: 0, y: 18 },
  show: { opacity: 1, y: 0 },
};

const steps = [
  {
    number: '01',
    icon: Building2,
    title: 'Enter organization workspace',
    detail: 'Clerk keeps each organization in its own dedicated space from day one.',
  },
  {
    number: '02',
    icon: Tags,
    title: 'Select business category',
    detail: 'Shape the workspace and knowledge prompts around the tenant’s business context.',
  },
  {
    number: '03',
    icon: BookOpenCheck,
    title: 'Publish private KB',
    detail: 'Required answers turn trusted business knowledge into call readiness.',
  },
  {
    number: '04',
    icon: PhoneCall,
    title: 'Add lead and Call now',
    detail: 'Place a tenant-grounded call immediately—no scheduler required.',
  },
];

const readiness = [
  'Category selected',
  'Active KB published',
  'Valid lead available',
];

export default function OnboardingSlide() {
  return (
    <div className="slide-page relative bg-bg-base text-text-primary">
      <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        <div className="absolute -left-40 top-20 h-[30rem] w-[30rem] rounded-full bg-primary-500/20 blur-[120px]" />
        <div className="absolute -right-28 -top-24 h-[34rem] w-[34rem] rounded-full bg-accent-500/10 blur-[130px]" />
        <div className="absolute bottom-0 right-1/4 h-48 w-[32rem] rounded-full bg-primary-400/10 blur-[100px]" />
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
        <motion.div variants={reveal} className="mb-3 flex items-center gap-3">
          <span className="font-body text-xs font-semibold tracking-[0.2em] text-primary-300">
            ACTIVATION PATH
          </span>
          <span className="h-px w-14 bg-gradient-to-r from-primary-400/60 to-transparent" />
        </motion.div>
        <motion.h1
          variants={reveal}
          transition={{ duration: 0.5 }}
          className="font-display text-[3.25rem] font-semibold leading-[1.02] tracking-[-0.04em] text-text-primary"
        >
          Guided from workspace to <span className="text-primary-300">first call</span>
        </motion.h1>
        <motion.p
          variants={reveal}
          transition={{ duration: 0.45 }}
          className="mt-3 font-body text-lg text-text-secondary"
        >
          Readiness is a product state—not a setup document.
        </motion.p>
      </motion.header>

      <div className="slide-content relative z-10 grid grid-cols-[1.42fr_0.58fr] gap-7">
        <motion.section
          className="glass relative overflow-hidden rounded-2xl border border-border-default/70 px-7 py-6"
          initial="hidden"
          animate="show"
          transition={{ staggerChildren: 0.12, delayChildren: 0.15 }}
          aria-label="Four-step onboarding path"
        >
          <div className="absolute bottom-10 left-[3.25rem] top-10 w-px bg-border-default" />
          <motion.div
            className="absolute left-[3.18rem] top-10 w-1 rounded-full bg-primary-300"
            initial={{ height: 0 }}
            animate={{ height: 'calc(100% - 5rem)' }}
            transition={{ duration: 1.15, delay: 0.35, ease: 'easeOut' }}
          />

          <div className="relative flex flex-col justify-between gap-3">
            {steps.map(({ number, icon: Icon, title, detail }, index) => (
              <motion.article
                key={number}
                variants={reveal}
                transition={{ duration: 0.45 }}
                className="group grid grid-cols-[3.25rem_1fr_auto] items-center gap-5 rounded-xl border border-border-subtle bg-bg-card/50 px-4 py-3.5 backdrop-blur-md"
                whileHover={{ x: 5 }}
              >
                <div className="relative z-10 flex h-10 w-10 items-center justify-center rounded-full border border-primary-300/40 bg-bg-base text-primary-200 shadow-lg">
                <Icon className="h-[1.125rem] w-[1.125rem]" strokeWidth={1.8} />
                </div>
                <div className="min-w-0">
                  <div className="flex items-baseline gap-3">
                    <span className="font-display text-sm font-semibold tracking-[0.14em] text-primary-300">
                      {number}
                    </span>
                    <h2 className="font-display text-xl font-semibold tracking-[-0.015em] text-text-primary">
                      {title}
                    </h2>
                  </div>
                  <p className="mt-1 font-body text-sm leading-relaxed text-text-secondary">{detail}</p>
                </div>
                {index < steps.length - 1 ? (
                  <ArrowRight className="h-4 w-4 text-text-muted transition-transform group-hover:translate-x-1" />
                ) : (
                  <CircleCheckBig className="h-5 w-5 text-primary-300" />
                )}
              </motion.article>
            ))}
          </div>
        </motion.section>

        <motion.aside
          className="flex min-w-0 flex-col gap-4"
          initial="hidden"
          animate="show"
          transition={{ staggerChildren: 0.12, delayChildren: 0.35 }}
        >
          <motion.div
            variants={reveal}
            className="glass rounded-2xl border border-primary-300/25 p-5"
          >
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="font-body text-xs font-semibold tracking-[0.17em] text-primary-300">PRODUCT STATE</p>
                <h2 className="mt-1 font-display text-2xl font-semibold tracking-[-0.025em] text-text-primary">
                  Ready to call
                </h2>
              </div>
              <motion.div
                className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary-500/15 text-primary-300"
                animate={{ boxShadow: ['0 0 0 0 currentColor', '0 0 0 10px transparent'] }}
                transition={{ duration: 2.2, repeat: Infinity, ease: 'easeOut' }}
              >
                <PhoneCall className="h-5 w-5 text-primary-200" />
              </motion.div>
            </div>

            <div className="mt-5 space-y-3">
              {readiness.map((item) => (
                <div key={item} className="flex items-center gap-3 rounded-lg bg-bg-base/50 px-3 py-2.5">
                  <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary-500/20">
                    <Check className="h-3.5 w-3.5 text-primary-200" strokeWidth={2.4} />
                  </span>
                  <span className="font-body text-sm font-medium text-text-secondary">{item}</span>
                </div>
              ))}
            </div>
          </motion.div>

          <motion.div
            variants={reveal}
            className="rounded-2xl border border-border-default/70 bg-bg-card/65 p-5 backdrop-blur-md"
          >
            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-accent-500/10 p-2.5">
                <LayoutDashboard className="h-5 w-5 text-accent-200" />
              </div>
              <div>
                <p className="font-body text-xs font-semibold tracking-[0.15em] text-text-muted">ALWAYS ORIENTED</p>
                <p className="mt-2 font-display text-lg font-semibold leading-snug text-text-primary">
                  The dashboard points to the next incomplete action.
                </p>
                <div className="mt-4 flex items-center gap-2 font-body text-sm font-semibold text-primary-300">
                  <UserRoundPlus className="h-4 w-4" />
                  <span>Progress stays visible</span>
                </div>
              </div>
            </div>
          </motion.div>
        </motion.aside>
      </div>
    </div>
  );
}
