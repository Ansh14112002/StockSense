// DOM Elements
const sidebar = document.querySelector('.sidebar');
const sidebarToggle = document.querySelector('.sidebar-toggle');
const toast = document.querySelector('.toast');
const spinnerContainer = document.querySelector('.spinner-container');

// Toggle sidebar on mobile
sidebarToggle.addEventListener('click', () => {
  sidebar.classList.toggle('active');
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
    showToast('Data loaded successfully');
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
    });
  });
  
  // Auto-fetch live data every 60 seconds
  fetchLiveData();
  setInterval(fetchLiveData, 60000);
  
  // Simulate initial data load
  setTimeout(simulateDataLoad, 1000);
});


// Go back to home
function goBack() {
  window.location.href = "/";
}

// Export sentiment table to CSV
function exportToCSV() {
  const table = document.getElementById("sentimentTable");
  let csv = [];
  for (let row of table.rows) {
    let rowData = [];
    for (let cell of row.cells) {
      rowData.push(cell.innerText.replace(/,/g, ""));
    }
    csv.push(rowData.join(","));
  }

  const csvContent = "data:text/csv;charset=utf-8," + csv.join("\n");
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", "sentiment_results.csv");
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

let sensexChart = null;

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
          ${arrow} ${idx.change_pct !== null ? idx.change_pct.toFixed(2) + '%' : '—'}
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
              ticks: { color: '#636e72' },
            },
            y: {
              grid: { color: 'rgba(0,0,0,0.05)', drawBorder: false },
              ticks: { color: '#636e72' },
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