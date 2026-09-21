import React, { useRef, useState, useEffect } from 'react';
import { Maximize2, Minimize2 } from 'lucide-react';
import teamFilmstripHtml from './teamFilmstripHtml.js';
import '@designcodeio/threeui/style.css';

function processFilmstrip(html) {
  return html
    .replaceAll("performance.now()", "window.__CHARACTER_CAROUSEL_NOW()")
    .replace(/<script[^>]+cloudflareinsights\.com[^>]*><\/script>/gi, "")
    .replace("</head>", `<style data-character-carousel-focus>
:root { --character-carousel-scale: 1; }
html, body, .stage { width: 100%; height: 100%; margin: 0; overflow: hidden; }
.stage { min-height: 0 !important; }
.deck { transform: scale(var(--character-carousel-scale)); transform-origin: 50% 50%; }
</style><script data-character-carousel-controls>
(function () {
  var nativeFrame = window.requestAnimationFrame.bind(window);
  var clock = { real: null, virtual: null };
  var controls = window.__CHARACTER_CAROUSEL_CONTROLS = { speed: 1, scale: 1, paused: false };
  window.__CHARACTER_CAROUSEL_NOW = function () {
    return clock.virtual === null ? performance.now() : clock.virtual;
  };
  window.requestAnimationFrame = function (callback) {
    function tick(realTime) {
      if (clock.real === null) {
        clock.real = realTime;
        clock.virtual = realTime;
      } else {
        if (!controls.paused) clock.virtual += (realTime - clock.real) * controls.speed;
        clock.real = realTime;
      }
      if (controls.paused) {
        return nativeFrame(tick);
      }
      callback(clock.virtual);
    }
    return nativeFrame(tick);
  };
  window.addEventListener('message', function (event) {
    if (!event.data || event.data.type !== 'character-carousel-controls') return;
    var next = event.data.controls || {};
    if (Number.isFinite(next.speed)) controls.speed = Math.max(0, Math.min(2.5, next.speed));
    if (Number.isFinite(next.scale)) controls.scale = Math.max(0.7, Math.min(1.3, next.scale));
    controls.paused = Boolean(next.paused);
    document.documentElement.style.setProperty('--character-carousel-scale', String(controls.scale));
  });
})();
</script></head>`);
}

const PROCESSED_HTML = processFilmstrip(teamFilmstripHtml);

export function Scene({ activeIndex, iframeRef: externalRef, isFullscreen = false } = {}) {
  const localRef = useRef(null);
  const iframeRef = externalRef || localRef;

  useEffect(() => {
    const postControls = () => {
      iframeRef.current?.contentWindow?.postMessage({
        type: 'character-carousel-controls',
        controls: { speed: 1, scale: isFullscreen ? 1.12 : 1, paused: false }
      }, '*');
    };
    postControls();
  }, [iframeRef, isFullscreen]);

  useEffect(() => {
    if (typeof activeIndex === 'number') {
      iframeRef.current?.contentWindow?.postMessage({
        type: 'focus-card',
        index: activeIndex
      }, '*');
    }
  }, [activeIndex, iframeRef]);

  return (
    <div
      className={`shader-frame w-full rounded-2xl overflow-hidden shadow-2xl relative border border-white/15 bg-[#d8c9ad] transition-all duration-300 ${
        isFullscreen ? 'h-full flex-1 min-h-[500px]' : 'h-[460px] sm:h-[520px]'
      }`}
    >
      <iframe
        ref={iframeRef}
        title="The Minds Behind SatyaDhVani - Team Prime Vector 3D Filmstrip"
        srcDoc={PROCESSED_HTML}
        sandbox="allow-scripts"
        className="w-full h-full border-0 block"
        style={{
          width: '100%',
          height: '100%',
          border: 0,
          background: '#d8c9ad',
          pointerEvents: 'auto'
        }}
      />
    </div>
  );
}

export default function TeamSection() {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const sectionRef = useRef(null);

  const toggleFullscreen = async () => {
    try {
      if (!document.fullscreenElement && !isFullscreen) {
        if (sectionRef.current?.requestFullscreen) {
          await sectionRef.current.requestFullscreen();
        } else {
          setIsFullscreen(true);
        }
      } else {
        if (document.fullscreenElement && document.exitFullscreen) {
          await document.exitFullscreen();
        } else {
          setIsFullscreen(false);
        }
      }
    } catch (err) {
      setIsFullscreen((prev) => !prev);
    }
  };

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(Boolean(document.fullscreenElement));
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  return (
    <section
      ref={sectionRef}
      className={`bg-forest text-white spade-cut-md relative overflow-hidden shadow-spade-lg border border-forest/20 transition-all duration-300 ${
        isFullscreen
          ? 'fixed inset-0 z-[9999] rounded-none p-6 sm:p-10 flex flex-col justify-between h-screen w-screen'
          : 'rounded-2xl p-6 sm:p-10 space-y-6'
      }`}
    >
      {/* Background Decorative Grid */}
      <div className="absolute inset-0 bg-grid-spade opacity-10 pointer-events-none" />

      {/* Header: Title, Team Subtitle, and Fullscreen Button */}
      <div className="relative z-10 flex items-center justify-between border-b border-white/10 pb-5">
        <div className="space-y-1 text-left">
          <h2 className="font-display text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            The Minds Behind SatyaDhVani
          </h2>
          <p className="text-lemongrass font-mono text-sm sm:text-base font-semibold tracking-wider uppercase">
            Team Prime Vector
          </p>
        </div>

        <button
          type="button"
          onClick={toggleFullscreen}
          aria-label={isFullscreen ? "Exit full screen" : "View section in full screen"}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white/10 hover:bg-white/20 active:scale-95 border border-white/15 text-lemongrass font-mono text-xs font-bold transition-all shadow-sm cursor-pointer shrink-0"
          title={isFullscreen ? "Exit full screen" : "View section in full screen"}
        >
          {isFullscreen ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
          <span className="hidden sm:inline">{isFullscreen ? "Exit Fullscreen" : "Fullscreen"}</span>
        </button>
      </div>

      {/* 3D Character Carousel Scene (Only 6 Cards arranged 01 to 06) */}
      <div className={`relative z-10 ${isFullscreen ? 'flex-1 h-full min-h-0 pt-4' : ''}`}>
        <Scene isFullscreen={isFullscreen} />
      </div>
    </section>
  );
}
