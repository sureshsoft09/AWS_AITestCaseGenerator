import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/Enhance.css';
import { extractErrorMessage } from '../utils/errorHandler';

interface Project {
  project_id: string;
  project_name: string;
  jira_project_key?: string;
}

interface Artifact {
  id: string;
  type: string;
  name: string;
  description: string;
  priority: string;
  status: string;
  jira_key?: string;
  jira_url?: string;
  compliance_mapping: string[];
  children?: Artifact[];
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface Preview {
  original: any;
  modified: any;
  changes: string[];
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002';

const Enhance: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [selectedArtifact, setSelectedArtifact] = useState<Artifact | null>(null);
  const [filterType, setFilterType] = useState<string>('all');
  
  // Enhancement session state
  const [sessionId, setSessionId] = useState<string>('');
  const [showModal, setShowModal] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [userMessage, setUserMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [preview, setPreview] = useState<Preview | null>(null);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Fetch projects on mount
  useEffect(() => {
    fetchProjects();
  }, []);

  // Fetch artifacts when project is selected
  useEffect(() => {
    if (selectedProject) {
      fetchArtifacts(selectedProject);
    }
  }, [selectedProject]);

  const fetchProjects = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.get(`${API_BASE_URL}/api/projects`);
      setProjects(response.data.projects);
      
      if (response.data.projects.length > 0 && !selectedProject) {
        setSelectedProject(response.data.projects[0].project_id);
      }
    } catch (err: any) {
      setError(extractErrorMessage(err, 'Failed to load projects'));
      console.error('Error fetching projects:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchArtifacts = async (projectId: string) => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.get(`${API_BASE_URL}/api/projects/${projectId}/artifacts`);
      setArtifacts(response.data.artifacts);
    } catch (err: any) {
      setError(extractErrorMessage(err, 'Failed to load artifacts'));
      console.error('Error fetching artifacts:', err);
    } finally {
      setLoading(false);
    }
  };

  const flattenArtifacts = (artifacts: Artifact[]): Artifact[] => {
    const flattened: Artifact[] = [];
    
    const flatten = (artifact: Artifact) => {
      flattened.push(artifact);
      if (artifact.children) {
        artifact.children.forEach(flatten);
      }
    };
    
    artifacts.forEach(flatten);
    return flattened;
  };

  const getFilteredArtifacts = (): Artifact[] => {
    const flat = flattenArtifacts(artifacts);
    
    if (filterType === 'all') {
      return flat;
    }
    
    return flat.filter(a => a.type === filterType);
  };

  const canRefactor = (artifact: Artifact): boolean => {
    return artifact.type === 'use_case' || artifact.type === 'test_case';
  };

  const startEnhancement = async (artifact: Artifact) => {
    if (!canRefactor(artifact)) {
      setError('Enhancement only available for Use Cases and Test Cases');
      return;
    }

    setLoading(true);
    setError('');
    setSelectedArtifact(artifact);
    
    try {
      const response = await axios.post(`${API_BASE_URL}/api/enhance/start`, {
        artifact_id: artifact.id,
        artifact_type: artifact.type,
        project_id: selectedProject
      });

      setSessionId(response.data.session_id);
      setMessages([{
        role: 'assistant',
        content: `Enhancement session started for ${artifact.name}. How would you like to enhance this ${artifact.type.replace('_', ' ')}?`,
        timestamp: new Date()
      }]);
      setShowModal(true);
      
    } catch (err: any) {
      setError(extractErrorMessage(err, 'Failed to start enhancement'));
      console.error('Enhancement start error:', err);
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
      const response = await axios.post(`${API_BASE_URL}/api/enhance/chat`, {
        session_id: sessionId,
        enhancement_instructions: newMessage.content
      });

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.agent_response,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Update preview if available
      if (response.data.preview) {
        setPreview(response.data.preview);
      }
      
    } catch (err: any) {
      setError(extractErrorMessage(err, 'Failed to send message'));
      console.error('Chat error:', err);
    } finally {
      setIsSending(false);
    }
  };

  const applyEnhancement = async () => {
    if (!sessionId) return;

    setLoading(true);
    
    try {
      const response = await axios.post(`${API_BASE_URL}/api/enhance/apply`, {
        session_id: sessionId,
        approved: true
      });

      if (response.data.applied) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: 'Enhancement applied successfully! The artifact has been updated in Jira and DynamoDB.',
          timestamp: new Date()
        }]);
        
        // Refresh artifacts
        await fetchArtifacts(selectedProject);
        
        // Close modal after a delay
        setTimeout(() => {
          closeModal();
        }, 2000);
      }
      
    } catch (err: any) {
      setError(extractErrorMessage(err, 'Failed to apply enhancement'));
      console.error('Apply error:', err);
    } finally {
      setLoading(false);
    }
  };

  const closeModal = () => {
    setShowModal(false);
    setSessionId('');
    setMessages([]);
    setPreview(null);
    setSelectedArtifact(null);
  };

  const filteredArtifacts = getFilteredArtifacts();

  return (
    <div className="enhance-container">
      <header className="enhance-header">
        <h1>Enhance Artifacts</h1>
        <p>Refine and improve use cases and test cases with AI assistance</p>
      </header>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
          <button onClick={() => setError('')} className="close-error">×</button>
        </div>
      )}

      <div className="enhance-controls">
        <div className="project-selector">
          <label htmlFor="project-select">Select Project:</label>
          <select
            id="project-select"
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            disabled={loading || projects.length === 0}
          >
            <option value="">-- Select a project --</option>
            {projects.map(project => (
              <option key={project.project_id} value={project.project_id}>
                {project.project_name} {project.jira_project_key && `(${project.jira_project_key})`}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-selector">
          <label htmlFor="filter-select">Filter by Type:</label>
          <select
            id="filter-select"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            disabled={loading}
          >
            <option value="all">All Artifacts</option>
            <option value="epic">Epics</option>
            <option value="feature">Features</option>
            <option value="use_case">Use Cases</option>
            <option value="test_case">Test Cases</option>
          </select>
        </div>
      </div>

      {loading && !showModal && (
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading...</p>
        </div>
      )}

      {!loading && selectedProject && filteredArtifacts.length > 0 && (
        <div className="artifacts-list">
          <h2>Artifacts ({filteredArtifacts.length})</h2>
          <div className="artifacts-grid">
            {filteredArtifacts.map(artifact => (
              <div key={artifact.id} className={`artifact-card artifact-${artifact.type}`}>
                <div className="artifact-card-header">
                  <span className={`artifact-type-badge ${artifact.type}`}>
                    {artifact.type.replace('_', ' ').toUpperCase()}
                  </span>
                  {artifact.jira_key && (
                    <a
                      href={artifact.jira_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="jira-link"
                      title={`Open ${artifact.jira_key} in Jira`}
                    >
                      {artifact.jira_key}
                    </a>
                  )}
                </div>
                
                <h3 className="artifact-name">{artifact.name}</h3>
                
                <div className="artifact-meta">
                  <span className={`priority-badge ${artifact.priority.toLowerCase()}`}>
                    {artifact.priority}
                  </span>
                  <span className={`status-badge ${artifact.status.toLowerCase()}`}>
                    {artifact.status}
                  </span>
                </div>
                
                {artifact.description && (
                  <p className="artifact-description">{artifact.description}</p>
                )}
                
                {artifact.compliance_mapping.length > 0 && (
                  <div className="compliance-tags">
                    {artifact.compliance_mapping.slice(0, 3).map(tag => (
                      <span key={tag} className="compliance-tag">{tag}</span>
                    ))}
                    {artifact.compliance_mapping.length > 3 && (
                      <span className="compliance-tag">+{artifact.compliance_mapping.length - 3}</span>
                    )}
                  </div>
                )}
                
                {canRefactor(artifact) && (
                  <button
                    onClick={() => startEnhancement(artifact)}
                    className="btn-refactor"
                    disabled={loading}
                  >
                    Refactor
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {!loading && selectedProject && filteredArtifacts.length === 0 && !error && (
        <div className="empty-state">
          <p>No artifacts found for this project.</p>
        </div>
      )}

      {/* Enhancement Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && closeModal()}>
          <div className="modal-content">
            <div className="modal-header">
              <h2>Enhance: {selectedArtifact?.name}</h2>
              <button onClick={closeModal} className="modal-close">×</button>
            </div>

            <div className="modal-body">
              {selectedArtifact && (
                <div className="artifact-details">
                  <div className="detail-row">
                    <span className="detail-label">Type:</span>
                    <span className={`artifact-type-badge ${selectedArtifact.type}`}>
                      {selectedArtifact.type.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Priority:</span>
                    <span className={`priority-badge ${selectedArtifact.priority.toLowerCase()}`}>
                      {selectedArtifact.priority}
                    </span>
                  </div>
                  {selectedArtifact.jira_key && (
                    <div className="detail-row">
                      <span className="detail-label">Jira:</span>
                      <a
                        href={selectedArtifact.jira_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="jira-link"
                      >
                        {selectedArtifact.jira_key}
                      </a>
                    </div>
                  )}
                </div>
              )}

              <div className="chat-section">
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
                    placeholder="Describe your enhancement..."
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
              </div>

              {preview && (
                <div className="preview-section">
                  <h3>Preview Changes</h3>
                  <div className="preview-comparison">
                    <div className="preview-column">
                      <h4>Original</h4>
                      <pre>{JSON.stringify(preview.original, null, 2)}</pre>
                    </div>
                    <div className="preview-column">
                      <h4>Modified</h4>
                      <pre>{JSON.stringify(preview.modified, null, 2)}</pre>
                    </div>
                  </div>
                  {preview.changes && preview.changes.length > 0 && (
                    <div className="changes-list">
                      <h4>Changes:</h4>
                      <ul>
                        {preview.changes.map((change, index) => (
                          <li key={index}>{change}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <button
                    onClick={applyEnhancement}
                    disabled={loading}
                    className="btn-apply"
                  >
                    {loading ? 'Applying...' : 'Apply Enhancement'}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Enhance;
