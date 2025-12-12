import React, { useState } from 'react';
import {
  Container,
  Grid,
  Typography,
  Box,
  Card,
  CardContent,
  Chip,
  IconButton,
  Switch,
  FormControlLabel,
  Alert,
  Button,
} from '@mui/material';
import {
  CheckCircle,
  Error,
  Warning,
  Refresh,
  Settings,
  PlayArrow,
  Stop,
  Visibility,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { api } from '../services/api';

interface Camera {
  id: number;
  camera_code: string;
  role: 'ENTRY' | 'EXIT' | 'INDOOR';
  status: 'ACTIVE' | 'INACTIVE' | 'MAINTENANCE';
  rtsp_url?: string;
  floor_id?: number;
}

const CameraMonitoring: React.FC = () => {
  const [showInactive, setShowInactive] = useState<boolean>(false);

  // Fetch cameras data
  const { data: cameras, refetch } = useQuery<Camera[]>(
    'cameras',
    api.getCameras,
    {
      refetchInterval: 5000,
    }
  );

  const getCameraStatusColor = (status?: string): 'success' | 'error' | 'warning' | 'default' => {
    switch (status?.toUpperCase()) {
      case 'ACTIVE':
        return 'success';
      case 'INACTIVE':
        return 'error';
      case 'MAINTENANCE':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getCameraStatusIcon = (status?: string) => {
    switch (status?.toUpperCase()) {
      case 'ACTIVE':
        return <CheckCircle color="success" />;
      case 'INACTIVE':
        return <Error color="error" />;
      case 'MAINTENANCE':
        return <Warning color="warning" />;
      default:
        return <Error />;
    }
  };

  const getRoleDescription = (role: string): string => {
    switch (role) {
      case 'ENTRY':
        return 'Entry Gate Monitoring';
      case 'EXIT':
        return 'Exit Gate Monitoring';
      case 'INDOOR':
        return 'Slot Occupancy Detection';
      default:
        return 'Unknown Role';
    }
  };

  const filteredCameras = cameras?.filter(camera => 
    showInactive || camera.status === 'ACTIVE'
  ) || [];

  const renderCameraCard = (camera: Camera) => (
    <Card key={camera.id} sx={{ mb: 2 }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box display="flex" alignItems="center">
            {getCameraStatusIcon(camera.status)}
            <Box ml={2}>
              <Typography variant="h6">{camera.camera_code}</Typography>
              <Typography variant="body2" color="text.secondary">
                {getRoleDescription(camera.role)}
              </Typography>
            </Box>
          </Box>
          <Box display="flex" flexDirection="column" alignItems="flex-end">
            <Chip 
              label={camera.status || 'UNKNOWN'} 
              color={getCameraStatusColor(camera.status)} 
              size="small" 
              sx={{ mb: 1 }}
            />
            <Box>
              <IconButton size="small" color="primary" title="View Feed">
                <Visibility />
              </IconButton>
              <IconButton size="small" title="Settings">
                <Settings />
              </IconButton>
            </Box>
          </Box>
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Typography variant="body2" color="text.secondary">
              <strong>Location:</strong> {camera.floor_id ? `Floor ${camera.floor_id === 1 ? 'A' : 'B'}` : 'Entry/Exit Gate'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              <strong>RTSP URL:</strong> {camera.rtsp_url || 'Not configured'}
            </Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="body2" color="text.secondary">
              <strong>Last Detection:</strong> 2 min ago
            </Typography>
            <Typography variant="body2" color="text.secondary">
              <strong>Detection Count:</strong> 152 today
            </Typography>
          </Grid>
        </Grid>

        <Box mt={2} display="flex" justifyContent="space-between" alignItems="center">
          <Box display="flex" gap={1}>
            {camera.status === 'ACTIVE' ? (
              <Button 
                startIcon={<Stop />} 
                size="small" 
                color="error"
                variant="outlined"
              >
                Stop
              </Button>
            ) : (
              <Button 
                startIcon={<PlayArrow />} 
                size="small" 
                color="success"
                variant="outlined"
              >
                Start
              </Button>
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Container maxWidth="xl" sx={{ mt: 2, mb: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Camera Monitoring System
        </Typography>
        <Box>
          <FormControlLabel
            control={
              <Switch
                checked={showInactive}
                onChange={(e) => setShowInactive(e.target.checked)}
              />
            }
            label="Show Inactive"
          />
          <IconButton onClick={() => refetch()} color="primary">
            <Refresh />
          </IconButton>
        </Box>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        Computer Vision system is processing feeds from {filteredCameras.length} active cameras
      </Alert>

      <Grid container spacing={3}>
        {filteredCameras.map((camera) => (
          <Grid item xs={12} md={6} lg={4} key={camera.id}>
            {renderCameraCard(camera)}
          </Grid>
        ))}
      </Grid>
    </Container>
  );
};

export default CameraMonitoring;
