import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { BarChart3 } from 'lucide-react';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

export default function DistributionChart({ chartData, theme = 'dark' }) {
  if (!chartData) return null;

  const { goals_distribution, top_scores } = chartData;
  const isLight = theme === 'light';

  const labels = goals_distribution.map((item) => item.goals);
  const dataValues = goals_distribution.map((item) => item.probability);
  const maxProbability = Math.max(...dataValues, 1);

  // Paleta Warm Stealth / Warm Light mate sin bordes fluorescentes
  const backgroundColors = dataValues.map((val) => {
    if (val === maxProbability) {
      return isLight ? '#9f7240' : '#d6b484';
    }
    if (val >= maxProbability * 0.65) {
      return isLight ? 'rgba(159, 114, 64, 0.55)' : 'rgba(214, 180, 132, 0.52)';
    }
    if (val >= maxProbability * 0.35) {
      return isLight ? 'rgba(120, 113, 108, 0.38)' : 'rgba(168, 162, 158, 0.32)';
    }
    return isLight ? 'rgba(120, 113, 108, 0.20)' : 'rgba(168, 162, 158, 0.16)';
  });

  const data = {
    labels,
    datasets: [
      {
        label: 'Probabilidad (%)',
        data: dataValues,
        backgroundColor: backgroundColors,
        borderWidth: 0,
        borderRadius: 6,
        barPercentage: 0.6,
        categoryPercentage: 0.78,
      }
    ]
  };

  const gridColor = isLight ? 'rgba(28, 25, 23, 0.06)' : 'rgba(245, 245, 244, 0.05)';
  const tickColor = isLight ? '#78716c' : '#a8a29e';

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        backgroundColor: isLight ? '#1c1917' : '#1b1a17',
        titleColor: '#f5f5f4',
        bodyColor: '#d6b484',
        borderColor: isLight ? 'rgba(28, 25, 23, 0.15)' : 'rgba(245, 245, 244, 0.12)',
        borderWidth: 1,
        padding: 10,
        displayColors: false,
        callbacks: {
          label: (context) => `${context.parsed.y}% de probabilidad`
        }
      }
    },
    scales: {
      x: {
        grid: {
          display: false,
        },
        ticks: {
          color: tickColor,
          font: {
            family: "'JetBrains Mono', monospace",
            size: 11
          }
        }
      },
      y: {
        grid: {
          color: gridColor,
        },
        ticks: {
          color: tickColor,
          font: {
            family: "'JetBrains Mono', monospace",
            size: 10
          },
          callback: (value) => `${value}%`
        },
        suggestedMax: 35
      }
    }
  };

  return (
    <div className="chart-panel">
      <div className="panel-header">
        <span className="panel-title">
          <BarChart3 size={15} color="var(--sand)" />
          <span>Distribución de goles (0 a 5+)</span>
        </span>
        <span className="v5-meta-dim">
          Probabilidad conjunta
        </span>
      </div>

      <div className="chart-wrapper">
        <Bar data={data} options={options} />
      </div>

      <div style={{ marginTop: '0.45rem' }}>
        <span className="v5-meta-dim">
          Marcadores más probables:
        </span>
        <div className="top-scores-container">
          {top_scores && top_scores.map((s, idx) => (
            <div key={idx} className="score-chip">
              <span className="score-name">{s.score}</span>
              <span className="score-prob">{s.probability}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
