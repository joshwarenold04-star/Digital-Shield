/*
=============================================================================
Digital Shield – main.js  |  Shared Utilities
=============================================================================
*/

// ── Theme (Dark/Light) Toggle ─────────────────────────────────────────────
const savedTheme = localStorage.getItem('ds-theme') || 'dark';
document.documentElement.setAttribute('data-theme', savedTheme);

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('ds-theme', next);
  document.querySelectorAll('.theme-toggle').forEach(btn => {
    btn.classList.toggle('light', next === 'light');
    btn.title = next === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode';
  });
}

// ── Mobile Nav Toggle ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Apply saved theme to toggle buttons
  document.querySelectorAll('.theme-toggle').forEach(btn => {
    btn.classList.toggle('light', savedTheme === 'light');
    btn.addEventListener('click', toggleTheme);
  });

  // Hamburger nav
  const navToggle = document.getElementById('nav-toggle');
  const navLinks  = document.getElementById('nav-links');
  if (navToggle && navLinks) {
    navToggle.addEventListener('click', () => {
      navLinks.classList.toggle('open');
      navToggle.textContent = navLinks.classList.contains('open') ? '✕' : '☰';
    });
    // Close on outside click
    document.addEventListener('click', (e) => {
      if (!navToggle.contains(e.target) && !navLinks.contains(e.target)) {
        navLinks.classList.remove('open');
        navToggle.textContent = '☰';
      }
    });
  }

  // Auto-dismiss flash messages
  document.querySelectorAll('.alert[data-auto-dismiss]').forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.4s';
      alert.style.opacity = '0';
      setTimeout(() => alert.remove(), 400);
    }, 4500);
  });

  // Active nav link highlighting
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-links a').forEach(link => {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });

  // Inject hidden YouTube player container into the page
  injectYouTubePlayer();
});

// ── Clock (live) ──────────────────────────────────────────────────────────
function updateClock(el, dateEl) {
  const now  = new Date();
  const time = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false });
  const date = now.toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' });
  if (el)   el.textContent   = time;
  if (dateEl) dateEl.textContent = date;
}

function startClock(timeId, dateId) {
  const tEl = document.getElementById(timeId);
  const dEl = document.getElementById(dateId);
  updateClock(tEl, dEl);
  setInterval(() => updateClock(tEl, dEl), 1000);
}

// ── Toast notification ─────────────────────────────────────────────────────
function showToast(msg, type = 'info', duration = 4000) {
  const colors = { success: '#00e676', danger: '#ff6e7a', warning: '#ffc107', info: '#64b5f6' };
  const icons = { success: '✅', danger: '🚨', warning: '⚠️', info: 'ℹ️' };
  const toast = document.createElement('div');
  toast.style.cssText = `
    position:fixed; bottom:1.5rem; right:1.5rem; z-index:9999;
    background:rgba(10,25,47,0.97); border:1px solid ${colors[type]};
    color:${colors[type]}; padding:0.9rem 1.4rem;
    border-radius:14px; font-family:Inter,sans-serif; font-size:0.88rem;
    font-weight:500; box-shadow:0 10px 40px rgba(0,0,0,0.4);
    display:flex; align-items:center; gap:0.6rem;
    transform:translateY(80px); opacity:0;
    transition:all 0.35s cubic-bezier(0.34,1.56,0.64,1);
    max-width:320px; backdrop-filter:blur(15px);
  `;
  toast.innerHTML = `<span>${icons[type]}</span><span>${msg}</span>`;
  document.body.appendChild(toast);
  requestAnimationFrame(() => {
    toast.style.transform = 'translateY(0)';
    toast.style.opacity   = '1';
  });
  setTimeout(() => {
    toast.style.transform = 'translateY(80px)';
    toast.style.opacity   = '0';
    setTimeout(() => toast.remove(), 400);
  }, duration);
}

// ── Format date helper ────────────────────────────────────────────────────
function formatDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', hour12: true });
}

// ── YouTube IFrame Emergency Sound ────────────────────────────────────────
let ytPlayer = null;
let ytPlayerReady = false;
// Video IDs for each SOS type
const YT_VIDEO_IDS = {
  women: 'bOjTNcqt-kM',            // Women emergency tone
  pregnancy: 'bqiBG33CPts'          // Pregnancy emergency tone (updated per user request)
};

function injectYouTubePlayer() {
  const container = document.createElement('div');
  container.id = 'yt-emergency-player';
  container.style.cssText = 'position:fixed;bottom:-9999px;left:-9999px;width:1px;height:1px;overflow:hidden;';
  document.body.appendChild(container);
  if (!document.getElementById('yt-iframe-api-script')) {
    const script = document.createElement('script');
    script.id  = 'yt-iframe-api-script';
    script.src = 'https://www.youtube.com/iframe_api';
    document.head.appendChild(script);
  }
}

function onYouTubeIframeAPIReady() {
  ytPlayer = new YT.Player('yt-emergency-player', {
    height: '1',
    width: '1',
    videoId: YT_VIDEO_IDS.women, // default – will be changed on demand
    playerVars: {
      autoplay: 0,
      mute: 0,
      controls: 0,
      disablekb: 1,
      modestbranding: 1,
      rel: 0,
      loop: 1,
      playlist: YT_VIDEO_IDS.women
    },
    events: {
      onReady: (event) => {
        ytPlayerReady = true;
        event.target.setVolume(100);
      }
    }
  });
}

function playEmergencySound(type = 'women') {
  if (!YT_VIDEO_IDS[type]) {
    console.warn('No YouTube video defined for SOS type:', type);
    playFallbackBeep(type);
    return;
  }
  const videoId = YT_VIDEO_IDS[type];
  if (ytPlayer && ytPlayerReady) {
    // Load the correct video (if not already) and play from start
    ytPlayer.loadVideoById({
      videoId: videoId,
      startSeconds: 0,
      suggestedQuality: 'highres'
    });
    ytPlayer.setVolume(100);
    ytPlayer.playVideo();
  } else {
    // Player not ready yet – fallback to beep
    playFallbackBeep(type);
  }
}

function stopEmergencySound() {
  if (ytPlayer && ytPlayerReady) {
    try { ytPlayer.stopVideo(); } catch(e) {}
  }
  stopFallbackBeep();
}

// ── Fallback Web Audio Beep (used if YouTube player is not ready) ─────────
let audioCtx = null;
let melodyTimeoutId = null;
let activeAlarmSources = [];
const NOTE_FREQS = { 'G4': 392.00, 'A#4': 466.16, 'C5': 523.25, 'D5': 587.33, 'D#5': 622.25 };
const MELODY = [
  { note: 'C5',  dur: 0.35 }, { note: 'D5',  dur: 0.35 },
  { note: 'D#5', dur: 0.35 }, { note: 'D5',  dur: 0.35 },
  { note: 'C5',  dur: 0.35 }, { note: 'D5',  dur: 0.35 },
  { note: 'A#4', dur: 0.35 }, { note: 'G4',  dur: 0.35 },
  { note: 'D5',  dur: 0.70 }, { note: null,  dur: 0.15 },
  { note: 'C5',  dur: 0.35 }, { note: 'D5',  dur: 0.35 },
  { note: 'D#5', dur: 0.35 }, { note: 'D5',  dur: 0.35 },
  { note: 'C5',  dur: 0.35 }, { note: 'D5',  dur: 0.35 },
  { note: 'A#4', dur: 0.35 }, { note: 'G4',  dur: 0.35 },
  { note: 'D5',  dur: 0.50 }, { note: 'C5',  dur: 0.70 },
  { note: null,  dur: 0.80 }
];

function playFallbackBeep(type = 'women') {
  stopFallbackBeep();
  try {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const compressor = audioCtx.createDynamicsCompressor();
    compressor.threshold.setValueAtTime(-10, audioCtx.currentTime);
    compressor.ratio.setValueAtTime(12, audioCtx.currentTime);
    compressor.connect(audioCtx.destination);
    const waveType  = (type === 'women') ? 'sawtooth' : 'triangle';
    const gainLevel = 0.9;
    function playMelodyLoop() {
      if (!audioCtx || audioCtx.state === 'closed') return;
      let startTime = audioCtx.currentTime + 0.01;
      MELODY.forEach(step => {
        if (step.note && audioCtx) {
          const freq = NOTE_FREQS[step.note];
          const osc  = audioCtx.createOscillator();
          const gain = audioCtx.createGain();
          osc.connect(gain);
          gain.connect(compressor);
          osc.type = waveType;
          osc.frequency.setValueAtTime(freq, startTime);
          const decayEnd = Math.max(startTime + 0.01, startTime + step.dur - 0.04);
          gain.gain.setValueAtTime(0.001, startTime);
          gain.gain.linearRampToValueAtTime(gainLevel, startTime + 0.03);
          gain.gain.exponentialRampToValueAtTime(0.001, decayEnd);
          osc.start(startTime);
          osc.stop(startTime + step.dur);
          activeAlarmSources.push(osc);
        }
        startTime += step.dur;
      });
      const totalDuration = MELODY.reduce((acc, step) => acc + step.dur, 0);
      melodyTimeoutId = setTimeout(playMelodyLoop, (totalDuration - 0.05) * 1000);
    }
    playMelodyLoop();
  } catch (err) {
    console.warn('Web Audio API error:', err);
  }
}

function stopFallbackBeep() {
  if (melodyTimeoutId) { clearTimeout(melodyTimeoutId); melodyTimeoutId = null; }
  activeAlarmSources.forEach(src => { try { src.stop(); } catch(e) {} });
  activeAlarmSources = [];
  if (audioCtx && audioCtx.state !== 'closed') { try { audioCtx.close(); } catch(e) {} audioCtx = null; }
}
