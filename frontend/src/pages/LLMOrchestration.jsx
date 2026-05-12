import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  Divider,
  Paper,
  Grid,
  LinearProgress
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import HistoryIcon from '@mui/icons-material/History';
import InsightIcon from '@mui/icons-material/Insights';
import WarningIcon from '@mui/icons-material/Warning';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import {
  getOrchestrationContext,
  generateOrchestrationPlan,
  getOrchestrationHistory,
  getOrchestrationMetrics,
  explainDecision
} from '../services/api';

const LLMOrchestration = () => {
  const [context, setContext] = useState(null);
  const [plan, setPlan] = useState(null);
  const [history, setHistory] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedDecision, setSelectedDecision] = useState(null);
  const [explanation, setExplanation] = useState(null);

  useEffect(() => {
    loadContext();
    loadHistory();
    loadMetrics();
  }, []);

  const loadContext = async () => {
    try {
      const data = await getOrchestrationContext();
      if (data.success) {
        setContext(data.context);
      }
    } catch (err) {
      console.error('Error loading context:', err);
    }
  };

  const loadHistory = async () => {
    try {
      const data = await getOrchestrationHistory();
      if (data.success) {
        setHistory(data.history || []);
      }
    } catch (err) {
      console.error('Error loading history:', err);
    }
  };

  const loadMetrics = async () => {
    try {
      const data = await getOrchestrationMetrics();
      if (data.success) {
        setMetrics(data.metrics);
      }
    } catch (err) {
      console.error('Error loading metrics:', err);
    }
  };

  const handleGeneratePlan = async (dryRun = true) => {
    setLoading(true);
    setError(null);
    setPlan(null);

    try {
      const result = await generateOrchestrationPlan({ dry_run: dryRun });
      if (result.success) {
        setPlan(result);
        loadHistory(); // Refresh history
      } else {
        setError(result.error || 'Failed to generate plan');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleExplain = async (decisionId) => {
    try {
      const data = await explainDecision(decisionId);
      if (data.success) {
        setExplanation(data.explanation);
        setSelectedDecision(decisionId);
      }
    } catch (err) {
      console.error('Error getting explanation:', err);
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success': return <CheckCircleIcon color="success" />;
      case 'failed': return <ErrorIcon color="error" />;
      default: return <CircularProgress size={20} />;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <AutoAwesomeIcon color="primary" />
        LLM Orchestration Layer
      </Typography>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        AI-powered autonomous orchestration for multi-agent supply chain optimization
      </Typography>

      {/* Action Controls */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              startIcon={loading ? <CircularProgress size={20} /> : <PlayArrowIcon />}
              onClick={() => handleGeneratePlan(true)}
              disabled={loading}
              color="primary"
            >
              Generate Plan (Dry Run)
            </Button>
            <Button
              variant="contained"
              startIcon={loading ? <CircularProgress size={20} /> : <PlayArrowIcon />}
              onClick={() => handleGeneratePlan(false)}
              disabled={loading}
              color="secondary"
            >
              Generate & Execute
            </Button>
            <Button
              variant="outlined"
              startIcon={<InsightIcon />}
              onClick={loadContext}
            >
              Refresh Context
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Context Summary */}
      {context && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Operational Context
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6} sm={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {context.signals?.total_active || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Active Signals
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="warning.main">
                    {context.critical_issues?.length || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Critical Issues
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="info.main">
                    {context.inventory_summary?.total_low_stock || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Low Stock Items
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4">
                    {context.warehouse_summary?.avg_utilization_percent?.toFixed(1) || 0}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Avg Warehouse Util
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={context.warehouse_summary?.avg_utilization_percent || 0}
                    sx={{ mt: 1 }}
                  />
                </Paper>
              </Grid>
            </Grid>

            {/* Recommended Focus */}
            {context.recommended_focus?.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Recommended Focus Areas:
                </Typography>
                <List dense>
                  {context.recommended_focus.map((focus, idx) => (
                    <ListItem key={idx}>
                      <ListItemText primary={focus} />
                    </ListItem>
                  ))}
                </List>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* Generated Plan */}
      {plan && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AutoAwesomeIcon color="primary" />
              Generated Orchestration Plan
              <Chip
                label={plan.decision?.llm_plan?.priority || 'medium'}
                size="small"
                color={getSeverityColor(plan.decision?.llm_plan?.severity)}
              />
            </Typography>

            {plan.decision?.llm_plan && (
              <Box>
                <Alert severity="info" sx={{ mb: 2 }}>
                  <Typography variant="subtitle2">Situation:</Typography>
                  {plan.decision.llm_plan.situation}
                </Alert>

                {/* Reasoning */}
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Reasoning:
                  </Typography>
                  <List dense>
                    {plan.decision.llm_plan.reasoning?.map((reason, idx) => (
                      <ListItem key={idx}>
                        <ListItemText primary={`• ${reason}`} />
                      </ListItem>
                    ))}
                  </List>
                </Box>

                {/* Actions */}
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Recommended Actions:
                  </Typography>
                  {plan.decision.llm_plan.actions?.map((action, idx) => (
                    <Paper key={idx} sx={{ p: 2, mb: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Box>
                          <Chip
                            label={action.action_type}
                            size="small"
                            color="primary"
                            sx={{ mr: 1 }}
                          />
                          <Chip
                            label={action.priority}
                            size="small"
                            variant="outlined"
                          />
                        </Box>
                        {action.reason && (
                          <Typography variant="body2" color="text.secondary">
                            {action.reason}
                          </Typography>
                        )}
                      </Box>
                      {action.sku && (
                        <Typography variant="body2" sx={{ mt: 1 }}>
                          SKU: {action.sku} | Quantity: {action.quantity || 'N/A'}
                        </Typography>
                      )}
                    </Paper>
                  ))}
                </Box>

                {/* Expected Outcome & Risk */}
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2">Expected Outcome:</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {plan.decision.llm_plan.expected_outcome || 'Not specified'}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2">Risk Assessment:</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {plan.decision.llm_plan.risk_assessment || 'Not specified'}
                    </Typography>
                  </Grid>
                </Grid>

                {/* Validation Status */}
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Validation Status:
                  </Typography>
                  {plan.decision.validation_results?.map((v, idx) => (
                    <Chip
                      key={idx}
                      label={v.valid ? '✓ Valid' : `✗ ${v.errors?.join(', ')}`}
                      color={v.valid ? 'success' : 'error'}
                      size="small"
                      sx={{ mr: 1 }}
                    />
                  ))}
                </Box>

                {/* Confidence Score */}
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Confidence Score: {(plan.decision.llm_plan.confidence * 100).toFixed(0)}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={(plan.decision.llm_plan.confidence || 0) * 100}
                    sx={{ height: 10, borderRadius: 5 }}
                  />
                </Box>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* Orchestration History */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <HistoryIcon color="primary" />
            Orchestration History
          </Typography>

          {history.length === 0 ? (
            <Typography color="text.secondary">No orchestration decisions yet</Typography>
          ) : (
            <List>
              {history.map((item, idx) => (
                <React.Fragment key={idx}>
                  <ListItem
                    alignItems="flex-start"
                    secondaryAction={
                      <Button
                        size="small"
                        onClick={() => handleExplain(item.decision_id)}
                      >
                        Explain
                      </Button>
                    }
                  >
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Chip
                            label={item.llm_plan?.priority || 'unknown'}
                            size="small"
                            color={getSeverityColor(item.llm_plan?.severity)}
                          />
                          <Typography variant="body2">
                            {item.llm_plan?.situation || 'No situation summary'}
                          </Typography>
                        </Box>
                      }
                      secondary={
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="caption" color="text.secondary">
                            {new Date(item.timestamp).toLocaleString()}
                          </Typography>
                          <Chip
                            label={item.can_auto_execute ? 'Auto-Execute' : 'Requires Review'}
                            size="small"
                            variant="outlined"
                            sx={{ ml: 1 }}
                          />
                        </Box>
                      }
                    />
                  </ListItem>
                  {idx < history.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          )}
        </CardContent>
      </Card>

      {/* Explanation Modal */}
      {explanation && selectedDecision && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Decision Explanation: {selectedDecision}
            </Typography>
            <Divider sx={{ mb: 2 }} />

            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Typography variant="subtitle2">Situation</Typography>
                <Typography variant="body2" color="text.secondary">
                  {explanation.situation}
                </Typography>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle2">Reasoning Chain</Typography>
                <List dense>
                  {explanation.reasoning?.map((r, idx) => (
                    <ListItem key={idx}>
                      <ListItemText primary={`${idx + 1}. ${r}`} />
                    </ListItem>
                  ))}
                </List>
              </Grid>

              <Grid item xs={6}>
                <Typography variant="subtitle2">Expected Outcome</Typography>
                <Typography variant="body2" color="text.secondary">
                  {explanation.expected_outcome}
                </Typography>
              </Grid>

              <Grid item xs={6}>
                <Typography variant="subtitle2">Risk Assessment</Typography>
                <Typography variant="body2" color="text.secondary">
                  {explanation.risk_assessment}
                </Typography>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle2">Context at Decision Time</Typography>
                <Paper sx={{ p: 1, bgcolor: 'grey.100' }}>
                  <pre style={{ fontSize: '0.75rem', margin: 0, overflow: 'auto' }}>
                    {JSON.stringify(explanation.context_at_decision, null, 2)}
                  </pre>
                </Paper>
              </Grid>
            </Grid>

            <Button sx={{ mt: 2 }} onClick={() => { setExplanation(null); setSelectedDecision(null); }}>
              Close
            </Button>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default LLMOrchestration;
