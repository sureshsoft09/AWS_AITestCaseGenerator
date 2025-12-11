/* eslint-disable no-unused-vars */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  IconButton,
  Chip,
  LinearProgress,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  CircularProgress,
  Menu,
  MenuItem,
  ListItemButton,
  Collapse,
  Badge,
  Tooltip,
  Fab,
  Container,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Add as AddIcon,
  Folder as ProjectIcon,
  Assessment as EpicIcon,
  Functions as FeatureIcon,
  Assignment as UseCaseIcon,
  CheckCircle as TestCaseIcon,
  TrendingUp as TrendingUpIcon,
  Schedule as ScheduleIcon,
  Warning as WarningIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Info as InfoIcon,
  Download as DownloadIcon,
  Visibility as ViewIcon,
  Close as CloseIcon,
  Security as ComplianceIcon,
  Psychology as ExplanationIcon,
  Refresh as RefreshIcon,
  TableChart as ExcelIcon,
  Code as XmlIcon,
  Launch as LaunchIcon,
} from '@mui/icons-material';
import { useNotification } from '../contexts/NotificationContext';
import JiraImage from '../assets/Jira_Image.png';
import api from '../services/api';
import exportService from '../services/exportService';

// Custom Jira Icon component using the actual Jira image
const JiraIcon = ({ sx = {} }) => (
  <img 
    src={JiraImage} 
    alt="Jira" 
    style={{
      width: sx.fontSize || '16px',
      height: sx.fontSize || '16px',
      objectFit: 'contain',
      ...sx
    }}
  />
);

const Dashboard = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [expandedProjects, setExpandedProjects] = useState({});
  const [expandedEpics, setExpandedEpics] = useState({});
  const [expandedFeatures, setExpandedFeatures] = useState({});
  const [expandedUseCases, setExpandedUseCases] = useState({});
  const [modelExplanationDialog, setModelExplanationDialog] = useState({
    open: false,
    title: '',
    explanation: '',
    loading: false,
  });
  const [statistics, setStatistics] = useState({
    totalProjects: 0,
    totalEpics: 0,
    totalFeatures: 0,
    totalUseCases: 0,
    totalTestCases: 0,
  });
  const [exportMenuAnchor, setExportMenuAnchor] = useState(null);
  const [selectedProjectForExport, setSelectedProjectForExport] = useState(null);
  const [exportLoading, setExportLoading] = useState(false);
  const { showNotification } = useNotification();

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/projects');
      const projectsData = response.data.projects || [];
      
      // Load detailed hierarchy for each project
      const projectsWithHierarchy = await Promise.all(
        projectsData.map(async (project) => {
          try {
            const hierarchyResponse = await api.get(`/api/projects/${project.project_id}/hierarchy`);
            return {
              ...project,
              hierarchy: hierarchyResponse.data.hierarchy || {}
            };
          } catch (error) {
            console.error(`Error loading hierarchy for project ${project.project_id}:`, error);
            return {
              ...project,
              hierarchy: {}
            };
          }
        })
      );
      
      setProjects(projectsWithHierarchy);
      calculateStatistics(projectsWithHierarchy);
      
    } catch (error) {
      console.error('Error loading projects:', error);
      showNotification('Failed to load projects', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadProjects();
    setRefreshing(false);
    showNotification('Projects refreshed successfully', 'success');
  };

  const handleOpenExportMenu = (event, project) => {
    setExportMenuAnchor(event.currentTarget);
    setSelectedProjectForExport(project);
  };

  const handleCloseExportMenu = () => {
    setExportMenuAnchor(null);
    setSelectedProjectForExport(null);
  };

  const handleExport = async (format) => {
    if (!selectedProjectForExport) return;
    setExportLoading(true);
    try {
      const project = selectedProjectForExport;
      // Use the hierarchy object as the base, but include a friendly name and id
      const projectData = {
        ...project.hierarchy,
        name: project.project_name,
        project_id: project.project_id,
        jira_project_key: project.jira_project_key,
        jira_project_url: project.jira_project_url,
        statistics: project.statistics || {}
      };
      await exportService.exportProject(projectData, format, project.project_name);
      showNotification(`Exported ${project.project_name} as ${format.toUpperCase()}`, 'success');
    } catch (err) {
      console.error('Export error', err);
      showNotification('Export failed', 'error');
    } finally {
      setExportLoading(false);
      handleCloseExportMenu();
    }
  };

  const calculateStatistics = (projectsData) => {
    let totalEpics = 0;
    let totalFeatures = 0;
    let totalUseCases = 0;
    let totalTestCases = 0;

    projectsData.forEach(project => {
      const epics = project.hierarchy?.epics || [];
      totalEpics += epics.length;
      
      epics.forEach(epic => {
        const features = epic.features || [];
        totalFeatures += features.length;
        
        features.forEach(feature => {
          const useCases = feature.use_cases || [];
          totalUseCases += useCases.length;
          
          useCases.forEach(useCase => {
            const testCases = useCase.test_cases || [];
            totalTestCases += testCases.length;
          });
        });
      });
    });

    setStatistics({
      totalProjects: projectsData.length,
      totalEpics,
      totalFeatures,
      totalUseCases,
      totalTestCases,
    });
  };

  const handleModelExplanation = async (item, itemType, projectId) => {
    setModelExplanationDialog({
      open: true,
      title: `${itemType}: ${item.title || item.use_case_title || item.test_case_title || item.project_name}`,
      explanation: '',
      loading: true,
    });

    try {
      const itemId = item.epic_id || item.feature_id || item.use_case_id || item.test_case_id || item.project_id;
      const response = await api.get(`/api/projects/${projectId}/model-explanation`, {
        params: { item_type: itemType, item_id: itemId }
      });
      
      setModelExplanationDialog(prev => ({
        ...prev,
        explanation: response.data.explanation || item.model_explanation || 'No explanation available',
        loading: false,
      }));
    } catch (error) {
      console.error('Error loading model explanation:', error);
      setModelExplanationDialog(prev => ({
        ...prev,
        explanation: item.model_explanation || 'No explanation available',
        loading: false,
      }));
    }
  };

  const handleExportProject = async (project, format) => {
    try {
      const projectData = {
        project_id: project.project_id,
        name: project.project_name,
        created_date: project.created_at,
        status: project.status,
        jira_project_key: project.jira_project_key,
        jira_project_url: project.jira_project_url,
        statistics: {
          total_epics: project.total_epics || 0,
          total_features: project.total_features || 0,
          total_use_cases: project.total_use_cases || 0,
          total_test_cases: project.total_test_cases || 0,
        },
        epics: project.hierarchy?.epics || []
      };

      const result = await exportService.exportProject(projectData, format, project.project_name);
      showNotification(`Successfully exported ${project.project_name} as ${format.toUpperCase()}`, 'success');
      return result;
    } catch (error) {
      console.error(`Error exporting project as ${format}:`, error);
      showNotification(`Failed to export project as ${format.toUpperCase()}`, 'error');
    }
  };



  const toggleProjectExpansion = (projectId) => {
    setExpandedProjects(prev => ({
      ...prev,
      [projectId]: !prev[projectId]
    }));
  };

  const toggleEpicExpansion = (epicId) => {
    setExpandedEpics(prev => ({
      ...prev,
      [epicId]: !prev[epicId]
    }));
  };

  const toggleFeatureExpansion = (featureId) => {
    setExpandedFeatures(prev => ({
      ...prev,
      [featureId]: !prev[featureId]
    }));
  };

  const toggleUseCaseExpansion = (useCaseId) => {
    setExpandedUseCases(prev => ({
      ...prev,
      [useCaseId]: !prev[useCaseId]
    }));
  };

  const StatCard = ({ title, value, subtitle, icon, color = '#667eea' }) => (
    <Card
      sx={{
        height: '100%',
        background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(248, 250, 255, 0.9) 100%)',
        border: '1px solid rgba(102, 126, 234, 0.1)',
        transition: 'transform 0.2s ease, box-shadow 0.2s ease',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: '0 8px 25px rgba(102, 126, 234, 0.15)',
        },
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700, color: color, mb: 1 }}>
              {value}
            </Typography>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
              {title}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {subtitle}
            </Typography>
          </Box>
          <Avatar sx={{ bgcolor: `${color}20`, color: color, width: 56, height: 56 }}>
            {icon}
          </Avatar>
        </Box>
      </CardContent>
    </Card>
  );

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

  const ComplianceDisplay = ({ item, showIcon = true }) => {
    const compliance = item.compliance_mapping || [];
    
    if (!compliance || compliance.length === 0) {
      return null;
    }

    return (
      <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 0.5 }}>
        {showIcon && <ComplianceIcon sx={{ fontSize: 16, color: '#ff9800', mr: 0.5 }} />}
        <Typography variant="caption" color="text.secondary" sx={{ mr: 1 }}>
          Compliance:
        </Typography>
        {compliance.map((item, index) => (
          <Chip
            key={index}
            label={typeof item === 'string' ? item : item.standard || item.name || 'Unknown'}
            size="small"
            variant="outlined"
            color="warning"
            sx={{ fontSize: '0.7rem', height: 20 }}
          />
        ))}
      </Box>
    );
  };

  const TestCaseItem = ({ testCase, projectId }) => (
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
              <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 0.5 }}>
                <Typography variant="subtitle2">
                  {testCase.test_case_title || `Test Case ${testCase.test_case_id}`}
                </Typography>
                <InfoButton
                  onClick={() => handleModelExplanation(testCase, 'test_case', projectId)}
                  hasInfo={!!testCase.model_explanation}
                  tooltip="View AI Model Explanation"
                />
                {testCase.jira_issue_key && (
                  <Chip
                    icon={<JiraIcon sx={{ fontSize: '14px' }} />}
                    label={testCase.jira_issue_key}
                    size="small"
                    variant="outlined"
                    color="primary"
                    sx={{ 
                      fontSize: '0.7rem', 
                      height: '20px',
                      borderColor: '#0052CC',
                      color: '#0052CC',
                      '& .MuiChip-icon': {
                        marginLeft: '4px',
                        marginRight: '-2px'
                      }
                    }}
                  />
                )}
                {testCase.priority && (
                  <Chip
                    label={`Priority: ${testCase.priority}`}
                    size="small"
                    variant="outlined"
                    color={testCase.priority === 'High' ? 'error' : testCase.priority === 'Medium' ? 'warning' : 'default'}
                    sx={{ fontSize: '0.7rem', height: '20px' }}
                  />
                )}
              </Box>
              {testCase.review_status && (
                <Chip
                  label={testCase.review_status}
                  size="small"
                  color={testCase.review_status === 'Approved' ? 'success' : 'default'}
                />
              )}
            </Box>
            {testCase.compliance_mapping && testCase.compliance_mapping.length > 0 && (
              <ComplianceDisplay 
                item={testCase} 
                showIcon={true}
              />
            )}
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
          </Box>
        }
      />
    </ListItem>
  );

  const UseCaseItem = ({ useCase, projectId }) => {
    const isExpanded = expandedUseCases[useCase.use_case_id];
    const testCases = useCase.test_cases || [];

    return (
      <Card sx={{ mb: 1, border: '1px solid #e0e0e0' }}>
        <ListItemButton onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          toggleUseCaseExpansion(useCase.use_case_id);
        }}>
          <ListItemIcon>
            <UseCaseIcon color="info" />
          </ListItemIcon>
          <ListItemText
            primary={
              <Box>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                    {useCase.use_case_title || `Use Case ${useCase.use_case_id}`}
                  </Typography>
                  <Badge badgeContent={testCases.length} color="success" sx={{ ml: 1 }}>
                    <TestCaseIcon fontSize="small" />
                  </Badge>
                  {useCase.jira_issue_key && (
                    <Chip
                      icon={<JiraIcon sx={{ fontSize: '16px' }} />}
                      label={useCase.jira_issue_key}
                      size="small"
                      variant="outlined"
                      color="primary"
                      sx={{ 
                        ml: 1, 
                        fontSize: '0.75rem',
                        borderColor: '#0052CC',
                        color: '#0052CC',
                        '& .MuiChip-icon': {
                          marginLeft: '4px',
                          marginRight: '-2px'
                        }
                      }}
                    />
                  )}
                  {useCase.priority && (
                    <Chip
                      label={`Priority: ${useCase.priority}`}
                      size="small"
                      variant="outlined"
                      color={useCase.priority === 'High' ? 'error' : useCase.priority === 'Medium' ? 'warning' : 'default'}
                      sx={{ ml: 1, fontSize: '0.75rem' }}
                    />
                  )}
                  <InfoButton
                    onClick={() => handleModelExplanation(useCase, 'use_case', projectId)}
                    hasInfo={!!useCase.model_explanation}
                    tooltip="View AI Model Explanation"
                  />
                </Box>
                {useCase.compliance_mapping && useCase.compliance_mapping.length > 0 && (
                  <ComplianceDisplay 
                    item={useCase} 
                    showIcon={true}
                  />
                )}
              </Box>
            }
            secondary={useCase.description}
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
                <TestCaseItem
                  key={testCase.test_case_id}
                  testCase={testCase}
                  projectId={projectId}
                />
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

  const FeatureItem = ({ feature, projectId }) => {
    const isExpanded = expandedFeatures[feature.feature_id];
    const useCases = feature.use_cases || [];

    return (
      <Card sx={{ mb: 1, border: '1px solid #d0d0d0' }}>
        <ListItemButton onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          toggleFeatureExpansion(feature.feature_id);
        }}>
          <ListItemIcon>
            <FeatureIcon color="warning" />
          </ListItemIcon>
          <ListItemText
            primary={
              <Box>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    {feature.title || feature.feature_title || `Feature ${feature.feature_id}`}
                  </Typography>
                  <Badge badgeContent={useCases.length} color="info" sx={{ ml: 1 }}>
                    <UseCaseIcon fontSize="small" />
                  </Badge>
                  {feature.jira_issue_key && (
                    <Chip
                      icon={<JiraIcon sx={{ fontSize: '16px' }} />}
                      label={feature.jira_issue_key}
                      size="small"
                      variant="outlined"
                      color="primary"
                      sx={{ 
                        ml: 1, 
                        fontSize: '0.75rem',
                        borderColor: '#0052CC',
                        color: '#0052CC',
                        '& .MuiChip-icon': {
                          marginLeft: '4px',
                          marginRight: '-2px'
                        }
                      }}
                    />
                  )}
                  {feature.priority && (
                    <Chip
                      label={`Priority: ${feature.priority}`}
                      size="small"
                      variant="outlined"
                      color={feature.priority === 'High' ? 'error' : feature.priority === 'Medium' ? 'warning' : 'default'}
                      sx={{ ml: 1, fontSize: '0.75rem' }}
                    />
                  )}
                  <InfoButton
                    onClick={() => handleModelExplanation(feature, 'feature', projectId)}
                    hasInfo={!!feature.model_explanation}
                    tooltip="View AI Model Explanation"
                  />
                </Box>
                {feature.compliance_mapping && feature.compliance_mapping.length > 0 && (
                  <ComplianceDisplay 
                    item={feature} 
                    showIcon={true}
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
                <UseCaseItem
                  key={useCase.use_case_id}
                  useCase={useCase}
                  projectId={projectId}
                />
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

  const EpicItem = ({ epic, projectId }) => {
    const isExpanded = expandedEpics[epic.epic_id];
    const features = epic.features || [];

    return (
      <Card sx={{ mb: 2, border: '1px solid #c0c0c0' }}>
        <ListItemButton onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          toggleEpicExpansion(epic.epic_id);
        }}>
          <ListItemIcon>
            <EpicIcon color="secondary" />
          </ListItemIcon>
          <ListItemText
            primary={
              <Box>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    {epic.title || epic.epic_title || `Epic ${epic.epic_id}`}
                  </Typography>
                  <Badge badgeContent={features.length} color="warning" sx={{ ml: 1 }}>
                    <FeatureIcon fontSize="small" />
                  </Badge>
                  {epic.jira_issue_key && (
                    <Chip
                      icon={<JiraIcon sx={{ fontSize: '16px' }} />}
                      label={epic.jira_issue_key}
                      size="small"
                      variant="outlined"
                      color="primary"
                      sx={{ 
                        ml: 1, 
                        fontSize: '0.75rem',
                        borderColor: '#0052CC',
                        color: '#0052CC',
                        '& .MuiChip-icon': {
                          marginLeft: '4px',
                          marginRight: '-2px'
                        }
                      }}
                    />
                  )}
                  {epic.priority && (
                    <Chip
                      label={`Priority: ${epic.priority}`}
                      size="small"
                      variant="outlined"
                      color={epic.priority === 'High' ? 'error' : epic.priority === 'Medium' ? 'warning' : 'default'}
                      sx={{ ml: 1, fontSize: '0.75rem' }}
                    />
                  )}
                  <InfoButton
                    onClick={() => handleModelExplanation(epic, 'epic', projectId)}
                    hasInfo={!!epic.model_explanation}
                    tooltip="View AI Model Explanation"
                  />
                </Box>
                {epic.compliance_mapping && epic.compliance_mapping.length > 0 && (
                  <ComplianceDisplay 
                    item={epic} 
                    showIcon={true}
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
                <FeatureItem
                  key={feature.feature_id}
                  feature={feature}
                  projectId={projectId}
                />
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

  const ProjectAccordion = ({ project }) => {
    const isExpanded = expandedProjects[project.project_id];
    const epics = project.hierarchy?.epics || [];

    return (
      <Accordion
        expanded={isExpanded}
        onChange={() => toggleProjectExpansion(project.project_id)}
        sx={{
          mb: 2,
          '&:before': { display: 'none' },
          border: '1px solid #e0e0e0',
          borderRadius: '8px !important',
          '&.Mui-expanded': {
            margin: '0 0 16px 0',
          },
        }}
      >
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          sx={{
            backgroundColor: '#f8f9fa',
            borderRadius: '8px',
            '&.Mui-expanded': {
              borderBottomLeftRadius: 0,
              borderBottomRightRadius: 0,
            },
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
            <Avatar sx={{ bgcolor: '#667eea', mr: 2 }}>
              <ProjectIcon />
            </Avatar>
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {project.project_name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {project.description || 'No description available'}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mr: 2 }}>
              <Badge badgeContent={epics.length} color="secondary">
                <EpicIcon />
              </Badge>
              <Chip
                label={project.status || 'Active'}
                color={project.status === 'Active' ? 'success' : 'default'}
                size="small"
              />
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  handleExportProject(project, 'excel');
                }}
                title="Export to Excel"
                sx={{ color: '#1976d2' }}
              >
                <ExcelIcon fontSize="small" />
              </IconButton>
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  handleExportProject(project, 'xml');
                }}
                title="Export to XML"
                sx={{ color: '#f57c00' }}
              >
                <XmlIcon fontSize="small" />
              </IconButton>
            </Box>
          </Box>
        </AccordionSummary>
        <AccordionDetails sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
            Epics ({epics.length})
          </Typography>
          {epics.length > 0 ? (
            epics.map((epic) => (
              <EpicItem
                key={epic.epic_id}
                epic={epic}
                projectId={project.project_id}
              />
            ))
          ) : (
            <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
              No epics available for this project
            </Typography>
          )}
        </AccordionDetails>
      </Accordion>
    );
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
          <CircularProgress size={60} />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, color: '#667eea' }}>
          Project Dashboard
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Button
            variant="contained"
            startIcon={<LaunchIcon />}
            onClick={() => window.open('https://vibetesting-app-145534422719.europe-west1.run.app/', '_blank')}
            sx={{ 
              backgroundColor: '#667eea',
              '&:hover': {
                backgroundColor: '#5a67d8'
              }
            }}
          >
            Vibe Testing
          </Button>
          <Button
            variant="outlined"
            startIcon={refreshing ? <CircularProgress size={16} /> : <RefreshIcon />}
            onClick={handleRefresh}
            disabled={refreshing}
          >
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
        </Box>
      </Box>

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={2.4}>
          <StatCard
            title="Projects"
            value={statistics.totalProjects}
            subtitle="Total active projects"
            icon={<ProjectIcon />}
            color="#667eea"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <StatCard
            title="Epics"
            value={statistics.totalEpics}
            subtitle="Total epics"
            icon={<EpicIcon />}
            color="#9c27b0"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <StatCard
            title="Features"
            value={statistics.totalFeatures}
            subtitle="Total features"
            icon={<FeatureIcon />}
            color="#ff9800"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <StatCard
            title="Use Cases"
            value={statistics.totalUseCases}
            subtitle="Total use cases"
            icon={<UseCaseIcon />}
            color="#2196f3"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <StatCard
            title="Test Cases"
            value={statistics.totalTestCases}
            subtitle="Total test cases"
            icon={<TestCaseIcon />}
            color="#4caf50"
          />
        </Grid>
      </Grid>

      {/* Projects List */}
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h5" sx={{ fontWeight: 600 }}>
            Projects Overview
          </Typography>
        </Box>
        {projects.length > 0 ? (
          projects.map((project) => (
            <ProjectAccordion key={project.project_id} project={project} />
          ))
        ) : (
          <Typography variant="body1" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
            No projects found. Create your first project to get started.
          </Typography>
        )}
      </Paper>

      {/* Model Explanation Dialog */}
      <Dialog
        open={modelExplanationDialog.open}
        onClose={() => setModelExplanationDialog({ ...modelExplanationDialog, open: false })}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center' }}>
          <ExplanationIcon sx={{ mr: 1, color: '#667eea' }} />
          AI Model Explanation
        </DialogTitle>
        <DialogContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            {modelExplanationDialog.title}
          </Typography>
          {modelExplanationDialog.loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
              <CircularProgress />
            </Box>
          ) : (
            <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
              {modelExplanationDialog.explanation}
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setModelExplanationDialog({ ...modelExplanationDialog, open: false })}>
            Close
          </Button>
        </DialogActions>
      </Dialog>

    </Container>
  );
};

export default Dashboard;