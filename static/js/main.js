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
  const colors = {
    success: '#00e676', danger: '#ff6e7a',
    warning: '#ffc107', info:   '#64b5f6'
  };
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
  return d.toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit', hour12: true
  });
}

// ── Web Audio Emergency Alarm ─────────────────────────────────────────────
let activeAlarmSources = [];
let audioCtx = null;
let melodyTimeoutId = null;

// Note frequency map for "Ennai Vittu Uyir Ponaalum" (Love Today)
const NOTE_FREQS = {
  'G4': 392.00,
  'A#4': 466.16,
  'C5': 523.25,
  'D5': 587.33,
  'D#5': 622.25
};

// Main melody notes & durations (in seconds)
const MELODY = [
  { note: 'C5', dur: 0.35 },
  { note: 'D5', dur: 0.35 },
  { note: 'D#5', dur: 0.35 },
  { note: 'D5', dur: 0.35 },
  { note: 'C5', dur: 0.35 },
  { note: 'D5', dur: 0.35 },
  { note: 'A#4', dur: 0.35 },
  { note: 'G4', dur: 0.35 },
  { note: 'D5', dur: 0.70 },
  
  { note: null, dur: 0.15 }, // pause
  
  { note: 'C5', dur: 0.35 },
  { note: 'D5', dur: 0.35 },
  { note: 'D#5', dur: 0.35 },
  { note: 'D5', dur: 0.35 },
  { note: 'C5', dur: 0.35 },
  { note: 'D5', dur: 0.35 },
  { note: 'A#4', dur: 0.35 },
  { note: 'G4', dur: 0.35 },
  { note: 'D5', dur: 0.50 },
  { note: 'C5', dur: 0.70 },
  
  { note: null, dur: 0.80 } // delay before repeating loop
];

function playEmergencySound(type = 'women') {
  stopEmergencySound(); // Reset any playing audio loop first

  try {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();

    // Resume audioCtx – required by Chrome/Edge autoplay policy
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }

    // Dynamics compressor prevents clipping & distortion at max volume
    const compressor = audioCtx.createDynamicsCompressor();
    compressor.threshold.setValueAtTime(-10, audioCtx.currentTime);
    compressor.knee.setValueAtTime(10, audioCtx.currentTime);
    compressor.ratio.setValueAtTime(12, audioCtx.currentTime);
    compressor.attack.setValueAtTime(0, audioCtx.currentTime);
    compressor.release.setValueAtTime(0.25, audioCtx.currentTime);
    compressor.connect(audioCtx.destination);

    // Sawtooth = loud buzzy danger; Triangle = clean medical tone
    const waveType   = (type === 'women') ? 'sawtooth' : 'triangle';
    const gainLevel  = 0.9; // safe max — no clipping/distortion

    function playMelodyLoop() {
      if (!audioCtx || audioCtx.state === 'closed') return;

      let startTime = audioCtx.currentTime + 0.01; // tiny offset avoids timing edge cases

      MELODY.forEach(step => {
        if (step.note && audioCtx) {
          const freq   = NOTE_FREQS[step.note];
          const osc    = audioCtx.createOscillator();
          const gain   = audioCtx.createGain();

          osc.connect(gain);
          gain.connect(compressor);

          osc.type = waveType;
          osc.frequency.setValueAtTime(freq, startTime);

          // Smooth attack/release envelope (no clicks or pops)
          const decayEnd = Math.max(startTime + 0.01, startTime + step.dur - 0.04);
          gain.gain.setValueAtTime(0.001, startTime);                     // avoid click on start
          gain.gain.linearRampToValueAtTime(gainLevel, startTime + 0.03); // attack 30ms
          gain.gain.exponentialRampToValueAtTime(0.001, decayEnd);        // decay to silence

          osc.start(startTime);
          osc.stop(startTime + step.dur);

          activeAlarmSources.push(osc);
        }
        startTime += step.dur;
      });

      // Calculate total loop duration and schedule next repeat
      const totalDuration = MELODY.reduce((acc, step) => acc + step.dur, 0);
      melodyTimeoutId = setTimeout(playMelodyLoop, (totalDuration - 0.05) * 1000);
    }

    // Kick off infinite loop
    playMelodyLoop();

  } catch (err) {
    console.warn('Web Audio API error:', err);
  }
}

function stopEmergencySound() {
  if (melodyTimeoutId) {
    clearTimeout(melodyTimeoutId);
    melodyTimeoutId = null;
  }
  // Stop all scheduled oscillators
  activeAlarmSources.forEach(src => {
    try { src.stop(); } catch(e) {}
  });
  activeAlarmSources = [];
  
  if (audioCtx && audioCtx.state !== 'closed') {
    try { audioCtx.close(); } catch(e) {}
    audioCtx = null;
  }
}



