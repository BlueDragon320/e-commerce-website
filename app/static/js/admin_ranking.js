/**
 * admin_ranking.js — Admin Panel Ranking Engine Controller
 * Manages iframe embedding navigation, live engine health polling,
 * and API-driven weight simulation.
 */

document.addEventListener('DOMContentLoaded', () => {
  initIframeToolbar();
  initEngineHealthCheck();
  initRankingSimulator();
});

function initIframeToolbar() {
  const iframe = document.getElementById('engineIframe');
  const addressBar = document.getElementById('browserAddress');
  const tabs = document.querySelectorAll('.engine-nav-tab');

  if (!iframe || !addressBar) return;

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const targetUrl = tab.getAttribute('data-url');
      iframe.src = targetUrl;
      addressBar.textContent = targetUrl;
    });
  });
}

function initEngineHealthCheck() {
  const statusPill = document.getElementById('engineStatusPill');
  const statusText = document.getElementById('engineStatusText');
  const latencyText = document.getElementById('engineLatencyText');

  const checkStatus = async () => {
    try {
      const res = await fetch('/admin/api/engine-status');
      const data = await res.json();
      if (data.status === 'online') {
        if (statusPill) statusPill.className = 'engine-status-pill';
        if (statusText) statusText.textContent = `Online (${data.company_name})`;
        if (latencyText) latencyText.textContent = `${data.latency_ms}ms latency`;
      } else {
        if (statusPill) statusPill.className = 'engine-status-pill offline';
        if (statusText) statusText.textContent = 'Engine Offline (Fallback Active)';
        if (latencyText) latencyText.textContent = 'Offline';
      }
    } catch (e) {
      if (statusPill) statusPill.className = 'engine-status-pill offline';
      if (statusText) statusText.textContent = 'Engine Connection Failed';
    }
  };

  checkStatus();
}

function initRankingSimulator() {
  const simBtn = document.getElementById('runSimulatorBtn');
  const simQueryInput = document.getElementById('simQuery');
  const simResultsBox = document.getElementById('simResultsJson');

  if (!simBtn || !simQueryInput || !simResultsBox) return;

  simBtn.addEventListener('click', async () => {
    const q = simQueryInput.value.trim();
    simBtn.disabled = true;
    simBtn.textContent = 'Querying Engine...';
    try {
      const res = await fetch(`/api/smart-rank?q=${encodeURIComponent(q)}`);
      const data = await res.json();
      simResultsBox.textContent = JSON.stringify(data, null, 2);
    } catch (err) {
      simResultsBox.textContent = `Error querying ranking engine: ${err.message}`;
    } finally {
      simBtn.disabled = false;
      simBtn.textContent = 'Run Test Query';
    }
  });
}
