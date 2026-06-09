/*
=============================================================================
Digital Shield – operator_console.js  |  Operator Console Logic
=============================================================================
*/

let allAlerts = [];
let selectedAlertId = null;
let selectedAlertType = null;
let lastKnownAlertTime = null;
let pollIntervalId = null;
let alertedIds = new Set(); // Store alert IDs that we have already alerted/played sound for

document.addEventListener('DOMContentLoaded', () => {
  // Initial load
  loadConsoleData();
  
  // Start polling every 5 seconds
  pollIntervalId = setInterval(loadConsoleData, 5000);
});

async function loadConsoleData() {
  await fetchStats();
  await fetchAlerts();
}

async function fetchStats() {
  try {
    const res = await fetch('/api/admin/stats');
    if (!res.ok) return;
    const stats = await res.json();
    
    // Update stats bar
    const usersEl = document.getElementById('stat-users');
    const womenEl = document.getElementById('stat-women');
    const pregEl  = document.getElementById('stat-preg');
    const contactsEl = document.getElementById('stat-contacts');
    
    if (usersEl) usersEl.textContent = stats.total_users;
    if (womenEl) womenEl.textContent = stats.total_women_alerts;
    if (pregEl) pregEl.textContent = stats.total_pregnancy_alerts;
    if (contactsEl) contactsEl.textContent = stats.total_contacts;
  } catch (err) {
    console.error('Error fetching stats:', err);
  }
}

async function fetchAlerts() {
  try {
    const res = await fetch('/api/operator/alerts');
    if (!res.ok) return;
    const alerts = await res.json();
    
    // Save previous alerts count to detect new dispatches
    const hadAlerts = allAlerts.length > 0;
    allAlerts = alerts;
    
    renderAlertFeed();
    checkNewEmergencyAlerts(hadAlerts);
  } catch (err) {
    console.error('Error fetching alerts:', err);
  }
}

function renderAlertFeed() {
  const feed = document.getElementById('incident-feed');
  if (!feed) return;
  
  if (allAlerts.length === 0) {
    feed.innerHTML = `
      <div style="padding: 3rem; text-align: center;" class="text-muted">
        No emergency dispatches logged.
      </div>
    `;
    return;
  }
  
  feed.innerHTML = '';
  
  allAlerts.forEach(alert => {
    const isSelected = selectedAlertId === alert.id && selectedAlertType === alert.type;
    const isWomen = alert.type.toLowerCase().includes('women');
    const isActive = alert.status === 'sent';
    
    let animClass = '';
    if (isActive) {
      animClass = isWomen ? 'pulse-red' : 'pulse-green';
    }
    
    const card = document.createElement('div');
    card.className = `incident-card ${isSelected ? 'selected' : ''} ${animClass}`;
    card.onclick = () => selectIncident(alert.id, alert.type);
    
    const badgeClass = isWomen ? 'badge-red' : 'badge-green';
    const typeLabel = isWomen ? '🔴 Women SOS' : '🏥 Pregnancy';
    
    const dateStr = formatDate(alert.created_at);
    
    card.innerHTML = `
      <div class="card-top">
        <span class="badge ${badgeClass}">${typeLabel}</span>
        <span class="badge badge-status-${alert.status}">${alert.status.toUpperCase()}</span>
      </div>
      <div class="victim-name">${alert.full_name}</div>
      <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.2rem;">${alert.mobile}</div>
      <div class="incident-address" title="${alert.address}">${alert.address}</div>
      <div style="font-size: 0.75rem; text-align: right; color: var(--text-muted); margin-top: 0.5rem;">${dateStr}</div>
    `;
    
    feed.appendChild(card);
  });
}

function checkNewEmergencyAlerts(hadAlerts) {
  // Check if there's any active alert with status 'sent'
  const activeAlerts = allAlerts.filter(a => a.status === 'sent');
  
  const indicator = document.getElementById('active-incident-badge');
  if (indicator) {
    indicator.style.display = activeAlerts.length > 0 ? 'inline-flex' : 'none';
  }
  
  if (activeAlerts.length === 0) {
    stopEmergencySound();
    return;
  }
  
  // Find if there is a new alert we haven't seen yet
  let hasNewSentAlert = false;
  let newestType = 'women';
  
  activeAlerts.forEach(alert => {
    const alertKey = `${alert.type}_${alert.id}`;
    if (!alertedIds.has(alertKey)) {
      hasNewSentAlert = true;
      newestType = alert.type.toLowerCase().includes('women') ? 'women' : 'pregnancy';
      alertedIds.add(alertKey);
    }
  });
  
  if (hasNewSentAlert) {
    // Show toast for new alert
    showToast(`NEW EMERGENCY SIGNAL RECEIVED!`, 'danger', 6000);
    
    // Play sound loop if not muted in browser options
    const isSirenMuted = localStorage.getItem('operator-siren-muted') === 'true';
    if (!isSirenMuted) {
      playEmergencySound(newestType);
    }
  }
}

async function selectIncident(id, type) {
  selectedAlertId = id;
  selectedAlertType = type;
  
  // Re-render feed to show selected highlight
  renderAlertFeed();
  
  const alert = allAlerts.find(a => a.id === id && a.type === type);
  if (!alert) return;
  
  // Hide empty state and show details view
  document.getElementById('empty-details-view').style.display = 'none';
  const details = document.getElementById('incident-details-view');
  details.style.display = 'block';
  
  // Update details DOM
  const isWomen = type.toLowerCase().includes('women');
  const typeEl = document.getElementById('detail-type');
  typeEl.textContent = isWomen ? 'Women Emergency SOS' : 'Pregnancy Emergency SOS';
  typeEl.className = isWomen ? 'text-red h3' : 'text-green h3';
  
  document.getElementById('detail-time').textContent = `Reported: ${formatDate(alert.created_at)}`;
  
  const statusBadge = document.getElementById('detail-status-badge');
  statusBadge.textContent = alert.status.toUpperCase();
  statusBadge.className = `badge badge-status-${alert.status}`;
  
  document.getElementById('detail-name').textContent = alert.full_name;
  
  const phoneLink = document.getElementById('detail-phone-link');
  phoneLink.textContent = alert.mobile;
  phoneLink.href = `tel:${alert.mobile}`;
  
  const bloodBadge = document.getElementById('detail-blood');
  if (alert.blood_group) {
    bloodBadge.textContent = alert.blood_group;
    bloodBadge.style.display = 'inline-flex';
  } else {
    bloodBadge.style.display = 'none';
  }
  
  document.getElementById('detail-home-address').textContent = alert.home_address || 'No registered home address';
  document.getElementById('detail-sos-address').textContent = alert.address;
  document.getElementById('detail-coords').textContent = `${alert.latitude}, ${alert.longitude}`;
  
  // Set status select dropdown value
  document.getElementById('dispatch-status-select').value = alert.status;
  
  // Update map iframe
  const mapFrame = document.getElementById('incident-map');
  if (alert.latitude && alert.longitude) {
    mapFrame.src = `https://maps.google.com/maps?q=${alert.latitude},${alert.longitude}&z=15&output=embed`;
    mapFrame.style.display = 'block';
  } else {
    mapFrame.style.display = 'none';
  }
  
  // Fetch victim's emergency contacts list
  const contactsList = document.getElementById('detail-contacts-list');
  contactsList.innerHTML = '<span class="text-muted" style="font-size:0.8rem;">Loading contacts...</span>';
  
  try {
    const res = await fetch(`/api/operator/contacts/${alert.user_id}`);
    if (res.ok) {
      const contacts = await res.json();
      contactsList.innerHTML = '';
      if (contacts.length === 0) {
        contactsList.innerHTML = '<span class="text-muted" style="font-size:0.8rem;">No emergency contacts configured for this user.</span>';
      } else {
        contacts.forEach(c => {
          const item = document.createElement('div');
          item.className = 'contact-item';
          item.innerHTML = `
            <div>
              <div style="font-weight:600; font-size:0.85rem;">${c.name} (${c.relation})</div>
              <div style="font-size:0.75rem; color:var(--text-secondary);">${c.phone}</div>
            </div>
            <a href="tel:${c.phone}" class="btn btn-outline btn-sm" style="padding:0.2rem 0.5rem; font-size:0.7rem;">📞 Call</a>
          `;
          contactsList.appendChild(item);
        });
      }
    } else {
      contactsList.innerHTML = '<span class="text-red" style="font-size:0.8rem;">Error loading contacts.</span>';
    }
  } catch (err) {
    console.error(err);
    contactsList.innerHTML = '<span class="text-red" style="font-size:0.8rem;">Error loading contacts.</span>';
  }
}

async function updateIncidentStatus() {
  if (!selectedAlertId || !selectedAlertType) return;
  
  const status = document.getElementById('dispatch-status-select').value;
  const shortType = selectedAlertType.toLowerCase().includes('women') ? 'women' : 'pregnancy';
  
  try {
    const res = await fetch(`/api/operator/change_status/${shortType}/${selectedAlertId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: status })
    });
    
    const data = await res.json();
    if (data.success) {
      showToast('Alert status updated successfully.', 'success');
      
      // Stop the siren if this was the active alert and we resolved it
      if (status !== 'sent') {
        const alertKey = `${selectedAlertType}_${selectedAlertId}`;
        // If it was the only alert causing the sound, stop the alarm sound
        const remainingActive = allAlerts.filter(a => a.status === 'sent' && !(`${a.type}_${a.id}` === alertKey));
        if (remainingActive.length === 0) {
          stopEmergencySound();
        }
      }
      
      // Refresh console to pull latest data
      await loadConsoleData();
      
      // Re-select same incident to update status badges
      selectIncident(selectedAlertId, selectedAlertType);
    } else {
      showToast('Failed to update status.', 'danger');
    }
  } catch (err) {
    console.error(err);
    showToast('Network error updating status.', 'danger');
  }
}
