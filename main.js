/**
 * APEX DRIVE - Client-side core interactive utilities
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Menu Toggle
  const toggleBtn = document.getElementById('navToggleBtn');
  const navLinks = document.getElementById('navLinks');
  if (toggleBtn && navLinks) {
    toggleBtn.addEventListener('click', () => {
      navLinks.classList.toggle('show');
    });
  }

  // 2. Flash Message Close Buttons
  const alertCloses = document.querySelectorAll('.alert-close');
  alertCloses.forEach(btn => {
    btn.addEventListener('click', () => {
      const alert = btn.closest('.alert');
      if (alert) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(() => alert.remove(), 250);
      }
    });
  });

  // Auto-dismiss info/success alerts after 6 seconds
  setTimeout(() => {
    document.querySelectorAll('.alert-success, .alert-info').forEach(alert => {
      alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-10px)';
      setTimeout(() => alert.remove(), 500);
    });
  }, 6000);

  // 3. Modal helper functions
  window.openModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('active');
    }
  };

  window.closeModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('active');
    }
  };

  // Close modals on backdrop click
  document.querySelectorAll('.modal-backdrop').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('active');
      }
    });
  });

  // 4. Quick-fill credentials for demo accounts
  window.fillCredentials = function(username, password) {
    const loginIdInput = document.getElementById('login_id');
    const passwordInput = document.getElementById('password');
    if (loginIdInput && passwordInput) {
      loginIdInput.value = username;
      passwordInput.value = password;
      // Visual feedback
      loginIdInput.style.borderColor = '#10b981';
      passwordInput.style.borderColor = '#10b981';
      setTimeout(() => {
        loginIdInput.style.borderColor = '';
        passwordInput.style.borderColor = '';
      }, 1000);
    }
  };
});
