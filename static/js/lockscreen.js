/*
=============================================================================
Digital Shield – lockscreen.js  |  Lock Screen Simulation
=============================================================================
*/

document.addEventListener('DOMContentLoaded', () => {
  // Start clock in lockscreen
  startClock('ls-clock', 'ls-date');

  const powerBtn    = document.getElementById('ls-power-btn');
  const restartBtn  = document.getElementById('ls-restart-btn');
  const womenBtn    = document.getElementById('ls-women-btn');
  const pregBtn     = document.getElementById('ls-preg-btn');
  const powerMenu   = document.getElementById('power-menu');
  const cancelMenu  = document.getElementById('power-menu-cancel');

  // Popup items inside power menu
  const pmWomenSos = document.getElementById('pm-women-sos');
  const pmPregSos  = document.getElementById('pm-preg-sos');
  const pmPowerOff = document.getElementById('pm-power-off');
  const pmRestart  = document.getElementById('pm-restart');

  let pressTimer;

  // ── Long Press Logic for Power Button ─────────────────────────────────────
  if (powerBtn) {
    // Touch Events
    powerBtn.addEventListener('touchstart', (e) => {
      e.preventDefault();
      startPress();
    });
    powerBtn.addEventListener('touchend', endPress);
    powerBtn.addEventListener('touchcancel', endPress);

    // Mouse Events
    powerBtn.addEventListener('mousedown', startPress);
    powerBtn.addEventListener('mouseup', endPress);
    powerBtn.addEventListener('mouseleave', endPress);
  }

  function startPress() {
    powerBtn.style.transform = 'scale(0.95)';
    pressTimer = setTimeout(() => {
      openPowerMenu();
    }, 1000); // 1-second long-press triggers Android emergency popup
  }

  function endPress() {
    powerBtn.style.transform = '';
    clearTimeout(pressTimer);
  }

  // Open/Close power menu
  function openPowerMenu() {
    if (powerMenu) powerMenu.classList.add('open');
  }

  function closePowerMenu() {
    if (powerMenu) powerMenu.classList.remove('open');
  }

  if (cancelMenu) {
    cancelMenu.addEventListener('click', closePowerMenu);
  }
  if (powerMenu) {
    powerMenu.addEventListener('click', (e) => {
      if (e.target === powerMenu) closePowerMenu();
    });
  }

  // ── Restart Action ────────────────────────────────────────────────────────
  if (restartBtn) {
    restartBtn.addEventListener('click', () => {
      showToast('System Restarting...', 'warning');
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    });
  }

  // ── SOS triggers from Lock Screen ──────────────────────────────────────────
  if (womenBtn) {
    womenBtn.addEventListener('click', () => triggerLockscreenSOS('women'));
  }
  if (pregBtn) {
    pregBtn.addEventListener('click', () => triggerLockscreenSOS('pregnancy'));
  }

  // Power Menu Actions
  if (pmWomenSos) {
    pmWomenSos.addEventListener('click', () => {
      closePowerMenu();
      triggerLockscreenSOS('women');
    });
  }
  if (pmPregSos) {
    pmPregSos.addEventListener('click', () => {
      closePowerMenu();
      triggerLockscreenSOS('pregnancy');
    });
  }
  if (pmPowerOff) {
    pmPowerOff.addEventListener('click', () => {
      closePowerMenu();
      showToast('Shutting Down Screen Simulation...', 'danger');
      setTimeout(() => {
        window.location.href = '/';
      }, 1500);
    });
  }
  if (pmRestart) {
    pmRestart.addEventListener('click', () => {
      closePowerMenu();
      showToast('System Restarting...', 'warning');
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    });
  }
});

// Trigger SOS alerts directly from lock screen
async function triggerLockscreenSOS(type) {
  // Play emergency beep alarm immediately
  playEmergencySound(type);

  showToast(`Initiating Lock Screen SOS (${type.toUpperCase()})...`, 'warning');

  // Try to acquire position
  let lat = 0.0, lon = 0.0, address = 'Lock Screen GPS Location';
  try {
    const pos = await LocationService.getCurrentPosition();
    lat = pos.coords.latitude;
    lon = pos.coords.longitude;
    address = await LocationService.reverseGeocode(lat, lon);
  } catch (err) {
    console.warn('Geolocation failed on lock screen, sending default.', err);
  }

  const payload = { latitude: lat, longitude: lon, address: address };
  const endpoint = type === 'women' ? '/api/sos/women' : '/api/sos/pregnancy';

  try {
    // If not logged in, Flask backend API might block it (login_required).
    // For prototype lockscreen accessibility, let's see how the server responds.
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.status === 401 || res.redirected) {
      // Mock alert success for simulation if not logged in
      const mockNotified = type === 'women' ? ['Police', 'Family', 'Friends'] : ['Doctor', 'Ambulance', 'Hospital'];
      showLockscreenSOSSuccess(type, mockNotified);
    } else {
      const data = await res.json();
      if (data.success) {
        showLockscreenSOSSuccess(type, data.notified);
      } else {
        showToast('SOS trigger failed.', 'danger');
      }
    }
  } catch (err) {
    // Mock simulation on server failure
    const mockNotified = type === 'women' ? ['Police', 'Family', 'Friends'] : ['Doctor', 'Ambulance', 'Hospital'];
    showLockscreenSOSSuccess(type, mockNotified);
  }
}

function showLockscreenSOSSuccess(type, notified) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay active';
  overlay.style.zIndex = '4000';

  const modal = document.createElement('div');
  modal.className = 'modal';

  const icon  = type === 'women' ? '🚨' : '🏥';
  const title = type === 'women' ? 'SOS Women Emergency Alert' : 'SOS Pregnancy Emergency Request';
  const titleClass = type === 'women' ? 'modal-title text-red' : 'modal-title text-green';
  const desc  = type === 'women' 
    ? 'ALERT SENT SUCCESSFULLY! Help is arriving shortly. Your location details have been dispatched to:' 
    : 'MEDICAL ASSISTANCE REQUESTED! Ambulance and emergency units have been notified. Contacts pinged:';

  let badges = '';
  notified.forEach(c => {
    badges += `<span class="badge ${type === 'women' ? 'badge-red' : 'badge-green'}" style="margin: 0.25rem;">🔔 ${c}</span>`;
  });

  modal.innerHTML = `
    <div class="modal-icon">${icon}</div>
    <div class="${titleClass}">${title}</div>
    <div class="modal-msg" style="margin-top: 1rem;">${desc}</div>
    <div class="modal-contacts" style="margin-bottom: 2rem;">${badges}</div>
    <button class="btn btn-primary btn-block" onclick="stopEmergencySound(); this.closest('.modal-overlay').remove()">Dismiss</button>
  `;

  overlay.appendChild(modal);
  document.body.appendChild(overlay);
}
