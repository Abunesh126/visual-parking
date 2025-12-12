import React, { useState } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  SelectChangeEvent,
} from '@mui/material';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { useQuery } from 'react-query';
import { api } from '../services/api';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div
    role="tabpanel"
    hidden={value !== index}
    id={`analytics-tabpanel-${index}`}
    aria-labelledby={`analytics-tab-${index}`}
  >
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
);

const Analytics: React.FC = () => {
  const [timeRange, setTimeRange] = useState<string>('today');
  const [activeTab, setActiveTab] = useState<number>(0);

  // Fetch analytics data
  const { data: hourlyStats } = useQuery(
    ['hourly-stats', timeRange],
    api.getHourlyStats,
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  const { data: dailyStats } = useQuery(
    ['daily-stats'],
    api.getDailyStats
  );

  const { data: availability } = useQuery(
    'parking-availability',
    api.getParkingAvailability
  );

  // Colors for charts
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

  // Pie chart data for floor distribution
  const floorDistributionData = availability?.floors ? 
    Object.entries(availability.floors).map(([floorName, floorData]) => ({
      name: `Floor ${floorName}`,
      value: floorData.car_slots.occupied + floorData.bike_slots.occupied,
      total: floorData.car_slots.total + floorData.bike_slots.total,
    })) : [];

  return (
    <Container maxWidth="xl" sx={{ mt: 2, mb: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Analytics & Insights
        </Typography>
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>Time Range</InputLabel>
          <Select
            value={timeRange}
            label="Time Range"
            onChange={(e: SelectChangeEvent) => setTimeRange(e.target.value)}
          >
            <MenuItem value="today">Today</MenuItem>
            <MenuItem value="week">Last 7 Days</MenuItem>
            <MenuItem value="month">Last 30 Days</MenuItem>
          </Select>
        </FormControl>
      </Box>

      <Tabs value={activeTab} onChange={(_e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
        <Tab label="Occupancy Trends" />
        <Tab label="Entry/Exit Analysis" />
        <Tab label="Floor Distribution" />
      </Tabs>

      <TabPanel value={activeTab} index={0}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Hourly Occupancy Trends
          </Typography>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={hourlyStats}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="occupancy" stroke="#8884d8" name="Occupancy" />
            </LineChart>
          </ResponsiveContainer>
        </Paper>
      </TabPanel>

      <TabPanel value={activeTab} index={1}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Entry & Exit Patterns
          </Typography>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={hourlyStats}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="entries" fill="#82ca9d" name="Entries" />
              <Bar dataKey="exits" fill="#8884d8" name="Exits" />
            </BarChart>
          </ResponsiveContainer>
        </Paper>
      </TabPanel>

      <TabPanel value={activeTab} index={2}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Floor Occupancy Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={floorDistributionData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry) => entry.name}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {floorDistributionData.map((_entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Daily Statistics
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={dailyStats}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="total_entries" fill="#82ca9d" name="Entries" />
                  <Bar dataKey="total_exits" fill="#8884d8" name="Exits" />
                </BarChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>
        </Grid>
      </TabPanel>
    </Container>
  );
};

export default Analytics;
