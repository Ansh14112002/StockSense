// DOM Elements
const sidebar = document.querySelector('.sidebar');
const sidebarToggle = document.querySelector('.sidebar-toggle');
const sidebarClose = document.querySelector('.sidebar-close');
const toast = document.querySelector('.toast');
const spinnerContainer = document.querySelector('.spinner-container');

// Toggle sidebar on mobile
sidebarToggle.addEventListener('click', () => {
  sidebar.classList.add('active');
});

// Close sidebar with close button
sidebarClose.addEventListener('click', () => {
  sidebar.classList.remove('active');
});

// Close sidebar when clicking outside
document.addEventListener('click', (e) => {
  const isSidebarOpen = sidebar.classList.contains('active');
  const isClickInsideSidebar = sidebar.contains(e.target);
  const isClickOnToggle = sidebarToggle.contains(e.target);
  
  if (isSidebarOpen && !isClickInsideSidebar && !isClickOnToggle) {
    sidebar.classList.remove('active');
  }
});

// Show toast notification
function showToast(message) {
  const toastMessage = toast.querySelector('.toast-message');
  toastMessage.textContent = message;
  toast.classList.add('show');
  
  setTimeout(() => {
    toast.classList.remove('show');
  }, 3000);
}

// Show loading spinner
function showSpinner() {
  spinnerContainer.style.display = 'flex';
}

// Hide loading spinner
function hideSpinner() {
  spinnerContainer.style.display = 'none';
}

// Simulate data loading
function simulateDataLoad() {
  showSpinner();
  setTimeout(() => {
    hideSpinner();
    showToast('Market data updated successfully');
  }, 1500);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  // Animate sections
  const sections = document.querySelectorAll('.section');
  sections.forEach((section, index) => {
    section.style.animationDelay = `${index * 0.1}s`;
  });
  
  // Set active nav item
  const navLinks = document.querySelectorAll('.nav-menu a');
  navLinks.forEach(link => {
    link.addEventListener('click', function() {
      navLinks.forEach(l => l.parentNode.classList.remove('active'));
      this.parentNode.classList.add('active');
      
      // Close sidebar on mobile after clicking a link
      if (window.innerWidth <= 992) {
        sidebar.classList.remove('active');
      }
    });
  });
  
  // Auto-fetch live data every 60 seconds
  fetchLiveData();
  setInterval(fetchLiveData, 60000);
  
  // Simulate initial data load
  setTimeout(simulateDataLoad, 1000);
});

// Fetch and update index and chart data
async function fetchLiveData() {
  try {
    const response = await fetch('/live_data');
    const data = await response.json();

    // 1. Update index cards
    const indicesContainer = document.getElementById('indices-container');
    indicesContainer.innerHTML = '';

    Object.keys(data.indices).forEach((name) => {
      const idx = data.indices[name];
      const arrow = idx.change_pct >= 0 ? '▲' : '▼';
      const changeColor = idx.change_pct >= 0 ? 'gain' : 'loss';

      const card = document.createElement('div');
      card.classList.add('index-card', 'fade-in');
      card.innerHTML = `
        <h3><i class="fas fa-chart-line"></i> ${name}</h3>
        <p class="index-value">${idx.current !== null ? idx.current : '—'}</p>
        <p class="index-change ${changeColor}">
          <i class="fas ${idx.change_pct >= 0 ? 'fa-arrow-up' : 'fa-arrow-down'}"></i>
          ${idx.change_pct !== null ? Math.abs(idx.change_pct).toFixed(2) + '%' : '—'}
        </p>
      `;
      indicesContainer.appendChild(card);
    });

    // 2. Update Sensex intraday chart
    const hist = data.sensex_history;
    const times = hist.map(pt => pt.time);
    const values = hist.map(pt => pt.value);
    const ctx = document.getElementById('sensexChart').getContext('2d');

    if (sensexChart) {
      sensexChart.data.labels = times;
      sensexChart.data.datasets[0].data = values;
      sensexChart.update();
    } else {
      sensexChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: times,
          datasets: [{
            label: 'Sensex',
            data: values,
            borderColor: '#6c5ce7',
            backgroundColor: 'rgba(108, 92, 231, 0.1)',
            borderWidth: 3,
            tension: 0.4,
            fill: true,
            pointRadius: 0,
            pointHoverRadius: 5,
            pointBackgroundColor: '#6c5ce7',
            pointHoverBackgroundColor: '#6c5ce7',
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          plugins: {
            legend: { display: false },
            tooltip: {
              mode: 'index',
              intersect: false,
              backgroundColor: 'rgba(0,0,0,0.8)',
              titleFont: { size: 14, weight: 'bold' },
              bodyFont: { size: 12 },
              padding: 12,
              cornerRadius: 10,
            },
          },
          scales: {
            x: {
              grid: { display: false, drawBorder: false },
              ticks: { color: '#b2bec3' },
            },
            y: {
              grid: { color: 'rgba(255,255,255,0.05)', drawBorder: false },
              ticks: { color: '#b2bec3' },
            },
          },
          interaction: {
            mode: 'nearest',
            axis: 'x',
            intersect: false,
          },
        },
      });
    }
  } catch (err) {
    console.error('Error fetching live data:', err);
    showToast('Failed to load market data');
  }
}

// Animate sections on load
document.addEventListener('DOMContentLoaded', () => {
  const sections = document.querySelectorAll('.section');
  sections.forEach((section, index) => {
    section.style.animationDelay = `${index * 0.1}s`;
  });
});

// Auto-fetch live data every 60 seconds
fetchLiveData();
setInterval(fetchLiveData, 60000);