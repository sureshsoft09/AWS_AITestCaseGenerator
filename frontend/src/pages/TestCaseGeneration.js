/* eslint-disable no-unused-vars */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { v4 as uuidv4 } from 'uuid';
import api from '../services/api';
import {
  Box,
  Container,
  Typography,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Button,
  Paper,
  Card,
  CardContent,
  CardActions,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemButton,
  Chip,
  Grid,
  Divider,
  Alert,
  LinearProgress,
  IconButton,
  Menu,
  MenuItem,
  Tooltip,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Avatar,
  Badge,
  Stack,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  CloudUpload as CloudUploadIcon,
  Description as FileIcon,
  Chat as ChatIcon,
  PlaylistAddCheck as TestCaseIcon,
  GetApp as ExportIcon,
  ExpandMore as ExpandMoreIcon,
  Send as SendIcon,
  Check as CheckIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Folder as FolderIcon,
  InsertDriveFile as DocumentIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  MoreVert as MoreVertIcon,
  Download as DownloadIcon,
  Visibility as ViewIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  Assessment as EpicIcon,
  Functions as FeatureIcon,
  Assignment as UseCaseIcon,
  CheckCircle
} from '@mui/icons-material';
import { TreeView, TreeItem } from '@mui/x-tree-view';
import ExportService from '../services/exportService';
import { useNotification } from '../contexts/NotificationContext';

const TestCaseGeneration = () => {
  // Refs
  const chatMessagesRef = useRef(null);
  
  // Hooks
  const { showNotification } = useNotification();

  // State management
  const [sessionId, setSessionId] = useState(null);
  const [uploadId, setUploadId] = useState(null);
  const [activeStep, setActiveStep] = useState(0);
  const [projectData, setProjectData] = useState({
    name: '',
    description: '',
    jiraProjectKey: 'HS25SKL',
    notificationEmail: '',
    created: null,
    id: null
  });
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [extractedContent, setExtractedContent] = useState('');
  const [uploadCompleted, setUploadCompleted] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [assistantEnabled, setAssistantEnabled] = useState(false);
  const [readinessMeta, setReadinessMeta] = useState(null); // raw backend response metadata
  const [readinessPlan, setReadinessPlan] = useState(null);
  const [generatedTestCases, setGeneratedTestCases] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [testGenerationStats, setTestGenerationStats] = useState(null);
  const [exportFormat, setExportFormat] = useState('pdf');
  const [completionDialog, setCompletionDialog] = useState(false);
  const [isChatProcessing, setIsChatProcessing] = useState(false);
  
  // Generation Summary Popup State
  const [generationSummaryOpen, setGenerationSummaryOpen] = useState(false);
  const [generationData, setGenerationData] = useState(null);
  const [pushingToServices, setPushingToServices] = useState(false);

  // Derived readiness flag
  const isReadyForGeneration = Boolean(
    readinessMeta?.readiness_plan?.overall_status?.toString()?.toLowerCase().includes('ready for test generation') ||
    readinessMeta?.readiness_plan?.overall_status?.toString()?.toLowerCase() === 'ready' ||
    readinessMeta?.test_generation_status?.ready_for_generation ||
    readinessPlan?.test_generation_status?.ready_for_generation
  );
  
  // Dialog states
  const [newProjectDialog, setNewProjectDialog] = useState(false);
  const [exportDialog, setExportDialog] = useState(false);
  const [creatingProject, setCreatingProject] = useState(false);

  // Generate session ID on component mount
  useEffect(() => {
    const newSessionId = uuidv4();
    setSessionId(newSessionId);
    console.log(`Generated session ID: ${newSessionId}`);
  }, []);

  // Auto-scroll to bottom when chat messages change
  useEffect(() => {
    if (chatMessagesRef.current) {
      chatMessagesRef.current.scrollTop = chatMessagesRef.current.scrollHeight;
    }
  }, [chatMessages, isProcessing]);

  // Step definitions
  const steps = [
    {
      label: 'Create New Project',
      description: 'Set up your test case generation project'
    },
    {
      label: 'Upload Requirements',
      description: 'Upload PDF or DOCX requirement documents'
    },
    {
      label: 'Review & Chat',
      description: 'Review documents and clarify requirements through chat'
    },
    {
      label: 'Generate Test Cases',
      description: 'View generated test cases and access dashboard for complete details'
    }
  ];

  // Navigation hook
  const navigate = useNavigate();

  // Completion dialog handler
  const handleCompletionDialogClose = () => {
    setCompletionDialog(false);
    setActiveStep(3); // Move to step 4 (0-indexed, so 3 = step 4)
  };

  // Navigate to dashboard
  const handleGoToDashboard = () => {
    setCompletionDialog(false);
    navigate('/dashboard');
  };

  // Handle opening new project dialog and reset form
  const handleOpenNewProjectDialog = () => {
    setProjectData({
      name: '',
      description: '',
      jiraProjectKey: 'HS25SKL',
      notificationEmail: '',
      created: null,
      id: null
    });
    setNewProjectDialog(true);
  };

  // Step 1: Create New Project
  const handleCreateProject = async () => {
    if (!projectData.name.trim()) {
      showNotification('Please enter a project name', 'error');
      return;
    }

    if (!projectData.jiraProjectKey.trim()) {
      showNotification('Please enter a Jira Project Key', 'error');
      return;
    }

    if (!projectData.notificationEmail.trim()) {
      showNotification('Please enter a notification email address', 'error');
      return;
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(projectData.notificationEmail)) {
      showNotification('Please enter a valid email address', 'error');
      return;
    }
    
    try {
      setCreatingProject(true);
      
      // Project will be created in backend during file upload step
      // No API call here - just validate and store the data
      // Generate a temporary client-side project ID
      const tempProjectId = `${projectData.name.toLowerCase().replace(/\s+/g, '_')}_${Date.now()}`;
      
      setProjectData({
        ...projectData,
        created: new Date(),
        id: tempProjectId
      });
      setNewProjectDialog(false);
      setActiveStep(1);
      showNotification(`Project "${projectData.name}" validated successfully. Please upload requirement files.`, 'success');
      
    } catch (error) {
      console.error('Error validating project:', error);
      const errorMessage = error.message || 'Unknown error occurred';
      showNotification(`Failed to validate project: ${errorMessage}`, 'error');
    } finally {
      setCreatingProject(false);
    }
  };

  // Step 2: File Selection and Upload
  const handleFileSelection = (event) => {
    const files = Array.from(event.target.files);
    const validFiles = files.filter(file => 
      file.type === 'application/pdf' || 
      file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    );

    if (validFiles.length !== files.length) {
      showNotification('Only PDF and DOCX files are supported', 'warning');
    }

    setSelectedFiles(validFiles);
    setUploadCompleted(false);
    
    if (validFiles.length > 0) {
      showNotification(`${validFiles.length} file(s) selected for upload`, 'info');
    }
  };

  const handleFileUpload = async () => {
    if (selectedFiles.length === 0) {
      showNotification('Please select files first', 'warning');
      return;
    }

    if (!projectData.id || !projectData.name) {
      showNotification('Project information missing', 'error');
      return;
    }

    if (!sessionId) {
      showNotification('Session not initialized. Please refresh the page.', 'error');
      return;
    }

    setIsUploading(true);
    
    try {
      const formData = new FormData();
      formData.append('project_name', projectData.name);
      formData.append('session_id', sessionId);
      formData.append('jira_project_key', projectData.jiraProjectKey);
      formData.append('notification_email', projectData.notificationEmail);
      
      selectedFiles.forEach((file) => {
        formData.append('files', file);
      });

      const response = await api.uploadRequirementFile(formData);
      
      console.log('Upload response:', response.data);
      
      // Handle new response structure
      if (response.data.upload_id && response.data.project_id) {
        // Store upload_id for later use
        setUploadId(response.data.upload_id);
        
        // Update project data with backend-generated project_id
        setProjectData(prev => ({
          ...prev,
          id: response.data.project_id
        }));
        
        // Process uploaded files
        const processedFiles = response.data.files.map(file => ({
          id: Date.now() + Math.random(),
          name: file.filename,
          size: file.file_size,
          type: file.content_type,
          uploaded: new Date(),
          status: 'uploaded',
          cloudPath: file.s3_key,
          fileId: file.file_id
        }));
        
        setUploadedFiles(processedFiles);
        setUploadCompleted(true);
        setIsUploading(false);
        
        // Show notification based on upload status
        const uploadStatus = response.data.upload_status;
        if (uploadStatus === 'completed') {
          showNotification(
            `Successfully uploaded and processed ${processedFiles.length} file(s)!`, 
            'success'
          );
        } else if (uploadStatus === 'partial') {
          const errors = response.data.errors || [];
          showNotification(
            `Partially uploaded: ${processedFiles.length} succeeded, ${errors.length} failed.`, 
            'warning'
          );
        }        
  
      } else {
        throw new Error('Upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
      setIsUploading(false);
      showNotification(
        getErrorMessage(error, 'Failed to upload files. Please try again.'),
        'error'
      );
    }
  };

  const removeFile = (fileId) => {
    setUploadedFiles(uploadedFiles.filter(file => file.id !== fileId));
    showNotification('File removed', 'info');
  };

  // Note: Clarification chat is handled in handleSendMessage below (calls backend)

  // Helper function to safely extract error message from API response
  const getErrorMessage = (error, defaultMessage = 'An error occurred') => {
    if (!error) return defaultMessage;
    
    // Check if detail is a string
    if (error.response?.data?.detail) {
      const detail = error.response.data.detail;
      if (typeof detail === 'string') {
        return detail;
      }
      // If detail is an array (FastAPI validation errors)
      if (Array.isArray(detail)) {
        return detail.map(err => err.msg || JSON.stringify(err)).join(', ');
      }
      // If detail is an object
      if (typeof detail === 'object') {
        return detail.msg || detail.message || JSON.stringify(detail);
      }
    }
    
    // Fallback to error message or default
    return error.message || defaultMessage;
  };

  // Helper function to parse AI response and extract structured data
  const parseAIResponse = (aiResponse) => {
    // Ensure aiResponse is a string
    let responseText = '';
    if (typeof aiResponse === 'string') {
      responseText = aiResponse;
    } else if (aiResponse && typeof aiResponse === 'object') {
      responseText = JSON.stringify(aiResponse);
    } else {
      responseText = String(aiResponse || '');
    }
    
    // Try to extract structured information from the AI response
    const lines = responseText.split('\n').filter(line => line.trim());
    const parsedData = {
      documentAnalysis: {
        totalPages: uploadedFiles.length * 15, // Estimate
        keyFeatures: Math.floor(extractedContent.length / 1000), // Rough estimate
        requirements: Math.floor(extractedContent.length / 500), // Rough estimate
        riskAreas: 3
      },
      testingStrategy: {
        functionalTests: 85,
        nonFunctionalTests: 25,
        integrationTests: 15,
        edgeCases: 20
      },
      coverage: {
        requirementsCoverage: 95,
        featureCoverage: 88,
        riskCoverage: 100
      },
      recommendations: []
    };

    // Try to extract recommendations from AI response
    const recommendationKeywords = ['recommend', 'suggest', 'should', 'consider', 'important'];
    const potentialRecommendations = lines.filter(line => 
      recommendationKeywords.some(keyword => line.toLowerCase().includes(keyword))
    ).slice(0, 5); // Take first 5 recommendations

    if (potentialRecommendations.length > 0) {
      parsedData.recommendations = potentialRecommendations.map(rec => 
        rec.replace(/^\d+\.?\s*/, '').trim() // Remove numbering if present
      );
    } else {
      // Fallback recommendations
      parsedData.recommendations = [
        "Focus on authentication and authorization testing",
        "Include performance testing for data processing modules",
        "Add comprehensive error handling test cases",
        "Consider accessibility testing requirements"
      ];
    }

    return parsedData;
  };

  const handleReviewDocuments = async () => {
    if (!uploadCompleted) {
      showNotification('Please upload files first', 'warning');
      return;
    }

    if (!projectData.id || !projectData.name) {
      showNotification('Project information missing', 'error');
      return;
    }

    if (!sessionId) {
      showNotification('Session not initialized. Please refresh the page.', 'error');
      return;
    }

    if (!uploadId) {
      showNotification('Upload information missing. Please upload files again.', 'error');
      return;
    }

    setIsProcessing(true);
    
    try {
      const response = await api.reviewRequirementSpecifications({
        session_id: sessionId,
        upload_id: uploadId,
        project_id: projectData.id,
        project_name: projectData.name,
        jira_project_key: projectData.jiraProjectKey,
        notification_email: projectData.notificationEmail
      });

      console.log('Review response:', response);

      // The response structure is: { session_id, project_id, status, message, analysis }
      // The actual JSON data is in response.data.message as a string
      let data;
      const apiResponse = response.data;
      
      // Check if we have the message field
      if (!apiResponse.message) {
        throw new Error('No response from analysis service');
      }
      
      // Parse the message string which contains the JSON structure
      const responseString = apiResponse.message;
      
      if (typeof responseString === 'string') {
        // Response is a string - try to parse JSON
        try {
          // Check if wrapped in ```json``` markdown
          const jsonMatch = responseString.match(/```json\n([\s\S]*?)\n```/);
          if (jsonMatch) {
            data = JSON.parse(jsonMatch[1]);
          } else {
            // Try parsing the whole string as JSON
            data = JSON.parse(responseString);
          }
        } catch (parseError) {
          console.error('Failed to parse JSON response:', parseError);
          throw new Error('Invalid response format from analysis service');
        }
      } else if (typeof responseString === 'object' && responseString !== null) {
        // Response is already a parsed object
        data = responseString;
      } else {
        throw new Error('Invalid response format from analysis service');
      }

      console.log('Parsed review data:', data);

      // Store raw metadata for control logic
      setReadinessMeta(data);

      // Build chat messages from assistant_response array
      const assistantLines = Array.isArray(data.assistant_response) 
        ? data.assistant_response 
        : (data.assistant_response ? [data.assistant_response] : []);
      
      const aiAnalysisText = assistantLines.join('\n\n') || '';

      // Keep existing parsed readinessPlan for existing UI widgets
      const parsedData = aiAnalysisText ? parseAIResponse(aiAnalysisText) : parseAIResponse(data.readiness_plan ? JSON.stringify(data.readiness_plan) : '');
      const mergedPlan = {
        ...parsedData,
        aiAnalysis: aiAnalysisText,
        // keep a reference to backend readiness summary
        backendReadiness: data.readiness_plan || null,
        test_generation_status: data.test_generation_status || {},
        // Store estimated counts for display
        estimatedCounts: {
          epics: data.readiness_plan?.estimated_epics || 0,
          features: data.readiness_plan?.estimated_features || 0,
          useCases: data.readiness_plan?.estimated_use_cases || 0,
          testCases: data.readiness_plan?.estimated_test_cases || 0
        }
      };

      setReadinessPlan(mergedPlan);
      setIsProcessing(false);
      
      // Check status and overall_status to determine next step
      const status = data.status || '';
      const overall = data.readiness_plan?.overall_status || '';
      const nextAction = data.next_action || '';
      const testGenStatus = data.test_generation_status?.ready_for_generation || false;

      console.log('Review documents - checking readiness:', { 
        status, 
        overall, 
        nextAction,
        testGenStatus, 
        data 
      });

      // Determine if ready for test generation
      const isReady = (
        overall.toLowerCase().includes('ready for test generation') || 
        overall.toLowerCase() === 'ready' ||
        status === 'ready_for_generation' ||
        testGenStatus
      );

      if (isReady) {
        // Ready for test generation: disable assistant, enable generate, advance to step 3
        setAssistantEnabled(false);
        setActiveStep(3);
        showNotification('Requirements are ready for test case generation!', 'success');
        console.log('Advanced to step 3 after review - ready for generation');
        
        // Show assistant final confirmation in chat
        const initialMessage = {
          id: Date.now(),
          text: aiAnalysisText || "All clarifications have been addressed. Ready for test case generation.",
          sender: 'ai',
          timestamp: new Date()
        };
        setChatMessages([initialMessage]);
      } else {
        // Not ready: enable assistant, stay on step 2 (Review & Chat)
        setAssistantEnabled(true);
        setActiveStep(2);
        
        // Determine notification message based on status
        let notificationMessage = 'Clarifications needed - please use the chat to provide additional information.';
        if (status === 'review_in_progress' || nextAction === 'await_user_clarifications') {
          notificationMessage = 'Review in progress - please provide clarifications as requested.';
        }
        
        showNotification(notificationMessage, 'warning');
        
        // Create chat messages from assistant_response array
        const initialMessages = assistantLines.length > 0 
          ? assistantLines.map((m, i) => ({ 
              id: Date.now() + i + 1, 
              text: m, 
              sender: 'ai', 
              timestamp: new Date() 
            })) 
          : [{ 
              id: Date.now(), 
              text: 'The analysis indicates clarifications are needed. Please provide the requested information.', 
              sender: 'ai', 
              timestamp: new Date() 
            }];
        setChatMessages(initialMessages);
      }
    } catch (error) {
      console.error('Review error:', error);
      setIsProcessing(false);
      showNotification(
        getErrorMessage(error, 'Failed to analyze documents. Please try again.'),
        'error'
      );
    }
  };

  // Clarification chat handler that calls backend and loops until overall_status becomes Ready
  const handleSendMessage = async () => {
    if (!newMessage.trim()) return;

    const userMessage = {
      id: Date.now(),
      text: newMessage,
      sender: 'user',
      timestamp: new Date()
    };

    // Append user message to chat
    setChatMessages(prev => [...prev, userMessage]);
    setNewMessage('');
    setIsProcessing(true);
    setIsChatProcessing(true); // Indicate this is chat processing

    try {
      // Call chat API - backend expects { session_id, user_message }
      const payload = {
        session_id: sessionId,
        user_message: userMessage.text
      };

      const resp = await api.requirementClarificationChat(payload);
      console.log('Chat response:', resp.data);
      
      // Parse the agent_response from the backend
      // Response structure: { session_id, agent_response, status }
      // agent_response contains JSON string with one of two formats
      const responseString = resp.data.agent_response || resp.data;
      let respData;
      
      if (typeof responseString === 'string') {
        try {
          const jsonMatch = responseString.match(/```json\n([\s\S]*?)\n```/);
          if (jsonMatch) {
            respData = JSON.parse(jsonMatch[1]);
          } else {
            respData = JSON.parse(responseString);
          }
        } catch (parseError) {
          console.error('Failed to parse clarification response:', parseError);
          respData = { assistant_response: [responseString] };
        }
      } else {
        respData = responseString;
      }

      // Extract assistant reply from the response
      let assistantReply;
      if (respData?.assistant_response) {
        if (Array.isArray(respData.assistant_response)) {
          assistantReply = respData.assistant_response.join('\n');
        } else if (typeof respData.assistant_response === 'string') {
          assistantReply = respData.assistant_response;
        } else {
          assistantReply = 'Thank you for the clarification.';
        }
      } else if (respData?.action_summary && typeof respData.action_summary === 'string') {
        // For ready_for_generation status
        assistantReply = respData.action_summary;
      } else {
        assistantReply = 'Thank you for the clarification.';
      }

      const aiMessage = {
        id: Date.now() + 1,
        text: assistantReply,
        sender: 'ai',
        timestamp: new Date()
      };

      setChatMessages(prev => [...prev, aiMessage]);

      // Update readiness meta if backend returned updated readiness_plan
      if (respData) {
        setReadinessMeta(respData);
      }

      // Check status to see if ready for generation
      const status = respData?.status;
      const overall = respData?.readiness_plan?.overall_status || readinessMeta?.readiness_plan?.overall_status || null;
      const testGenStatus = respData?.test_generation_status?.ready_for_generation || readinessMeta?.test_generation_status?.ready_for_generation || false;

      console.log('Checking readiness:', { status, overall, testGenStatus, respData });

      if (status === 'ready_for_generation' || 
          (overall && (overall.toLowerCase().includes('ready for test generation') || overall.toLowerCase().includes('ready'))) || 
          testGenStatus) {
        // Ready to generate - stay on step 3 (Review & Chat) to show the Generate Test Cases button
        setAssistantEnabled(false);
        // Stay on current step (step 3 - index 2) - don't advance to step 4 yet
        showNotification('Requirements are ready for test generation! Click the Generate Test Cases button to proceed.', 'success');
        console.log('Ready for generation - staying on step 3 to show Generate button');
      } else {
        // Still needs clarification; keep assistant enabled and stay on step 2
        setAssistantEnabled(true);
        console.log('Still needs clarification, staying on step 3 for more chat');
        // Don't change step - stay on Review & Chat
      }

      setIsProcessing(false);
      setIsChatProcessing(false);
    } catch (err) {
      console.error('Clarification chat error:', err);
      setIsProcessing(false);
      setIsChatProcessing(false);
      
      // Add error message to chat
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I encountered an error processing your message. Please try again.',
        sender: 'ai',
        timestamp: new Date()
      };
      setChatMessages(prev => [...prev, errorMessage]);
      
      // Extract error message safely
      let errorText = 'Clarification request failed';
      if (err.response?.data?.detail && typeof err.response.data.detail === 'string') {
        errorText = err.response.data.detail;
      } else if (err.message && typeof err.message === 'string') {
        errorText = err.message;
      }
      
      showNotification(errorText, 'error');
    }
  };

  // Step 4: Generate Test Cases
  const handleGenerateTestCases = useCallback(async () => {
    if (!projectData.id || !projectData.name) {
      showNotification('Project information missing', 'error');
      return;
    }

    // Prevent multiple concurrent calls
    if (isGenerating) {
      console.log('Test case generation already in progress, ignoring duplicate call');
      return;
    }

    setIsGenerating(true);
    
    try {
      const payload = {
        session_id: sessionId,
        project_id: projectData.id,
        jira_project_key: projectData.jiraProjectKey,
        notification_email: projectData.notificationEmail,
        approved: true
      };

      console.log('Generating test cases with payload:', payload);
      const response = await api.generateTestCases(payload);
      
      console.log('Test case generation response:', response);

      // Parse the response - the JSON structure is in response.data.message
      const responseData = response.data;
      let testCaseData;
      
      // Extract the message field which contains the JSON structure
      const messageString = responseData.message || responseData.response || responseData;
      
      if (typeof messageString === 'string') {
        try {
          // Try to extract JSON from markdown code blocks first
          const jsonMatch = messageString.match(/```json\n([\s\S]*?)\n```/);
          if (jsonMatch) {
            testCaseData = JSON.parse(jsonMatch[1]);
          } else {
            // Parse as plain JSON
            testCaseData = JSON.parse(messageString);
          }
        } catch (parseError) {
          console.error('Failed to parse test case response:', parseError);
          // Fallback structure if parsing fails
          testCaseData = { status: 'failed', test_generation_status: { status: 'failed' } };
        }
      } else if (typeof messageString === 'object' && messageString !== null) {
        testCaseData = messageString;
      } else {
        testCaseData = { status: 'failed', test_generation_status: { status: 'failed' } };
      }

      // Check if test generation was completed successfully
      const generationStatus = responseData.status || testCaseData.status;
      if (generationStatus === 'generation_completed' || testCaseData.status === 'mcp_push_complete') {
        console.log('Test cases generated successfully:', testCaseData);
        
        // Store generation data for popup
        setGenerationData(testCaseData);
        
        // Show generation summary popup
        setGenerationSummaryOpen(true);
        setIsGenerating(false);
        
        showNotification('Test cases generated successfully!', 'success');
        
      } else {
        // Test generation failed or is still in progress
        const status = testGenerationStatus?.status || 'unknown';
        console.log('Test generation status:', status);
        
        setIsGenerating(false);
        showNotification(`Test generation status: ${status}. Please try again if needed.`, 'warning');
        
        // Don't advance to next step if generation wasn't completed
      }
      
    } catch (error) {
      console.error('Test case generation error:', error);
      setIsGenerating(false);
      
      // Show error notification
      const errorMessage = getErrorMessage(error, 'Failed to generate test cases. Please try again.');
      showNotification(errorMessage, 'error');
      
      // Don't advance to next step on error - let user try again
      // Optionally, show fallback test cases for demo purposes but don't advance step
      // const fallbackTestCases = generateFallbackTestCases();
      // setGeneratedTestCases(fallbackTestCases);
    }
  }, [projectData.id, projectData.name, isGenerating, readinessMeta?.readiness_plan, showNotification]);

  const pushToServices = async () => {
    try {
      setPushingToServices(true);
      setGenerationSummaryOpen(false); // Close popup and show loading
      
      const response = await api.post('/push_test_artifacts_to_jira_firestore', {
        prompt: `Push generated artifacts to Jira and Firestore for project ${projectData.name} (ID: ${projectData.id})`
      });
      
      // Parse response
      let responseData = response.data.response || response.data;
      if (typeof responseData === 'string' && responseData.includes('```json')) {
        const jsonMatch = responseData.match(/```json\n([\s\S]*?)\n```/);
        if (jsonMatch) {
          responseData = JSON.parse(jsonMatch[1]);
        }
      }
      
      if (responseData.status === 'mcp_push_complete') {
        showNotification('Artifacts successfully pushed to Jira and Firestore!', 'success');
        
        // Update test generation stats with push status
        setTestGenerationStats({
          epics_created: responseData.test_generation_status?.epics_created || generationData?.test_generation_status?.epics_generated || 0,
          features_created: responseData.test_generation_status?.features_created || generationData?.test_generation_status?.features_generated || 0,
          use_cases_created: responseData.test_generation_status?.use_cases_created || generationData?.test_generation_status?.use_cases_generated || 0,
          test_cases_created: responseData.test_generation_status?.test_cases_created || generationData?.test_generation_status?.test_cases_generated || 0,
          approved_items: responseData.test_generation_status?.approved_items || generationData?.test_generation_status?.approved_items || 0,
          clarifications_needed: responseData.test_generation_status?.clarifications_needed || generationData?.test_generation_status?.clarifications_needed || 0,
          stored_in_firestore: true,
          pushed_to_jira: true
        });
        
        // Move to step 4 to show results
        setActiveStep(3);
      } else {
        showNotification('Failed to push artifacts to services', 'error');
      }
    } catch (error) {
      console.error('Error pushing to services:', error);
      showNotification('Failed to push artifacts to services', 'error');
    } finally {
      setPushingToServices(false);
    }
  };

  // Helper function to generate fallback test cases
  const generateFallbackTestCases = () => {
    return [
      {
        id: 'tc-001',
        category: 'Authentication',
        title: 'User Login Validation',
        priority: 'High',
        status: 'Generated',
        children: [
          {
            id: 'tc-001-01',
            title: 'Valid credentials login',
            steps: ['Navigate to login page', 'Enter valid username', 'Enter valid password', 'Click login button'],
            expected: 'User should be redirected to dashboard',
            priority: 'High'
          },
          {
            id: 'tc-001-02',
            title: 'Invalid credentials login',
            steps: ['Navigate to login page', 'Enter invalid username', 'Enter invalid password', 'Click login button'],
            expected: 'Error message should be displayed',
            priority: 'High'
          }
        ]
      },
      {
        id: 'tc-002',
        category: 'Data Processing',
        title: 'File Upload and Processing',
        priority: 'Medium',
        status: 'Generated',
        children: [
          {
            id: 'tc-002-01',
            title: 'Valid file upload',
            steps: ['Navigate to upload page', 'Select valid file', 'Click upload button'],
            expected: 'File should be uploaded and processed successfully',
            priority: 'Medium'
          },
          {
            id: 'tc-002-02',
            title: 'Invalid file type upload',
            steps: ['Navigate to upload page', 'Select invalid file type', 'Click upload button'],
            expected: 'Error message for unsupported file type',
            priority: 'Medium'
          }
        ]
      },
      {
        id: 'tc-003',
        category: 'Performance',
        title: 'System Performance Tests',
        priority: 'Medium',
        status: 'Generated',
        children: [
          {
            id: 'tc-003-01',
            title: 'Load testing with 100 concurrent users',
            steps: ['Setup load testing environment', 'Configure 100 virtual users', 'Execute load test'],
            expected: 'System should handle load with <2s response time',
            priority: 'Medium'
          }
        ]
      }
    ];
  };

  // Step 5: Export Test Cases
  const handleExportTestCases = async (format = 'pdf') => {
    if (generatedTestCases.length === 0) {
      showNotification('No test cases to export', 'warning');
      return;
    }

    try {
      setIsProcessing(true);
      
      // Format data for export service
      const exportData = {
        project: {
          id: projectData.id || 'test-case-gen',
          name: projectData.name || 'Generated Test Cases',
          description: projectData.description || 'Test cases generated from requirements',
          created_at: projectData.created || new Date().toISOString(),
          last_updated: new Date().toISOString(),
          total_test_cases: generatedTestCases.length,
          model_explanation: 'Test cases generated using AI-powered analysis of requirement documents'
        },
        epics: [{
          id: 'epic-1',
          title: 'Main Epic',
          description: 'Primary epic containing all generated test features',
          model_explanation: 'Epic created to organize generated test cases hierarchically',
          features: [{
            id: 'feature-1',
            title: 'Generated Features',
            description: 'Features extracted from requirement analysis',
            model_explanation: 'Features derived from requirement document analysis',
            use_cases: [{
              id: 'use-case-1',
              title: 'Test Use Cases',
              description: 'Use cases covering requirement functionality',
              model_explanation: 'Use cases generated based on functional requirements',
              test_cases: generatedTestCases.map((testCase, index) => ({
                id: testCase.id || `tc-${index + 1}`,
                title: testCase.title || testCase.name || `Test Case ${index + 1}`,
                description: testCase.description || 'Generated test case',
                test_steps: Array.isArray(testCase.steps) ? testCase.steps : [testCase.steps || 'Execute test'],
                expected_result: testCase.expectedResult || testCase.expected || 'Test passes successfully',
                test_data: testCase.testData || {},
                priority: testCase.priority || 'Medium',
                tags: testCase.tags || [],
                model_explanation: testCase.model_explanation || 'Test case generated from requirement analysis'
              }))
            }]
          }]
        }]
      };
      
      // Use export service
      const exportService = new ExportService();
      await exportService.exportProject(exportData, format);
      
      showNotification(`Test cases exported as ${format.toUpperCase()}`, 'success');
    } catch (error) {
      console.error('Export error:', error);
      showNotification('Failed to export test cases', 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  // Chat Message Component
  const ChatMessage = ({ message }) => (
    <Box
      sx={{
        display: 'flex',
        justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
        mb: 2,
        px: 1
      }}
    >
      <Card
        sx={{
          maxWidth: '85%',
          bgcolor: message.sender === 'user' ? 'primary.main' : 'grey.100',
          color: message.sender === 'user' ? 'white' : 'text.primary',
          boxShadow: 1
        }}
      >
        <CardContent sx={{ py: 1, px: 2, '&:last-child': { pb: 1 } }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <Avatar
              sx={{
                width: 24,
                height: 24,
                mr: 1,
                bgcolor: message.sender === 'user' ? 'primary.dark' : 'secondary.main'
              }}
            >
              {message.sender === 'user' ? <PersonIcon /> : <BotIcon />}
            </Avatar>
            <Typography variant="caption">
              {message.sender === 'user' ? 'You' : 'AI Assistant'}
            </Typography>
          </Box>
          <Typography 
            variant="body2" 
            sx={{ 
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              lineHeight: 1.4
            }}
          >
            {typeof message.text === 'string' ? message.text : 'Invalid message format'}
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );

  // Test Case Tree Component
  const TestCaseTree = ({ testCases }) => (
    <TreeView
      defaultCollapseIcon={<ExpandMoreIcon />}
      defaultExpandIcon={<FolderIcon />}
      sx={{ height: 400, flexGrow: 1, maxWidth: '100%', overflowY: 'auto' }}
    >
      {testCases.map((category) => (
        <TreeItem
          key={category.id}
          nodeId={category.id}
          label={
            <Box sx={{ display: 'flex', alignItems: 'center', py: 1 }}>
              <Typography variant="subtitle2">{category.title}</Typography>
              <Chip
                label={category.priority}
                size="small"
                color={category.priority === 'High' ? 'error' : 'default'}
                sx={{ ml: 1 }}
              />
            </Box>
          }
        >
          {category.children?.map((testCase) => (
            <TreeItem
              key={testCase.id}
              nodeId={testCase.id}
              label={
                <Box sx={{ py: 0.5 }}>
                  <Typography variant="body2">{testCase.title}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {testCase.steps?.length || 0} steps
                  </Typography>
                </Box>
              }
            />
          ))}
        </TreeItem>
      ))}
    </TreeView>
  );

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Test Case Generation
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Generate comprehensive test cases from your requirement documents
        </Typography>
      </Box>



      {/* Main Stepper */}
      <Paper sx={{ p: 3 }}>
        <Stepper activeStep={activeStep} orientation="vertical">
          {steps.map((step, index) => (
            <Step key={step.label}>
              <StepLabel>
                <Typography variant="h6">{step.label}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {step.description}
                </Typography>
              </StepLabel>
              <StepContent>
                {/* Step 1: Create New Project */}
                {index === 0 && (
                  <Box sx={{ py: 2 }}>
                    {!projectData.created ? (
                      <Card sx={{ mb: 2 }}>
                        <CardContent>
                          <Typography variant="h6" gutterBottom>
                            Create New Project
                          </Typography>
                          <Button
                            variant="contained"
                            startIcon={<AddIcon />}
                            onClick={handleOpenNewProjectDialog}
                          >
                            Create New Project
                          </Button>
                        </CardContent>
                      </Card>
                    ) : (
                      <Card sx={{ mb: 2 }}>
                        <CardContent>
                          <Typography variant="h6" gutterBottom>
                            Project: {projectData.name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {projectData.description}
                          </Typography>
                          <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                            Created: {projectData.created.toLocaleString()}
                          </Typography>
                        </CardContent>
                      </Card>
                    )}
                    <Button
                      variant="contained"
                      onClick={() => setActiveStep(1)}
                      disabled={!projectData.created}
                    >
                      Continue
                    </Button>
                  </Box>
                )}

                {/* Step 2: Upload Requirements */}
                {index === 1 && (
                  <Box sx={{ py: 2 }}>
                    <Card sx={{ mb: 2 }}>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Upload Requirement Documents
                        </Typography>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Select PDF or DOCX files containing your project requirements
                        </Typography>
                        
                        {/* File Selection */}
                        <Box sx={{ mt: 2, mb: 2 }}>
                          <input
                            accept=".pdf,.docx"
                            style={{ display: 'none' }}
                            id="file-select"
                            type="file"
                            multiple
                            onChange={handleFileSelection}
                          />
                          <label htmlFor="file-select">
                            <Button
                              variant="outlined"
                              component="span"
                              startIcon={<FileIcon />}
                              disabled={isUploading}
                            >
                              Select Files
                            </Button>
                          </label>
                        </Box>

                        {/* Selected Files Display */}
                        {selectedFiles.length > 0 && (
                          <Box sx={{ mb: 2 }}>
                            <Typography variant="subtitle2" gutterBottom>
                              Selected Files ({selectedFiles.length})
                            </Typography>
                            <List>
                              {selectedFiles.map((file, index) => (
                                <ListItem key={index}>
                                  <ListItemIcon>
                                    <DocumentIcon />
                                  </ListItemIcon>
                                  <ListItemText
                                    primary={file.name}
                                    secondary={`${(file.size / 1024).toFixed(1)} KB - ${file.type.includes('pdf') ? 'PDF' : 'DOCX'}`}
                                  />
                                </ListItem>
                              ))}
                            </List>
                            
                            {/* Upload Button */}
                            <Button
                              variant="contained"
                              startIcon={isUploading ? <CircularProgress size={20} /> : <UploadIcon />}
                              onClick={handleFileUpload}
                              disabled={isUploading}
                              sx={{ mt: 1 }}
                            >
                              {isUploading ? 'Uploading...' : 'Upload Files'}
                            </Button>
                          </Box>
                        )}

                        {isUploading && <LinearProgress sx={{ mb: 2 }} />}

                        {/* Uploaded Files Display */}
                        {uploadedFiles.length > 0 && (
                          <Box>
                            <Alert severity="success" sx={{ mb: 2 }}>
                              Successfully uploaded and processed {uploadedFiles.length} file(s)!
                            </Alert>
                            <Typography variant="subtitle2" gutterBottom>
                              Processed Files ({uploadedFiles.length})
                            </Typography>
                            <List>
                              {uploadedFiles.map((file) => (
                                <ListItem key={file.id}>
                                  <ListItemIcon>
                                    <CheckIcon color="success" />
                                  </ListItemIcon>
                                  <ListItemText
                                    primary={file.name}
                                    secondary={`${(file.size / 1024).toFixed(1)} KB - Processed ${file.uploaded.toLocaleTimeString()} - ${file.textLength} characters extracted`}
                                  />
                                  <IconButton onClick={() => removeFile(file.id)}>
                                    <DeleteIcon />
                                  </IconButton>
                                </ListItem>
                              ))}
                            </List>
                          </Box>
                        )}
                      </CardContent>
                    </Card>
                    
                    <Stack direction="row" spacing={2}>
                      <Button onClick={() => setActiveStep(0)}>
                        Back
                      </Button>
                      <Button
                        variant="contained"
                        onClick={handleReviewDocuments}
                        disabled={!uploadCompleted || isProcessing}
                        startIcon={isProcessing ? <CircularProgress size={20} /> : <ChatIcon />}
                      >
                        {isProcessing ? 'Analyzing...' : 'Review Documents'}
                      </Button>
                    </Stack>
                  </Box>
                )}

                {/* Step 3: Review & Chat */}
                {index === 2 && (
                  <Box sx={{ py: 2 }}>
                    <Grid container spacing={3}>
                      {/* Readiness Plan */}
                      <Grid item xs={12} md={6}>
                        <Card>
                          <CardContent>
                            <Typography variant="h6" gutterBottom>
                              Readiness Plan
                            </Typography>
                            {isProcessing ? (
                              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4 }}>
                                <CircularProgress size={40} sx={{ mb: 2 }} />
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                  Analyzing with AI assistant...
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  This may take a few moments
                                </Typography>
                              </Box>
                            ) : readinessPlan ? (
                              <Box>
                                {/* AI Analysis Section */}
                                {readinessPlan.aiAnalysis && (
                                  <Accordion defaultExpanded>
                                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                      <Typography variant="subtitle1" sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center' }}>
                                        <BotIcon sx={{ mr: 1, color: 'primary.main' }} />
                                        AI Analysis Report
                                        <Chip 
                                          label="Live Analysis" 
                                          size="small" 
                                          color="success" 
                                          sx={{ ml: 1 }}
                                        />
                                      </Typography>
                                    </AccordionSummary>
                                    <AccordionDetails>
                                      <Paper 
                                        elevation={1} 
                                        sx={{ 
                                          p: 2, 
                                          backgroundColor: 'grey.50',
                                          maxHeight: 300,
                                          overflow: 'auto',
                                          border: '1px solid',
                                          borderColor: 'primary.light'
                                        }}
                                      >
                                        <Typography 
                                          variant="body2" 
                                          sx={{ 
                                            whiteSpace: 'pre-wrap',
                                            lineHeight: 1.6,
                                            color: 'text.primary'
                                          }}
                                        >
                                          {typeof readinessPlan.aiAnalysis === 'string' 
                                            ? readinessPlan.aiAnalysis 
                                            : 'Analysis data is not available'}
                                        </Typography>
                                      </Paper>
                                      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <Typography variant="caption" color="text.secondary">
                                          Analysis generated: {new Date().toLocaleString()}
                                        </Typography>
                                        <Chip 
                                          label={`${Math.ceil((readinessPlan.aiAnalysis && typeof readinessPlan.aiAnalysis === 'string' ? readinessPlan.aiAnalysis.length : 0) / 100)} insights`} 
                                          size="small" 
                                          variant="outlined"
                                        />
                                      </Box>
                                    </AccordionDetails>
                                  </Accordion>
                                )}

                                <Accordion defaultExpanded>
                                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                    <Typography>Readiness Plan</Typography>
                                  </AccordionSummary>
                                  <AccordionDetails>
                                    <Grid container spacing={2}>
                                      <Grid item xs={6}>
                                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                          <Typography variant="body2" fontWeight="bold">Estimated Epics:</Typography>
                                          <Chip 
                                            label={readinessMeta?.readiness_plan?.estimated_epics || readinessPlan?.backendReadiness?.estimated_epics || 0} 
                                            size="small" 
                                            color="primary" 
                                            sx={{ ml: 1 }} 
                                          />
                                        </Box>
                                      </Grid>
                                      <Grid item xs={6}>
                                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                          <Typography variant="body2" fontWeight="bold">Estimated Features:</Typography>
                                          <Chip 
                                            label={readinessMeta?.readiness_plan?.estimated_features || readinessPlan?.backendReadiness?.estimated_features || 0} 
                                            size="small" 
                                            color="secondary" 
                                            sx={{ ml: 1 }} 
                                          />
                                        </Box>
                                      </Grid>
                                      <Grid item xs={6}>
                                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                          <Typography variant="body2" fontWeight="bold">Estimated Use Cases:</Typography>
                                          <Chip 
                                            label={readinessMeta?.readiness_plan?.estimated_use_cases || readinessPlan?.backendReadiness?.estimated_use_cases || 0} 
                                            size="small" 
                                            color="info" 
                                            sx={{ ml: 1 }} 
                                          />
                                        </Box>
                                      </Grid>
                                      <Grid item xs={6}>
                                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                          <Typography variant="body2" fontWeight="bold">Estimated Test Cases:</Typography>
                                          <Chip 
                                            label={readinessMeta?.readiness_plan?.estimated_test_cases || readinessPlan?.backendReadiness?.estimated_test_cases || 0} 
                                            size="small" 
                                            color="success" 
                                            sx={{ ml: 1 }} 
                                          />
                                        </Box>
                                      </Grid>
                                      <Grid item xs={12}>
                                        <Divider sx={{ my: 1 }} />
                                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                          <Typography variant="body2" fontWeight="bold" color="text.secondary">
                                            Overall Status:
                                          </Typography>
                                          <Chip 
                                            label={readinessMeta?.readiness_plan?.overall_status || readinessPlan?.backendReadiness?.overall_status || 'Not Ready'} 
                                            size="small" 
                                            color={isReadyForGeneration ? "success" : "warning"}
                                            sx={{ ml: 1 }} 
                                          />
                                        </Box>
                                      </Grid>
                                    </Grid>
                                  </AccordionDetails>
                                </Accordion>
                              </Box>
                            ) : (
                              <Typography variant="body2" color="text.secondary">
                                Upload documents to see readiness plan
                              </Typography>
                            )}
                          </CardContent>
                        </Card>
                      </Grid>

                      {/* Chat Interface */}
                      <Grid item xs={12} md={6}>
                        <Card sx={{ height: 520, display: 'flex', flexDirection: 'column' }}>
                          <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', pb: 2 }}>
                            <Typography variant="h6" gutterBottom>
                              AI Assistant Chat
                              {!assistantEnabled && (
                                <Chip 
                                  label="Assistant Disabled - Ready for Generation" 
                                  size="small" 
                                  color="success" 
                                  sx={{ ml: 2 }}
                                />
                              )}
                              {assistantEnabled && (
                                <Chip 
                                  label="Clarifications Needed" 
                                  size="small" 
                                  color="warning" 
                                  sx={{ ml: 2 }}
                                />
                              )}
                            </Typography>
                            
                            {/* Chat Messages */}
                            <Box 
                              ref={chatMessagesRef}
                              sx={{ 
                                flex: 1, 
                                minHeight: '300px',
                                maxHeight: '350px',
                                overflowY: 'scroll',
                                overflowX: 'hidden',
                                mb: 2,
                                pr: 1,
                                scrollBehavior: 'smooth',
                                border: '1px solid rgba(0,0,0,0.1)',
                                borderRadius: '8px',
                                padding: '8px',
                                backgroundColor: 'rgba(0,0,0,0.02)',
                                // Custom scrollbar for webkit browsers
                                '&::-webkit-scrollbar': {
                                  width: '8px',
                                },
                                '&::-webkit-scrollbar-track': {
                                  background: '#f1f1f1',
                                  borderRadius: '4px',
                                },
                                '&::-webkit-scrollbar-thumb': {
                                  background: '#888',
                                  borderRadius: '4px',
                                  '&:hover': {
                                    background: '#555',
                                  },
                                },
                                // Firefox scrollbar
                                scrollbarWidth: 'thin',
                                scrollbarColor: '#888 #f1f1f1',
                              }}
                            >
                              {chatMessages.length === 0 && !isProcessing && (
                                <Box sx={{ 
                                  display: 'flex', 
                                  alignItems: 'center', 
                                  justifyContent: 'center', 
                                  height: '100%',
                                  flexDirection: 'column',
                                  color: 'text.secondary'
                                }}>
                                  <ChatIcon sx={{ fontSize: 48, mb: 2, opacity: 0.3 }} />
                                  <Typography variant="body2" align="center">
                                    {assistantEnabled 
                                      ? "Start a conversation by asking about requirements or test scenarios"
                                      : "Requirements analysis complete. Ready for test case generation."
                                    }
                                  </Typography>
                                </Box>
                              )}
                              {chatMessages.map((message) => (
                                <ChatMessage key={message.id} message={message} />
                              ))}
                              {isProcessing && (
                                <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
                                  <Card sx={{ bgcolor: 'grey.100' }}>
                                    <CardContent sx={{ py: 1, px: 2, '&:last-child': { pb: 1 } }}>
                                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                        <CircularProgress size={16} sx={{ mr: 1 }} />
                                        <Typography variant="body2">AI is typing...</Typography>
                                      </Box>
                                    </CardContent>
                                  </Card>
                                </Box>
                              )}
                            </Box>

                            {/* Chat Input - Fixed at bottom */}
                            <Box 
                              sx={{ 
                                display: 'flex', 
                                gap: 1,
                                mt: 'auto',
                                borderTop: '1px solid',
                                borderColor: 'divider',
                                pt: 2,
                                pb: 1,
                                backgroundColor: 'background.paper',
                                minHeight: 'auto'
                              }}
                            >
                              <TextField
                                fullWidth
                                size="small"
                                multiline
                                minRows={3}
                                maxRows={6}
                                placeholder={
                                  !assistantEnabled 
                                    ? "Requirements are ready for test generation - Assistant disabled"
                                    : isProcessing 
                                      ? "Analyzing with AI assistant..."
                                      : "Ask about requirements or test scenarios... (Shift+Enter for new line, Enter to send)"
                                }
                                value={newMessage}
                                onChange={(e) => setNewMessage(e.target.value)}
                                onKeyPress={(e) => {
                                  if (e.key === 'Enter' && !e.shiftKey && assistantEnabled && !isProcessing) {
                                    e.preventDefault();
                                    handleSendMessage();
                                  }
                                }}
                                disabled={!assistantEnabled || isProcessing}
                                sx={{
                                  '& .MuiInputBase-input': {
                                    color: !assistantEnabled ? 'text.disabled' : 'text.primary',
                                    resize: 'none', // Prevent manual resizing
                                  },
                                  '& .MuiInputBase-input::placeholder': {
                                    color: !assistantEnabled ? 'text.disabled' : 'text.secondary',
                                    opacity: 1,
                                  },
                                  '& .MuiInputBase-root': {
                                    alignItems: 'flex-start', // Align text to top when multiline
                                  }
                                }}
                              />
                              <IconButton 
                                onClick={handleSendMessage}
                                disabled={!assistantEnabled || !newMessage.trim() || isProcessing}
                                color="primary"
                                sx={{
                                  opacity: !assistantEnabled ? 0.3 : 1,
                                }}
                              >
                                <SendIcon />
                              </IconButton>
                            </Box>
                          </CardContent>
                        </Card>
                      </Grid>
                    </Grid>

                    <Stack direction="row" spacing={2} sx={{ mt: 3 }}>
                      <Button onClick={() => setActiveStep(1)}>
                        Back
                      </Button>
                      
                      {/* Show Generate Test Cases button if not yet generated */}
                      {!testGenerationStats ? (
                        <Button
                          variant="contained"
                          onClick={handleGenerateTestCases}
                          disabled={!isReadyForGeneration || isGenerating || pushingToServices}
                          startIcon={(isGenerating || pushingToServices) ? <CircularProgress size={20} /> : <TestCaseIcon />}
                        >
                          {pushingToServices ? 'Pushing to Services...' : isGenerating ? 'Generating...' : 'Generate Test Cases'}
                        </Button>
                      ) : (
                        /* Show Continue to Results button if test cases are already generated */
                        <Button
                          variant="contained"
                          onClick={() => setActiveStep(3)}
                          startIcon={<ViewIcon />}
                          color="success"
                        >
                          View Generated Test Cases
                        </Button>
                      )}
                    </Stack>
                  </Box>
                )}

                {/* Step 4: Generate Test Cases */}
                {index === 3 && (
                  <Box sx={{ py: 2 }}>
                    {/* Test Generation Statistics */}
                    {testGenerationStats && (
                      <Card sx={{ mb: 2 }}>
                        <CardContent>
                          <Typography variant="h6" gutterBottom>
                            Test Generation Summary
                          </Typography>
                          <Grid container spacing={2}>
                            <Grid item xs={6} sm={3}>
                              <Box sx={{ textAlign: 'center' }}>
                                <Typography variant="h4" color="primary">
                                  {testGenerationStats.epics_created}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  Epics Created
                                </Typography>
                              </Box>
                            </Grid>
                            <Grid item xs={6} sm={3}>
                              <Box sx={{ textAlign: 'center' }}>
                                <Typography variant="h4" color="secondary">
                                  {testGenerationStats.features_created}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  Features Created
                                </Typography>
                              </Box>
                            </Grid>
                            <Grid item xs={6} sm={3}>
                              <Box sx={{ textAlign: 'center' }}>
                                <Typography variant="h4" color="success.main">
                                  {testGenerationStats.use_cases_created}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  Use Cases Created
                                </Typography>
                              </Box>
                            </Grid>
                            <Grid item xs={6} sm={3}>
                              <Box sx={{ textAlign: 'center' }}>
                                <Typography variant="h4" color="info.main">
                                  {testGenerationStats.test_cases_created}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  Test Cases Created
                                </Typography>
                              </Box>
                            </Grid>
                          </Grid>
                          <Divider sx={{ my: 2 }} />
                          <Grid container spacing={2}>
                            <Grid item xs={12} sm={6}>
                              <Stack direction="row" spacing={1} alignItems="center">
                                <Chip 
                                  label={testGenerationStats.stored_in_firestore ? "Stored in Firestore" : "Not Stored"} 
                                  color={testGenerationStats.stored_in_firestore ? "success" : "error"}
                                  size="small"
                                />
                                <Chip 
                                  label={testGenerationStats.pushed_to_jira ? "Pushed to Jira" : "Not Pushed"} 
                                  color={testGenerationStats.pushed_to_jira ? "success" : "warning"}
                                  size="small"
                                />
                              </Stack>
                            </Grid>
                            <Grid item xs={12} sm={6}>
                              <Typography variant="body2" color="text.secondary">
                                Approved Items: {testGenerationStats.approved_items} | 
                                Clarifications Needed: {testGenerationStats.clarifications_needed}
                              </Typography>
                            </Grid>
                          </Grid>
                        </CardContent>
                      </Card>
                    )}

                    <Alert severity="info" sx={{ mb: 3 }}>
                      <Typography variant="body2">
                        <strong>Complete Details Available:</strong> Go to Dashboard page to see all generated test case details, 
                        hierarchical view with epics, features, use cases, and export options.
                      </Typography>
                    </Alert>

                    <Stack direction="row" spacing={2} sx={{ mt: 3 }}>
                      <Button onClick={() => setActiveStep(2)}>
                        Back
                      </Button>
                      <Button
                        variant="contained"
                        onClick={handleGoToDashboard}
                        startIcon={<ViewIcon />}
                      >
                        Go to Dashboard
                      </Button>
                    </Stack>
                  </Box>
                )}
              </StepContent>
            </Step>
          ))}
        </Stepper>
      </Paper>

      {/* New Project Dialog */}
      <Dialog open={newProjectDialog} onClose={() => setNewProjectDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Project</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Project Name"
            fullWidth
            variant="outlined"
            value={projectData.name}
            onChange={(e) => setProjectData({ ...projectData, name: e.target.value })}
            sx={{ mb: 2 }}
            required
          />
          <TextField
            margin="dense"
            label="Description (Optional)"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={projectData.description}
            onChange={(e) => setProjectData({ ...projectData, description: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Jira Project Key"
            fullWidth
            variant="outlined"
            value={projectData.jiraProjectKey}
            onChange={(e) => setProjectData({ ...projectData, jiraProjectKey: e.target.value })}
            sx={{ mb: 2 }}
            required
            helperText="e.g., PROJ, TEST, DEV"
          />
          <TextField
            margin="dense"
            label="Notification Email"
            fullWidth
            variant="outlined"
            type="email"
            value={projectData.notificationEmail}
            onChange={(e) => setProjectData({ ...projectData, notificationEmail: e.target.value })}
            required
            helperText="Email address for project notifications"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewProjectDialog(false)} disabled={creatingProject}>Cancel</Button>
          <Button 
            onClick={handleCreateProject} 
            variant="contained" 
            disabled={creatingProject}
            startIcon={creatingProject ? <CircularProgress size={16} /> : null}
          >
            {creatingProject ? 'Creating...' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Export Dialog */}
      <Dialog open={exportDialog} onClose={() => setExportDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Export Test Cases</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Export Format</InputLabel>
            <Select
              value={exportFormat}
              label="Export Format"
              onChange={(e) => setExportFormat(e.target.value)}
            >
              <MenuItem value="pdf">PDF Document</MenuItem>
              <MenuItem value="word">Word Document</MenuItem>
              <MenuItem value="xml">XML Format</MenuItem>
              <MenuItem value="markdown">Markdown Format</MenuItem>
            </Select>
          </FormControl>
          
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            The export will include all generated test cases with detailed steps, expected results, hierarchical structure, and AI model explanations.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialog(false)}>Cancel</Button>
          <Button 
            onClick={() => {
              handleExportTestCases(exportFormat);
              setExportDialog(false);
            }} 
            variant="contained" 
            startIcon={isProcessing ? <CircularProgress size={16} /> : <DownloadIcon />}
            disabled={isProcessing}
          >
            {isProcessing ? 'Exporting...' : 'Export'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Generation Summary Dialog */}
      <Dialog 
        open={generationSummaryOpen} 
        maxWidth="md" 
        fullWidth
        disableEscapeKeyDown
        PaperProps={{
          sx: {
            borderRadius: 3,
            boxShadow: '0 10px 40px rgba(0,0,0,0.1)'
          }
        }}
      >
        <DialogTitle sx={{ 
          textAlign: 'center', 
          pb: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 1,
          bgcolor: 'primary.50'
        }}>
          <CheckCircle color="success" />
          Test Cases Generated Successfully
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <Alert severity="success" sx={{ mb: 3 }}>
            All test cases have been generated successfully! Review the summary below and push to services.
          </Alert>
          
          {generationData && (
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid item xs={6} sm={3}>
                <Card sx={{ textAlign: 'center', bgcolor: 'primary.50' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                      <EpicIcon sx={{ fontSize: 32, color: 'primary.main', mb: 1 }} />
                      <Typography variant="h4" color="primary.main">
                        {generationData.epics_created || 0}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Epics Generated
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Card sx={{ textAlign: 'center', bgcolor: 'secondary.50' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                      <FeatureIcon sx={{ fontSize: 32, color: 'secondary.main', mb: 1 }} />
                      <Typography variant="h4" color="secondary.main">
                        {generationData.features_created || 0}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Features Generated
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Card sx={{ textAlign: 'center', bgcolor: 'success.50' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                      <UseCaseIcon sx={{ fontSize: 32, color: 'success.main', mb: 1 }} />
                      <Typography variant="h4" color="success.main">
                        {generationData.use_cases_created || 0}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Use Cases Generated
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Card sx={{ textAlign: 'center', bgcolor: 'info.50' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                      <CheckCircle sx={{ fontSize: 32, color: 'info.main', mb: 1 }} />
                      <Typography variant="h4" color="info.main">
                        {generationData.test_cases_created || 0}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Test Cases Generated
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}

          <Alert severity="info" sx={{ mb: 2 }}>
            <Typography variant="body2">
              Click "Push to Services" to save all generated artifacts to Firestore and create Jira issues.
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions sx={{ p: 3, gap: 2 }}>
          <Button 
            onClick={pushToServices}
            variant="contained"
            size="large"
            disabled={pushingToServices}
            startIcon={pushingToServices ? <CircularProgress size={16} /> : <CloudUploadIcon />}
            sx={{ minWidth: 200 }}
          >
            {pushingToServices ? 'Pushing to Services...' : 'Push to Services'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Test Case Generation Completion Dialog */}
      <Dialog 
        open={completionDialog} 
        onClose={handleCompletionDialogClose} 
        maxWidth="md" 
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 3,
            boxShadow: '0 10px 40px rgba(0,0,0,0.1)'
          }
        }}
      >
        <DialogTitle sx={{ 
          textAlign: 'center', 
          pb: 1,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 1
        }}>
          <CheckIcon />
          Test Case Generation Completed
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <Alert severity="success" sx={{ mb: 3 }}>
            Test cases have been successfully generated and stored in Firestore and Jira!
          </Alert>
          
          {testGenerationStats && (
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid item xs={6} sm={3}>
                <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'primary.50', borderRadius: 2 }}>
                  <Typography variant="h4" color="primary.main">
                    {testGenerationStats.epics_created}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Epics Created
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'secondary.50', borderRadius: 2 }}>
                  <Typography variant="h4" color="secondary.main">
                    {testGenerationStats.features_created}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Features Created
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'success.50', borderRadius: 2 }}>
                  <Typography variant="h4" color="success.main">
                    {testGenerationStats.use_cases_created}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Use Cases Created
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'info.50', borderRadius: 2 }}>
                  <Typography variant="h4" color="info.main">
                    {testGenerationStats.test_cases_created}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Test Cases Created
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          )}

          <Box sx={{ mb: 2 }}>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 1 }}>
              ✅ Stored in Firestore: {testGenerationStats?.stored_in_firestore ? 'Yes' : 'No'}
            </Typography>
            <Typography variant="body1" color="text.secondary">
              ✅ Pushed to Jira: {testGenerationStats?.pushed_to_jira ? 'Yes' : 'No'}
            </Typography>
          </Box>

          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              Go to the Dashboard page to see complete generated test case details and export options.
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions sx={{ p: 3, gap: 2 }}>
          <Button 
            onClick={handleCompletionDialogClose}
            variant="outlined"
          >
            View Generated Cases
          </Button>
          <Button 
            onClick={handleGoToDashboard}
            variant="contained"
            startIcon={<ViewIcon />}
          >
            Go to Dashboard
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default TestCaseGeneration;