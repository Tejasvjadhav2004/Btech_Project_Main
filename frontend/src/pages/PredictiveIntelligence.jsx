import React, { useEffect, useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, PieChart, Pie, Cell
} from 'recharts';
import {
  getDemandPredictions, getStockoutRisks, getDelayRisks, getAllPredictiveRisks,
  runPredictiveSensing, generateDemandPredictions, getModelStatus
} from '../services/api';

const COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
  increasing: '#3b82f6',
  decreasing: '#ef4444',
  stable: '#6b7280'
};

const PIE_COLORS = ['#ef4444', '#f97316', '#eab308', '#22c55e'];

const PredictiveIntelligence = () => {
  const [loading, setLoading] = useState(true);
  const [demandPredictions, setDemandPredictions] = useState([]);
  const [stockoutRisks, setStockoutRisks] = useState([]);
  const [delayRisks, setDelayRisks] = useState([]);
  const [allRisks, setAllRisks] = useState([]);
  const [modelStatus, setModelStatus] = useState(null);
  const [activeTab, setActiveTab] = useState('demand');
  const [selectedSku, setSelectedSku] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [demand, stockouts, delays, risks, status] = await Promise.all([
        getDemandPredictions().catch(() => []),
        getStockoutRisks().catch(() => []),
        getDelayRisks().catch(() => []),
        getAllPredictiveRisks().catch(() => []),
        getModelStatus().catch(() => null)
      ]);

      setDemandPredictions(Array.isArray(demand) ? demand : []);
      setStockoutRisks(Array.isArray(stockouts) ? stockouts : []);
      setDelayRisks(Array.isArray(delays) ? delays : []);
      setAllRisks(Array.isArray(risks) ? risks : []);
      setModelStatus(status);
    } catch (err) {
      console.error('Error loading data:', err);
      setError('Failed to load prediction data');
    }
    setLoading(false);
  };

  const handleRunPredictiveSensing = async () => {
    try {
      setLoading(true);
      await runPredictiveSensing();
      await loadAllData();
    } catch (err) {
      setError('Failed to run predictive sensing');
      setLoading(false);
    }
  };

  const handleGeneratePredictions = async () => {
    try {
      setLoading(true);
      await generateDemandPredictions();
      await loadAllData();
    } catch (err) {
      setError('Failed to generate predictions');
      setLoading(false);
    }
  };

  const getTrendIcon = (trend) => {
    if (trend === 'increasing') return '↑';
    if (trend === 'decreasing') return '↓';
    return '→';
  };

  const getTrendColor = (trend) => {
    return COLORS[trend] || COLORS.stable;
  };

  const getSeverityColor = (severity) => {
    return COLORS[severity] || COLORS.medium;
  };

  // Prepare data for charts
  const demandTrendData = demandPredictions.slice(0, 10).map(p => ({
    name: p.sku?.slice(-4) || 'N/A',
    predicted: p.predicted_demand_7d || 0,
    confidence: (p.confidence || 0) * 100,
    trend: p.trend
  }));

  const riskDistribution = [
    { name: 'Critical', value: allRisks.filter(r => r.severity === 'critical').length },
    { name: 'High', value: allRisks.filter(r => r.severity === 'high').length },
    { name: 'Medium', value: allRisks.filter(r => r.severity === 'medium').length },
    { name: 'Low', value: allRisks.filter(r => r.severity === 'low').length }
  ].filter(d => d.value > 0);

  if (loading) {
    return <div style={{ padding: '20px', textAlign: 'center' }}>Loading Predictive Intelligence...</div>;
  }

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1 style={{ color: '#0f172a', margin: 0 }}>Predictive Intelligence</h1>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={handleGeneratePredictions}
            style={{
              padding: '10px 20px',
              backgroundColor: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            Generate Forecasts
          </button>
          <button
            onClick={handleRunPredictiveSensing}
            style={{
              padding: '10px 20px',
              backgroundColor: '#10b981',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            Run Risk Detection
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: '10px', backgroundColor: '#fef2f2', color: '#ef4444', borderRadius: '6px', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {/* Model Status */}
      {modelStatus && (
        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '10px', marginBottom: '20px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          <h3 style={{ margin: '0 0 10px 0', color: '#334155' }}>ML Model Status</h3>
          <div style={{ display: 'flex', gap: '20px' }}>
            <div>
              <span style={{ color: '#64748b' }}>Demand Forecast Model: </span>
              <span style={{ color: modelStatus.demand_forecast_model?.exists ? '#10b981' : '#ef4444' }}>
                {modelStatus.demand_forecast_model?.exists ? '✓ Loaded' : '✗ Not Found'}
              </span>
            </div>
            {modelStatus.demand_forecast_model?.metadata?.metrics && (
              <div>
                <span style={{ color: '#64748b' }}>R² Score: </span>
                <span style={{ color: '#3b82f6' }}>
                  {(modelStatus.demand_forecast_model.metadata.metrics.R2 * 100).toFixed(1)}%
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '15px', marginBottom: '20px' }}>
        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          <div style={{ color: '#64748b', fontSize: '14px' }}>Demand Predictions</div>
          <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#0f172a' }}>{demandPredictions.length}</div>
          <div style={{ color: '#10b981', fontSize: '12px' }}>SKU-Store combinations</div>
        </div>
        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          <div style={{ color: '#64748b', fontSize: '14px' }}>Stockout Risks</div>
          <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#ef4444' }}>{stockoutRisks.length}</div>
          <div style={{ color: '#f97316', fontSize: '12px' }}>Predicted stockouts</div>
        </div>
        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          <div style={{ color: '#64748b', fontSize: '14px' }}>Delay Risks</div>
          <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#f97316' }}>{delayRisks.length}</div>
          <div style={{ color: '#eab308', fontSize: '12px' }}>Predicted delays</div>
        </div>
        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          <div style={{ color: '#64748b', fontSize: '14px' }}>Total Predictive Risks</div>
          <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#0f172a' }}>{allRisks.length}</div>
          <div style={{ color: '#64748b', fontSize: '12px' }}>All risk types</div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div style={{ display: 'flex', gap: '5px', marginBottom: '20px' }}>
        {['demand', 'stockout', 'delays', 'all-risks'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '10px 20px',
              backgroundColor: activeTab === tab ? '#3b82f6' : '#f1f5f9',
              color: activeTab === tab ? 'white' : '#334155',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              textTransform: 'capitalize'
            }}
          >
            {tab.replace('-', ' ')}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'demand' && (
        <div>
          {/* Demand Trend Chart */}
          <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '10px', marginBottom: '20px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
            <h3 style={{ margin: '0 0 20px 0', color: '#334155' }}>Predicted Demand (7-Day Forecast)</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={demandTrendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="predicted" fill="#3b82f6" name="Predicted Demand" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Demand Predictions Table */}
          <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
            <h3 style={{ margin: '0 0 20px 0', color: '#334155' }}>Demand Predictions Detail</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
                  <th style={{ padding: '12px', textAlign: 'left', color: '#475569' }}>SKU</th>
                  <th style={{ padding: '12px', textAlign: 'left', color: '#475569' }}>Store</th>
                  <th style={{ padding: '12px', textAlign: 'center', color: '#475569' }}>Predicted (7d)</th>
                  <th style={{ padding: '12px', textAlign: 'center', color: '#475569' }}>Daily Avg</th>
                  <th style={{ padding: '12px', textAlign: 'center', color: '#475569' }}>Confidence</th>
                  <th style={{ padding: '12px', textAlign: 'center', color: '#475569' }}>Trend</th>
                </tr>
              </thead>
              <tbody>
                {demandPredictions.slice(0, 20).map((pred, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '12px', fontWeight: 'bold' }}>{pred.sku}</td>
                    <td style={{ padding: '12px' }}>{pred.store_id}</td>
                    <td style={{ padding: '12px', textAlign: 'center', color: '#3b82f6', fontWeight: 'bold' }}>
                      {pred.predicted_demand_7d?.toFixed(0) || '-'}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>{pred.predicted_daily_avg?.toFixed(1) || '-'}</td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      <span style={{
                        color: (pred.confidence || 0) >= 0.8 ? '#10b981' : (pred.confidence || 0) >= 0.6 ? '#eab308' : '#ef4444'
                      }}>
                        {((pred.confidence || 0) * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      <span style={{ color: getTrendColor(pred.trend) }}>
                        {getTrendIcon(pred.trend)} {pred.trend}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'stockout' && (
        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          <h3 style={{ margin: '0 0 20px 0', color: '#334155' }}>Predicted Stockout Risks</h3>
          {stockoutRisks.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
              No stockout risks predicted. Run risk detection to generate predictions.
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
                  <th style={{ padding: '12px', textAlign: 'left', color: '#475569' }}>SKU</th>
                  <th style={{ padding: '12px', textAlign: 'left', color: '#475569' }}>Store</th>
                  <th style={{ padding: '12px', textAlign: 'center', color: '#475569' }}>Days Remaining</th>
                  <th style={{ padding: '12px', textAlign: 'center', color: '#475569' }}>Current Stock</th>
                  <th style={{ padding: '12px', textAlign: 'center', color: '#475569' }}>Predicted Stockout</th>
                  <th style={{ padding: '12px', textAlign: 'center', color: '#475569' }}>Severity</th>
                </tr>
              </thead>
              <tbody>
                {stockoutRisks.map((risk, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '12px', fontWeight: 'bold' }}>{risk.product_id || risk.details?.sku}</td>
                    <td style={{ padding: '12px' }}>{risk.entity_id}</td>
                    <td style={{ padding: '12px', textAlign: 'center', color: '#ef4444', fontWeight: 'bold' }}>
                      {risk.details?.days_remaining?.toFixed(1) || '-'} days
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>{risk.details?.current_stock || '-'}</td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>{risk.details?.stockout_date || '-'}</td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      <span style={{
                        padding: '4px 12px',
                        borderRadius: '12px',
                        backgroundColor: getSeverityColor(risk.severity) + '20',
                        color: getSeverityColor(risk.severity),
                        fontWeight: 'bold'
                      }}>
                        {risk.severity?.toUpperCase()}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {activeTab === 'delays' && (
        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          <h3 style={{ margin: '0 0 20px 0', color: '#334155' }}>Predicted Delivery Delays</h3>
          {delayRisks.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
              No delay risks predicted.
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
                  <th style={{ padding: '12px', textAlign: 'left', color: '#475569' }}>Delivery ID</th>
                  <th style={{ padding: '12px', textAlign: 'center', color: '#475569' }}>Probability</th>
                  <th style={{ padding: '12px', textAlign: 'center', color: '#475569' }}>Severity</th>
                  <th style={{ padding: '12px', textAlign: 'left', color: '#475569' }}>Message</th>
                </tr>
              </thead>
              <tbody>
                {delayRisks.map((risk, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '12px', fontWeight: 'bold' }}>{risk.entity_id}</td>
                    <td style={{ padding: '12px', textAlign: 'center', color: '#f97316', fontWeight: 'bold' }}>
                      {((risk.details?.probability || 0) * 100).toFixed(0)}%
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      <span style={{
                        padding: '4px 12px',
                        borderRadius: '12px',
                        backgroundColor: getSeverityColor(risk.severity) + '20',
                        color: getSeverityColor(risk.severity),
                        fontWeight: 'bold'
                      }}>
                        {risk.severity?.toUpperCase()}
                      </span>
                    </td>
                    <td style={{ padding: '12px' }}>{risk.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {activeTab === 'all-risks' && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
            {/* Risk Distribution Pie Chart */}
            <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
              <h3 style={{ margin: '0 0 20px 0', color: '#334155' }}>Risk Distribution by Severity</h3>
              {riskDistribution.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={riskDistribution}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {riskDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>No risks to display</div>
              )}
            </div>

            {/* Risk Summary */}
            <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
              <h3 style={{ margin: '0 0 20px 0', color: '#334155' }}>Risk Summary by Type</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>Predicted Stockout</span>
                  <span style={{ fontWeight: 'bold', color: '#ef4444' }}>{stockoutRisks.length}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>Predicted Delay</span>
                  <span style={{ fontWeight: 'bold', color: '#f97316' }}>{delayRisks.length}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>Demand Surge</span>
                  <span style={{ fontWeight: 'bold', color: '#3b82f6' }}>
                    {allRisks.filter(r => r.type === 'DEMAND_SURGE_FORECAST').length}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>Over-Utilization</span>
                  <span style={{ fontWeight: 'bold', color: '#eab308' }}>
                    {allRisks.filter(r => r.type === 'PREDICTED_OVER_UTILIZATION').length}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* All Risks Table */}
          <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
            <h3 style={{ margin: '0 0 20px 0', color: '#334155' }}>All Predictive Risks</h3>
            {allRisks.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
                No predictive risks. Run risk detection to identify future risks.
              </div>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
                    <th style={{ padding: '12px', textAlign: 'left', color: '#475569' }}>Type</th>
                    <th style={{ padding: '12px', textAlign: 'left', color: '#475569' }}>Entity</th>
                    <th style={{ padding: '12px', textAlign: 'left', color: '#475569' }}>Product</th>
                    <th style={{ padding: '12px', textAlign: 'center', color: '#475569' }}>Severity</th>
                    <th style={{ padding: '12px', textAlign: 'left', color: '#475569' }}>Message</th>
                  </tr>
                </thead>
                <tbody>
                  {allRisks.slice(0, 30).map((risk, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '12px' }}>
                        <span style={{ fontSize: '12px', color: '#64748b' }}>{risk.type?.replace(/_/g, ' ')}</span>
                      </td>
                      <td style={{ padding: '12px' }}>{risk.entity_id}</td>
                      <td style={{ padding: '12px' }}>{risk.product_id || '-'}</td>
                      <td style={{ padding: '12px', textAlign: 'center' }}>
                        <span style={{
                          padding: '4px 12px',
                          borderRadius: '12px',
                          backgroundColor: getSeverityColor(risk.severity) + '20',
                          color: getSeverityColor(risk.severity),
                          fontWeight: 'bold'
                        }}>
                          {risk.severity?.toUpperCase()}
                        </span>
                      </td>
                      <td style={{ padding: '12px', fontSize: '14px' }}>{risk.message}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default PredictiveIntelligence;
