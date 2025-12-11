import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import '../styles/Generate.css';
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

interface ReadinessPlan {
  estimated_epics: number;
  estimated_features: number;
  estimated_use_cases: number;
  estimated_test_cases: number;
  overall_status: string;
}

interface ReviewResponse {
  readiness_plan?: ReadinessPlan;
  status?: string;
  next_action?: string;
  assistant_response?: string[];
  test_generation_status?: any;
}

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8002';

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
  const [readinessPlan, setReadinessPlan] = useState<ReadinessPlan | null>(null);
  const [reviewStatus, setReviewStatus] = useState<string>('');
  
  // Status state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [generationStatus, setGenerationStatus] = useState('');
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Generate session ID on component mount
  useEffect(() => {
    const newSessionId = generateSessionId();
    setSessionId(newSessionId);
    console.log('Generated session ID for Generate tab:', newSessionId);
  }, []);

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Generate unique session ID
  const generateSessionId = (): string => {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 15);
    const userAgent = navigator.userAgent;
    const hash = btoa(`${timestamp}-${random}-${userAgent}`).substring(0, 32);
    return `session_${hash}_${timestamp}`;
  };

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

    if (!sessionId) {
      setError('Session ID not initialized');
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
      
      // Add session ID
      formData.append('session_id', sessionId);
      
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
      
      // Start review process with session ID
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
        session_id: sessionId,
        upload_id: uploadId,
        project_id: projId,
        project_name: projectName,
        jira_project_key: jiraProjectKey || undefined,
        notification_email: notificationEmail || undefined
      });

      // Session ID should remain the same as frontend-generated one
      if (response.data.session_id !== sessionId) {
        console.warn('Backend returned different session ID, keeping frontend session ID');
      }
      
      // Parse the JSON response from agent
      let reviewData: ReviewResponse | null = null;
      if (response.data.message) {
        try {
          reviewData = JSON.parse(response.data.message);
        } catch (e) {
          console.error('Failed to parse review response as JSON:', e);
          // Fallback to plain text message
          setMessages([{
            role: 'assistant',
            content: response.data.message,
            timestamp: new Date()
          }]);
        }
      }
      
      if (reviewData) {
        // Extract readiness plan
        if (reviewData.readiness_plan) {
          setReadinessPlan(reviewData.readiness_plan);
          // Also set artifact estimate for consistency
          const plan = reviewData.readiness_plan;
          setArtifactEstimate({
            epics: plan.estimated_epics,
            features: plan.estimated_features,
            use_cases: plan.estimated_use_cases,
            test_cases: plan.estimated_test_cases,
            total: plan.estimated_epics + plan.estimated_features + 
                   plan.estimated_use_cases + plan.estimated_test_cases
          });
        }
        
        // Set review status
        if (reviewData.status) {
          setReviewStatus(reviewData.status);
        }
        
        // Add assistant responses as messages
        if (reviewData.assistant_response && Array.isArray(reviewData.assistant_response)) {
          const assistantMessages: Message[] = reviewData.assistant_response.map((msg, idx) => ({
            role: 'assistant',
            content: msg,
            timestamp: new Date(Date.now() + idx * 100) // Slight offset for ordering
          }));
          setMessages(assistantMessages);
        }
        
        // Enable chat if status is review_in_progress
        if (reviewData.status === 'review_in_progress') {
          setPhase('chat');
        } else {
          setPhase('review');
        }
      } else {
        setPhase('chat');
      }
      
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

      // Try to parse response as JSON
      let chatData: ReviewResponse | null = null;
      let responseText = response.data.agent_response;
      
      try {
        chatData = JSON.parse(responseText);
      } catch (e) {
        // Not JSON, use as plain text
        console.log('Chat response is plain text, not JSON');
      }
      
      if (chatData) {
        // Update readiness plan if present
        if (chatData.readiness_plan) {
          setReadinessPlan(chatData.readiness_plan);
          const plan = chatData.readiness_plan;
          setArtifactEstimate({
            epics: plan.estimated_epics,
            features: plan.estimated_features,
            use_cases: plan.estimated_use_cases,
            test_cases: plan.estimated_test_cases,
            total: plan.estimated_epics + plan.estimated_features + 
                   plan.estimated_use_cases + plan.estimated_test_cases
          });
        }
        
        // Update review status
        if (chatData.status) {
          setReviewStatus(chatData.status);
        }
        
        // Add assistant responses as separate messages
        if (chatData.assistant_response && Array.isArray(chatData.assistant_response)) {
          const assistantMessages: Message[] = chatData.assistant_response.map((msg, idx) => ({
            role: 'assistant',
            content: msg,
            timestamp: new Date(Date.now() + idx * 100)
          }));
          setMessages(prev => [...prev, ...assistantMessages]);
        } else {
          // Add single message
          const assistantMessage: Message = {
            role: 'assistant',
            content: responseText,
            timestamp: new Date()
          };
          setMessages(prev => [...prev, assistantMessage]);
        }
      } else {
        // Plain text response
        const assistantMessage: Message = {
          role: 'assistant',
          content: responseText,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, assistantMessage]);
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
        <h1 className="generate-title">✨ Generate Test Artifacts</h1>
        <p className="generate-subtitle">Upload requirements documents and generate comprehensive test artifacts</p>
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
            {reviewStatus && (
              <div className="review-status-badge">
                Status: {reviewStatus.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </div>
            )}
          </div>
          
          {readinessPlan && (
            <div className="readiness-plan">
              <h3>Readiness Plan</h3>
              <div className="estimate-grid">
                <div className="estimate-item">
                  <span className="estimate-label">Estimated Epics</span>
                  <span className="estimate-value">{readinessPlan.estimated_epics}</span>
                </div>
                <div className="estimate-item">
                  <span className="estimate-label">Estimated Features</span>
                  <span className="estimate-value">{readinessPlan.estimated_features}</span>
                </div>
                <div className="estimate-item">
                  <span className="estimate-label">Estimated Use Cases</span>
                  <span className="estimate-value">{readinessPlan.estimated_use_cases}</span>
                </div>
                <div className="estimate-item">
                  <span className="estimate-label">Estimated Test Cases</span>
                  <span className="estimate-value">{readinessPlan.estimated_test_cases}</span>
                </div>
                <div className="estimate-item total">
                  <span className="estimate-label">Overall Status</span>
                  <span className="estimate-value status-badge">{readinessPlan.overall_status}</span>
                </div>
              </div>
            </div>
          )}

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
              onKeyPress={(e) => e.key === 'Enter' && !isSending && phase === 'chat' && sendMessage()}
              placeholder={phase === 'chat' ? "Type your message..." : "Waiting for review to complete..."}
              disabled={isSending || loading || phase !== 'chat'}
              className="chat-input"
            />
            <button
              onClick={sendMessage}
              disabled={!userMessage.trim() || isSending || loading || phase !== 'chat'}
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
