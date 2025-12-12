import React, { useState } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  TextField,
  Switch,
  FormControlLabel,
  Button,
  Alert,
  Tabs,
  Tab,
  Slider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  SelectChangeEvent,
} from '@mui/material';
import {
  Save,
  Security,
  Videocam,
  Settings as SettingsIcon,
} from '@mui/icons-material';

interface TabPanelProps {
  children?: React.ReactNode;
  value: number;
  index: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => (
  <div
    role="tabpanel"
    hidden={value !== index}
    id={`settings-tabpanel-${index}`}
    aria-labelledby={`settings-tab-${index}`}
    {...other}
  >
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
);

interface CVSettings {
  confidenceThreshold: number;
  plateConfidenceThreshold: number;
  processingFps: number;
  enableGpuAcceleration: boolean;
  autoSlotAssignment: boolean;
  debugMode: boolean;
}

interface SystemSettings {
  maxParkingDuration: number;
  notificationEnabled: boolean;
  emailNotifications: boolean;
  smsNotifications: boolean;
  dataRetentionDays: number;
  backupInterval: string;
  timezone: string;
}

interface CameraSettings {
  recordingEnabled: boolean;
  recordingQuality: string;
  motionDetection: boolean;
  nightVision: boolean;
  recordingDuration: number;
}

const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState<number>(0);
  const [saveStatus, setSaveStatus] = useState<string>('');
  
  // CV Settings
  const [cvSettings, setCvSettings] = useState<CVSettings>({
    confidenceThreshold: 0.7,
    plateConfidenceThreshold: 0.8,
    processingFps: 5,
    enableGpuAcceleration: true,
    autoSlotAssignment: true,
    debugMode: false,
  });
  
  // System Settings
  const [systemSettings, setSystemSettings] = useState<SystemSettings>({
    maxParkingDuration: 24,
    notificationEnabled: true,
    emailNotifications: true,
    smsNotifications: false,
    dataRetentionDays: 90,
    backupInterval: 'daily',
    timezone: 'UTC',
  });
  
  // Camera Settings
  const [cameraSettings, setCameraSettings] = useState<CameraSettings>({
    recordingEnabled: true,
    recordingQuality: 'HD',
    motionDetection: true,
    nightVision: true,
    recordingDuration: 30,
  });

  const handleSave = (category: string) => {
    setSaveStatus(`${category} settings saved successfully!`);
    setTimeout(() => setSaveStatus(''), 3000);
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 2, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        System Settings
      </Typography>
      
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Configure computer vision system and parking management settings
      </Typography>

      {saveStatus && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSaveStatus('')}>
          {saveStatus}
        </Alert>
      )}

      <Paper>
        <Tabs value={activeTab} onChange={(_e, newValue) => setActiveTab(newValue)}>
          <Tab icon={<Videocam />} label="Computer Vision" />
          <Tab icon={<SettingsIcon />} label="System" />
          <Tab icon={<Security />} label="Camera" />
        </Tabs>

        <TabPanel value={activeTab} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Detection Settings
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography gutterBottom>
                Vehicle Detection Confidence: {cvSettings.confidenceThreshold}
              </Typography>
              <Slider
                value={cvSettings.confidenceThreshold}
                onChange={(_e, value) => 
                  setCvSettings({ ...cvSettings, confidenceThreshold: value as number })
                }
                min={0.5}
                max={1}
                step={0.05}
                valueLabelDisplay="auto"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography gutterBottom>
                License Plate Confidence: {cvSettings.plateConfidenceThreshold}
              </Typography>
              <Slider
                value={cvSettings.plateConfidenceThreshold}
                onChange={(_e, value) => 
                  setCvSettings({ ...cvSettings, plateConfidenceThreshold: value as number })
                }
                min={0.5}
                max={1}
                step={0.05}
                valueLabelDisplay="auto"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={cvSettings.enableGpuAcceleration}
                    onChange={(e) =>
                      setCvSettings({ ...cvSettings, enableGpuAcceleration: e.target.checked })
                    }
                  />
                }
                label="Enable GPU Acceleration"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={cvSettings.autoSlotAssignment}
                    onChange={(e) =>
                      setCvSettings({ ...cvSettings, autoSlotAssignment: e.target.checked })
                    }
                  />
                }
                label="Auto Slot Assignment"
              />
            </Grid>
            <Grid item xs={12}>
              <Button
                variant="contained"
                startIcon={<Save />}
                onClick={() => handleSave('Computer Vision')}
              >
                Save CV Settings
              </Button>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                General Settings
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Max Parking Duration (hours)"
                type="number"
                value={systemSettings.maxParkingDuration}
                onChange={(e) =>
                  setSystemSettings({
                    ...systemSettings,
                    maxParkingDuration: parseInt(e.target.value),
                  })
                }
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Data Retention (days)"
                type="number"
                value={systemSettings.dataRetentionDays}
                onChange={(e) =>
                  setSystemSettings({
                    ...systemSettings,
                    dataRetentionDays: parseInt(e.target.value),
                  })
                }
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={systemSettings.emailNotifications}
                    onChange={(e) =>
                      setSystemSettings({
                        ...systemSettings,
                        emailNotifications: e.target.checked,
                      })
                    }
                  />
                }
                label="Email Notifications"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={systemSettings.smsNotifications}
                    onChange={(e) =>
                      setSystemSettings({
                        ...systemSettings,
                        smsNotifications: e.target.checked,
                      })
                    }
                  />
                }
                label="SMS Notifications"
              />
            </Grid>
            <Grid item xs={12}>
              <Button
                variant="contained"
                startIcon={<Save />}
                onClick={() => handleSave('System')}
              >
                Save System Settings
              </Button>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Camera & Recording Settings
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={cameraSettings.recordingEnabled}
                    onChange={(e) =>
                      setCameraSettings({
                        ...cameraSettings,
                        recordingEnabled: e.target.checked,
                      })
                    }
                  />
                }
                label="Enable Recording"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Recording Quality</InputLabel>
                <Select
                  value={cameraSettings.recordingQuality}
                  label="Recording Quality"
                  onChange={(e: SelectChangeEvent) =>
                    setCameraSettings({
                      ...cameraSettings,
                      recordingQuality: e.target.value,
                    })
                  }
                >
                  <MenuItem value="SD">SD (480p)</MenuItem>
                  <MenuItem value="HD">HD (720p)</MenuItem>
                  <MenuItem value="FHD">Full HD (1080p)</MenuItem>
                  <MenuItem value="4K">4K</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={cameraSettings.motionDetection}
                    onChange={(e) =>
                      setCameraSettings({
                        ...cameraSettings,
                        motionDetection: e.target.checked,
                      })
                    }
                  />
                }
                label="Motion Detection"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={cameraSettings.nightVision}
                    onChange={(e) =>
                      setCameraSettings({
                        ...cameraSettings,
                        nightVision: e.target.checked,
                      })
                    }
                  />
                }
                label="Night Vision"
              />
            </Grid>
            <Grid item xs={12}>
              <Button
                variant="contained"
                startIcon={<Save />}
                onClick={() => handleSave('Camera')}
              >
                Save Camera Settings
              </Button>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>
    </Container>
  );
};

export default Settings;
