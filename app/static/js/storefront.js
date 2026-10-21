/**
 * storefront.js — Interactive Client Behavior for Noise Storefront
 * Handles: Recommendation Tuner drawer, Dynamic Weight Sliders,
 * Presets, and Smart Ranking AJAX calls.
 */

document.addEventListener('DOMContentLoaded', () => {
  initRecommendationTuner();
  initCartFeedback();
});

function initRecommendationTuner() {
  const modal = document.getElementById('tunerModal');
  const openBtns = document.querySelectorAll('.open-tuner-btn');
  const closeBtn = document.getElementById('closeTunerBtn');
  const cancelBtn = document.getElementById('cancelTunerBtn');
  const applyBtn = document.getElementById('applyTunerBtn');

  if (!modal) return;

  // Open modal
  openBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      modal.classList.add('active');
    });
  });

  // Close modal
  const closeModal = () => modal.classList.remove('active');
  if (closeBtn) closeBtn.addEventListener('click', closeModal);
  if (cancelBtn) cancelBtn.addEventListener('click', closeModal);

  // Close when clicking backdrop
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
  });

  // Sliders and sum calculation
  const sliders = document.querySelectorAll('.weight-range-input');
  const sumValEl = document.getElementById('totalWeightVal');
  const sumBoxEl = document.getElementById('weightSumBox');

  const updateWeights = () => {
    let sum = 0;
    sliders.forEach(s => {
      const val = parseFloat(s.value) || 0;
      const display = document.getElementById(`val_${s.name}`);
      if (display) display.textContent = `${val}%`;
      sum += val;
    });

    if (sumValEl) sumValEl.textContent = `${sum}%`;

    if (sumBoxEl) {
      if (Math.abs(sum - 100) < 0.1) {
        sumBoxEl.className = 'weight-sum-indicator valid';
        if (applyBtn) applyBtn.disabled = false;
      } else {
        sumBoxEl.className = 'weight-sum-indicator invalid';
        if (applyBtn) applyBtn.disabled = true;
      }
    }
  };

  sliders.forEach(s => {
    s.addEventListener('input', updateWeights);
  });

  // Presets
  const presets = {
    battery: { battery: 50, price: 20, rating: 15, anc: 15 },
    budget: { battery: 20, price: 60, rating: 10, anc: 10 },
    anc: { battery: 20, price: 20, rating: 20, anc: 40 },
    balanced: { battery: 35, price: 35, rating: 15, anc: 15 }
  };

  document.querySelectorAll('.preset-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('.preset-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      const presetKey = chip.getAttribute('data-preset');
      const weights = presets[presetKey];
      if (weights) {
        Object.keys(weights).forEach(k => {
          const input = document.querySelector(`input[name="${k}"]`);
          if (input) input.value = weights[k];
        });
        updateWeights();
      }
    });
  });

  // Apply weights
  if (applyBtn) {
    applyBtn.addEventListener('click', () => {
      const weightParams = {};
      sliders.forEach(s => {
        weightParams[s.name] = parseFloat(s.value);
      });

      // Redirect with custom weights in URL or perform AJAX
      const searchParams = new URLSearchParams(window.location.search);
      searchParams.set('custom_weights', JSON.stringify(weightParams));
      window.location.href = `/shop?${searchParams.toString()}`;
    });
  }

  // Initial calculation
  updateWeights();
}

function initCartFeedback() {
  document.querySelectorAll('.btn-card-add').forEach(btn => {
    btn.addEventListener('click', function(e) {
      const origText = this.innerHTML;
      this.innerHTML = '✓ Added!';
      this.style.background = '#10b981';
      setTimeout(() => {
        this.innerHTML = origText;
        this.style.background = '';
      }, 1200);
    });
  });
}
