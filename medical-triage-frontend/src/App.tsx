import React, { useState } from 'react';
import {
  Container,
  Typography,
  TextField,
  Button,
  Box,
  Paper,
  CircularProgress,
  Alert,
  AppBar,
  Toolbar,
  ThemeProvider,
  createTheme,
  Card,
  CardContent,
  Grid,
  Chip,
  Stack,
  useMediaQuery
} from '@mui/material';
import { styled } from '@mui/material/styles';
import MedicalServicesIcon from '@mui/icons-material/MedicalServices';
import DescriptionIcon from '@mui/icons-material/Description';
import AssessmentIcon from '@mui/icons-material/Assessment';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1a73e8',
      light: '#4285f4',
      dark: '#0d47a1',
    },
    secondary: {
      main: '#ea4335',
      light: '#fbbc05',
      dark: '#34a853',
    },
    background: {
      default: '#ffffff',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Google Sans", "Roboto", "Arial", sans-serif',
    h4: {
      fontWeight: 500,
      letterSpacing: '-0.5px',
    },
    h6: {
      fontWeight: 500,
      letterSpacing: '-0.25px',
    },
    subtitle1: {
      fontWeight: 500,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: '4px',
          padding: '8px 24px',
          fontWeight: 500,
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 1px 2px 0 rgba(60,64,67,.3), 0 1px 3px 1px rgba(60,64,67,.15)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
          boxShadow: '0 1px 2px 0 rgba(60,64,67,.3), 0 1px 3px 1px rgba(60,64,67,.15)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
          boxShadow: '0 1px 2px 0 rgba(60,64,67,.3), 0 1px 3px 1px rgba(60,64,67,.15)',
        },
      },
    },
  },
});

const Input = styled('input')({
  display: 'none',
});

const StyledCard = styled(Card)(({ theme }) => ({
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  transition: 'transform 0.2s, box-shadow 0.2s',
  '&:hover': {
    transform: 'translateY(-4px)',
    boxShadow: '0 4px 8px 0 rgba(60,64,67,.3), 0 4px 12px 4px rgba(60,64,67,.15)',
  },
}));

const UploadBox = styled(Box)(({ theme }) => ({
  border: '2px dashed #dadce0',
  borderRadius: '8px',
  padding: '32px',
  textAlign: 'center',
  cursor: 'pointer',
  transition: 'border-color 0.2s',
  '&:hover': {
    borderColor: theme.palette.primary.main,
  },
}));

const App: React.FC = () => {
  const [text, setText] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [textLoading, setTextLoading] = useState(false);
  const [fileLoading, setFileLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const handleTextChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setText(event.target.value);
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setFile(event.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTextLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:3001/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });
      const data = await response.json();
      setResult(data);
      if (data.pdf_url) {
        const link = document.createElement('a');
        link.href = `http://localhost:3001${data.pdf_url}`;
        link.target = '_blank';
        link.download = 'medical_triage_report.pdf';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    } catch (err) {
      setError('Failed to analyze text. Please try again.');
      console.error('Error:', err);
    } finally {
      setTextLoading(false);
    }
  };

  const handleFileSubmit = async () => {
    if (!file) {
      setError('Please upload a document.');
      return;
    }
    setFileLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await fetch('http://localhost:3001/api/analyze-document', {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) throw new Error('Failed to analyze document');
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setFileLoading(false);
    }
  };

  const getRiskColor = (riskLevel?: string) => {
    switch (riskLevel?.toLowerCase()) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'success';
      default:
        return 'default';
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <Box sx={{ flexGrow: 1, minHeight: '100vh', bgcolor: 'background.default' }}>
        <AppBar position="static" elevation={0} sx={{ bgcolor: 'white', color: 'text.primary' }}>
          <Toolbar>
            <MedicalServicesIcon sx={{ mr: 2, color: 'primary.main' }} />
            <Typography variant="h6" component="div" sx={{ flexGrow: 1, color: 'text.primary' }}>
              MedAssist AI
            </Typography>
          </Toolbar>
        </AppBar>

        <Container maxWidth="lg" sx={{ py: 4 }}>
          <Typography variant="h4" sx={{ mb: 4, textAlign: 'center', color: 'text.primary' }}>
            Intelligent Medical Triage
          </Typography>

          <Grid container spacing={4}>
            <Grid item xs={12} md={6}>
              <StyledCard>
                <CardContent sx={{ p: 3 }}>
                  <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 3 }}>
                    <DescriptionIcon color="primary" />
                    <Typography variant="h6">Text Analysis</Typography>
                  </Stack>
                  <TextField
                    fullWidth
                    multiline
                    rows={6}
                    value={text}
                    onChange={handleTextChange}
                    placeholder="Enter medical case description here..."
                    variant="outlined"
                    sx={{ mb: 3 }}
                  />
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={handleSubmit}
                    disabled={textLoading}
                    fullWidth
                    size="large"
                    sx={{ py: 1.5 }}
                  >
                    {textLoading ? <CircularProgress size={24} /> : 'Analyze Text'}
                  </Button>
                </CardContent>
              </StyledCard>
            </Grid>

            <Grid item xs={12} md={6}>
              <StyledCard>
                <CardContent sx={{ p: 3 }}>
                  <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 3 }}>
                    <AssessmentIcon color="primary" />
                    <Typography variant="h6">Document Analysis</Typography>
                  </Stack>
                  <label htmlFor="file-upload">
                    <UploadBox>
                      <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                      <Typography variant="subtitle1" gutterBottom>
                        {file ? 'File selected' : 'Drag and drop a file here'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        or click to browse
                      </Typography>
                      <Input
                        id="file-upload"
                        type="file"
                        onChange={handleFileChange}
                        accept=".pdf,.docx,.txt"
                      />
                    </UploadBox>
                  </label>
                  {file && (
                    <Chip
                      label={file.name}
                      onDelete={() => setFile(null)}
                      sx={{ mt: 2 }}
                    />
                  )}
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={handleFileSubmit}
                    disabled={fileLoading || !file}
                    fullWidth
                    size="large"
                    sx={{ mt: 2, py: 1.5 }}
                  >
                    {fileLoading ? <CircularProgress size={24} /> : 'Analyze Document'}
                  </Button>
                </CardContent>
              </StyledCard>
            </Grid>

            {error && (
              <Grid item xs={12}>
                <Alert severity="error" sx={{ mb: 2 }}>
                  {error}
                </Alert>
              </Grid>
            )}

            {result && (
              <Grid item xs={12}>
                <StyledCard>
                  <CardContent sx={{ p: 3 }}>
                    <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 3 }}>
                      <AssessmentIcon color="primary" />
                      <Typography variant="h6">Analysis Results</Typography>
                    </Stack>
                    <Grid container spacing={3}>
                      <Grid item xs={12}>
                        <Paper sx={{ p: 3, bgcolor: 'background.paper' }}>
                          <Typography variant="subtitle1" gutterBottom>
                            Risk Assessment
                          </Typography>
                          <Stack direction="row" spacing={1} alignItems="center">
                            <Chip
                              label={result.risk_assessment?.risk_level}
                              color={getRiskColor(result.risk_assessment?.risk_level)}
                              size="medium"
                              sx={{ fontWeight: 500 }}
                            />
                          </Stack>
                          <Typography variant="body2" sx={{ mt: 2, color: 'text.secondary' }}>
                            {result.risk_assessment?.explanation}
                          </Typography>
                        </Paper>
                      </Grid>
                    </Grid>
                    {result.pdf_url && (
                      <Box sx={{ mt: 3, textAlign: 'center' }}>
                        <Button
                          variant="contained"
                          color="secondary"
                          href={`http://localhost:3001${result.pdf_url}`}
                          target="_blank"
                          startIcon={<DescriptionIcon />}
                          size="large"
                          sx={{ py: 1.5 }}
                        >
                          Download PDF Report
                        </Button>
                      </Box>
                    )}
                  </CardContent>
                </StyledCard>
              </Grid>
            )}
          </Grid>
        </Container>
      </Box>
    </ThemeProvider>
  );
};

export default App; 