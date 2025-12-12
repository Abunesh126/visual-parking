import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import {
  ParkingAvailability,
  EntryEvent,
  ExitEvent,
  Slot,
  HealthStatus,
  DetailedHealth,
  CVEntryDetection,
  SystemStatus,
  QueryParams,
} from '../types';

// Create axios instance with base configuration
const apiClient: AxiosInstance = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    throw new Error(error.response?.data?.detail || 'API request failed');
  }
);

interface HourlyStat {
  hour: string;
  entries: number;
  exits: number;
  occupancy: number;
}

interface DailyStat {
  date: string;
  day: string;
  total_entries: number;
  total_exits: number;
  peak_occupancy: number;
  avg_duration: number;
}

interface CameraData {
  id: number;
  camera_code: string;
  role: 'ENTRY' | 'EXIT' | 'INDOOR';
  status: 'ACTIVE' | 'INACTIVE' | 'MAINTENANCE';
  rtsp_url?: string;
  floor_id?: number;
}

// API service methods
export const api = {
  // Parking availability
  getParkingAvailability: (): Promise<ParkingAvailability> => 
    apiClient.get('/parking-availability'),
  
  // Entry events
  getEntryEvents: (params: QueryParams = {}): Promise<EntryEvent[]> => {
    const queryString = new URLSearchParams(params as Record<string, string>).toString();
    return apiClient.get(`/entry-events?${queryString}`);
  },
  
  createEntryEvent: (data: Partial<EntryEvent>): Promise<EntryEvent> => 
    apiClient.post('/entry-events', data),
  
  getEntryEventById: (id: number): Promise<EntryEvent> => 
    apiClient.get(`/entry-events/${id}`),
  
  getEntryEventByLicense: (license: string): Promise<EntryEvent> => 
    apiClient.get(`/entry-events/license/${license}`),
  
  // Exit events
  getExitEvents: (params: QueryParams = {}): Promise<ExitEvent[]> => {
    const queryString = new URLSearchParams(params as Record<string, string>).toString();
    return apiClient.get(`/exit-events?${queryString}`);
  },
  
  createExitEvent: (ticketId: string, data: Partial<ExitEvent> = {}): Promise<ExitEvent> => 
    apiClient.post(`/exit-events/${ticketId}`, data),
  
  createExitEventByLicense: (license: string, data: Partial<ExitEvent> = {}): Promise<ExitEvent> => 
    apiClient.post(`/exit-events/license/${license}`, data),
  
  // Slots
  getSlots: (params: QueryParams = {}): Promise<Slot[]> => {
    const queryString = new URLSearchParams(params as Record<string, string>).toString();
    return apiClient.get(`/slots?${queryString}`);
  },
  
  getSlotById: (id: number): Promise<Slot> => 
    apiClient.get(`/slots/${id}`),
  
  updateSlot: (id: number, data: Partial<Slot>): Promise<Slot> => 
    apiClient.put(`/slots/${id}`, data),
  
  getAvailableSlots: (params: QueryParams = {}): Promise<Slot[]> => {
    const queryString = new URLSearchParams(params as Record<string, string>).toString();
    return apiClient.get(`/slots/available?${queryString}`);
  },
  
  getSlotsByFloor: (floorId: string): Promise<Slot[]> => 
    apiClient.get(`/slots/floor/${floorId}`),
  
  getSlotByCode: (code: string): Promise<Slot> => 
    apiClient.get(`/slots/search/${code}`),
  
  // Health and monitoring
  getHealthStatus: (): Promise<HealthStatus> => 
    apiClient.get('/health'),
  
  getDetailedHealth: (): Promise<DetailedHealth> => 
    apiClient.get('/health/detailed'),
  
  // CV system integration
  handleCVEntryDetection: (data: CVEntryDetection): Promise<EntryEvent> => 
    apiClient.post('/cv-entry-detection', data),
  
  // System status (mock endpoint - would need to be implemented)
  getSystemStatus: async (): Promise<SystemStatus> => {
    try {
      // Try to get actual system status
      return await apiClient.get('/system-status');
    } catch (error) {
      // Return mock data if endpoint doesn't exist
      return {
        cv_system: {
          is_running: true,
          config: {
            confidence_threshold: 0.6,
            plate_confidence_threshold: 0.7,
            processing_fps: 5
          }
        },
        cameras: {
          '1': { status: 'ACTIVE', last_seen: new Date().toISOString() },
          '2': { status: 'ACTIVE', last_seen: new Date().toISOString() },
        },
        database: {
          status: 'ONLINE'
        }
      };
    }
  },
  
  // Occupancy tracking
  getOccupancyOverview: (): Promise<any> => 
    apiClient.get('/slot-occupancy'),
  
  // Analytics (mock endpoints)
  getHourlyStats: async (): Promise<HourlyStat[]> => {
    // Mock hourly statistics
    const hours: HourlyStat[] = [];
    const currentHour = new Date().getHours();
    
    for (let i = 0; i < 24; i++) {
      const hour = (currentHour - 23 + i + 24) % 24;
      hours.push({
        hour: `${hour.toString().padStart(2, '0')}:00`,
        entries: Math.floor(Math.random() * 20) + 5,
        exits: Math.floor(Math.random() * 18) + 3,
        occupancy: Math.floor(Math.random() * 40) + 30
      });
    }
    
    return hours;
  },
  
  getDailyStats: async (): Promise<DailyStat[]> => {
    // Mock daily statistics
    const days: DailyStat[] = [];
    const today = new Date();
    
    for (let i = 6; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      
      days.push({
        date: date.toISOString().split('T')[0],
        day: date.toLocaleDateString('en-US', { weekday: 'short' }),
        total_entries: Math.floor(Math.random() * 200) + 100,
        total_exits: Math.floor(Math.random() * 190) + 95,
        peak_occupancy: Math.floor(Math.random() * 30) + 60,
        avg_duration: Math.floor(Math.random() * 60) + 90 // minutes
      });
    }
    
    return days;
  },
  
  // Camera management
  getCameras: async (): Promise<CameraData[]> => {
    // Mock camera data
    return [
      { id: 1, camera_code: 'ENTRY_1', role: 'ENTRY', status: 'ACTIVE', rtsp_url: 'rtsp://192.168.1.100:554/entry' },
      { id: 2, camera_code: 'EXIT_1', role: 'EXIT', status: 'ACTIVE', rtsp_url: 'rtsp://192.168.1.101:554/exit' },
      { id: 3, camera_code: 'A_CAR_01', role: 'INDOOR', status: 'ACTIVE', floor_id: 1 },
      { id: 4, camera_code: 'A_CAR_02', role: 'INDOOR', status: 'ACTIVE', floor_id: 1 },
      { id: 5, camera_code: 'A_BIKE_01', role: 'INDOOR', status: 'ACTIVE', floor_id: 1 },
      { id: 6, camera_code: 'B_CAR_01', role: 'INDOOR', status: 'ACTIVE', floor_id: 2 },
    ];
  },
};

export default apiClient;
