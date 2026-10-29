/**
 * APEX DRIVE - Booking & Live Quote Calculation
 */

document.addEventListener('DOMContentLoaded', () => {
  const pickupInput = document.getElementById('pickup_date');
  const returnInput = document.getElementById('return_date');
  const vehicleIdEl = document.getElementById('bookingVehicleId');
  const dailyRateEl = document.getElementById('bookingDailyRate');
  const submitBtn = document.getElementById('submitBookingBtn');
  
  const quoteContainer = document.getElementById('liveQuoteContainer');
  const quoteDaysEl = document.getElementById('quoteDays');
  const quoteSubtotalEl = document.getElementById('quoteSubtotal');
  const quoteTaxEl = document.getElementById('quoteTax');
  const quoteTotalEl = document.getElementById('quoteTotal');
  const quoteDaysExplEl = document.getElementById('quoteDaysExplanation');
  const quoteFeedbackEl = document.getElementById('quoteFeedback');

  function calculateAndCheck() {
    if (!pickupInput || !returnInput || !vehicleIdEl) return;

    const pickupVal = pickupInput.value;
    const returnVal = returnInput.value;

    if (!pickupVal || !returnVal) {
      if (quoteContainer) quoteContainer.style.display = 'none';
      if (quoteFeedbackEl) quoteFeedbackEl.innerHTML = '';
      return;
    }

    const pDate = new Date(pickupVal + 'T00:00:00');
    const rDate = new Date(returnVal + 'T00:00:00');

    if (rDate <= pDate) {
      if (quoteContainer) quoteContainer.style.display = 'none';
      if (quoteFeedbackEl) {
        quoteFeedbackEl.innerHTML = `
          <div style="color: #fb7185; font-size: 0.85rem; margin-top: 0.5rem; display: flex; align-items: center; gap: 0.35rem;">
            <span>⚠️</span> Return date must be strictly after pickup date (minimum 1 day).
          </div>
        `;
      }
      if (submitBtn) submitBtn.disabled = true;
      return;
    }

    const vehicleId = vehicleIdEl.value;

    // Fetch live availability & quote from API
    fetch(`/api/vehicles/${vehicleId}/availability?pickup_date=${pickupVal}&return_date=${returnVal}`)
      .then(res => res.json())
      .then(data => {
        if (!data.success) {
          if (quoteContainer) quoteContainer.style.display = 'none';
          if (quoteFeedbackEl) {
            quoteFeedbackEl.innerHTML = `
              <div style="color: #fb7185; font-size: 0.85rem; margin-top: 0.5rem;">
                ⚠️ ${data.error}
              </div>
            `;
          }
          if (submitBtn) submitBtn.disabled = true;
          return;
        }

        const q = data.quote;
        const sym = window.CURRENCY_SYMBOL || '₹';
        if (quoteDaysEl) quoteDaysEl.textContent = `${q.days} day${q.days > 1 ? 's' : ''}`;
        if (quoteSubtotalEl) quoteSubtotalEl.textContent = `${sym}${q.subtotal.toFixed(2)}`;
        if (quoteTaxEl) quoteTaxEl.textContent = `${sym}${q.tax.toFixed(2)}`;
        if (quoteTotalEl) quoteTotalEl.textContent = `${sym}${q.total.toFixed(2)}`;
        if (quoteDaysExplEl) quoteDaysExplEl.textContent = q.days_explanation;
        if (quoteContainer) quoteContainer.style.display = 'block';

        if (data.available) {
          if (quoteFeedbackEl) {
            quoteFeedbackEl.innerHTML = `
              <div style="color: #34d399; font-size: 0.85rem; margin-top: 0.65rem; display: flex; align-items: center; gap: 0.35rem; font-weight: 600;">
                <span>✓</span> Available for these dates!
              </div>
            `;
          }
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = `Reserve for ${sym}${q.total.toFixed(2)}`;
          }
        } else {
          if (quoteFeedbackEl) {
            quoteFeedbackEl.innerHTML = `
              <div style="color: #fb7185; font-size: 0.85rem; margin-top: 0.65rem; display: flex; align-items: center; gap: 0.35rem; font-weight: 600;">
                <span>✕</span> Reserved on selected dates. Please adjust dates.
              </div>
            `;
          }
          if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Vehicle Unavailable for Selected Dates';
          }
        }
      })
      .catch(err => {
        console.error('Availability check error:', err);
      });
  }

  if (pickupInput && returnInput) {
    pickupInput.addEventListener('change', () => {
      // Set min return date as pickup date + 1 day
      if (pickupInput.value) {
        const nextDay = new Date(pickupInput.value + 'T00:00:00');
        nextDay.setDate(nextDay.getDate() + 1);
        returnInput.min = nextDay.toISOString().split('T')[0];
        if (returnInput.value && returnInput.value <= pickupInput.value) {
          returnInput.value = returnInput.min;
        }
      }
      calculateAndCheck();
    });

    returnInput.addEventListener('change', calculateAndCheck);

    // Initial check if values present
    if (pickupInput.value && returnInput.value) {
      calculateAndCheck();
    }
  }

  // --- Indian Payment Simulation Helper Functions ---
  window.selectPaymentTab = function(tab) {
    const tabs = ['upi', 'card', 'netbanking', 'hub'];
    const modeInput = document.getElementById('selected_payment_mode');
    const methodInput = document.getElementById('selected_payment_method');

    tabs.forEach(t => {
      const section = document.getElementById(`section_${t}`);
      const btn = document.getElementById(`tab_${t}`);
      if (section) section.style.display = (t === tab) ? 'block' : 'none';
      if (btn) {
        if (t === tab) {
          btn.className = 'btn btn-primary btn-sm payment-tab-btn';
        } else {
          btn.className = 'btn btn-secondary btn-sm payment-tab-btn';
        }
      }
    });

    if (modeInput) modeInput.value = tab;
    if (methodInput) {
      if (tab === 'upi') methodInput.value = 'UPI (Google Pay / PhonePe / Paytm)';
      else if (tab === 'card') methodInput.value = 'Simulated RuPay / Card';
      else if (tab === 'netbanking') methodInput.value = 'Net Banking';
      else if (tab === 'hub') methodInput.value = 'Pay at Hub';
    }
  };

  window.fillSimulatedPayment = function(scenario) {
    const cardholderInput = document.getElementById('cardholder_name');
    const cardNumInput = document.getElementById('card_number');
    const expiryInput = document.getElementById('card_expiry');
    const cvvInput = document.getElementById('card_cvv');
    const upiInput = document.getElementById('upi_id');
    const outcomeSuccessRadio = document.getElementById('outcome_success');
    const outcomeFailRadio = document.getElementById('outcome_failure');
    const failureReasonBox = document.getElementById('failureReasonContainer');
    const payBtn = document.getElementById('simulatePayBtn');

    if (scenario === 'success') {
      if (upiInput) upiInput.value = 'priya@okaxis';
      if (cardNumInput) cardNumInput.value = '6070 1234 5678 9010';
      if (expiryInput) expiryInput.value = '12/28';
      if (cvvInput) cvvInput.value = '888';
      if (outcomeSuccessRadio) outcomeSuccessRadio.checked = true;
      if (failureReasonBox) failureReasonBox.style.display = 'none';
      if (payBtn) {
        payBtn.className = 'btn btn-emerald btn-lg btn-block';
        payBtn.innerHTML = '🔒 Complete Simulated Payment (Approve)';
      }
    } else if (scenario === 'failure') {
      if (upiInput) upiInput.value = 'invalid.pin@upi';
      if (cardNumInput) cardNumInput.value = '6070 9999 8888 0002';
      if (expiryInput) expiryInput.value = '08/27';
      if (cvvInput) cvvInput.value = '000';
      if (outcomeFailRadio) outcomeFailRadio.checked = true;
      if (failureReasonBox) failureReasonBox.style.display = 'block';
      if (payBtn) {
        payBtn.className = 'btn btn-danger btn-lg btn-block';
        payBtn.innerHTML = '⚠️ Simulate Decline / Failure';
      }
    }
  };

  // Backwards compatibility alias
  window.fillSimulatedCard = window.fillSimulatedPayment;

  // Outcome radio listener
  const outcomeRadios = document.querySelectorAll('input[name="simulated_outcome"]');
  outcomeRadios.forEach(r => {
    r.addEventListener('change', (e) => {
      const failureReasonBox = document.getElementById('failureReasonContainer');
      const payBtn = document.getElementById('simulatePayBtn');
      if (e.target.value === 'failure') {
        if (failureReasonBox) failureReasonBox.style.display = 'block';
        if (payBtn) {
          payBtn.className = 'btn btn-danger btn-lg btn-block';
          payBtn.innerHTML = '⚠️ Simulate Decline / Failure';
        }
      } else {
        if (failureReasonBox) failureReasonBox.style.display = 'none';
        if (payBtn) {
          payBtn.className = 'btn btn-emerald btn-lg btn-block';
          payBtn.innerHTML = '🔒 Complete Simulated Payment (Approve)';
        }
      }
    });
  });
});
