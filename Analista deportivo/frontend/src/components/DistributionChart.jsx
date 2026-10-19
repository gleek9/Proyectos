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

  const data = {
    labels,
    datasets: [
      {
        label: 'Probabilidad (%)',
        data: dataValues,
        backgroundColor: [
          'rgba(148, 163, 184, 0.4)',
          'rgba(56, 189, 248, 0.5)',
          'rgba(163, 230, 53, 0.7)',
          'rgba(163, 230, 53, 0.8)',
          'rgba(56, 189, 248, 0.6)',
          'rgba(168, 85, 247, 0.5)',
        ],
        borderColor: [
          '#94a3b8',
          '#38bdf8',
          '#a3e635',
          '#a3e635',
          '#38bdf8',
          '#a855f7',
        ],
        borderWidth: 1,
        borderRadius: 4,
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
        backgroundColor: '#16161a',
        titleColor: '#f8fafc',
        bodyColor: '#38bdf8',
        borderColor: '#26262e',
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
          color: '#26262e'
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
          color: '#1a1a22'
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
          <span>Distribución de Goles (0 a 5+)</span>
        </span>
        <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
          PROBABILIDAD CONJUNTA
        </span>
      </div>

      <div className="chart-wrapper">
        <Bar data={data} options={options} />
      </div>

      <div style={{ marginTop: '0.5rem' }}>
        <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
          MARCADORES EXACTOS MÁS PROBABLES:
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
