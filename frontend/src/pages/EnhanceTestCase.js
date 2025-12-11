/* eslint-disable no-unused-vars */
import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  CircularProgress,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Container,
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
  IconButton,
  Collapse,
  Badge,
  ListItemButton,
  Tooltip,
} from '@mui/material';
import {
  Assessment as EpicIcon,
  Functions as FeatureIcon,
  Assignment as UseCaseIcon,
  CheckCircle as TestCaseIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  AutoAwesome as RefactorIcon,
  Send as SendIcon,
  Close as CloseIcon,
  Check,
  Psychology as AIIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  Psychology as ExplanationIcon,
  Check as ApplyIcon,
} from '@mui/icons-material';
import { useNotification } from '../contexts/NotificationContext';
import api from '../services/api';

const EnhanceTestCase = () => {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState('');
  const [projectHierarchy, setProjectHierarchy] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [projectClarificationStatus, setProjectClarificationStatus] = useState({});
  const [expandedEpics, setExpandedEpics] = useState({});
  const [expandedFeatures, setExpandedFeatures] = useState({});
  const [expandedUseCases, setExpandedUseCases] = useState({});
  
  // AI Assistant Dialog State
  const [aiDialogOpen, setAiDialogOpen] = useState(false);
  const [currentArtifact, setCurrentArtifact] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [userMessage, setUserMessage] = useState('');
  const [sendingMessage, setSendingMessage] = useState(false);
  const [agentStatus, setAgentStatus] = useState(null);
  const [canApplyEnhancement, setCanApplyEnhancement] = useState(false);
  
  // Model Explanation Dialog State
  const [explanationDialogOpen, setExplanationDialogOpen] = useState(false);
  const [currentExplanation, setCurrentExplanation] = useState(null);
  
  // Chat scroll reference
  const chatHistoryRef = useRef(null);
  
  // Success popup state
  const [successPopupOpen, setSuccessPopupOpen] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  
  // Info section toggle
  const [showInfoSection, setShowInfoSection] = useState(false);
  
  const { showNotification } = useNotification();

  // Load projects on component mount
  useEffect(() => {
    loadProjects();
  }, []);

  // Auto-scroll chat to bottom when new messages are added
  useEffect(() => {
    if (chatHistoryRef.current) {
      chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight;
    }
  }, [chatHistory, sendingMessage]);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/projects');
      const projectsList = response.data.projects || [];
      setProjects(projectsList);
      
      // Check clarification status for each project
      const clarificationStatuses = {};
      for (const project of projectsList) {
        clarificationStatuses[project.project_id] = await checkProjectClarificationStatus(project.project_id);
      }
      setProjectClarificationStatus(clarificationStatuses);
      
    } catch (error) {
      console.error('Error loading projects:', error);
      showNotification('Failed to load projects', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleProjectSelect = (event) => {
    setSelectedProject(event.target.value);
    setProjectHierarchy(null);
    // Reset expansion states
    setExpandedEpics({});
    setExpandedFeatures({});
    setExpandedUseCases({});
  };

  const analyzeTestCases = async () => {
    if (!selectedProject) return;
    
    try {
      setAnalyzing(true);
      const response = await api.get(`/api/projects/${selectedProject}/hierarchy`);
      setProjectHierarchy(response.data.hierarchy);
      showNotification('Test cases analyzed successfully', 'success');
    } catch (error) {
      console.error('Error analyzing test cases:', error);
      showNotification('Failed to analyze test cases', 'error');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleRefactor = (artifact, type, context = {}) => {
    const enhancedArtifact = { ...artifact, type, ...context };
    setCurrentArtifact(enhancedArtifact);
    
    // Prefill context message
    const contextMessage = {
      role: 'system',
      content: `Analyzing ${type}: ${artifact.use_case_title || artifact.test_case_title || artifact.title}
      
Project: ${projectHierarchy?.project_name || 'Unknown'}
Project ID: ${selectedProject}
${context.epic_id ? `Epic ID: ${context.epic_id}` : ''}
${context.feature_id ? `Feature ID: ${context.feature_id}` : ''}
Artifact ID: ${artifact.use_case_id || artifact.test_case_id}
Jira Issue Key: ${artifact.jira_issue_key || 'Not assigned'}
Current Review Status: ${artifact.review_status || 'Pending'}
Priority: ${artifact.priority || 'Not set'}
Comments: ${artifact.comments || 'No comments available'}

${type === 'use_case' ? 
  `Description: ${artifact.description || 'No description'}
  
Acceptance Criteria:
${Array.isArray(artifact.acceptance_criteria) ? 
  artifact.acceptance_criteria.map((criteria, index) => `${index + 1}. ${criteria}`).join('\n') : 
  artifact.acceptance_criteria || 'None'}
  
Model Explanation: ${artifact.model_explanation || 'No explanation available'}` :
  `Test Type: ${artifact.test_type || 'Functional'}
  
Preconditions:
${Array.isArray(artifact.preconditions) ? 
  artifact.preconditions.map((precondition, index) => `${index + 1}. ${precondition}`).join('\n') : 
  artifact.preconditions || 'None'}
  
Test Steps:
${Array.isArray(artifact.test_steps) ? 
  artifact.test_steps.map((step, index) => `Step ${index + 1}: ${step}`).join('\n') : 
  artifact.test_steps || 'None'}
  
Expected Result: ${artifact.expected_result || 'None'}
  
Model Explanation: ${artifact.model_explanation || 'No explanation available'}`}

Please provide enhancement suggestions or ask clarifying questions.`
    };
    
    setChatHistory([contextMessage]);
    setCanApplyEnhancement(false); // Reset apply state when opening dialog
    setAiDialogOpen(true);
  };

  const applyEnhancement = async () => {
    try {
      if (!currentArtifact) return;
      
      setSendingMessage(true);
      setAgentStatus('Applying enhancement and pushing to Jira and Firestore...');
      
      // Prepare the request data with project keys
      const requestData = {
        project_id: selectedProject,
        jira_project_key: projectHierarchy?.jira_project_key || 'DEFAULT',
        firestore_project_id: selectedProject,
        prompt: `The generated enhanced test case looks fine, push the enhanced test case to Jira project key: ${projectHierarchy?.jira_project_key || 'DEFAULT'} and Firestore project ID: ${selectedProject} through MCP tool by master_agent. Include Preconditions, Test Steps, Expected Result into jira issue description`
      };

      // Call the new applyEnhancement API
      const response = await api.applyEnhancement(requestData);
      
      // Handle response that comes as response.data.response with JSON wrapped in markdown
      let responseData = response.data.response || response.data;
      if (typeof responseData === 'string' && responseData.includes('```json')) {
        // Extract JSON from markdown code block
        const jsonMatch = responseData.match(/```json\n([\s\S]*?)\n```/);
        if (jsonMatch) {
          responseData = JSON.parse(jsonMatch[1]);
        }
      }
      
      if (responseData.status === 'enhancement_update_completed') {
        // Show success popup
        setSuccessMessage(responseData.action_summary || 'Enhanced artifact successfully updated in database and Jira.');
        setSuccessPopupOpen(true);
        setCanApplyEnhancement(false);
        setAiDialogOpen(false);
        
        // Note: We don't refresh here as it's handled in the success popup dialog
        return; // Exit successfully without triggering catch block
      } else {
        showNotification(responseData.message || 'Failed to apply enhancement', 'error');
      }
      
    } catch (error) {
      console.error('Error applying enhancement:', error);
      showNotification('Failed to apply enhancement', 'error');
    } finally {
      setSendingMessage(false);
      setAgentStatus(null);
    }
  };

  const sendMessage = async () => {
    if (!userMessage.trim() || sendingMessage) return;

    const newMessage = { role: 'user', content: userMessage };
    const updatedHistory = [...chatHistory, newMessage];
    setChatHistory(updatedHistory);
    setUserMessage('');
    setSendingMessage(true);

    try {
      // Create comprehensive prompt with all context
      const artifactType = currentArtifact.type;
      const artifactDetails = {
        project_id: selectedProject,
        project_name: projectHierarchy?.project_name || 'Unknown',
        epic_id: currentArtifact.epic_id || null,
        feature_id: currentArtifact.feature_id || null,
        use_case_id: artifactType === 'use_case' ? currentArtifact.use_case_id : null,
        test_case_id: artifactType === 'test_case' ? currentArtifact.test_case_id : null,
        artifact_type: artifactType,
        title: currentArtifact.use_case_title || currentArtifact.test_case_title || currentArtifact.title,
        description: currentArtifact.description || '',
        review_status: currentArtifact.review_status || 'Pending',
        model_explanation: currentArtifact.model_explanation || '',
        ...(artifactType === 'use_case' ? {
          acceptance_criteria: currentArtifact.acceptance_criteria || []
        } : {
          test_type: currentArtifact.test_type || 'Functional',
          preconditions: currentArtifact.preconditions || [],
          test_steps: currentArtifact.test_steps || [],
          expected_result: currentArtifact.expected_result || '',
          test_data: currentArtifact.test_data || null,
          priority: currentArtifact.priority || 'Medium',
          jira_issue_key: currentArtifact.jira_issue_key || null,
          tags: currentArtifact.tags || []
        })
      };

      const contextualPrompt = `
Project Context:
- Project ID: ${selectedProject}
- Project Name: ${projectHierarchy?.project_name || 'Unknown'}
${currentArtifact.epic_id ? `- Epic ID: ${currentArtifact.epic_id}` : ''}
${currentArtifact.feature_id ? `- Feature ID: ${currentArtifact.feature_id}` : ''}

Artifact Details:
${JSON.stringify(artifactDetails, null, 2)}

User Input: ${userMessage}

Previous Context: ${chatHistory.filter(msg => msg.role === 'system').map(msg => msg.content).join('\n')}

Please analyze the existing ${artifactType} and either ask clarifying questions or provide enhancement suggestions based on the user input.`;

      const payload = {
        prompt: contextualPrompt
      };

      const response = await api.enhanceTestCasesChat(payload);
      const agentResponse = response.data;
      
      setAgentStatus(agentResponse);
      
      const assistantMessage = {
        role: 'assistant',
        content: agentResponse.response || 'No response received from agent'
      };
      
      setChatHistory(prev => [...prev, assistantMessage]);
      setCanApplyEnhancement(true); // Enable apply button after AI response
      
      // Check if the response indicates completion or success
      if (agentResponse.response && (
        agentResponse.response.toLowerCase().includes('completed') ||
        agentResponse.response.toLowerCase().includes('updated') ||
        agentResponse.response.toLowerCase().includes('enhanced')
      )) {
        showNotification('Enhancement request processed! Check the response for details.', 'success');
      }
      
    } catch (error) {
      console.error('Error sending message:', error);
      console.error('Error details:', error.response?.data || error.message);
      
      let errorDetails = 'Unknown error occurred';
      if (error.response?.data?.detail) {
        errorDetails = error.response.data.detail;
      } else if (error.message) {
        errorDetails = error.message;
      }
      
      showNotification(`Failed to send message: ${errorDetails}`, 'error');
      const errorMessage = {
        role: 'assistant',
        content: `Sorry, I encountered an error: ${errorDetails}. Please try again.`
      };
      setChatHistory(prev => [...prev, errorMessage]);
    } finally {
      setSendingMessage(false);
    }
  };

  const toggleEpicExpansion = (epicId) => {
    setExpandedEpics(prev => ({ ...prev, [epicId]: !prev[epicId] }));
  };

  const toggleFeatureExpansion = (featureId) => {
    setExpandedFeatures(prev => ({ ...prev, [featureId]: !prev[featureId] }));
  };

  const toggleUseCaseExpansion = (useCaseId) => {
    setExpandedUseCases(prev => ({ ...prev, [useCaseId]: !prev[useCaseId] }));
  };

  const isNonApproved = (item) => {
    return item.review_status !== 'Approved';
  };

  // Helper functions to check for clarification needs
  const needsClarification = (item) => {
    return item.review_status === 'Need Clarification' || 
           item.review_status === 'Needs Clarification' ||
           item.review_status === 'Pending Review' ||
           isNonApproved(item);
  };

  const hasTestCasesNeedingClarification = (useCase) => {
    const testCases = useCase.test_cases || [];
    return needsClarification(useCase) || testCases.some(tc => needsClarification(tc));
  };

  const hasUseCasesNeedingClarification = (feature) => {
    const useCases = feature.use_cases || [];
    return useCases.some(uc => hasTestCasesNeedingClarification(uc));
  };

  const hasFeaturesNeedingClarification = (epic) => {
    const features = epic.features || [];
    return features.some(f => hasUseCasesNeedingClarification(f));
  };

  const hasProjectClarificationNeeds = (projectHierarchy) => {
    if (!projectHierarchy || !projectHierarchy.epics) return false;
    return projectHierarchy.epics.some(epic => hasFeaturesNeedingClarification(epic));
  };

  const checkProjectClarificationStatus = async (projectId) => {
    try {
      const response = await api.get(`/api/projects/${projectId}/hierarchy`);
      const hierarchy = response.data.hierarchy;
      return hasProjectClarificationNeeds(hierarchy);
    } catch (error) {
      console.error(`Error checking clarification status for project ${projectId}:`, error);
      return false;
    }
  };

  // InfoButton component for model explanations
  const InfoButton = ({ onClick, hasInfo, tooltip }) => (
    <Tooltip title={tooltip}>
      <IconButton
        size="small"
        onClick={(e) => {
          e.stopPropagation();
          onClick();
        }}
        sx={{
          ml: 1,
          color: hasInfo ? '#667eea' : '#ccc',
          '&:hover': {
            backgroundColor: hasInfo ? 'rgba(102, 126, 234, 0.1)' : 'rgba(204, 204, 204, 0.1)',
          },
        }}
      >
        <ExplanationIcon fontSize="small" />
      </IconButton>
    </Tooltip>
  );

  // Handle model explanation display
  const handleModelExplanation = (item, type) => {
    if (item.model_explanation) {
      setCurrentExplanation({
        title: item.use_case_title || item.test_case_title || item.feature_name || item.epic_name || item.title || `${type} explanation`,
        type: type,
        content: item.model_explanation
      });
      setExplanationDialogOpen(true);
    } else {
      showNotification('No model explanation available', 'info');
    }
  };

  const TestCaseItem = ({ testCase, epic, feature, useCase }) => (
    <ListItem
      sx={{
        border: '1px solid #e0e0e0',
        borderRadius: 1,
        mb: 1,
        backgroundColor: '#fafafa',
      }}
    >
      <ListItemIcon>
        <TestCaseIcon color="success" />
      </ListItemIcon>
      <ListItemText
        primary={
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Typography variant="subtitle2">
                  {testCase.test_case_title || `Test Case ${testCase.test_case_id}`}
                </Typography>
                <InfoButton
                  onClick={() => handleModelExplanation(testCase, 'test_case')}
                  hasInfo={!!testCase.model_explanation}
                  tooltip="View AI Model Explanation"
                />
                {needsClarification(testCase) && (
                  <WarningIcon 
                    sx={{ ml: 1, color: '#ff9800', fontSize: 14 }} 
                    titleAccess="Needs clarification"
                  />
                )}
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip
                  label={testCase.review_status || 'Pending'}
                  size="small"
                  color={testCase.review_status === 'Approved' ? 'success' : 'warning'}
                />
                {testCase.priority && (
                  <Chip
                    label={`Priority: ${testCase.priority}`}
                    size="small"
                    variant="outlined"
                    color={testCase.priority === 'High' ? 'error' : testCase.priority === 'Medium' ? 'warning' : 'default'}
                    sx={{ fontSize: '0.7rem' }}
                  />
                )}
                {testCase.jira_issue_key && (
                  <Chip
                    label={`Jira: ${testCase.jira_issue_key}`}
                    size="small"
                    variant="outlined"
                    color="primary"
                    sx={{ fontSize: '0.7rem' }}
                  />
                )}
                <Button
                  size="small"
                  variant="outlined"
                  startIcon={<RefactorIcon />}
                  onClick={() => handleRefactor(testCase, 'test_case', { 
                    epic_id: epic?.epic_id,
                    feature_id: feature?.feature_id,
                    use_case_id: useCase?.use_case_id
                  })}
                  sx={{ color: '#667eea', borderColor: '#667eea' }}
                >
                  Refactor
                </Button>
              </Box>
            </Box>
          </Box>
        }
        secondary={
          <Box sx={{ mt: 1 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Type: {testCase.test_type || 'Functional'}
            </Typography>
            
            {testCase.preconditions && (
              <Box sx={{ mb: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 600, color: 'primary.main' }}>
                  Preconditions:
                </Typography>
                {Array.isArray(testCase.preconditions) ? (
                  testCase.preconditions.map((precondition, index) => (
                    <Typography key={index} variant="body2" color="text.secondary" sx={{ ml: 1, mb: 0.5 }}>
                      • {precondition}
                    </Typography>
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                    {testCase.preconditions}
                  </Typography>
                )}
              </Box>
            )}
            
            {testCase.test_steps && (
              <Box sx={{ mb: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 600, color: 'primary.main' }}>
                  Test Steps:
                </Typography>
                {Array.isArray(testCase.test_steps) ? (
                  testCase.test_steps.map((step, index) => (
                    <Typography key={index} variant="body2" color="text.secondary" sx={{ ml: 1, mb: 0.5 }}>
                      {index + 1}. {step}
                    </Typography>
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                    {testCase.test_steps}
                  </Typography>
                )}
              </Box>
            )}
            
            {testCase.expected_result && (
              <Box sx={{ mb: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 600, color: 'primary.main' }}>
                  Expected Result:
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                  {testCase.expected_result}
                </Typography>
              </Box>
            )}

            {testCase.comments && (
              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic', mt: 1 }}>
                Comments: {testCase.comments}
              </Typography>
            )}
          </Box>
        }
      />
    </ListItem>
  );

  const UseCaseItem = ({ useCase, epic, feature }) => {
    const isExpanded = expandedUseCases[useCase.use_case_id];
    const testCases = useCase.test_cases || [];

    return (
      <Card sx={{ mb: 1, border: '1px solid #e0e0e0' }}>
        <ListItemButton onClick={() => toggleUseCaseExpansion(useCase.use_case_id)}>
          <ListItemIcon>
            <UseCaseIcon color="info" />
          </ListItemIcon>
          <ListItemText
            primary={
              <Box>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                      {useCase.use_case_title || `Use Case ${useCase.use_case_id}`}
                    </Typography>
                    <Badge badgeContent={testCases.length} color="success" sx={{ ml: 1 }}>
                      <TestCaseIcon fontSize="small" />
                    </Badge>
                    <InfoButton
                      onClick={() => handleModelExplanation(useCase, 'use_case')}
                      hasInfo={!!useCase.model_explanation}
                      tooltip="View AI Model Explanation"
                    />
                    {hasTestCasesNeedingClarification(useCase) && (
                      <WarningIcon 
                        sx={{ ml: 1, color: '#ff9800', fontSize: 16 }} 
                        titleAccess="Contains items needing clarification"
                      />
                    )}
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip
                      label={useCase.review_status || 'Pending'}
                      size="small"
                      color={useCase.review_status === 'Approved' ? 'success' : 'warning'}
                    />
                    {useCase.priority && (
                      <Chip
                        label={`Priority: ${useCase.priority}`}
                        size="small"
                        variant="outlined"
                        color={useCase.priority === 'High' ? 'error' : useCase.priority === 'Medium' ? 'warning' : 'default'}
                        sx={{ fontSize: '0.75rem' }}
                      />
                    )}
                    {useCase.jira_issue_key && (
                      <Chip
                        label={`Jira: ${useCase.jira_issue_key}`}
                        size="small"
                        variant="outlined"
                        color="primary"
                        sx={{ fontSize: '0.75rem' }}
                      />
                    )}
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<RefactorIcon />}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRefactor(useCase, 'use_case', {
                          epic_id: epic?.epic_id,
                          feature_id: feature?.feature_id
                        });
                      }}
                      sx={{ color: '#667eea', borderColor: '#667eea' }}
                    >
                      Refactor
                    </Button>
                  </Box>
                </Box>
              </Box>
            }
            secondary={
              <Box>
                {useCase.description && (
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    {useCase.description}
                  </Typography>
                )}
                {useCase.acceptance_criteria && (
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="body2" sx={{ fontWeight: 600, color: 'primary.main' }}>
                      Acceptance Criteria:
                    </Typography>
                    {Array.isArray(useCase.acceptance_criteria) ? (
                      useCase.acceptance_criteria.map((criteria, index) => (
                        <Typography key={index} variant="body2" color="text.secondary" sx={{ ml: 1, mb: 0.5 }}>
                          • {criteria}
                        </Typography>
                      ))
                    ) : (
                      <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                        {useCase.acceptance_criteria}
                      </Typography>
                    )}
                  </Box>
                )}
              </Box>
            }
          />
          {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </ListItemButton>
        <Collapse in={isExpanded}>
          <Box sx={{ p: 2, backgroundColor: '#f9f9f9' }}>
            <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
              Test Cases ({testCases.length})
            </Typography>
            {testCases.length > 0 ? (
              testCases.map((testCase) => (
                <TestCaseItem key={testCase.test_case_id} testCase={testCase} epic={epic} feature={feature} useCase={useCase} />
              ))
            ) : (
              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                No test cases available
              </Typography>
            )}
          </Box>
        </Collapse>
      </Card>
    );
  };

  const FeatureItem = ({ feature, epic }) => {
    const isExpanded = expandedFeatures[feature.feature_id];
    const useCases = feature.use_cases || [];

    return (
      <Card sx={{ mb: 1, border: '1px solid #d0d0d0' }}>
        <ListItemButton onClick={() => toggleFeatureExpansion(feature.feature_id)}>
          <ListItemIcon>
            <FeatureIcon color="warning" />
          </ListItemIcon>
          <ListItemText
            primary={
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {feature.feature_name || feature.title || `Feature ${feature.feature_id}`}
                </Typography>
                <Badge badgeContent={useCases.length} color="info" sx={{ ml: 1 }}>
                  <UseCaseIcon fontSize="small" />
                </Badge>
                <InfoButton
                  onClick={() => handleModelExplanation(feature, 'feature')}
                  hasInfo={!!feature.model_explanation}
                  tooltip="View AI Model Explanation"
                />
                {feature.priority && (
                  <Chip
                    label={`Priority: ${feature.priority}`}
                    size="small"
                    variant="outlined"
                    color={feature.priority === 'High' ? 'error' : feature.priority === 'Medium' ? 'warning' : 'default'}
                    sx={{ ml: 1, fontSize: '0.75rem' }}
                  />
                )}
                {feature.jira_issue_key && (
                  <Chip
                    label={`Jira: ${feature.jira_issue_key}`}
                    size="small"
                    variant="outlined"
                    color="primary"
                    sx={{ ml: 1, fontSize: '0.75rem' }}
                  />
                )}
                {hasUseCasesNeedingClarification(feature) && (
                  <WarningIcon 
                    sx={{ ml: 1, color: '#ff9800', fontSize: 18 }} 
                    titleAccess="Contains items needing clarification"
                  />
                )}
              </Box>
            }
            secondary={feature.description}
          />
          {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </ListItemButton>
        <Collapse in={isExpanded}>
          <Box sx={{ p: 2, backgroundColor: '#f5f5f5' }}>
            <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
              Use Cases ({useCases.length})
            </Typography>
            {useCases.length > 0 ? (
              useCases.map((useCase) => (
                <UseCaseItem key={useCase.use_case_id} useCase={useCase} epic={epic} feature={feature} />
              ))
            ) : (
              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                No use cases available
              </Typography>
            )}
          </Box>
        </Collapse>
      </Card>
    );
  };

  const EpicItem = ({ epic }) => {
    const isExpanded = expandedEpics[epic.epic_id];
    const features = epic.features || [];

    return (
      <Card sx={{ mb: 2, border: '1px solid #c0c0c0' }}>
        <ListItemButton onClick={() => toggleEpicExpansion(epic.epic_id)}>
          <ListItemIcon>
            <EpicIcon color="secondary" />
          </ListItemIcon>
          <ListItemText
            primary={
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {epic.epic_name || epic.title || `Epic ${epic.epic_id}`}
                </Typography>
                <Badge badgeContent={features.length} color="warning" sx={{ ml: 1 }}>
                  <FeatureIcon fontSize="small" />
                </Badge>
                <InfoButton
                  onClick={() => handleModelExplanation(epic, 'epic')}
                  hasInfo={!!epic.model_explanation}
                  tooltip="View AI Model Explanation"
                />
                {epic.priority && (
                  <Chip
                    label={`Priority: ${epic.priority}`}
                    size="small"
                    variant="outlined"
                    color={epic.priority === 'High' ? 'error' : epic.priority === 'Medium' ? 'warning' : 'default'}
                    sx={{ ml: 1, fontSize: '0.75rem' }}
                  />
                )}
                {epic.jira_issue_key && (
                  <Chip
                    label={`Jira: ${epic.jira_issue_key}`}
                    size="small"
                    variant="outlined"
                    color="primary"
                    sx={{ ml: 1, fontSize: '0.75rem' }}
                  />
                )}
                {hasFeaturesNeedingClarification(epic) && (
                  <WarningIcon 
                    sx={{ ml: 1, color: '#ff9800', fontSize: 20 }} 
                    titleAccess="Contains items needing clarification"
                  />
                )}
              </Box>
            }
            secondary={epic.description}
          />
          {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </ListItemButton>
        <Collapse in={isExpanded}>
          <Box sx={{ p: 2, backgroundColor: '#f0f0f0' }}>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
              Features ({features.length})
            </Typography>
            {features.length > 0 ? (
              features.map((feature) => (
                <FeatureItem key={feature.feature_id} feature={feature} epic={epic} />
              ))
            ) : (
              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                No features available
              </Typography>
            )}
          </Box>
        </Collapse>
      </Card>
    );
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, color: '#667eea' }}>
          Enhance Test Cases
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={loadProjects}
          disabled={loading}
        >
          Refresh Projects
        </Button>
      </Box>

      {/* Project Selection */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
          Select Project to Analyze
        </Typography>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={8}>
            <FormControl fullWidth>
              <InputLabel id="project-select-label">
                {loading ? (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CircularProgress size={16} />
                    <span>Loading Projects...</span>
                  </Box>
                ) : (
                  'Choose Project'
                )}
              </InputLabel>
              <Select
                labelId="project-select-label"
                value={selectedProject}
                label="Choose Project"
                onChange={handleProjectSelect}
                disabled={loading}
                startAdornment={loading && (
                  <CircularProgress size={20} sx={{ mr: 1, ml: 1 }} />
                )}
              >
                {loading ? (
                  <MenuItem disabled>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, py: 2 }}>
                      <CircularProgress size={20} />
                      <Typography color="text.secondary">Loading projects...</Typography>
                    </Box>
                  </MenuItem>
                ) : (
                  projects.map((project) => (
                    <MenuItem key={project.project_id} value={project.project_id}>
                      <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                        <Typography sx={{ flexGrow: 1 }}>
                          {project.project_name} ({project.project_id})
                        </Typography>
                        {projectClarificationStatus[project.project_id] && (
                          <Tooltip title="Contains items needing clarification">
                            <WarningIcon 
                              sx={{ 
                                color: '#ff9800', 
                                fontSize: '1.2rem',
                                ml: 1
                              }} 
                            />
                          </Tooltip>
                        )}
                      </Box>
                    </MenuItem>
                  ))
                )}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={4}>
            <Button
              variant="contained"
              onClick={analyzeTestCases}
              disabled={!selectedProject || analyzing}
              startIcon={analyzing ? <CircularProgress size={16} /> : <AIIcon />}
              sx={{ 
                backgroundColor: '#667eea',
                '&:hover': { backgroundColor: '#5a67d8' }
              }}
            >
              {analyzing ? 'Analyzing...' : 'Analyze Test Cases'}
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Test Cases Hierarchy */}
      {projectHierarchy && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Project Hierarchy - {projectHierarchy.project_name}
            </Typography>
            {/* Clarification Summary */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              {projectHierarchy.epics && projectHierarchy.epics.some(epic => hasFeaturesNeedingClarification(epic)) && (
                <Chip
                  icon={<WarningIcon />}
                  label="Contains items needing clarification"
                  color="warning"
                  variant="outlined"
                  size="small"
                />
              )}
            </Box>
          </Box>
          
          {/* Legend */}
          <Box sx={{ mb: 3, p: 2, backgroundColor: '#f8f9fa', borderRadius: 1, border: '1px solid #e9ecef' }}>
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
              Legend:
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <WarningIcon sx={{ color: '#ff9800', fontSize: 16 }} />
                <Typography variant="body2" color="text.secondary">
                  Items needing clarification
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <RefactorIcon sx={{ color: '#667eea', fontSize: 16 }} />
                <Typography variant="body2" color="text.secondary">
                  Refactor available
                </Typography>
              </Box>
            </Box>
          </Box>
          {projectHierarchy.epics && projectHierarchy.epics.length > 0 ? (
            projectHierarchy.epics.map((epic) => (
              <EpicItem key={epic.epic_id} epic={epic} />
            ))
          ) : (
            <Typography variant="body1" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
              No epics found in this project.
            </Typography>
          )}
        </Paper>
      )}

      {/* AI Assistant Dialog */}
      <Dialog
        open={aiDialogOpen}
        onClose={() => {}}
        maxWidth="lg"
        fullWidth
        disableEscapeKeyDown
        sx={{
          '& .MuiDialog-paper': {
            height: '80vh',
            maxHeight: '800px',
            width: '90vw',
            maxWidth: '1000px',
            borderRadius: 2,
            boxShadow: 3
          }
        }}
      >
        <DialogTitle sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          backgroundColor: '#667eea',
          color: 'white',
          py: 2
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <AIIcon sx={{ mr: 1 }} />
            AI Enhancement Assistant
          </Box>
          <IconButton 
            onClick={() => setAiDialogOpen(false)}
            sx={{ color: 'white' }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent sx={{ 
          height: 'calc(80vh - 120px)', 
          display: 'flex', 
          flexDirection: 'column',
          p: 3
        }}>
          {/* Chat History */}
          <Box 
            ref={chatHistoryRef}
            sx={{ flexGrow: 1, overflow: 'auto', mb: 2, p: 1, border: '1px solid #e0e0e0', borderRadius: 1 }}
          >
            {chatHistory.map((message, index) => (
              <Box
                key={index}
                sx={{
                  mb: 2,
                  p: 2,
                  borderRadius: 1,
                  backgroundColor: message.role === 'user' ? '#e3f2fd' : '#f5f5f5',
                  ml: message.role === 'user' ? 2 : 0,
                  mr: message.role === 'user' ? 0 : 2,
                }}
              >
                <Typography variant="body2" sx={{ fontWeight: 600, mb: 1, color: message.role === 'user' ? '#1976d2' : '#666' }}>
                  {message.role === 'user' ? 'You' : 'AI Assistant'}
                </Typography>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {message.content}
                </Typography>
              </Box>
            ))}
            {sendingMessage && (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
                <CircularProgress size={24} />
              </Box>
            )}
          </Box>



          {/* Message Input */}
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              multiline
              rows={3}
              value={userMessage}
              onChange={(e) => setUserMessage(e.target.value)}
              placeholder="Type your enhancement instructions or clarifications here..."
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
            />
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <IconButton
                color="primary"
                onClick={sendMessage}
                disabled={!userMessage.trim() || sendingMessage}
                title="Send Message"
              >
                <SendIcon />
              </IconButton>
              <IconButton
                color="success"
                onClick={applyEnhancement}
                disabled={!canApplyEnhancement || sendingMessage}
                title="Apply Enhancement"
                sx={{ 
                  backgroundColor: canApplyEnhancement ? '#4caf50' : 'transparent',
                  color: canApplyEnhancement ? 'white' : 'inherit',
                  border: canApplyEnhancement ? '2px solid #4caf50' : '1px solid #ccc',
                  animation: canApplyEnhancement ? 'pulse 2s infinite' : 'none',
                  '@keyframes pulse': {
                    '0%': {
                      boxShadow: '0 0 0 0 rgba(76, 175, 80, 0.7)'
                    },
                    '70%': {
                      boxShadow: '0 0 0 10px rgba(76, 175, 80, 0)'
                    },
                    '100%': {
                      boxShadow: '0 0 0 0 rgba(76, 175, 80, 0)'
                    }
                  },
                  '&:hover': {
                    backgroundColor: canApplyEnhancement ? '#45a049' : 'transparent',
                    transform: canApplyEnhancement ? 'scale(1.1)' : 'none'
                  },
                  '&:disabled': {
                    backgroundColor: 'transparent',
                    color: '#ccc'
                  }
                }}
              >
                {sendingMessage ? <CircularProgress size={20} color="inherit" /> : <Check />}
              </IconButton>
            </Box>
          </Box>
          
          {/* Info Button and Collapsible Section */}
          <Box sx={{ mt: 2 }}>
            <Button
              size="small"
              variant="outlined"
              onClick={() => setShowInfoSection(!showInfoSection)}
              startIcon={showInfoSection ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              sx={{ 
                textTransform: 'none',
                borderColor: '#667eea',
                color: '#667eea',
                '&:hover': {
                  borderColor: '#5a67d8',
                  backgroundColor: 'rgba(102, 126, 234, 0.04)'
                }
              }}
            >
              How to use AI Enhancement Assistant
            </Button>
            
            <Collapse in={showInfoSection}>
              <Box sx={{ 
                mt: 2, 
                p: 3, 
                backgroundColor: '#f8f9fa', 
                borderRadius: 1, 
                border: '1px solid #e9ecef',
                borderLeft: '4px solid #667eea'
              }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, color: '#667eea' }}>
                  🤖 AI Enhancement Assistant Guide
                </Typography>
                
                <Typography variant="body2" sx={{ fontWeight: 600, mb: 1, color: '#333' }}>
                  💬 Step 1: Interactive Enhancement Chat
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2, ml: 2 }}>
                  • Start a conversation with the AI about your test case<br/>
                  • Ask for specific improvements like edge cases, boundary conditions, or error scenarios<br/>
                  • Request additional test steps, validation points, or preconditions<br/>
                  • Discuss performance, security, or usability aspects<br/>
                  • Get suggestions for better test data or more comprehensive coverage
                </Typography>
                
                <Typography variant="body2" sx={{ fontWeight: 600, mb: 1, color: '#333' }}>
                  🔍 Step 2: Review AI Suggestions
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2, ml: 2 }}>
                  • The AI will provide detailed enhancement suggestions<br/>
                  • Review the proposed changes to preconditions, test steps, and expected results<br/>
                  • Continue chatting to refine or request additional improvements<br/>
                  • Ask for clarifications on any suggested enhancements
                </Typography>
                
                <Typography variant="body2" sx={{ fontWeight: 600, mb: 1, color: '#333' }}>
                  ✅ Step 3: Apply Enhancements
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2, ml: 2 }}>
                  • Once satisfied with the AI's suggestions, click the <strong style={{color: '#4caf50'}}>Apply Enhancement</strong> button<br/>
                  • The enhanced test case will be automatically updated in the database and Jira<br/>
                  • All improvements including preconditions, test steps, and expected results will be saved<br/>
                  • You'll receive a confirmation popup upon successful completion
                </Typography>
                
                <Box sx={{ 
                  mt: 3, 
                  p: 2, 
                  backgroundColor: '#e3f2fd', 
                  borderRadius: 1,
                  border: '1px solid #90caf9'
                }}>
                  <Typography variant="body2" sx={{ fontWeight: 600, mb: 1, color: '#1976d2' }}>
                    💡 Pro Tips:
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    • Be specific about what you want to improve (e.g., "Add negative test cases for invalid inputs")<br/>
                    • Ask for industry best practices or compliance requirements<br/>
                    • Request accessibility or cross-browser testing scenarios<br/>
                    • Get suggestions for automation-friendly test steps
                  </Typography>
                </Box>
              </Box>
            </Collapse>
          </Box>
        </DialogContent>
      </Dialog>

      {/* Success Popup Dialog */}
      <Dialog
        open={successPopupOpen}

        onClose={() => {}}
        maxWidth="sm"
        fullWidth
        disableEscapeKeyDown
      >
        <DialogTitle sx={{ 
          backgroundColor: '#4caf50',
          color: 'white',
          textAlign: 'center',
          py: 3
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Check sx={{ mr: 1, fontSize: '2rem' }} />
            Enhancement Applied Successfully!
          </Box>
        </DialogTitle>
        <DialogContent sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body1" sx={{ mb: 3 }}>
            Enhanced artifact successfully updated in Jira and database.
          </Typography>
          <Button
            variant="contained"
            onClick={() => {
              setSuccessPopupOpen(false);
              // Save current scroll position and refresh
              const currentScrollTop = window.pageYOffset || document.documentElement.scrollTop;
              if (selectedProject) {
                analyzeTestCases().then(() => {
                  setTimeout(() => {
                    window.scrollTo(0, currentScrollTop);
                  }, 100);
                });
              }
            }}
            sx={{
              backgroundColor: '#4caf50',
              '&:hover': { backgroundColor: '#45a049' },
              px: 4,
              py: 1
            }}
          >
            Continue
          </Button>
        </DialogContent>
      </Dialog>

      {/* Model Explanation Dialog */}
      <Dialog
        open={explanationDialogOpen}
        onClose={() => setExplanationDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <ExplanationIcon sx={{ mr: 1, color: '#667eea' }} />
            AI Model Explanation
          </Box>
          <IconButton onClick={() => setExplanationDialogOpen(false)}>
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          {currentExplanation && (
            <Box>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                {currentExplanation.title}
              </Typography>
              <Typography variant="body2" sx={{ mb: 1, color: '#666', textTransform: 'capitalize' }}>
                Type: {currentExplanation.type.replace('_', ' ')}
              </Typography>
              <Paper sx={{ p: 2, backgroundColor: '#f8f9fa', border: '1px solid #e9ecef' }}>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
                  {currentExplanation.content}
                </Typography>
              </Paper>
            </Box>
          )}
        </DialogContent>
      </Dialog>
    </Container>
  );
};

export default EnhanceTestCase;