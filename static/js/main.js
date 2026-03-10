// Chart.js defaults
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';
Chart.defaults.font.family = 'Inter';

// ─── Sidebar Toggle ───────────────────────────────────
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar = document.querySelector('.sidebar');
if (sidebarToggle && sidebar) {
  sidebarToggle.addEventListener('click', () => sidebar.classList.toggle('open'));
}

// ─── Auto-dismiss alerts ──────────────────────────────
document.querySelectorAll('.alert').forEach(alert => {
  setTimeout(() => {
    alert.style.opacity = '0';
    alert.style.transform = 'translateY(-10px)';
    alert.style.transition = 'all 0.4s ease';
    setTimeout(() => alert.remove(), 400);
  }, 4000);
});

// ─── Modal helpers ────────────────────────────────────
function openModal(id) {
  document.getElementById(id).classList.add('active');
}
function closeModal(id) {
  document.getElementById(id).classList.remove('active');
}
// Close modal on overlay click
document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', e => {
    if (e.target === overlay) overlay.classList.remove('active');
  });
});

// ─── Active nav highlight ─────────────────────────────
const currentPath = window.location.pathname;
document.querySelectorAll('.nav-item').forEach(link => {
  const href = link.getAttribute('href');
  if (href && currentPath.startsWith(href)) {
    link.classList.add('active');
  }
});

// ─── Remark modal population ──────────────────────────
function fillRemarkModal(permId, action) {
  const form = document.getElementById('remarkForm');
  if (form) {
    form.action = `/staff/approve/${permId}`;
    document.getElementById('remarkAction').value = action;
  }
}

function fillHODModal(permId, action) {
  const form = document.getElementById('hodRemarkForm');
  if (form) {
    form.action = `/hod/approve/${permId}`;
    document.getElementById('hodAction').value = action;
  }
}

function fillBonafideModal(bonId, action) {
  const form = document.getElementById('bonafideForm');
  if (form) {
    form.action = `/hod/bonafide/approve/${bonId}`;
    document.getElementById('bonafideAction').value = action;
  }
}

// ─── Create Donut Chart ───────────────────────────────
function createDonutChart(id, labels, data, colors) {
  const ctx = document.getElementById(id);
  if (!ctx) return;
  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: colors,
        borderWidth: 0,
        hoverOffset: 6,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      cutout: '72%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { padding: 16, usePointStyle: true, pointStyleWidth: 10 }
        }
      }
    }
  });
}

// ─── Create Bar Chart ─────────────────────────────────
function createBarChart(id, labels, datasets) {
  const ctx = document.getElementById(id);
  if (!ctx) return;
  return new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: 'top' } },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.05)' } },
        y: {
          grid: { color: 'rgba(255,255,255,0.05)' },
          beginAtZero: true,
          ticks: { precision: 0 }
        }
      }
    }
  });
}
