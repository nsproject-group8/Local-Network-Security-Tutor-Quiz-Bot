import React, { useState } from 'react';
import { MessageSquare, BookOpen, Upload, Home } from 'lucide-react';
import QATutor from './components/QATutor';
import QuizInterface from './components/QuizInterface';
import DocumentUpload from './components/DocumentUpload';
import Dashboard from './components/Dashboard';
import './index.css';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const tabs = [
    { id: 'dashboard', name: 'Dashboard', icon: Home },
    { id: 'qa', name: 'Q&A Tutor', icon: MessageSquare },
    { id: 'quiz', name: 'Quiz', icon: BookOpen },
    { id: 'upload', name: 'Documents', icon: Upload },
  ];

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <header style={{
        backgroundColor: '#1f2937',
        color: 'white',
        padding: '1rem 0',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <div className="container">
          <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
            Network Security Tutor & Quiz Bot
          </h1>
          <p style={{ fontSize: '0.875rem', color: '#9ca3af' }}>
            Privacy-Preserving AI-Powered Learning Assistant
          </p>
        </div>
      </header>

      {/* Navigation */}
      <nav style={{
        backgroundColor: 'white',
        borderBottom: '1px solid #e5e7eb',
        padding: '0.5rem 0'
      }}>
        <div className="container">
          <div style={{ display: 'flex', gap: '1rem' }}>
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  style={{
                    padding: '0.75rem 1.5rem',
                    borderRadius: '0.375rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    backgroundColor: activeTab === tab.id ? '#2563eb' : 'transparent',
                    color: activeTab === tab.id ? 'white' : '#4b5563',
                    fontWeight: activeTab === tab.id ? '600' : '400',
                    transition: 'all 0.2s'
                  }}
                >
                  <Icon size={20} />
                  {tab.name}
                </button>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main style={{ flex: 1, padding: '2rem 0' }}>
        <div className="container">
          {activeTab === 'dashboard' && <Dashboard />}
          {activeTab === 'qa' && <QATutor />}
          {activeTab === 'quiz' && <QuizInterface />}
          {activeTab === 'upload' && <DocumentUpload />}
        </div>
      </main>

      {/* Footer */}
      <footer style={{
        backgroundColor: '#f3f4f6',
        padding: '1.5rem 0',
        borderTop: '1px solid #e5e7eb',
        marginTop: 'auto'
      }}>
        <div className="container">
          <p style={{ textAlign: 'center', color: '#6b7280', fontSize: '0.875rem' }}>
            🔒 All data is processed locally - Your privacy is protected
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
