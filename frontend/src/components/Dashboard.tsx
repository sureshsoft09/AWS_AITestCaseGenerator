import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Dashboard.css';
import { extractErrorMessage } from '../utils/errorHandler';

interface Project {
  project_id: string;
  project_name: string;
  jira_project_key?: string;
  created_at: string;
  updated_at: string;
  artifact_counts: {
    epics: number;
    features: number;
    use_cases: number;
    test_cases: number;
    total: number;
  };
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

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const Dashboard: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());

  // Fetch projects on component mount
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
      
      // Auto-select first project if available
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

  const handleExport = async (format: 'excel' | 'xml') => {
    if (!selectedProject) return;
    
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/projects/${selectedProject}/export?format=${format}`,
        { responseType: 'blob' }
      );
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      const project = projects.find(p => p.project_id === selectedProject);
      const filename = `${project?.project_name.replace(/\s+/g, '_')}_artifacts.${format === 'excel' ? 'xlsx' : 'xml'}`;
      link.setAttribute('download', filename);
      
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(extractErrorMessage(err, `Failed to export as ${format.toUpperCase()}`));
      console.error('Error exporting:', err);
    }
  };

  const toggleNode = (nodeId: string) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  const renderArtifactTree = (artifact: Artifact, level: number = 0): React.ReactNode => {
    const hasChildren = artifact.children && artifact.children.length > 0;
    const isExpanded = expandedNodes.has(artifact.id);
    const indent = level * 24;

    return (
      <div key={artifact.id} className="artifact-node">
        <div 
          className={`artifact-item artifact-${artifact.type}`}
          style={{ paddingLeft: `${indent}px` }}
        >
          {hasChildren && (
            <button
              className="expand-button"
              onClick={() => toggleNode(artifact.id)}
              aria-label={isExpanded ? 'Collapse' : 'Expand'}
            >
              {isExpanded ? '▼' : '▶'}
            </button>
          )}
          
          <div className="artifact-content">
            <div className="artifact-header">
              <span className={`artifact-type-badge ${artifact.type}`}>
                {artifact.type.replace('_', ' ').toUpperCase()}
              </span>
              <span className="artifact-name">{artifact.name}</span>
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
            
            <div className="artifact-details">
              <span className={`priority-badge ${artifact.priority.toLowerCase()}`}>
                {artifact.priority}
              </span>
              <span className={`status-badge ${artifact.status.toLowerCase()}`}>
                {artifact.status}
              </span>
              {artifact.compliance_mapping.length > 0 && (
                <span className="compliance-tags">
                  {artifact.compliance_mapping.map(tag => (
                    <span key={tag} className="compliance-tag">{tag}</span>
                  ))}
                </span>
              )}
            </div>
            
            {artifact.description && (
              <p className="artifact-description">{artifact.description}</p>
            )}
          </div>
        </div>
        
        {hasChildren && isExpanded && (
          <div className="artifact-children">
            {artifact.children!.map(child => renderArtifactTree(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  const selectedProjectData = projects.find(p => p.project_id === selectedProject);

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>MedAssureAI Dashboard</h1>
        <p>View and manage your test artifacts</p>
      </header>

      <div className="dashboard-controls">
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

        {selectedProject && (
          <div className="export-buttons">
            <button
              onClick={() => handleExport('excel')}
              className="export-button excel"
              disabled={loading}
            >
              Export to Excel
            </button>
            <button
              onClick={() => handleExport('xml')}
              className="export-button xml"
              disabled={loading}
            >
              Export to XML
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {loading && (
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading...</p>
        </div>
      )}

      {selectedProjectData && !loading && (
        <div className="project-summary">
          <h2>{selectedProjectData.project_name}</h2>
          {selectedProjectData.jira_project_key && (
            <p className="jira-key">Jira Project: {selectedProjectData.jira_project_key}</p>
          )}
          <div className="artifact-counts">
            <div className="count-item">
              <span className="count-label">Epics:</span>
              <span className="count-value">{selectedProjectData.artifact_counts.epics}</span>
            </div>
            <div className="count-item">
              <span className="count-label">Features:</span>
              <span className="count-value">{selectedProjectData.artifact_counts.features}</span>
            </div>
            <div className="count-item">
              <span className="count-label">Use Cases:</span>
              <span className="count-value">{selectedProjectData.artifact_counts.use_cases}</span>
            </div>
            <div className="count-item">
              <span className="count-label">Test Cases:</span>
              <span className="count-value">{selectedProjectData.artifact_counts.test_cases}</span>
            </div>
            <div className="count-item total">
              <span className="count-label">Total:</span>
              <span className="count-value">{selectedProjectData.artifact_counts.total}</span>
            </div>
          </div>
        </div>
      )}

      {artifacts.length > 0 && !loading && (
        <div className="artifacts-tree">
          <h3>Artifact Hierarchy</h3>
          <div className="tree-container">
            {artifacts.map(artifact => renderArtifactTree(artifact))}
          </div>
        </div>
      )}

      {!loading && selectedProject && artifacts.length === 0 && !error && (
        <div className="empty-state">
          <p>No artifacts found for this project.</p>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
