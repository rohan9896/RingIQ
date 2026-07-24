import React from 'react';
import { motion } from 'framer-motion';
import {
  ArrowUpRight,
  Languages,
  Shapes,
  PhoneCall,
  Sparkles,
  UserRoundCheck,
} from 'lucide-react';

const reveal = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
};

const tags = [
  { icon: Languages, label: 'Hindi + English + Hinglish' },
  { icon: Shapes, label: 'Category-independent' },
  { icon: UserRoundCheck, label: 'Human follow-up where it matters' },
];

const waveform = [34, 56, 76, 44, 88, 64, 100, 72, 48, 84, 58, 38, 68, 92, 62, 42, 74];

export default function HeroSlide() {
  return (
    <div className="slide-page relative bg-bg-base text-text-primary" data-slide="01-hero">
      <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        <div className="absolute -left-32 -top-40 h-[34rem] w-[34rem] rounded-full bg-primary-500/20 blur-[110px]" />
        <div className="absolute -right-28 top-12 h-[32rem] w-[32rem] rounded-full bg-accent-500/15 blur-[120px]" />
        <div className="absolute bottom-0 left-1/3 h-56 w-[38rem] rounded-full bg-primary-400/10 blur-[100px]" />
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

      <div className="slide-content mobile-stack relative z-10 grid grid-cols-[1.08fr_0.92fr] items-center gap-14">
        <motion.section
          className="flex min-w-0 flex-col justify-center"
          initial="hidden"
          animate="show"
          transition={{ staggerChildren: 0.11 }}
        >
          <motion.div variants={reveal} transition={{ duration: 0.45 }} className="mb-7 flex items-center gap-3">
            <span className="inline-flex items-center gap-2 rounded-full border border-primary-400/30 bg-primary-500/10 px-3 py-1.5 font-body text-xs font-semibold tracking-[0.2em] text-primary-200">
              <Sparkles className="h-3.5 w-3.5 text-primary-300" />
              AI VOICE SALES PLATFORM
            </span>
            <span className="h-px w-16 bg-gradient-to-r from-primary-400/60 to-transparent" />
          </motion.div>

          <motion.h1
            variants={reveal}
            transition={{ duration: 0.55 }}
            className="mobile-title mobile-hero-title font-display text-[5.9rem] font-semibold leading-[0.88] tracking-[-0.055em] text-text-primary"
          >
            Ring<span className="text-primary-300">IQ</span>
          </motion.h1>

          <motion.h2
            variants={reveal}
            transition={{ duration: 0.55 }}
            className="mobile-subtitle mt-6 max-w-3xl font-display text-[2.05rem] font-medium leading-[1.12] tracking-[-0.025em] text-text-primary"
          >
            AI voice qualification that turns lead volume into{' '}
            <span className="text-primary-300">sales focus.</span>
          </motion.h2>

          <motion.p
            variants={reveal}
            transition={{ duration: 0.5 }}
            className="mt-5 max-w-2xl font-body text-lg leading-relaxed text-text-secondary"
          >
            A B2B, multi-tenant platform that automatically calls, qualifies, and prioritizes leads using each business&apos;s private knowledge base.
          </motion.p>

          <motion.div
            variants={reveal}
            transition={{ duration: 0.5 }}
            className="mobile-chip-row mt-8 flex flex-wrap gap-2.5"
          >
            {tags.map(({ icon: Icon, label }) => (
              <div
                key={label}
                className="flex items-center gap-2 rounded-lg border border-border-default/70 bg-bg-card/65 px-3.5 py-2 font-body text-sm text-text-secondary backdrop-blur-md"
              >
                <Icon className="h-4 w-4 text-primary-300" />
                <span>{label}</span>
              </div>
            ))}
          </motion.div>
        </motion.section>

        <motion.section
          className="mobile-visual relative flex items-center justify-center"
          initial={{ opacity: 0, scale: 0.94 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          aria-label="AI call signal prioritizing a qualified lead"
        >
          <div className="mobile-visual relative aspect-square w-full max-w-[38rem]">
            <motion.div
              className="absolute inset-[7%] rounded-full border border-primary-400/20"
              animate={{ rotate: 360 }}
              transition={{ duration: 30, repeat: Infinity, ease: 'linear' }}
            >
              <span className="absolute left-[10%] top-[18%] h-2.5 w-2.5 rounded-full bg-primary-300" />
              <span className="absolute bottom-[11%] right-[18%] h-2 w-2 rounded-full bg-accent-300" />
              <span className="absolute right-[2%] top-1/2 h-1.5 w-1.5 rounded-full bg-primary-400" />
            </motion.div>
            <motion.div
              className="absolute inset-[17%] rounded-full border border-dashed border-border-default/70"
              animate={{ rotate: -360 }}
              transition={{ duration: 22, repeat: Infinity, ease: 'linear' }}
            />

            <div className="absolute inset-[25%] rounded-full border border-primary-300/30 bg-bg-card/70 shadow-2xl backdrop-blur-xl">
              <div className="absolute inset-3 rounded-full border border-border-subtle bg-bg-base/70" />
              <div className="absolute inset-0 flex items-center justify-center">
                <motion.div
                  className="flex h-24 w-24 items-center justify-center rounded-full border border-primary-300/40 bg-primary-500/20"
                  animate={{ boxShadow: ['0 0 0 0 currentColor', '0 0 0 18px transparent'] }}
                  transition={{ duration: 2.2, repeat: Infinity, ease: 'easeOut' }}
                >
                  <PhoneCall className="h-10 w-10 text-primary-200" strokeWidth={1.7} />
                </motion.div>
              </div>
            </div>

            <div className="mobile-card glass absolute left-0 top-[14%] w-52 rounded-2xl p-4">
              <div className="mb-3 flex items-center justify-between font-body text-xs font-semibold tracking-[0.14em] text-text-muted">
                <span>LIVE VOICE SIGNAL</span>
                <span className="h-2 w-2 rounded-full bg-primary-300" />
              </div>
              <div className="flex h-12 items-center justify-between gap-1">
                {waveform.map((height, index) => (
                  <motion.span
                    key={index}
                    className="w-1 rounded-full bg-primary-300"
                    initial={{ height: '16%' }}
                    animate={{ height: [`${Math.max(18, height - 25)}%`, `${height}%`, `${Math.max(22, height - 15)}%`] }}
                    transition={{ duration: 0.7 + (index % 4) * 0.12, repeat: Infinity, repeatType: 'mirror', ease: 'easeInOut' }}
                  />
                ))}
              </div>
            </div>

            <motion.div
              className="mobile-card glass absolute bottom-[8%] right-0 w-60 rounded-2xl p-4"
              initial={{ opacity: 0, x: 24 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.7, duration: 0.5 }}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-body text-xs font-semibold tracking-[0.16em] text-primary-300">NEXT BEST ACTION</p>
                  <p className="mt-2 font-display text-lg font-semibold text-text-primary">Prioritize human follow-up</p>
                </div>
                <div className="rounded-lg bg-primary-500/15 p-2">
                  <ArrowUpRight className="h-5 w-5 text-primary-200" />
                </div>
              </div>
              <div className="mt-4 flex items-center gap-2">
                <span className="h-1.5 flex-1 rounded-full bg-primary-300" />
                <span className="h-1.5 w-10 rounded-full bg-primary-500/50" />
                <span className="h-1.5 w-6 rounded-full bg-border-default" />
              </div>
            </motion.div>

            <div className="absolute right-[5%] top-[12%] flex items-center gap-2 rounded-full border border-border-default/70 bg-bg-base/70 px-3 py-2 font-body text-xs text-text-secondary backdrop-blur-md">
              <span className="h-2 w-2 rounded-full bg-accent-300" />
              PRIVATE KNOWLEDGE
            </div>
          </div>
        </motion.section>
      </div>
    </div>
  );
}
