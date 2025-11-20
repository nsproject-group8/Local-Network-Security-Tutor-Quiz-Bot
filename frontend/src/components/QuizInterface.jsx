import React, { useState } from 'react';
import { Play, CheckCircle, XCircle, Award, RotateCcw } from 'lucide-react';
import { quizAPI } from '../api/api';

function QuizInterface() {
  const [quizConfig, setQuizConfig] = useState({
    mode: 'random',
    topic: '',
    numQuestions: 5,
    questionTypes: ['multiple_choice', 'true_false', 'open_ended'],
  });
  
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [grading, setGrading] = useState(null);
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState('config'); // config, quiz, results

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const result = await quizAPI.generateQuiz(
        quizConfig.mode,
        quizConfig.topic || null,
        quizConfig.numQuestions,
        quizConfig.questionTypes
      );
      setQuiz(result);
      setAnswers({});
      setGrading(null);
      setCurrentStep('quiz');
    } catch (error) {
      console.error('Error generating quiz:', error);
      alert('Failed to generate quiz. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!quiz) return;
    
    // Validate all questions answered
    const unanswered = quiz.questions.filter(q => !answers[q.id]);
    if (unanswered.length > 0) {
      alert(`Please answer all questions. ${unanswered.length} question(s) remaining.`);
      return;
    }

    setLoading(true);
    try {
      const submissions = quiz.questions.map(q => ({
        quiz_id: quiz.quiz_id,
        question_id: q.id,
        user_answer: answers[q.id],
      }));
      
      const result = await quizAPI.gradeQuiz(quiz.quiz_id, submissions);
      setGrading(result);
      setCurrentStep('results');
    } catch (error) {
      console.error('Error grading quiz:', error);
      alert('Failed to grade quiz. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setQuiz(null);
    setAnswers({});
    setGrading(null);
    setCurrentStep('config');
  };

  const renderQuestionTypes = () => (
    <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
      {[
        { value: 'multiple_choice', label: 'Multiple Choice' },
        { value: 'true_false', label: 'True/False' },
        { value: 'open_ended', label: 'Open-Ended' },
      ].map(type => (
        <label key={type.value} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={quizConfig.questionTypes.includes(type.value)}
            onChange={(e) => {
              if (e.target.checked) {
                setQuizConfig({
                  ...quizConfig,
                  questionTypes: [...quizConfig.questionTypes, type.value]
                });
              } else {
                setQuizConfig({
                  ...quizConfig,
                  questionTypes: quizConfig.questionTypes.filter(t => t !== type.value)
                });
              }
            }}
          />
          {type.label}
        </label>
      ))}
    </div>
  );

  const renderQuestion = (question, index) => {
    const isAnswered = !!answers[question.id];
    
    return (
      <div key={question.id} className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.5rem' }}>
            <span className="badge badge-info">Question {index + 1}</span>
            <span className="badge" style={{ backgroundColor: '#f3f4f6', color: '#4b5563' }}>
              {question.type.replace('_', ' ').toUpperCase()}
            </span>
          </div>
          <h4 style={{ fontSize: '1.125rem', fontWeight: '600', marginTop: '0.75rem' }}>
            {question.question}
          </h4>
        </div>

        {question.type === 'multiple_choice' && (
          <div style={{ display: 'grid', gap: '0.75rem' }}>
            {question.options.map((option, idx) => (
              <label
                key={idx}
                style={{
                  padding: '0.75rem',
                  border: '2px solid',
                  borderColor: answers[question.id] === option ? '#2563eb' : '#e5e7eb',
                  borderRadius: '0.375rem',
                  cursor: 'pointer',
                  backgroundColor: answers[question.id] === option ? '#eff6ff' : 'white',
                  transition: 'all 0.2s'
                }}
              >
                <input
                  type="radio"
                  name={question.id}
                  value={option}
                  checked={answers[question.id] === option}
                  onChange={(e) => setAnswers({ ...answers, [question.id]: e.target.value })}
                  style={{ marginRight: '0.5rem' }}
                />
                {option}
              </label>
            ))}
          </div>
        )}

        {question.type === 'true_false' && (
          <div style={{ display: 'flex', gap: '1rem' }}>
            {['True', 'False'].map((option) => (
              <label
                key={option}
                style={{
                  flex: 1,
                  padding: '0.75rem',
                  border: '2px solid',
                  borderColor: answers[question.id] === option ? '#2563eb' : '#e5e7eb',
                  borderRadius: '0.375rem',
                  cursor: 'pointer',
                  backgroundColor: answers[question.id] === option ? '#eff6ff' : 'white',
                  textAlign: 'center',
                  fontWeight: '600',
                  transition: 'all 0.2s'
                }}
              >
                <input
                  type="radio"
                  name={question.id}
                  value={option}
                  checked={answers[question.id] === option}
                  onChange={(e) => setAnswers({ ...answers, [question.id]: e.target.value })}
                  style={{ marginRight: '0.5rem' }}
                />
                {option}
              </label>
            ))}
          </div>
        )}

        {question.type === 'open_ended' && (
          <textarea
            className="textarea"
            value={answers[question.id] || ''}
            onChange={(e) => setAnswers({ ...answers, [question.id]: e.target.value })}
            placeholder="Type your answer here..."
            rows={4}
          />
        )}
      </div>
    );
  };

  const renderResults = () => {
    if (!grading) return null;

    const getGradeColor = (grade) => {
      switch(grade) {
        case 'A': return '#10b981';
        case 'B': return '#3b82f6';
        case 'C': return '#f59e0b';
        case 'D': return '#f97316';
        case 'F': return '#ef4444';
        default: return '#6b7280';
      }
    };

    return (
      <div>
        {/* Overall Score */}
        <div className="card" style={{ 
          marginBottom: '2rem', 
          textAlign: 'center',
          background: `linear-gradient(135deg, ${getGradeColor(grading.grade)}20, white)`
        }}>
          <Award size={48} color={getGradeColor(grading.grade)} style={{ margin: '0 auto 1rem' }} />
          <h2 style={{ fontSize: '3rem', fontWeight: 'bold', color: getGradeColor(grading.grade), marginBottom: '0.5rem' }}>
            {grading.grade}
          </h2>
          <p style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>
            {grading.score_percentage.toFixed(1)}%
          </p>
          <p style={{ color: '#6b7280' }}>
            {grading.correct_answers} out of {grading.total_questions} correct
          </p>
        </div>

        {/* Individual Feedback */}
        <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1rem' }}>
          Detailed Feedback
        </h3>
        <div style={{ display: 'grid', gap: '1.5rem' }}>
          {grading.feedback.map((fb, index) => (
            <div key={fb.question_id} className="card" style={{
              borderLeft: `4px solid ${fb.is_correct ? '#10b981' : '#ef4444'}`
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem' }}>
                <h4 style={{ fontSize: '1rem', fontWeight: '600' }}>
                  Question {index + 1}
                </h4>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  {fb.is_correct ? (
                    <CheckCircle size={20} color="#10b981" />
                  ) : (
                    <XCircle size={20} color="#ef4444" />
                  )}
                  <span className={`badge ${fb.is_correct ? 'badge-success' : 'badge-danger'}`}>
                    Grade: {fb.grade}
                  </span>
                </div>
              </div>

              {/* Display the question */}
              <div style={{ 
                marginBottom: '1rem', 
                padding: '0.75rem', 
                backgroundColor: '#f0f9ff', 
                borderRadius: '0.375rem',
                border: '1px solid #bfdbfe'
              }}>
                <strong style={{ color: '#1e40af' }}>Question:</strong>
                <p style={{ marginTop: '0.5rem', color: '#1e3a8a' }}>
                  {fb.question}
                </p>
              </div>

              <div style={{ marginBottom: '0.75rem' }}>
                <strong style={{ color: '#4b5563' }}>Your Answer:</strong>
                <p style={{ marginTop: '0.25rem', padding: '0.5rem', backgroundColor: '#f9fafb', borderRadius: '0.25rem' }}>
                  {fb.user_answer}
                </p>
              </div>

              {!fb.is_correct && (
                <div style={{ marginBottom: '0.75rem' }}>
                  <strong style={{ color: '#4b5563' }}>Correct Answer:</strong>
                  <p style={{ marginTop: '0.25rem', padding: '0.5rem', backgroundColor: '#d1fae5', borderRadius: '0.25rem' }}>
                    {fb.correct_answer}
                  </p>
                </div>
              )}

              {fb.similarity_score !== null && (
                <div style={{ marginBottom: '0.75rem' }}>
                  <strong style={{ color: '#4b5563' }}>Similarity Score:</strong>
                  <div style={{ marginTop: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div style={{ 
                      flex: 1, 
                      height: '8px', 
                      backgroundColor: '#e5e7eb', 
                      borderRadius: '4px',
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        height: '100%',
                        width: `${(fb.similarity_score * 100)}%`,
                        backgroundColor: getGradeColor(fb.grade),
                        transition: 'width 0.3s'
                      }} />
                    </div>
                    <span style={{ fontSize: '0.875rem', fontWeight: '600' }}>
                      {(fb.similarity_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              )}

              <div style={{ 
                padding: '0.75rem', 
                backgroundColor: '#fffbeb', 
                borderRadius: '0.375rem',
                border: '1px solid #fef3c7'
              }}>
                <strong style={{ color: '#92400e' }}>Feedback:</strong>
                <p style={{ marginTop: '0.25rem', color: '#78350f' }}>{fb.feedback}</p>
              </div>

              {fb.citations && fb.citations.length > 0 && (
                <div style={{ marginTop: '0.75rem', fontSize: '0.875rem' }}>
                  <strong>References:</strong> {fb.citations.map(c => c.source).join(', ')}
                </div>
              )}
            </div>
          ))}
        </div>

        <div style={{ marginTop: '2rem', textAlign: 'center' }}>
          <button onClick={handleReset} className="btn btn-primary">
            <RotateCcw size={16} />
            Take Another Quiz
          </button>
        </div>
      </div>
    );
  };

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      <h2 style={{ fontSize: '1.875rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
        Quiz Agent
      </h2>
      <p style={{ color: '#6b7280', marginBottom: '1.5rem' }}>
        Test your knowledge with AI-generated quizzes
      </p>

      {currentStep === 'config' && (
        <div className="card">
          <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1rem' }}>
            Quiz Configuration
          </h3>

          <div style={{ display: 'grid', gap: '1.5rem' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600' }}>
                Quiz Mode
              </label>
              <select
                className="input"
                value={quizConfig.mode}
                onChange={(e) => setQuizConfig({ ...quizConfig, mode: e.target.value })}
              >
                <option value="random">Random Questions</option>
                <option value="topic_specific">Topic Specific</option>
              </select>
            </div>

            {quizConfig.mode === 'topic_specific' && (
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600' }}>
                  Topic
                </label>
                <input
                  type="text"
                  className="input"
                  value={quizConfig.topic}
                  onChange={(e) => setQuizConfig({ ...quizConfig, topic: e.target.value })}
                  placeholder="e.g., Firewalls, Encryption, VPN"
                />
              </div>
            )}

            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600' }}>
                Number of Questions: {quizConfig.numQuestions}
              </label>
              <input
                type="range"
                min="3"
                max="15"
                value={quizConfig.numQuestions}
                onChange={(e) => setQuizConfig({ ...quizConfig, numQuestions: parseInt(e.target.value) })}
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600' }}>
                Question Types
              </label>
              {renderQuestionTypes()}
            </div>

            <button
              onClick={handleGenerate}
              className="btn btn-primary"
              disabled={loading || quizConfig.questionTypes.length === 0}
              style={{ width: '100%', justifyContent: 'center', padding: '0.75rem' }}
            >
              {loading ? (
                <>
                  <div className="loading" />
                  Generating Quiz...
                </>
              ) : (
                <>
                  <Play size={20} />
                  Generate Quiz
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {currentStep === 'quiz' && quiz && (
        <div>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            marginBottom: '1.5rem',
            padding: '1rem',
            backgroundColor: 'white',
            borderRadius: '0.5rem',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
          }}>
            <div>
              <p style={{ fontSize: '0.875rem', color: '#6b7280' }}>Progress</p>
              <p style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>
                {Object.keys(answers).length} / {quiz.questions.length}
              </p>
            </div>
            <button
              onClick={handleSubmit}
              className="btn btn-success"
              disabled={loading}
            >
              {loading ? (
                <>
                  <div className="loading" />
                  Grading...
                </>
              ) : (
                'Submit Quiz'
              )}
            </button>
          </div>

          {quiz.questions.map((q, idx) => renderQuestion(q, idx))}
        </div>
      )}

      {currentStep === 'results' && renderResults()}
    </div>
  );
}

export default QuizInterface;
