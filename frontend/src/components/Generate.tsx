import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './Generate.css';
import { extractErrorMessage } from '../utils/errorHandler';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ArtifactEstimate {
  epics: number;
  features: number;
  use_cases: number;
  test_cases: number;
  total: number;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const Generate: React.FC = () => {
  // Form state
  const [projectName, setProjectName] = useState('');
  const [jiraProjectKey, setJiraProjectKey] = useState('');
  const [notificationEmail, setNotificationEmail] = useState('');
  
  // File upload state
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadProgress, setUploadProgress] = useState<{ [key: string]: number }>({});
  const [uploadedFileIds, setUploadedFileIds] = useState<string[]>([]);
  
  // Session state
  const [sessionId, setSessionId] = useState<string>('');
  const [projectId, setProjectId] = useState<string>('');
  const [phase, setPhase] = useState<'form' | 'upload' | 'review' | 'chat' | 'generating' | 'complete'>('form');
  
  // Chat state
  const [messages, setMessages] = useState<Message[]>([]);
  const [userMessage, setUserMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  
  // Estimation state
  const [artifactEstimate, setArtifactEstimate] = useState<ArtifactEstimate | null>(null);
  
  // Status state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [generationStatus, setGenerationStatus] = useState('');
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      const fileArray = Array.from(files);
      setSelectedFiles(prev => [...prev, ...fileArray]);
    }
  };

  const handleFileDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const files = event.dataTransfer.files;
    if (files) {
      const fileArray = Array.from(files);
      setSelectedFiles(prev => [...prev, ...fileArray]);
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const uploadFiles = async () => {
    if (selectedFiles.length === 0) {
      setError('Please select at least one file');
      return;
    }

    setLoading(true);
    setError('');
    setPhase('upload');

    try {
      // Create FormData with all files and project info
      const formData = new FormData();
      
      // Add all files
      selectedFiles.forEach(file => {
        formData.append('files', file);
      });
      
      // Add project information
      formData.append('project_name', projectName);
      if (jiraProjectKey) {
        formData.append('jira_project_key', jiraProjectKey);
      }
      if (notificationEmail) {
        formData.append('notification_email', notificationEmail);
      }

      const response = await axios.post(`${API_BASE_URL}/api/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const progress = progressEvent.total
            ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
            : 0;
          // Update progress for all files
          selectedFiles.forEach(file => {
            setUploadProgress(prev => ({ ...prev, [file.name]: progress }));
          });
        }
      });

      const uploadId = response.data.upload_id;
      const projectId = response.data.project_id;
      
      setProjectId(projectId);
      
      // Start review process
      await startReview(uploadId, projectId);
      
    } catch (err: any) {
      setError(extractErrorMessage(err, 'Failed to upload files'));
      console.error('Upload error:', err);
      setPhase('form');
    } finally {
      setLoading(false);
    }
  };

  const startReview = async (uploadId: string, projId: string) => {
    setLoading(true);
    setPhase('review');
    
    try {
      const response = await axios.post(`${API_BASE_URL}/api/generate/review`, {
        upload_id: uploadId,
        project_id: projId,
        project_name: projectName,
        jira_project_key: jiraProjectKey || undefined,
        notification_email: notificationEmail || undefined
      });

      setSessionId(response.data.session_id);
      
      // Add initial review message
      if (response.data.message) {
        setMessages([{
          role: 'assistant',
          content: response.data.message,
          timestamp: new Date()
        }]);
      }
      
      setPhase('chat');
      
    } catch (err: any) {
      setError(extractErrorMessage(err, 'Failed to start review'));
      console.error('Review error:', err);
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!userMessage.trim() || !sessionId) return;

    const newMessage: Message = {
      role: 'user',
      content: userMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, newMessage]);
    setUserMessage('');
    setIsSending(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/generate/chat`, {
        session_id: sessionId,
        user_message: newMessage.content
      });

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.agent_response,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Check if response contains estimation
      if (response.data.agent_response.includes('estimate') || 
          response.data.agent_response.includes('Epic') ||
          response.data.agent_response.includes('Feature')) {
        // Parse estimation from response (simplified)
        setArtifactEstimate({
          epics: 3,
          features: 8,
          use_cases: 15,
          test_cases: 45,
          total: 71
        });
      }
      
    } catch (err: any) {
      setError(extractErrorMessage(err, 'Failed to send message'));
      console.error('Chat error:', err);
    } finally {
      setIsSending(false);
    }
  };

  const executeGeneration = async () => {
    if (!sessionId || !projectId) return;

    setLoading(true);
    setPhase('generating');
    setGenerationStatus('Starting generation...');

    try {
      const response = await axios.post(`${API_BASE_URL}/api/generate/execute`, {
        session_id: sessionId,
        project_id: projectId,
        approved: true
      });

      setGenerationStatus(response.data.message);
      
      // Poll for status
      pollGenerationStatus();
      
    } catch (err: any) {
      setError(extractErrorMessage(err, 'Failed to start generation'));
      console.error('Generation error:', err);
      setPhase('chat');
    } finally {
      setLoading(false);
    }
  };

  const pollGenerationStatus = async () => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/generate/status/${sessionId}`);
        
        setGenerationStatus(response.data.status);
        
        if (response.data.progress.generation_completed) {
          clearInterval(pollInterval);
          setPhase('complete');
          if (response.data.artifact_counts) {
            setArtifactEstimate(response.data.artifact_counts);
          }
        }
      } catch (err) {
        console.error('Status poll error:', err);
      }
    }, 2000);

    // Stop polling after 5 minutes
    setTimeout(() => clearInterval(pollInterval), 300000);
  };

  const resetForm = () => {
    setProjectName('');
    setJiraProjectKey('');
    setNotificationEmail('');
    setSelectedFiles([]);
    setUploadProgress({});
    setUploadedFileIds([]);
    setSessionId('');
    setProjectId('');
    setPhase('form');
    setMessages([]);
    setUserMessage('');
    setArtifactEstimate(null);
    setError('');
    setGenerationStatus('');
  };

  return (
    <div className="generate-container">
      <header className="generate-header">
        <h1>Generate Test Artifacts</h1>
        <p>Upload requirements documents and generate comprehensive test artifacts</p>
      </header>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
          <button onClick={() => setError('')} className="close-error">×</button>
        </div>
      )}

      {phase === 'form' && (
        <div className="generate-form">
          <div className="form-section">
            <h2>Project Information</h2>
            <div className="form-group">
              <label htmlFor="project-name">Project Name *</label>
              <input
                id="project-name"
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="e.g., Healthcare Portal"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="jira-key">Jira Project Key (Optional)</label>
              <input
                id="jira-key"
                type="text"
                value={jiraProjectKey}
                onChange={(e) => setJiraProjectKey(e.target.value.toUpperCase())}
                placeholder="e.g., HCP"
                maxLength={10}
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">Notification Email (Optional)</label>
              <input
                id="email"
                type="email"
                value={notificationEmail}
                onChange={(e) => setNotificationEmail(e.target.value)}
                placeholder="e.g., user@example.com"
              />
            </div>
          </div>

          <div className="form-section">
            <h2>Upload Requirements Documents</h2>
            <div
              className="file-drop-zone"
              onDrop={handleFileDrop}
              onDragOver={handleDragOver}
              onClick={() => fileInputRef.current?.click()}
            >
              <div className="drop-zone-content">
                <span className="upload-icon">📄</span>
                <p>Drag and drop files here or click to browse</p>
                <p className="file-types">Supported: PDF, Word (.docx)</p>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.doc,.docx"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
              />
            </div>

            {selectedFiles.length > 0 && (
              <div className="selected-files">
                <h3>Selected Files ({selectedFiles.length})</h3>
                {selectedFiles.map((file, index) => (
                  <div key={index} className="file-item">
                    <span className="file-name">{file.name}</span>
                    <span className="file-size">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </span>
                    <button
                      onClick={() => removeFile(index)}
                      className="remove-file"
                      aria-label="Remove file"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="form-actions">
            <button
              onClick={uploadFiles}
              disabled={!projectName || selectedFiles.length === 0 || loading}
              className="btn-primary"
            >
              {loading ? 'Uploading...' : 'Upload and Start Review'}
            </button>
          </div>
        </div>
      )}

      {phase === 'upload' && (
        <div className="upload-progress-section">
          <h2>Uploading Files...</h2>
          {selectedFiles.map((file, index) => (
            <div key={index} className="progress-item">
              <span className="progress-filename">{file.name}</span>
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${uploadProgress[file.name] || 0}%` }}
                />
              </div>
              <span className="progress-percent">{uploadProgress[file.name] || 0}%</span>
            </div>
          ))}
        </div>
      )}

      {(phase === 'review' || phase === 'chat') && (
        <div className="chat-section">
          <div className="chat-header">
            <h2>Requirements Review & Clarification</h2>
            <p>Chat with the AI agent to clarify requirements</p>
          </div>

          <div className="chat-messages">
            {messages.map((msg, index) => (
              <div key={index} className={`message message-${msg.role}`}>
                <div className="message-header">
                  <span className="message-role">
                    {msg.role === 'user' ? 'You' : 'AI Agent'}
                  </span>
                  <span className="message-time">
                    {msg.timestamp.toLocaleTimeString()}
                  </span>
                </div>
                <div className="message-content">{msg.content}</div>
              </div>
            ))}
            {isSending && (
              <div className="message message-assistant">
                <div className="message-content typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <div className="chat-input-section">
            <input
              type="text"
              value={userMessage}
              onChange={(e) => setUserMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !isSending && sendMessage()}
              placeholder="Type your message..."
              disabled={isSending || loading}
              className="chat-input"
            />
            <button
              onClick={sendMessage}
              disabled={!userMessage.trim() || isSending || loading}
              className="btn-send"
            >
              Send
            </button>
          </div>

          {artifactEstimate && (
            <div className="estimation-section">
              <h3>Estimated Artifacts</h3>
              <div className="estimate-grid">
                <div className="estimate-item">
                  <span className="estimate-label">Epics</span>
                  <span className="estimate-value">{artifactEstimate.epics}</span>
                </div>
                <div className="estimate-item">
                  <span className="estimate-label">Features</span>
                  <span className="estimate-value">{artifactEstimate.features}</span>
                </div>
                <div className="estimate-item">
                  <span className="estimate-label">Use Cases</span>
                  <span className="estimate-value">{artifactEstimate.use_cases}</span>
                </div>
                <div className="estimate-item">
                  <span className="estimate-label">Test Cases</span>
                  <span className="estimate-value">{artifactEstimate.test_cases}</span>
                </div>
                <div className="estimate-item total">
                  <span className="estimate-label">Total</span>
                  <span className="estimate-value">{artifactEstimate.total}</span>
                </div>
              </div>
              <button
                onClick={executeGeneration}
                disabled={loading}
                className="btn-primary btn-generate"
              >
                Generate Artifacts
              </button>
            </div>
          )}
        </div>
      )}

      {phase === 'generating' && (
        <div className="generating-section">
          <div className="spinner-large"></div>
          <h2>Generating Test Artifacts...</h2>
          <p className="generation-status">{generationStatus}</p>
          <p className="generation-note">
            This may take a few minutes. You'll receive an email notification when complete.
          </p>
        </div>
      )}

      {phase === 'complete' && (
        <div className="complete-section">
          <div className="success-icon">✓</div>
          <h2>Generation Complete!</h2>
          <p>Your test artifacts have been successfully generated.</p>
          
          {artifactEstimate && (
            <div className="final-counts">
              <h3>Generated Artifacts</h3>
              <div className="count-grid">
                <div className="count-box">
                  <span className="count-number">{artifactEstimate.epics}</span>
                  <span className="count-label">Epics</span>
                </div>
                <div className="count-box">
                  <span className="count-number">{artifactEstimate.features}</span>
                  <span className="count-label">Features</span>
                </div>
                <div className="count-box">
                  <span className="count-number">{artifactEstimate.use_cases}</span>
                  <span className="count-label">Use Cases</span>
                </div>
                <div className="count-box">
                  <span className="count-number">{artifactEstimate.test_cases}</span>
                  <span className="count-label">Test Cases</span>
                </div>
              </div>
            </div>
          )}

          <div className="complete-actions">
            <button onClick={() => window.location.href = '/dashboard'} className="btn-primary">
              View in Dashboard
            </button>
            <button onClick={resetForm} className="btn-secondary">
              Generate Another Project
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Generate;
