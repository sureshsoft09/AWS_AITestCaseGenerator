/* eslint-disable no-unused-vars */
import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  LinearProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Checkbox,
} from '@mui/material';
import {
  MoveUp as MigrateIcon,
  Upload as UploadIcon,
  CloudUpload as CloudUploadIcon,
  ExpandMore as ExpandMoreIcon,
  Assignment as TestCaseIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  SwapHoriz as TransformIcon,
  Folder as FolderIcon,
  InsertDriveFile as FileIcon,
  GetApp as DownloadIcon,
  Visibility as PreviewIcon,
  AutoAwesome as AIIcon,
  Link as MappingIcon,
} from '@mui/icons-material';
import { useNotification } from '../contexts/NotificationContext';
import api from '../services/api';

const MigrationTestCases = () => {
  const [projects, setProjects] = useState([]);
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [selectedProject, setSelectedProject] = useState('');
  const [activeStep, setActiveStep] = useState(0);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [migrationSettings, setMigrationSettings] = useState({
    sourceFormat: '',
    targetFormat: 'medassure',
    mapping: {},
    validation: true,
    preserveHierarchy: true,
  });
  const [parsedData, setParsedData] = useState(null);
  const [mappingConfig, setMappingConfig] = useState({});
  const [selectedTestCases, setSelectedTestCases] = useState([]);
  const [migrationResults, setMigrationResults] = useState(null);
  const [isMigrating, setIsMigrating] = useState(false);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [previewData, setPreviewData] = useState(null);

  // Ensure projects is always an array
  const safeProjects = projects || [];
  const fileInputRef = useRef(null);
  const { showNotification } = useNotification();

  const supportedFormats = [
    { value: 'excel', label: 'Excel/CSV (.xlsx, .xls, .csv)', extensions: ['.xlsx', '.xls', '.csv'] },
    { value: 'jira', label: 'Jira Export (.json, .xml)', extensions: ['.json', '.xml'] },
    { value: 'testlink', label: 'TestLink Export (.xml)', extensions: ['.xml'] },
    { value: 'qtest', label: 'qTest Export (.xlsx)', extensions: ['.xlsx'] },
    { value: 'testrail', label: 'TestRail Export (.csv, .json)', extensions: ['.csv', '.json'] },
    { value: 'azure_devops', label: 'Azure DevOps (.csv)', extensions: ['.csv'] },
    { value: 'hp_alm', label: 'HP ALM Export (.xlsx)', extensions: ['.xlsx'] },
  ];

  const migrationSteps = [
    'Upload Files',
    'Configure Mapping',
    'Preview & Validate',
    'Execute Migration',
    'Review Results',
  ];

  // Load projects from Firestore
  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoadingProjects(true);
      const response = await api.get('/api/projects');
      console.log('Projects API response:', response.data); // Debug log
      
      if (response.data) {
        // Handle different possible response structures
        let projectsArray = [];
        if (Array.isArray(response.data)) {
          projectsArray = response.data;
        } else if (response.data.projects && Array.isArray(response.data.projects)) {
          projectsArray = response.data.projects;
        } else if (response.data.data && Array.isArray(response.data.data)) {
          projectsArray = response.data.data;
        }
        
        console.log('Processed projects array:', projectsArray); // Debug log
        setProjects(projectsArray);
      } else {
        setProjects([]);
      }
    } catch (error) {
      console.error('Error loading projects:', error);
      setProjects([]);
      showNotification('Failed to load projects', 'error');
    } finally {
      setLoadingProjects(false);
    }
  };

  const handleFileUpload = (event) => {
    const files = Array.from(event.target.files);
    const newFiles = files.map(file => ({
      id: Date.now() + Math.random(),
      name: file.name,
      size: file.size,
      type: file.type,
      file: file,
      status: 'uploaded',
    }));
    setUploadedFiles(prev => [...prev, ...newFiles]);
    showNotification(`${files.length} file(s) uploaded successfully`, 'success');
  };

  const removeFile = (fileId) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const parseFiles = async () => {
    if (!migrationSettings.sourceFormat) {
      showNotification('Please select source format first', 'warning');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('source_format', migrationSettings.sourceFormat);
      uploadedFiles.forEach((fileData) => {
        formData.append('files', fileData.file);
      });

      const response = await api.post('/migration/parse', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setParsedData(response.data);
      setActiveStep(1);
      showNotification('Files parsed successfully!', 'success');
    } catch (error) {
      console.error('Error parsing files:', error);
      showNotification('Failed to parse files', 'error');
    }
  };

  const generateMapping = async () => {
    try {
      const response = await api.post('/migration/generate-mapping', {
        source_format: migrationSettings.sourceFormat,
        target_format: migrationSettings.targetFormat,
        sample_data: parsedData?.sample,
      });

      setMappingConfig(response.data.mapping);
      setActiveStep(2);
      showNotification('Mapping configuration generated!', 'success');
    } catch (error) {
      console.error('Error generating mapping:', error);
      showNotification('Failed to generate mapping', 'error');
    }
  };

  const validateMigration = async () => {
    try {
      const response = await api.post('/migration/validate', {
        source_data: parsedData,
        mapping: mappingConfig,
        settings: migrationSettings,
      });

      if (response.data.valid) {
        setActiveStep(3);
        showNotification('Validation successful!', 'success');
      } else {
        showNotification(`Validation failed: ${response.data.errors.join(', ')}`, 'error');
      }
    } catch (error) {
      console.error('Error validating migration:', error);
      showNotification('Validation failed', 'error');
    }
  };

  const executeMigration = async () => {
    try {
      setIsMigrating(true);
      
      const response = await api.post('/migration/execute', {
        project_id: selectedProject,
        source_data: parsedData,
        mapping: mappingConfig,
        settings: migrationSettings,
        selected_test_cases: selectedTestCases,
      });

      setMigrationResults(response.data);
      setActiveStep(4);
      showNotification('Migration completed successfully!', 'success');
    } catch (error) {
      console.error('Error executing migration:', error);
      showNotification('Migration failed', 'error');
    } finally {
      setIsMigrating(false);
    }
  };

  const previewTestCase = (testCase) => {
    setPreviewData(testCase);
    setPreviewDialogOpen(true);
  };

  const toggleTestCaseSelection = (testCaseId) => {
    setSelectedTestCases(prev =>
      prev.includes(testCaseId)
        ? prev.filter(id => id !== testCaseId)
        : [...prev, testCaseId]
    );
  };

  const MappingField = ({ sourceField, targetField, onChange }) => (
    <Grid container spacing={2} alignItems="center" sx={{ mb: 2 }}>
      <Grid item xs={5}>
        <TextField
          fullWidth
          label="Source Field"
          value={sourceField}
          disabled
          size="small"
        />
      </Grid>
      <Grid item xs={2} sx={{ textAlign: 'center' }}>
        <MappingIcon color="primary" />
      </Grid>
      <Grid item xs={5}>
        <FormControl fullWidth size="small">
          <InputLabel>Target Field</InputLabel>
          <Select
            value={targetField}
            onChange={(e) => onChange(sourceField, e.target.value)}
            label="Target Field"
          >
            <MenuItem value="title">Title</MenuItem>
            <MenuItem value="description">Description</MenuItem>
            <MenuItem value="preconditions">Preconditions</MenuItem>
            <MenuItem value="steps">Test Steps</MenuItem>
            <MenuItem value="expected_result">Expected Result</MenuItem>
            <MenuItem value="priority">Priority</MenuItem>
            <MenuItem value="type">Type</MenuItem>
            <MenuItem value="status">Status</MenuItem>
            <MenuItem value="risk_level">Risk Level</MenuItem>
            <MenuItem value="compliance_standards">Compliance Standards</MenuItem>
            <MenuItem value="ignore">Ignore</MenuItem>
          </Select>
        </FormControl>
      </Grid>
    </Grid>
  );

  const PreviewDialog = () => (
    <Dialog
      open={previewDialogOpen}
      onClose={() => setPreviewDialogOpen(false)}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle>Test Case Preview</DialogTitle>
      <DialogContent>
        {previewData && (
          <Box sx={{ pt: 2 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              {previewData.title}
            </Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              <strong>Description:</strong> {previewData.description}
            </Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              <strong>Priority:</strong> {previewData.priority}
            </Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              <strong>Type:</strong> {previewData.type}
            </Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              <strong>Preconditions:</strong> {previewData.preconditions}
            </Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              <strong>Expected Result:</strong> {previewData.expectedResult}
            </Typography>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setPreviewDialogOpen(false)}>Close</Button>
      </DialogActions>
    </Dialog>
  );

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography
          variant="h4"
          sx={{
            fontWeight: 700,
            mb: 1,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}
        >
          Migration Test Cases
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Import and migrate test cases from external systems and legacy formats
        </Typography>
      </Box>

      {/* Project Selection */}
      <Paper
        sx={{
          p: 3,
          mb: 3,
          background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(248, 250, 255, 0.9) 100%)',
          border: '1px solid rgba(102, 126, 234, 0.1)',
        }}
      >
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Target Project</InputLabel>
              <Select
                value={selectedProject}
                onChange={(e) => setSelectedProject(e.target.value)}
                label="Target Project"
                disabled={loadingProjects}
              >
                {loadingProjects ? (
                  <MenuItem disabled>Loading projects...</MenuItem>
                ) : safeProjects.length > 0 ? (
                  safeProjects.map((project, index) => (
                    <MenuItem 
                      key={project.project_id || project.id || project._id || index} 
                      value={project.project_id || project.id || project._id || `project_${index}`}
                    >
                      {project.project_name || project.name || project.title || `Project ${index + 1}`}
                    </MenuItem>
                  ))
                ) : (
                  <MenuItem disabled>No projects found</MenuItem>
                )}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Source Format</InputLabel>
              <Select
                value={migrationSettings.sourceFormat}
                onChange={(e) => setMigrationSettings(prev => ({ ...prev, sourceFormat: e.target.value }))}
                label="Source Format"
              >
                {supportedFormats.map((format) => (
                  <MenuItem key={format.value} value={format.value}>
                    {format.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Migration Stepper */}
      <Paper
        sx={{
          background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(248, 250, 255, 0.9) 100%)',
          border: '1px solid rgba(102, 126, 234, 0.1)',
        }}
      >
        <Stepper activeStep={activeStep} orientation="vertical" sx={{ p: 3 }}>
          {/* Step 1: Upload Files */}
          <Step>
            <StepLabel>Upload Files</StepLabel>
            <StepContent>
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Upload your test case files from external systems
                </Typography>

                {/* Upload Area */}
                <Card
                  sx={{
                    p: 4,
                    textAlign: 'center',
                    border: '2px dashed rgba(102, 126, 234, 0.3)',
                    cursor: 'pointer',
                    mb: 3,
                    '&:hover': {
                      borderColor: '#667eea',
                      backgroundColor: 'rgba(102, 126, 234, 0.05)',
                    },
                  }}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <CloudUploadIcon sx={{ fontSize: 48, color: '#667eea', mb: 2 }} />
                  <Typography variant="h6" sx={{ mb: 1 }}>
                    Drop files here or click to upload
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {migrationSettings.sourceFormat
                      ? `Supports: ${supportedFormats.find(f => f.value === migrationSettings.sourceFormat)?.extensions.join(', ')}`
                      : 'Please select source format first'}
                  </Typography>
                </Card>

                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept={migrationSettings.sourceFormat
                    ? supportedFormats.find(f => f.value === migrationSettings.sourceFormat)?.extensions.join(',')
                    : '*'
                  }
                  style={{ display: 'none' }}
                  onChange={handleFileUpload}
                />

                {/* Uploaded Files List */}
                {uploadedFiles.length > 0 && (
                  <Box>
                    <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
                      Uploaded Files ({uploadedFiles.length})
                    </Typography>
                    <List>
                      {uploadedFiles.map((file) => (
                        <ListItem
                          key={file.id}
                          sx={{
                            border: '1px solid rgba(102, 126, 234, 0.1)',
                            borderRadius: 1,
                            mb: 1,
                          }}
                        >
                          <ListItemIcon>
                            <Avatar sx={{ bgcolor: '#667eea20', color: '#667eea' }}>
                              <FileIcon />
                            </Avatar>
                          </ListItemIcon>
                          <ListItemText
                            primary={file.name}
                            secondary={`${(file.size / 1024 / 1024).toFixed(2)} MB`}
                          />
                          <IconButton
                            onClick={() => removeFile(file.id)}
                            color="error"
                            size="small"
                          >
                            <ErrorIcon />
                          </IconButton>
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}

                <Box sx={{ mt: 3 }}>
                  <Button
                    variant="contained"
                    onClick={parseFiles}
                    disabled={uploadedFiles.length === 0 || !migrationSettings.sourceFormat}
                    startIcon={<TransformIcon />}
                    sx={{
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
                      },
                    }}
                  >
                    Parse Files
                  </Button>
                </Box>
              </Box>
            </StepContent>
          </Step>

          {/* Step 2: Configure Mapping */}
          <Step>
            <StepLabel>Configure Mapping</StepLabel>
            <StepContent>
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Map source fields to target fields for proper data migration
                </Typography>

                {parsedData && (
                  <Box>
                    <Alert severity="info" sx={{ mb: 3 }}>
                      Found {parsedData.totalRecords} test cases in {parsedData.files?.length} file(s)
                    </Alert>

                    <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
                      Field Mapping Configuration
                    </Typography>
                    
                    {parsedData.sourceFields?.map((field) => (
                      <MappingField
                        key={field}
                        sourceField={field}
                        targetField={mappingConfig[field] || ''}
                        onChange={(source, target) => {
                          setMappingConfig(prev => ({ ...prev, [source]: target }));
                        }}
                      />
                    ))}
                  </Box>
                )}

                <Box sx={{ mt: 3 }}>
                  <Button
                    variant="outlined"
                    onClick={generateMapping}
                    startIcon={<AIIcon />}
                    sx={{ mr: 2 }}
                  >
                    Auto-Generate Mapping
                  </Button>
                  <Button
                    variant="contained"
                    onClick={() => setActiveStep(2)}
                    disabled={Object.keys(mappingConfig).length === 0}
                    sx={{
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
                      },
                    }}
                  >
                    Continue
                  </Button>
                </Box>
              </Box>
            </StepContent>
          </Step>

          {/* Step 3: Preview & Validate */}
          <Step>
            <StepLabel>Preview & Validate</StepLabel>
            <StepContent>
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Review the mapped data and select test cases to migrate
                </Typography>

                {parsedData && (
                  <Box>
                    <TableContainer sx={{ mb: 3, maxHeight: 400 }}>
                      <Table stickyHeader>
                        <TableHead>
                          <TableRow>
                            <TableCell padding="checkbox">
                              <Checkbox
                                checked={selectedTestCases.length === parsedData.testCases?.length}
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    setSelectedTestCases(parsedData.testCases.map(tc => tc.id));
                                  } else {
                                    setSelectedTestCases([]);
                                  }
                                }}
                              />
                            </TableCell>
                            <TableCell>Title</TableCell>
                            <TableCell>Type</TableCell>
                            <TableCell>Priority</TableCell>
                            <TableCell>Actions</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {parsedData.testCases?.map((testCase) => (
                            <TableRow key={testCase.id}>
                              <TableCell padding="checkbox">
                                <Checkbox
                                  checked={selectedTestCases.includes(testCase.id)}
                                  onChange={() => toggleTestCaseSelection(testCase.id)}
                                />
                              </TableCell>
                              <TableCell>{testCase.title}</TableCell>
                              <TableCell>{testCase.type}</TableCell>
                              <TableCell>{testCase.priority}</TableCell>
                              <TableCell>
                                <IconButton
                                  onClick={() => previewTestCase(testCase)}
                                  size="small"
                                >
                                  <PreviewIcon />
                                </IconButton>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Box>
                )}

                <Box sx={{ mt: 3 }}>
                  <Button
                    variant="contained"
                    onClick={validateMigration}
                    disabled={selectedTestCases.length === 0}
                    sx={{
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
                      },
                    }}
                  >
                    Validate & Continue
                  </Button>
                </Box>
              </Box>
            </StepContent>
          </Step>

          {/* Step 4: Execute Migration */}
          <Step>
            <StepLabel>Execute Migration</StepLabel>
            <StepContent>
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Execute the migration process to import test cases into your project
                </Typography>

                <Alert severity="info" sx={{ mb: 3 }}>
                  Ready to migrate {selectedTestCases.length} test cases to project "{selectedProject}"
                </Alert>

                {isMigrating && (
                  <Box sx={{ mb: 3 }}>
                    <LinearProgress
                      sx={{
                        '& .MuiLinearProgress-bar': {
                          background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
                        },
                      }}
                    />
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1, textAlign: 'center' }}>
                      Migrating test cases...
                    </Typography>
                  </Box>
                )}

                <Box sx={{ mt: 3 }}>
                  <Button
                    variant="contained"
                    onClick={executeMigration}
                    disabled={isMigrating || !selectedProject}
                    startIcon={<MigrateIcon />}
                    sx={{
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
                      },
                    }}
                  >
                    {isMigrating ? 'Migrating...' : 'Execute Migration'}
                  </Button>
                </Box>
              </Box>
            </StepContent>
          </Step>

          {/* Step 5: Review Results */}
          <Step>
            <StepLabel>Review Results</StepLabel>
            <StepContent>
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Review the migration results and download reports
                </Typography>

                {migrationResults && (
                  <Box>
                    <Alert severity="success" sx={{ mb: 3 }}>
                      Migration completed successfully! 
                      {migrationResults.successful} of {migrationResults.total} test cases migrated.
                    </Alert>

                    <Grid container spacing={2} sx={{ mb: 3 }}>
                      <Grid item xs={6} md={3}>
                        <Card sx={{ textAlign: 'center', p: 2 }}>
                          <Typography variant="h4" color="success.main">
                            {migrationResults.successful}
                          </Typography>
                          <Typography variant="body2">Successful</Typography>
                        </Card>
                      </Grid>
                      <Grid item xs={6} md={3}>
                        <Card sx={{ textAlign: 'center', p: 2 }}>
                          <Typography variant="h4" color="error.main">
                            {migrationResults.failed}
                          </Typography>
                          <Typography variant="body2">Failed</Typography>
                        </Card>
                      </Grid>
                      <Grid item xs={6} md={3}>
                        <Card sx={{ textAlign: 'center', p: 2 }}>
                          <Typography variant="h4" color="warning.main">
                            {migrationResults.warnings}
                          </Typography>
                          <Typography variant="body2">Warnings</Typography>
                        </Card>
                      </Grid>
                      <Grid item xs={6} md={3}>
                        <Card sx={{ textAlign: 'center', p: 2 }}>
                          <Typography variant="h4" color="primary.main">
                            {migrationResults.total}
                          </Typography>
                          <Typography variant="body2">Total</Typography>
                        </Card>
                      </Grid>
                    </Grid>

                    <Box sx={{ mt: 3 }}>
                      <Button
                        variant="contained"
                        startIcon={<DownloadIcon />}
                        sx={{
                          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                          '&:hover': {
                            background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
                          },
                        }}
                      >
                        Download Migration Report
                      </Button>
                    </Box>
                  </Box>
                )}
              </Box>
            </StepContent>
          </Step>
        </Stepper>
      </Paper>

      {/* Preview Dialog */}
      <PreviewDialog />
    </Box>
  );
};

export default MigrationTestCases;