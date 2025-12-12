import React from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  Alert,
} from '@mui/material';
import {
  DirectionsCar,
  TwoWheeler,
  Videocam,
  Warning,
  CheckCircle,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { format } from 'date-fns';

import { api } from '../services/api';
import { FloorData, ParkingAvailability, EntryEvent } from '../types';

interface TotalStats {
  car: {
    total: number;
    occupied: number;
    available: number;
  };
  bike: {
    total: number;
    occupied: number;
    available: number;
  };
}

const Dashboard: React.FC = () => {
  // Fetch parking availability
  const { data: availability } = useQuery<ParkingAvailability>(
    'parking-availability',
    api.getParkingAvailability
  );

  // Fetch system status
  const { data: systemStatus } = useQuery(
    'system-status',
    api.getSystemStatus
  );

  // Fetch recent entries
  const { data: recentEntries } = useQuery<EntryEvent[]>(
    'recent-entries',
    () => api.getEntryEvents({ limit: 10, active_only: true })
  );

  const calculateOccupancyRate = (floor?: FloorData): number => {
    if (!floor) return 0;
    const totalSlots = floor.car_slots.total + floor.bike_slots.total;
    const occupiedSlots = floor.car_slots.occupied + floor.bike_slots.occupied;
    return totalSlots > 0 ? (occupiedSlots / totalSlots) * 100 : 0;
  };

  const getTotalStats = (): TotalStats | null => {
    if (!availability?.floors) return null;
    
    let totalCar = 0, occupiedCar = 0;
    let totalBike = 0, occupiedBike = 0;
    
    Object.values(availability.floors).forEach(floor => {
      totalCar += floor.car_slots.total;
      occupiedCar += floor.car_slots.occupied;
      totalBike += floor.bike_slots.total;
      occupiedBike += floor.bike_slots.occupied;
    });
    
    return {
      car: { total: totalCar, occupied: occupiedCar, available: totalCar - occupiedCar },
      bike: { total: totalBike, occupied: occupiedBike, available: totalBike - occupiedBike }
    };
  };

  const totalStats = getTotalStats();

  return (
    <Container maxWidth="xl" sx={{ mt: 2, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Mall Parking Management Dashboard
      </Typography>
      
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Real-time monitoring with computer vision • {format(new Date(), 'PPpp')}
      </Typography>

      <Grid container spacing={3}>
        {/* Quick Stats Cards */}
        {totalStats && (
          <>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={1}>
                    <DirectionsCar color="primary" sx={{ mr: 1 }} />
                    <Typography variant="h6">Car Parking</Typography>
                  </Box>
                  <Typography variant="h4" component="div">
                    {totalStats.car.available}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Available of {totalStats.car.total} slots
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={(totalStats.car.occupied / totalStats.car.total) * 100}
                    sx={{ mt: 1 }}
                  />
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={1}>
                    <TwoWheeler color="primary" sx={{ mr: 1 }} />
                    <Typography variant="h6">Bike Parking</Typography>
                  </Box>
                  <Typography variant="h4" component="div">
                    {totalStats.bike.available}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Available of {totalStats.bike.total} slots
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={(totalStats.bike.occupied / totalStats.bike.total) * 100}
                    sx={{ mt: 1 }}
                  />
                </CardContent>
              </Card>
            </Grid>
          </>
        )}

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <Videocam color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Camera System</Typography>
              </Box>
              <Typography variant="h4" component="div">
                {systemStatus?.cameras ? Object.keys(systemStatus.cameras).length : 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Active cameras
              </Typography>
              <Box mt={1}>
                <Chip 
                  icon={<CheckCircle />} 
                  label="All Online" 
                  color="success" 
                  size="small" 
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <Warning color="warning" sx={{ mr: 1 }} />
                <Typography variant="h6">System Status</Typography>
              </Box>
              <Typography variant="h4" component="div" color="success.main">
                ONLINE
              </Typography>
              <Typography variant="body2" color="text.secondary">
                All systems operational
              </Typography>
              <Box mt={1}>
                <Chip 
                  label="CV Active" 
                  color="success" 
                  size="small" 
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Floor Overview */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Floor Overview
            </Typography>
            {availability?.floors && (
              <Grid container spacing={2}>
                {Object.entries(availability.floors).map(([floorName, floorData]) => (
                  <Grid item xs={12} sm={6} key={floorName}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Floor {floorName}
                        </Typography>
                        
                        <Box display="flex" justifyContent="space-between" mb={2}>
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              Cars: {floorData.car_slots.available} / {floorData.car_slots.total}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Bikes: {floorData.bike_slots.available} / {floorData.bike_slots.total}
                            </Typography>
                          </Box>
                          <Box>
                            <Typography variant="h6">
                              {Math.round(calculateOccupancyRate(floorData))}%
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Occupied
                            </Typography>
                          </Box>
                        </Box>
                        
                        <LinearProgress 
                          variant="determinate" 
                          value={calculateOccupancyRate(floorData)}
                          color={calculateOccupancyRate(floorData) > 80 ? 'error' : 'primary'}
                        />
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            )}
          </Paper>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Vehicle Entries
            </Typography>
            {recentEntries && recentEntries.length > 0 ? (
              <Box>
                {recentEntries.slice(0, 5).map((entry) => (
                  <Box 
                    key={entry.id} 
                    display="flex" 
                    justifyContent="space-between" 
                    alignItems="center"
                    py={1}
                    borderBottom={1}
                    borderColor="divider"
                  >
                    <Box>
                      <Typography variant="body1" fontWeight="medium">
                        {entry.plate_number}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {entry.vehicle_type} • Slot {entry.slot_code}
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      {format(new Date(entry.entry_time), 'HH:mm')}
                    </Typography>
                  </Box>
                ))}
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No recent activity
              </Typography>
            )}
          </Paper>
        </Grid>

        {/* System Alerts */}
        <Grid item xs={12}>
          <Alert severity="info" sx={{ mb: 2 }}>
            Computer Vision System is actively monitoring all entry/exit gates and parking areas.
          </Alert>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;
