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

export default function DistributionChart({ chartData }) {
  if (!chartData) return null;

  const { goals_distribution, top_scores } = chartData;

  const labels = goals_distribution.map(item => item.goals);
  const dataValues = goals_distribution.map(item => item.probability);
  const maxProbability = Math.max(...dataValues, 1);

  // Aurora UI: El rango modal se ilumina con emerald glow, los adyacentes en azure y las colas en slate
  const backgroundColors = dataValues.map(val => {
    if (val === maxProbability) return 'rgba(16, 185, 129, 0.85)';
    if (val >= maxProbability * 0.65) return 'rgba(14, 165, 233, 0.70)';
    if (val >= maxProbability * 0.35) return 'rgba(56, 189, 248, 0.45)';
    return 'rgba(148, 163, 184, 0.30)';
  });

  const borderColors = dataValues.map(val => {
    if (val === maxProbability) return '#10b981';
    if (val >= maxProbability * 0.65) return '#0ea5e9';
    if (val >= maxProbability * 0.35) return '#38bdf8';
    return 'rgba(148, 163, 184, 0.55)';
  });

  const data = {
    labels,
    datasets: [
      {
        label: 'Probabilidad (%)',
        data: dataValues,
        backgroundColor: backgroundColors,
        borderColor: borderColors,
        borderWidth: 1.5,
        borderRadius: 5,
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        backgroundColor: 'rgba(15, 18, 25, 0.94)',
        titleColor: '#f8fafc',
        bodyColor: '#38bdf8',
        borderColor: 'rgba(255, 255, 255, 0.12)',
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
          color: 'rgba(255, 255, 255, 0.05)'
        },
        ticks: {
          color: '#94a3b8',
          font: {
            family: "'JetBrains Mono', monospace",
            size: 11
          }
        }
      },
      y: {
        grid: {
          color: 'rgba(255, 255, 255, 0.04)'
        },
        ticks: {
          color: '#64748b',
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
          <BarChart3 size={15} color="var(--cyan)" />
          <span>Distribución de goles (0 a 5+)</span>
        </span>
        <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
          Probabilidad conjunta
        </span>
      </div>

      <div className="chart-wrapper">
        <Bar data={data} options={options} />
      </div>

      <div style={{ marginTop: '0.65rem' }}>
        <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
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
