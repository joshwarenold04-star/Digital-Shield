/*
=============================================================================
Digital Shield – dashboard.js  |  SOS button logic & modal popups
=============================================================================
*/

document.addEventListener('DOMContentLoaded', () => {
  // Load location immediately
  LocationService.fetchAndDisplay();

  const womenBtn = document.getElementById('women-sos-btn');
  const pregBtn  = document.getElementById('preg-sos-btn');

  if (womenBtn) {
    womenBtn.addEventListener('click', () => triggerSOS('women'));
  }
  if (pregBtn) {
    pregBtn.addEventListener('click', () => triggerSOS('pregnancy'));
  }

  // Modal dismiss buttons
  const modalClose = document.getElementById('modal-close-btn');
  if (modalClose) {
    modalClose.addEventListener('click', hideAlertModal);
  }
  const modalOverlay = document.getElementById('modal-overlay');
  if (modalOverlay) {
    modalOverlay.addEventListener('click', (e) => {
      if (e.target === modalOverlay) hideAlertModal();
    });
  }
});

async function triggerSOS(type) {
  // Play emergency beep alarm immediately
  playEmergencySound(type);

  // Disable buttons & show progress
  setSOSButtonsState(true, type);

  // Get current position or fall back
  let position = LocationService.getPosition();
  if (!position) {
    position = await LocationService.fetchAndDisplay();
  }

  const payload = {
    latitude: position ? position.latitude : 0.0,
    longitude: position ? position.longitude : 0.0,
    address: position ? position.address : 'GPS coordinates not acquired'
  };

  const endpoint = type === 'women' ? '/api/sos/women' : '/api/sos/pregnancy';

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await response.json();

    if (result.success) {
      showAlertModal(type, result.message, result.notified);
      showToast(result.message, type === 'women' ? 'danger' : 'success');
      // Refresh page data or alerts list after short delay
      setTimeout(() => {
        // Option to reload or fetch updated mini-alert panel
      }, 3000);
    } else {
      showToast('SOS trigger failed. Please try again.', 'danger');
    }
  } catch (err) {
    console.error('SOS Error:', err);
    showToast('Network error triggering SOS.', 'danger');
  } finally {
    setSOSButtonsState(false, type);
  }
}

function setSOSButtonsState(disabled, type) {
  const womenBtn = document.getElementById('women-sos-btn');
  const pregBtn  = document.getElementById('preg-sos-btn');
  const womenLoader = document.getElementById('women-sos-loader');
  const pregLoader  = document.getElementById('preg-sos-loader');

  if (womenBtn) womenBtn.disabled = disabled;
  if (pregBtn) pregBtn.disabled = disabled;

  if (disabled) {
    if (type === 'women' && womenLoader) {
      womenLoader.classList.add('active');
      const progressBar = womenLoader.querySelector('.sos-progress-bar');
      if (progressBar) progressBar.style.width = '100%';
    } else if (type === 'pregnancy' && pregLoader) {
      pregLoader.classList.add('active');
      const progressBar = pregLoader.querySelector('.sos-progress-bar');
      if (progressBar) progressBar.style.width = '100%';
    }
  } else {
    // Reset loader classes and sizes
    if (womenLoader) {
      womenLoader.classList.remove('active');
      const bar = womenLoader.querySelector('.sos-progress-bar');
      if (bar) bar.style.width = '0%';
    }
    if (pregLoader) {
      pregLoader.classList.remove('active');
      const bar = pregLoader.querySelector('.sos-progress-bar');
      if (bar) bar.style.width = '0%';
    }
  }
}

function showAlertModal(type, message, notifiedContacts) {
  const overlay = document.getElementById('modal-overlay');
  const icon = document.getElementById('modal-icon');
  const title = document.getElementById('modal-title');
  const msg = document.getElementById('modal-message');
  const list = document.getElementById('modal-contacts-list');

  if (!overlay) return;

  if (type === 'women') {
    icon.textContent = '🚨';
    title.textContent = 'SOS Alert Sent';
    title.className = 'modal-title text-red';
  } else {
    icon.textContent = '🏥';
    title.textContent = 'Medical SOS Sent';
    title.className = 'modal-title text-green';
  }

  msg.textContent = message;

  if (list) {
    list.innerHTML = '';
    notifiedContacts.forEach(contact => {
      const span = document.createElement('span');
      span.className = type === 'women' ? 'badge badge-red' : 'badge badge-green';
      span.textContent = `🔔 ${contact}`;
      list.appendChild(span);
    });
  }

  overlay.classList.add('active');
}

function hideAlertModal() {
  const overlay = document.getElementById('modal-overlay');
  if (overlay) overlay.classList.remove('active');
  stopEmergencySound();
}
