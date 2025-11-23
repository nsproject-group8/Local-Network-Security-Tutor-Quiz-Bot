import React, { useState } from 'react';
import { Send, FileText, ExternalLink } from 'lucide-react';
import { qaAPI } from '../api/api';
import ReactMarkdown from 'react-markdown';

// QATutor: Component for submitting questions and displaying answers with citations
function QATutor() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [history, setHistory] = useState([]);

  const handleAsk = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    try {
      const result = await qaAPI.askQuestion(question);
      setResponse(result);
      setHistory([{ question, response: result }, ...history]);
      setQuestion('');
    } catch (error) {
      console.error('Error asking question:', error);
      alert('Failed to get answer. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const renderCitations = (citations) => {
    if (!citations || citations.length === 0) return null;

    return (
      <div style={{ marginTop: '1.5rem' }}>
        <h4 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FileText size={16} />
          Citations & References
        </h4>
        <div style={{ display: 'grid', gap: '0.75rem' }}>
          {citations.map((citation, index) => (
            <div key={index} className="card" style={{ padding: '1rem', backgroundColor: '#f9fafb' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.5rem' }}>
                <strong style={{ color: '#2563eb' }}>{citation.source}</strong>
                {citation.url && (
                  <a href={citation.url} target="_blank" rel="noopener noreferrer" style={{ color: '#2563eb', textDecoration: 'none' }}>
                    <ExternalLink size={16} />
                  </a>
                )}
              </div>
              <p style={{ fontSize: '0.875rem', color: '#4b5563', marginBottom: '0.5rem' }}>
                {citation.content}
              </p>
              <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem', color: '#6b7280' }}>
                {citation.page && <span>Page {citation.page}</span>}
                {/*<span>Confidence: {(citation.confidence * 100).toFixed(0)}%</span>*/}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      <h2 style={{ fontSize: '1.875rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
        Q&A Tutor Agent
      </h2>
      <p style={{ color: '#6b7280', marginBottom: '1.5rem' }}>
        Ask any question about network security and get detailed answers with citations
      </p>

      {/* Question Input */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <form onSubmit={handleAsk}>
          <textarea
            className="textarea"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about network security... (e.g., 'What is a firewall?', 'Explain DDoS attacks')"
            rows={4}
            style={{ marginBottom: '1rem' }}
          />
          
          <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
            <button type="submit" className="btn btn-primary" disabled={loading || !question.trim()}>
              {loading ? (
                <>
                  <div className="loading" />
                  Asking...
                </>
              ) : (
                <>
                  <Send size={16} />
                  Ask Question
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Current Response */}
      {response && (
        <div className="card" style={{ marginBottom: '2rem', borderLeft: '4px solid #2563eb' }}>
          <div style={{ marginBottom: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#2563eb' }}>
              Answer
            </h3>
            <span className="badge badge-info">
              {/*Confidence: {(response.confidence_score * 100).toFixed(0)}%*/}
            </span>
          </div>
          
          <div style={{ 
            padding: '1rem', 
            backgroundColor: '#f9fafb', 
            borderRadius: '0.375rem',
            marginBottom: '1rem'
          }}>
            <ReactMarkdown>{response.answer}</ReactMarkdown>
          </div>

          {renderCitations(response.citations)}
        </div>
      )}

      {/* History */}
      {history.length > 0 && (
        <div>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1rem' }}>
            Recent Questions
          </h3>
          <div style={{ display: 'grid', gap: '1rem' }}>
            {history.slice(0, 5).map((item, index) => (
              <div key={index} className="card" style={{ opacity: 0.8 }}>
                <p style={{ fontWeight: '600', marginBottom: '0.5rem', color: '#1f2937' }}>
                  Q: {item.question}
                </p>
                <p style={{ fontSize: '0.875rem', color: '#6b7280', whiteSpace: 'pre-wrap' }}>
                  A: {item.response.answer.substring(0, 200)}...
                </p>
                <p style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.5rem' }}>
                  {item.response.citations.length} citation(s) • {new Date(item.response.timestamp).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default QATutor;
