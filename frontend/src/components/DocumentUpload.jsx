import React, { useState, useEffect } from 'react';
import { Upload, File, CheckCircle, XCircle, FolderOpen, Trash2 } from 'lucide-react';
import { documentAPI } from '../api/api';

function DocumentUpload() {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [docCount, setDocCount] = useState(0);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    loadDocumentCount();
  }, []);

  const loadDocumentCount = async () => {
    try {
      const result = await documentAPI.getDocumentCount();
      setDocCount(result.total_documents);
    } catch (error) {
      console.error('Error loading document count:', error);
    }
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.openxmlformats-officedocument.presentationml.presentation',
      'text/plain',
      'text/markdown'
    ];
    
    const validFiles = [];
    const invalidFiles = [];

    files.forEach(file => {
      if (allowedTypes.includes(file.type) || 
          file.name.endsWith('.md') || 
          file.name.endsWith('.txt')) {
        validFiles.push(file);
      } else {
        invalidFiles.push(file.name);
      }
    });

    if (invalidFiles.length > 0) {
      setMessage({ 
        type: 'error', 
        text: `Unsupported file type(s): ${invalidFiles.join(', ')}. Please upload PDF, DOCX, PPTX, TXT, or MD files.` 
      });
    }

    if (validFiles.length > 0) {
      setSelectedFiles(prevFiles => [...prevFiles, ...validFiles]);
      setMessage(null);
    }
  };

  const removeFile = (index) => {
    setSelectedFiles(prevFiles => prevFiles.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;

    setUploading(true);
    setMessage(null);

    const results = [];
    const errors = [];
    let totalChunks = 0;

    for (let i = 0; i < selectedFiles.length; i++) {
      const file = selectedFiles[i];
      try {
        const result = await documentAPI.uploadDocument(file, (progress) => {
          setUploadProgress(prev => ({
            ...prev,
            [file.name]: progress
          }));
        });

        results.push(result);
        totalChunks += result.chunks_indexed;
      } catch (error) {
        console.error(`Error uploading ${file.name}:`, error);
        errors.push(file.name);
      }
    }

    if (errors.length > 0) {
      setMessage({ 
        type: 'error', 
        text: `Failed to upload ${errors.length} file(s): ${errors.join(', ')}` 
      });
    } else {
      setMessage({ 
        type: 'success', 
        text: `Successfully uploaded ${selectedFiles.length} file(s) with ${totalChunks} total chunks indexed` 
      });
    }

    setSelectedFiles([]);
    setUploadProgress({});
    loadDocumentCount();
    setUploading(false);
  };

  const handleIngestDirectory = async () => {
    if (!confirm('This will ingest all documents from the default documents directory. Continue?')) {
      return;
    }

    setUploading(true);
    setMessage(null);

    try {
      const result = await documentAPI.ingestDirectory();
      setMessage({ 
        type: 'success', 
        text: `Successfully indexed ${result.chunks_indexed} chunks from ${result.directory}. Total documents: ${result.total_documents}` 
      });
      loadDocumentCount();
    } catch (error) {
      console.error('Error ingesting directory:', error);
      setMessage({ type: 'error', text: 'Failed to ingest directory. Please try again.' });
    } finally {
      setUploading(false);
    }
  };

  const handleClearDocuments = async () => {
    if (!confirm('This will delete ALL indexed documents. Are you sure? This action cannot be undone.')) {
      return;
    }

    try {
      await documentAPI.clearDocuments();
      setMessage({ type: 'success', text: 'All documents cleared successfully.' });
      setDocCount(0);
    } catch (error) {
      console.error('Error clearing documents:', error);
      setMessage({ type: 'error', text: 'Failed to clear documents. Please try again.' });
    }
  };

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      <h2 style={{ fontSize: '1.875rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
        Document Management
      </h2>
      <p style={{ color: '#6b7280', marginBottom: '1.5rem' }}>
        Upload network security materials to train the bot
      </p>

      {/* Status */}
      <div className="card" style={{ marginBottom: '1.5rem', backgroundColor: '#eff6ff', borderColor: '#bfdbfe' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <File size={32} color="#2563eb" />
          <div>
            <p style={{ fontSize: '0.875rem', color: '#1e40af', marginBottom: '0.25rem' }}>
              Documents Indexed
            </p>
            <p style={{ fontSize: '2rem', fontWeight: 'bold', color: '#1e3a8a' }}>
              {docCount}
            </p>
          </div>
        </div>
      </div>

      {/* Messages */}
      {message && (
        <div className={`alert alert-${message.type === 'success' ? 'success' : 'error'}`} style={{ marginBottom: '1.5rem' }}>
          {message.text}
        </div>
      )}

      {/* File Upload */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Upload size={20} />
          Upload Documents
        </h3>

        <div style={{ 
          border: '2px dashed #e5e7eb', 
          borderRadius: '0.5rem', 
          padding: '2rem',
          textAlign: 'center',
          marginBottom: '1rem',
          backgroundColor: '#f9fafb'
        }}>
          <input
            type="file"
            id="file-upload"
            onChange={handleFileSelect}
            accept=".pdf,.docx,.pptx,.txt,.md"
            multiple
            style={{ display: 'none' }}
          />
          <label
            htmlFor="file-upload"
            style={{
              cursor: 'pointer',
              display: 'inline-flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            <Upload size={48} color="#6b7280" />
            <span style={{ color: '#2563eb', fontWeight: '600' }}>
              Choose file(s)
            </span>
            <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>
              PDF, DOCX, PPTX, TXT, or MD • Select multiple files (max 50MB each)
            </span>
          </label>
        </div>

        {selectedFiles.length > 0 && (
          <div style={{ marginBottom: '1rem' }}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              marginBottom: '0.5rem'
            }}>
              <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#374151' }}>
                {selectedFiles.length} file(s) selected
              </span>
              <button
                onClick={() => setSelectedFiles([])}
                style={{ 
                  fontSize: '0.875rem', 
                  color: '#ef4444',
                  padding: '0.25rem 0.5rem',
                  textDecoration: 'underline'
                }}
              >
                Clear all
              </button>
            </div>
            <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
              {selectedFiles.map((file, index) => (
                <div 
                  key={index}
                  style={{ 
                    padding: '0.75rem', 
                    backgroundColor: '#f3f4f6', 
                    borderRadius: '0.375rem',
                    marginBottom: '0.5rem',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1 }}>
                    <File size={18} />
                    <span style={{ fontWeight: '600', fontSize: '0.875rem' }}>{file.name}</span>
                    <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                      ({(file.size / 1024 / 1024).toFixed(2)} MB)
                    </span>
                  </div>
                  {uploading && uploadProgress[file.name] !== undefined && (
                    <div style={{ 
                      width: '100px', 
                      height: '4px', 
                      backgroundColor: '#e5e7eb',
                      borderRadius: '2px',
                      marginRight: '0.5rem',
                      overflow: 'hidden'
                    }}>
                      <div style={{ 
                        width: `${uploadProgress[file.name]}%`, 
                        height: '100%',
                        backgroundColor: '#2563eb',
                        transition: 'width 0.3s'
                      }} />
                    </div>
                  )}
                  <button
                    onClick={() => removeFile(index)}
                    disabled={uploading}
                    style={{ padding: '0.25rem', color: '#ef4444', opacity: uploading ? 0.5 : 1 }}
                  >
                    <XCircle size={18} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {uploading && selectedFiles.length > 0 && (
          <div style={{ marginBottom: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>Uploading files...</span>
              <span style={{ fontSize: '0.875rem', fontWeight: '600' }}>
                {Object.keys(uploadProgress).length} / {selectedFiles.length}
              </span>
            </div>
          </div>
        )}

        <button
          onClick={handleUpload}
          className="btn btn-primary"
          disabled={selectedFiles.length === 0 || uploading}
          style={{ width: '100%', justifyContent: 'center' }}
        >
          {uploading ? (
            <>
              <div className="loading" />
              Uploading {selectedFiles.length} file(s)...
            </>
          ) : (
            <>
              <Upload size={16} />
              Upload and Index {selectedFiles.length > 0 ? `${selectedFiles.length} Document(s)` : 'Documents'}
            </>
          )}
        </button>
      </div>

      {/* Batch Operations */}
      <div className="card">
        <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1rem' }}>
          Batch Operations
        </h3>

        <div style={{ display: 'grid', gap: '1rem' }}>
          <div>
            <h4 style={{ fontWeight: '600', marginBottom: '0.5rem' }}>
              Ingest Directory
            </h4>
            <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.75rem' }}>
              Process all documents from the default documents directory (./data/documents)
            </p>
            <button
              onClick={handleIngestDirectory}
              className="btn btn-secondary"
              disabled={uploading}
              style={{ width: '100%', justifyContent: 'center' }}
            >
              <FolderOpen size={16} />
              Ingest Directory
            </button>
          </div>

          <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: '1rem' }}>
            <h4 style={{ fontWeight: '600', marginBottom: '0.5rem', color: '#ef4444' }}>
              Clear All Documents
            </h4>
            <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.75rem' }}>
              Remove all indexed documents from the database. This action cannot be undone.
            </p>
            <button
              onClick={handleClearDocuments}
              className="btn btn-danger"
              disabled={docCount === 0}
              style={{ width: '100%', justifyContent: 'center' }}
            >
              <Trash2 size={16} />
              Clear All Documents
            </button>
          </div>
        </div>
      </div>

      {/* Supported Formats Info */}
      <div className="card" style={{ marginTop: '1.5rem', backgroundColor: '#f9fafb' }}>
        <h4 style={{ fontWeight: '600', marginBottom: '0.75rem' }}>
          Supported Document Formats
        </h4>
        <ul style={{ paddingLeft: '1.5rem', display: 'grid', gap: '0.5rem', color: '#4b5563', fontSize: '0.875rem' }}>
          <li><strong>PDF</strong> - Portable Document Format (lecture slides, textbooks)</li>
          <li><strong>DOCX</strong> - Microsoft Word documents</li>
          <li><strong>PPTX</strong> - Microsoft PowerPoint presentations</li>
          <li><strong>TXT</strong> - Plain text files</li>
          <li><strong>MD</strong> - Markdown files</li>
        </ul>
      </div>
    </div>
  );
}

export default DocumentUpload;
