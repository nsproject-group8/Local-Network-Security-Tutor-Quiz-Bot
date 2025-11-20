import React, { useState, useEffect, useCallback } from 'react';
import { Activity, Database, Brain, Shield, CheckCircle, XCircle, RefreshCw, Clock } from 'lucide-react';
import { healthAPI, documentAPI } from '../api/api';

function Dashboard() {
  const [health, setHealth] = useState(null);
  const [docCount, setDocCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [error, setError] = useState(null);

  const loadDashboardData = useCallback(async (isManualRefresh = false) => {
    if (isManualRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);

    try {
      const [healthData, docData] = await Promise.all([
        healthAPI.checkHealth(),
        documentAPI.getDocumentCount(),
      ]);
      setHealth(healthData);
      setDocCount(docData.total_documents);
      setLastUpdated(new Date());
      setError(null);
    } catch (error) {
      console.error('Error loading dashboard:', error);
      setError('Failed to load dashboard data. Please check your connection.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadDashboardData();

    // Auto-refresh every 10 seconds
    const interval = setInterval(() => {
      loadDashboardData();
    }, 10000);

    return () => clearInterval(interval);
  }, [loadDashboardData]);

  const handleManualRefresh = () => {
    loadDashboardData(true);
  };

  const getStatusColor = (status) => {
    if (status === 'healthy') return { bg: '#dcfce7', text: '#166534', border: '#86efac' };
    if (status === 'degraded') return { bg: '#fef3c7', text: '#92400e', border: '#fcd34d' };
    return { bg: '#fee2e2', text: '#991b1b', border: '#fca5a5' };
  };

  const formatLastUpdated = () => {
    if (!lastUpdated) return 'Never';
    const seconds = Math.floor((new Date() - lastUpdated) / 1000);
    if (seconds < 10) return 'Just now';
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    return lastUpdated.toLocaleTimeString();
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem' }}>
        <div className="loading" style={{ 
          width: '40px', 
          height: '40px', 
          borderColor: '#2563eb',
          borderTopColor: 'transparent'
        }} />
        <p style={{ marginTop: '1rem', color: '#6b7280' }}>Loading dashboard...</p>
      </div>
    );
  }

  const getSystemStatusDetails = () => {
    const status = health?.status || 'unknown';
    if (status === 'healthy') return { label: 'Healthy', color: '#10b981', desc: 'All systems operational' };
    if (status === 'degraded') return { label: 'Degraded', color: '#f59e0b', desc: 'Some services unavailable' };
    return { label: 'Offline', color: '#ef4444', desc: 'System unavailable' };
  };

  const statusCards = [
    {
      title: 'System Status',
      value: getSystemStatusDetails().label,
      description: getSystemStatusDetails().desc,
      icon: Activity,
      color: getSystemStatusDetails().color,
      isGood: health?.status === 'healthy',
      pulse: health?.status === 'healthy',
    },
    {
      title: 'Ollama LLM',
      value: health?.ollama_available ? 'Connected' : 'Disconnected',
      description: health?.ollama_available ? 'Model: llama3.2:3b' : 'Service not available',
      icon: Brain,
      color: health?.ollama_available ? '#10b981' : '#ef4444',
      isGood: health?.ollama_available,
      pulse: health?.ollama_available,
    },
    {
      title: 'Vector Database',
      value: health?.chroma_initialized ? 'Ready' : 'Not Ready',
      description: health?.chroma_initialized ? 'ChromaDB operational' : 'Database not initialized',
      icon: Database,
      color: health?.chroma_initialized ? '#10b981' : '#ef4444',
      isGood: health?.chroma_initialized,
      pulse: false,
    },
    {
      title: 'Documents Indexed',
      value: docCount.toString(),
      description: docCount > 0 ? `${docCount} document${docCount !== 1 ? 's' : ''} ready` : 'No documents uploaded',
      icon: Shield,
      color: docCount > 0 ? '#2563eb' : '#6b7280',
      isGood: docCount > 0,
      pulse: false,
    },
  ];

  return (
    <div>
      {/* Header with Refresh */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ fontSize: '1.875rem', fontWeight: 'bold', marginBottom: '0.25rem' }}>
            System Dashboard
          </h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', color: '#6b7280' }}>
            <Clock size={14} />
            <span>Last updated: {formatLastUpdated()}</span>
            {refreshing && <span>(refreshing...)</span>}
          </div>
        </div>
        <button
          onClick={handleManualRefresh}
          disabled={refreshing}
          className="btn btn-secondary"
          style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '0.5rem',
            opacity: refreshing ? 0.5 : 1
          }}
        >
          <RefreshCw size={16} style={{ animation: refreshing ? 'spin 1s linear infinite' : 'none' }} />
          Refresh
        </button>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="alert alert-error" style={{ marginBottom: '1.5rem' }}>
          <XCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Status Cards */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', 
        gap: '1.5rem',
        marginBottom: '2rem'
      }}>
        {statusCards.map((card, index) => {
          const Icon = card.icon;
          const StatusIcon = card.isGood ? CheckCircle : XCircle;
          return (
            <div 
              key={index} 
              className="card" 
              style={{ 
                position: 'relative', 
                overflow: 'hidden',
                borderLeft: `4px solid ${card.color}`,
                transition: 'transform 0.2s, box-shadow 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 10px 15px -3px rgba(0, 0, 0, 0.1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 1px 3px 0 rgba(0, 0, 0, 0.1)';
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.75rem' }}>
                <div style={{ flex: 1 }}>
                  <p style={{ color: '#6b7280', fontSize: '0.875rem', marginBottom: '0.5rem', fontWeight: '500' }}>
                    {card.title}
                  </p>
                  <p style={{ fontSize: '1.5rem', fontWeight: 'bold', color: card.color, marginBottom: '0.25rem' }}>
                    {card.value}
                  </p>
                  <p style={{ fontSize: '0.75rem', color: '#9ca3af' }}>
                    {card.description}
                  </p>
                </div>
                <div style={{ 
                  padding: '0.75rem', 
                  backgroundColor: `${card.color}20`, 
                  borderRadius: '0.5rem',
                  position: 'relative'
                }}>
                  <Icon size={24} color={card.color} />
                  {card.pulse && (
                    <div style={{
                      position: 'absolute',
                      top: '50%',
                      left: '50%',
                      width: '100%',
                      height: '100%',
                      transform: 'translate(-50%, -50%)',
                      backgroundColor: card.color,
                      opacity: 0.3,
                      borderRadius: '0.5rem',
                      animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite'
                    }} />
                  )}
                </div>
              </div>
              <div style={{ 
                position: 'absolute', 
                bottom: '1rem', 
                right: '1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.25rem'
              }}>
                <StatusIcon size={18} color={card.color} />
              </div>
            </div>
          );
        })}
      </div>

      {/* System Statistics */}
      <div className="card" style={{ marginBottom: '2rem', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: 'white' }}>
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Activity size={20} />
              System Overview
            </h3>
            <p style={{ fontSize: '0.875rem', opacity: 0.9 }}>
              {health?.status === 'healthy' 
                ? '✓ All systems operational and ready to use'
                : health?.status === 'degraded'
                ? '⚠ Some services are unavailable'
                : '✗ System is currently offline'}
            </p>
          </div>
          <div style={{ 
            textAlign: 'right',
            padding: '1rem',
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '0.5rem',
            backdropFilter: 'blur(10px)'
          }}>
            <p style={{ fontSize: '0.875rem', opacity: 0.9, marginBottom: '0.25rem' }}>
              Uptime Status
            </p>
            <p style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
              {health?.ollama_available && health?.chroma_initialized ? '100%' : 
               health?.ollama_available || health?.chroma_initialized ? '50%' : '0%'}
            </p>
          </div>
        </div>
      </div>

      {/* Features Overview */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Shield size={20} />
          Privacy & Security Features
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.75rem' }}>
          {[
            { text: 'All data processed locally on your machine', icon: CheckCircle },
            { text: 'No external API calls for sensitive data', icon: CheckCircle },
            { text: 'Encrypted data storage at rest', icon: CheckCircle },
            { text: 'Audit logging for all operations', icon: CheckCircle },
            { text: 'Network traffic monitoring', icon: CheckCircle },
            { text: 'Offline-capable operation', icon: CheckCircle }
          ].map((feature, index) => (
            <div 
              key={index} 
              style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '0.5rem',
                padding: '0.5rem',
                backgroundColor: '#f9fafb',
                borderRadius: '0.375rem',
                transition: 'background-color 0.2s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#f9fafb'}
            >
              <feature.icon size={16} color="#10b981" style={{ flexShrink: 0 }} />
              <span style={{ color: '#4b5563', fontSize: '0.875rem' }}>{feature.text}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Start Guide */}
      <div className="card">
        <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1rem' }}>
          Quick Start Guide
        </h3>
        <ol style={{ paddingLeft: '1.5rem', display: 'grid', gap: '0.75rem', color: '#4b5563' }}>
          <li>
            <strong>Upload Documents:</strong> Go to the Documents tab and upload your network security materials (PDFs, DOCX, PPTX, etc.)
          </li>
          <li>
            <strong>Ask Questions:</strong> Use the Q&A Tutor to ask any questions about network security topics
          </li>
          <li>
            <strong>Take Quizzes:</strong> Test your knowledge with randomly generated or topic-specific quizzes
          </li>
          <li>
            <strong>Get Feedback:</strong> Receive detailed feedback with citations from your documents
          </li>
        </ol>
      </div>

      {/* Warnings & Tips */}
      <div style={{ display: 'grid', gap: '1rem', marginTop: '1.5rem' }}>
        {!health?.ollama_available && (
          <div className="alert alert-error" style={{ display: 'flex', alignItems: 'start', gap: '0.75rem' }}>
            <XCircle size={20} style={{ flexShrink: 0, marginTop: '0.125rem' }} />
            <div>
              <strong>Ollama Service Unavailable</strong>
              <p style={{ marginTop: '0.25rem', fontSize: '0.875rem' }}>
                Please make sure Ollama is running and the model is pulled:
              </p>
              <code style={{ 
                display: 'block', 
                marginTop: '0.5rem', 
                padding: '0.5rem', 
                backgroundColor: 'rgba(0, 0, 0, 0.05)',
                borderRadius: '0.25rem',
                fontSize: '0.875rem'
              }}>
                ollama pull llama3.2:3b
              </code>
            </div>
          </div>
        )}

        {!health?.chroma_initialized && health?.ollama_available && (
          <div className="alert alert-error" style={{ display: 'flex', alignItems: 'start', gap: '0.75rem' }}>
            <XCircle size={20} style={{ flexShrink: 0, marginTop: '0.125rem' }} />
            <div>
              <strong>Database Not Initialized</strong>
              <p style={{ marginTop: '0.25rem', fontSize: '0.875rem' }}>
                The vector database (ChromaDB) is not properly initialized. Try restarting the backend service.
              </p>
            </div>
          </div>
        )}

        {health?.ollama_available && health?.chroma_initialized && docCount === 0 && (
          <div className="alert alert-info" style={{ display: 'flex', alignItems: 'start', gap: '0.75rem' }}>
            <Activity size={20} style={{ flexShrink: 0, marginTop: '0.125rem' }} />
            <div>
              <strong>Ready to Start!</strong>
              <p style={{ marginTop: '0.25rem', fontSize: '0.875rem' }}>
                All systems are operational. Upload some network security documents to begin training the bot. 
                The more material you provide, the better the responses will be!
              </p>
            </div>
          </div>
        )}

        {docCount > 0 && health?.status === 'healthy' && (
          <div className="alert alert-success" style={{ display: 'flex', alignItems: 'start', gap: '0.75rem' }}>
            <CheckCircle size={20} style={{ flexShrink: 0, marginTop: '0.125rem' }} />
            <div>
              <strong>System Ready</strong>
              <p style={{ marginTop: '0.25rem', fontSize: '0.875rem' }}>
                Everything is operational with {docCount} document{docCount !== 1 ? 's' : ''} indexed. 
                You can now ask questions or take quizzes!
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
