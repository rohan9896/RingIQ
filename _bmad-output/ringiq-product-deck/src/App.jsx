import { useState, useEffect, useCallback } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import Navigation from './components/Navigation';
import Slide01 from './slides/01-hero';
import Slide02 from './slides/02-problem';
import Slide03 from './slides/03-solution';
import Slide04 from './slides/04-onboarding';
import Slide05 from './slides/05-knowledge';
import Slide06 from './slides/06-leads';
import Slide07 from './slides/07-campaigns';
import Slide08 from './slides/08-voice-ai';
import Slide09 from './slides/09-intelligence';
import Slide10 from './slides/10-platform';
import Slide11 from './slides/11-tech-stack';
import Slide12 from './slides/12-architecture';

const SLIDES = [
  Slide01,
  Slide02,
  Slide03,
  Slide04,
  Slide05,
  Slide06,
  Slide07,
  Slide08,
  Slide09,
  Slide10,
  Slide11,
  Slide12,
];

const NAV_ITEMS = [
  { slideIndex: 0, label: 'Vision' },
  { slideIndex: 1, label: 'Problem' },
  { slideIndex: 2, label: 'Solution' },
  { slideIndex: 3, label: 'Onboarding' },
  { slideIndex: 4, label: 'Knowledge' },
  { slideIndex: 5, label: 'Leads' },
  { slideIndex: 6, label: 'Campaigns' },
  { slideIndex: 7, label: 'Voice AI' },
  { slideIndex: 8, label: 'Intelligence' },
  { slideIndex: 9, label: 'Platform' },
  { slideIndex: 10, label: 'Tech Stack' },
  { slideIndex: 11, label: 'Architecture' },
];

// Slide transition variants
const slideVariants = {
  enter: (direction) => ({
    x: direction > 0 ? 300 : -300,
    opacity: 0,
    scale: 0.95
  }),
  center: {
    x: 0,
    opacity: 1,
    scale: 1
  },
  exit: (direction) => ({
    x: direction < 0 ? 300 : -300,
    opacity: 0,
    scale: 0.95
  })
};

const slideTransition = {
  type: 'spring',
  stiffness: 300,
  damping: 30
};

export default function App() {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [direction, setDirection] = useState(0);

  const goToSlide = useCallback((index) => {
    setDirection(index > currentSlide ? 1 : -1);
    setCurrentSlide(index);
  }, [currentSlide]);

  const nextSlide = useCallback(() => {
    if (currentSlide < SLIDES.length - 1) {
      setDirection(1);
      setCurrentSlide(prev => prev + 1);
    }
  }, [currentSlide]);

  const prevSlide = useCallback(() => {
    if (currentSlide > 0) {
      setDirection(-1);
      setCurrentSlide(prev => prev - 1);
    }
  }, [currentSlide]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === ' ') {
        e.preventDefault();
        nextSlide();
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault();
        prevSlide();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [nextSlide, prevSlide]);

  if (SLIDES.length === 0) {
    return (
      <div className="h-screen w-screen bg-bg-base flex items-center justify-center relative overflow-hidden">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center z-10"
        >
          <p className="text-xl mb-2 text-text-primary">No slides yet</p>
          <p className="text-sm text-text-muted">Slides will be generated here</p>
        </motion.div>
      </div>
    );
  }

  const CurrentSlideComponent = SLIDES[currentSlide];

  return (
    <div className="h-screen w-screen bg-bg-base overflow-hidden relative">
      <main className="relative h-full w-full z-10">
        <AnimatePresence initial={false} custom={direction} mode="wait">
          <motion.div
            key={currentSlide}
            custom={direction}
            variants={slideVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={slideTransition}
            className="absolute inset-0 h-full w-full"
          >
            <CurrentSlideComponent />
          </motion.div>
        </AnimatePresence>
      </main>

      <Navigation
        currentSlide={currentSlide}
        totalSlides={SLIDES.length}
        navItems={NAV_ITEMS}
        onPrev={prevSlide}
        onNext={nextSlide}
        onGoTo={goToSlide}
      />
    </div>
  );
}
