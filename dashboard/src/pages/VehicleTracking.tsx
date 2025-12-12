import React, { useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  SelectChangeEvent,
} from '@mui/material';
import {
  Search,
  Visibility,
  DirectionsCar,
  TwoWheeler,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { formatDistanceToNow, format } from 'date-fns';
import { api } from '../services/api';
import { EntryEvent } from '../types';

const VehicleTracking: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [vehicleTypeFilter, setVehicleTypeFilter] = useState<string>('all');

  // Fetch entry events (active vehicles)
  const { data: entryEvents } = useQuery<EntryEvent[]>(
    ['entry-events', { active_only: statusFilter === 'active' ? true : undefined }],
    () => api.getEntryEvents({ 
      limit: 100,
      active_only: statusFilter === 'active' ? true : undefined 
    }),
    {
      refetchInterval: 5000,
    }
  );

  const filteredVehicles = entryEvents?.filter(vehicle => {
    const matchesSearch = vehicle.plate_number.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = vehicleTypeFilter === 'all' || vehicle.vehicle_type === vehicleTypeFilter;
    const matchesStatus = statusFilter === 'all' || 
      (statusFilter === 'active' && !vehicle.exit_time) ||
      (statusFilter === 'exited' && vehicle.exit_time);
    
    return matchesSearch && matchesType && matchesStatus;
  }) || [];

  const getVehicleIcon = (type: string) => {
    return type === 'CAR' ? <DirectionsCar /> : <TwoWheeler />;
  };

  const getStatusChip = (vehicle: EntryEvent) => {
    if (vehicle.exit_time) {
      return <Chip label="Exited" color="default" size="small" />;
    }
    return <Chip label="Parked" color="success" size="small" />;
  };

  const calculateDuration = (entryTime: string, _exitTime?: string | null): string => {
    const startTime = new Date(entryTime);
    return formatDistanceToNow(startTime, { addSuffix: false });
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 2, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Vehicle Tracking
      </Typography>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              placeholder="Search by license plate..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                label="Status"
                onChange={(e: SelectChangeEvent) => setStatusFilter(e.target.value)}
              >
                <MenuItem value="all">All</MenuItem>
                <MenuItem value="active">Currently Parked</MenuItem>
                <MenuItem value="exited">Exited</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Vehicle Type</InputLabel>
              <Select
                value={vehicleTypeFilter}
                label="Vehicle Type"
                onChange={(e: SelectChangeEvent) => setVehicleTypeFilter(e.target.value)}
              >
                <MenuItem value="all">All Types</MenuItem>
                <MenuItem value="CAR">Cars</MenuItem>
                <MenuItem value="BIKE">Bikes</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Vehicle Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Type</TableCell>
              <TableCell>License Plate</TableCell>
              <TableCell>Entry Time</TableCell>
              <TableCell>Duration</TableCell>
              <TableCell>Slot</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredVehicles.map((vehicle) => (
              <TableRow key={vehicle.id}>
                <TableCell>{getVehicleIcon(vehicle.vehicle_type)}</TableCell>
                <TableCell>
                  <Typography variant="body1" fontWeight="medium">
                    {vehicle.plate_number}
                  </Typography>
                </TableCell>
                <TableCell>{format(new Date(vehicle.entry_time), 'PPpp')}</TableCell>
                <TableCell>{calculateDuration(vehicle.entry_time, vehicle.exit_time)}</TableCell>
                <TableCell>{vehicle.slot_code || 'N/A'}</TableCell>
                <TableCell>{getStatusChip(vehicle)}</TableCell>
                <TableCell>
                  <IconButton size="small" color="primary">
                    <Visibility />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Box mt={2}>
        <Typography variant="body2" color="text.secondary">
          Showing {filteredVehicles.length} vehicle(s)
        </Typography>
      </Box>
    </Container>
  );
};

export default VehicleTracking;
