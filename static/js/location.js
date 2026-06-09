/*
=============================================================================
Digital Shield – location.js  |  GPS Location Tracking
=============================================================================
Uses the browser Geolocation API + OpenStreetMap Nominatim reverse geocoding.
No API key required.
=============================================================================
*/

const LocationService = (() => {
  let currentPosition = null;
  let watchId = null;

  // ── Get current position (one-shot) ──────────────────────────────────────
  async function getCurrentPosition() {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation not supported by this browser.'));
        return;
      }
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 30000,
      });
    });
  }

  // ── Reverse geocode using OpenStreetMap Nominatim ─────────────────────────
  async function reverseGeocode(lat, lon) {
    try {
      const url = `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`;
      const res  = await fetch(url, {
        headers: { 'Accept-Language': 'en', 'User-Agent': 'DigitalShield/1.0' }
      });
      if (!res.ok) throw new Error('Geocode failed');
      const data = await res.json();
      return data.display_name || `${lat.toFixed(5)}, ${lon.toFixed(5)}`;
    } catch {
      return `${lat.toFixed(5)}, ${lon.toFixed(5)}`;
    }
  }

  // ── Fetch + update UI ─────────────────────────────────────────────────────
  async function fetchAndDisplay() {
    const locValue = document.getElementById('location-value');
    const locCoord = document.getElementById('location-coord');
    const mapFrame  = document.getElementById('map-frame');
    const mapHolder = document.getElementById('map-placeholder');

    if (locValue) locValue.textContent = 'Acquiring location…';

    try {
      const pos = await getCurrentPosition();
      const { latitude: lat, longitude: lon } = pos.coords;
      currentPosition = { latitude: lat, longitude: lon };

      // Reverse geocode for human-readable address
      const address = await reverseGeocode(lat, lon);
      currentPosition.address = address;

      if (locValue) locValue.textContent = address.length > 60
        ? address.substring(0, 57) + '…' : address;
      if (locCoord) locCoord.textContent = `${lat.toFixed(5)}, ${lon.toFixed(5)}`;

      // Embed OpenStreetMap
      if (mapFrame) {
        mapFrame.src = `https://maps.google.com/maps?q=${lat},${lon}&z=15&output=embed`;
        mapFrame.style.display = 'block';
        if (mapHolder) mapHolder.style.display = 'none';
      }

      return currentPosition;
    } catch (err) {
      const msg = err.code === 1
        ? 'Location access denied. Please enable GPS.'
        : 'Unable to retrieve location.';
      if (locValue) locValue.textContent = msg;
      showToast(msg, 'warning');
      return null;
    }
  }

  // ── Start live watch ──────────────────────────────────────────────────────
  function startWatch(callback) {
    if (!navigator.geolocation || watchId !== null) return;
    watchId = navigator.geolocation.watchPosition(
      (pos) => {
        const { latitude: lat, longitude: lon } = pos.coords;
        currentPosition = { latitude: lat, longitude: lon };
        if (callback) callback(lat, lon);
      },
      () => {},
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 10000 }
    );
  }

  function stopWatch() {
    if (watchId !== null) {
      navigator.geolocation.clearWatch(watchId);
      watchId = null;
    }
  }

  function getPosition() { return currentPosition; }

  return { fetchAndDisplay, getCurrentPosition, reverseGeocode, startWatch, stopWatch, getPosition };
})();
