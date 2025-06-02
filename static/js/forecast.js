// forecast.js
// Only run if `chartData` is defined (i.e., we injected it in the template)
if (typeof chartData !== 'undefined') {
  const ctx = document.getElementById('forecastChart').getContext('2d');
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: chartData.dates,
      datasets: [{
        label: 'Closing Price',
        data: chartData.prices,
        borderColor: 'rgba(75, 192, 192, 1)',
        backgroundColor: 'rgba(75, 192, 192, 0.1)',
        tension: 0.3,
        fill: true,
        pointRadius: 3,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: true,
          position: 'top'
        },
        title: {
          display: true,
          text: 'Last 30 Days Closing Prices'
        }
      },
      scales: {
        x: {
          display: true,
          title: {
            display: true,
            text: 'Date'
          }
        },
        y: {
          display: true,
          title: {
            display: true,
            text: 'Price (₹ or $)'
          }
        }
      }
    }
  });
}
