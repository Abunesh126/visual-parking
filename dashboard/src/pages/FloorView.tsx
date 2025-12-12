import React from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Chip,
  IconButton,
  Tooltip,
  LinearProgress,
} from '@mui/material';
import {
  DirectionsCar,
  TwoWheeler,
  Refresh,
  Videocam,
  CheckCircle,
} from '@mui/icons-material';
import { useParams } from 'react-router-dom';
import { useQuery } from 'react-query';
import { api } from '../services/api';
import { VehicleType, Slot } from '../types';

const FloorView: React.FC = () => {
  const { floorName } = useParams<{ floorName: string }>();
  
  // Fetch floor-specific data
  const { data: availability, isLoading, refetch } = useQuery(
    ['parking-availability', floorName],
    api.getParkingAvailability,
    {
      refetchInterval: 3000, // More frequent updates for floor view
    }
  );

  const { data: slots } = useQuery<Slot[]>(
    ['floor-slots', floorName],
    () => api.getSlots({ floor_name: floorName }),
    {
      enabled: !!floorName,
    }
  );

  const floorData = floorName ? availability?.floors?.[floorName] : undefined;

  const getSlotColor = (slot?: Slot): string => {
    if (!slot) return '#f5f5f5';
    if (slot.is_occupied) return '#ffcdd2'; // Light red for occupied
    if (slot.is_reserved) return '#fff3e0'; // Light orange for reserved
    return '#c8e6c9'; // Light green for available
  };

  const getSlotIcon = (vehicleType: string) => {
    return vehicleType === 'CAR' ? <DirectionsCar /> : <TwoWheeler />;
  };

  const renderSlotGrid = (vehicleType: VehicleType) => {
    const slotsForType = slots?.filter(slot => slot.vehicle_type === vehicleType) || [];
    const slotsPerRow = vehicleType === 'CAR' ? 4 : 8; // 4 car slots or 8 bike slots per row
    const rows: Slot[][] = [];
    
    for (let i = 0; i < slotsForType.length; i += slotsPerRow) {
      const rowSlots = slotsForType.slice(i, i + slotsPerRow);
      rows.push(rowSlots);
    }

    return (
      <Paper sx={{ p: 2, mt: 2 }}>
        <Box display="flex" alignItems="center" mb={2}>
          {getSlotIcon(vehicleType)}
          <Typography variant="h6" sx={{ ml: 1 }}>
            {vehicleType === 'CAR' ? 'Car Parking Slots' : 'Bike Parking Slots'}
          </Typography>
          <Box sx={{ ml: 'auto' }}>
            <Chip 
              label={`${vehicleType === 'CAR' ? floorData?.car_slots?.available : floorData?.bike_slots?.available || 0} Available`}
              color="success"
              size="small"
              sx={{ mr: 1 }}
            />
            <Chip 
              label={`${vehicleType === 'CAR' ? floorData?.car_slots?.occupied : floorData?.bike_slots?.occupied || 0} Occupied`}
              color="error"
              size="small"
            />
          </Box>
        </Box>

        {rows.map((row, rowIndex) => (
          <Grid container spacing={1} key={rowIndex} sx={{ mb: 1 }}>
            {row.map((slot) => (
              <Grid item xs={12 / slotsPerRow} key={slot.id}>
                <Card 
                  variant="outlined"
                  sx={{
                    height: 80,
                    backgroundColor: getSlotColor(slot),
                    border: slot.is_occupied ? '2px solid #f44336' : 
                           slot.is_reserved ? '2px solid #ff9800' : '2px solid #4caf50',
                    cursor: 'pointer',
                    transition: 'transform 0.2s',
                    '&:hover': {
                      transform: 'scale(1.05)',
                    }
                  }}
                >
                  <CardContent sx={{ p: 1, textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                    <Typography variant="body2" fontWeight="bold">
                      {slot.slot_code}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {slot.is_occupied ? 'Occupied' : 
                       slot.is_reserved ? 'Reserved' : 'Available'}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        ))}
      </Paper>
    );
  };

  const calculateOccupancyRate = (): number => {
    if (!floorData) return 0;
    const totalSlots = floorData.car_slots.total + floorData.bike_slots.total;
    const occupiedSlots = floorData.car_slots.occupied + floorData.bike_slots.occupied;
    return totalSlots > 0 ? (occupiedSlots / totalSlots) * 100 : 0;
  };

  if (isLoading) {
    return (
      <Container maxWidth="xl">
        <Typography>Loading floor data...</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 2, mb: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Floor {floorName} - Real-time View
        </Typography>
        <Tooltip title="Refresh Data">
          <IconButton onClick={() => refetch()} color="primary">
            <Refresh />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Floor Statistics */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <DirectionsCar color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Cars</Typography>
              </Box>
              <Typography variant="h4">
                {floorData?.car_slots?.available || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                of {floorData?.car_slots?.total || 0} available
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={floorData?.car_slots?.total ? 
                  (floorData.car_slots.occupied / floorData.car_slots.total) * 100 : 0}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <TwoWheeler color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Bikes</Typography>
              </Box>
              <Typography variant="h4">
                {floorData?.bike_slots?.available || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                of {floorData?.bike_slots?.total || 0} available
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={floorData?.bike_slots?.total ? 
                  (floorData.bike_slots.occupied / floorData.bike_slots.total) * 100 : 0}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <Videocam color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Cameras</Typography>
              </Box>
              <Typography variant="h4">
                {floorName === 'A' ? '7' : '7'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                cameras monitoring
              </Typography>
              <Box display="flex" alignItems="center" mt={1}>
                <CheckCircle color="success" fontSize="small" sx={{ mr: 0.5 }} />
                <Typography variant="body2" color="success.main">
                  All Online
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Occupancy Rate
              </Typography>
              <Typography variant="h4" color={calculateOccupancyRate() > 80 ? 'error.main' : 'primary.main'}>
                {Math.round(calculateOccupancyRate())}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                floor utilization
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={calculateOccupancyRate()}
                color={calculateOccupancyRate() > 80 ? 'error' : 'primary'}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Slot Grids */}
      <Grid container spacing={3}>
        <Grid item xs={12} lg={6}>
          {renderSlotGrid('CAR')}
        </Grid>
        <Grid item xs={12} lg={6}>
          {renderSlotGrid('BIKE')}
        </Grid>
      </Grid>

      {/* Legend */}
      <Paper sx={{ p: 2, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Legend
        </Typography>
        <Box display="flex" gap={3} flexWrap="wrap">
          <Box display="flex" alignItems="center">
            <Box sx={{ width: 20, height: 20, backgroundColor: '#c8e6c9', border: '2px solid #4caf50', mr: 1 }} />
            <Typography variant="body2">Available</Typography>
          </Box>
          <Box display="flex" alignItems="center">
            <Box sx={{ width: 20, height: 20, backgroundColor: '#ffcdd2', border: '2px solid #f44336', mr: 1 }} />
            <Typography variant="body2">Occupied</Typography>
          </Box>
          <Box display="flex" alignItems="center">
            <Box sx={{ width: 20, height: 20, backgroundColor: '#fff3e0', border: '2px solid #ff9800', mr: 1 }} />
            <Typography variant="body2">Reserved</Typography>
          </Box>
        </Box>
      </Paper>
    </Container>
  );
};

export default FloorView;
