// Type definitions for the parking management system

export interface ParkingSlots {
  total: number;
  occupied: number;
  available: number;
}

export interface FloorData {
  car_slots: ParkingSlots;
  bike_slots: ParkingSlots;
}

export interface ParkingAvailability {
  floors: {
    [floorName: string]: FloorData;
  };
  total_car_slots?: number;
  total_bike_slots?: number;
  last_updated?: string;
}

export type VehicleType = 'CAR' | 'BIKE';
export type SlotStatus = 'AVAILABLE' | 'OCCUPIED' | 'RESERVED' | 'MAINTENANCE';

export interface Slot {
  id: number;
  slot_code: string;
  floor_name: string;
  vehicle_type: VehicleType;
  is_occupied: boolean;
  is_reserved: boolean;
  status: SlotStatus;
  x_coordinate?: number;
  y_coordinate?: number;
  created_at?: string;
  updated_at?: string;
}

export interface EntryEvent {
  id: number;
  ticket_id: string;
  plate_number: string;
  vehicle_type: VehicleType;
  entry_time: string;
  exit_time?: string | null;
  slot_id?: number;
  slot_code?: string;
  floor_name?: string;
  entry_image_url?: string;
  plate_confidence?: number;
  created_at?: string;
}

export interface ExitEvent {
  id: number;
  ticket_id: string;
  plate_number: string;
  vehicle_type: VehicleType;
  exit_time: string;
  parking_duration_minutes: number;
  parking_fee: number;
  exit_image_url?: string;
  created_at?: string;
}

export interface Camera {
  id: number;
  camera_id: string;
  name: string;
  location: string;
  status: 'ACTIVE' | 'INACTIVE' | 'MAINTENANCE';
  role: 'ENTRY' | 'EXIT' | 'INDOOR';
  rtsp_url?: string;
  is_online: boolean;
  last_frame_time?: string;
  created_at?: string;
}

export interface SystemStatus {
  cv_system?: {
    is_running: boolean;
    config?: {
      confidence_threshold: number;
      plate_confidence_threshold: number;
      processing_fps: number;
    };
  };
  cameras?: {
    [cameraId: string]: {
      status: string;
      last_seen?: string;
    };
  };
  database?: {
    status: string;
  };
}

export interface CVEntryDetection {
  plate_number: string;
  vehicle_type: VehicleType;
  confidence: number;
  plate_confidence: number;
  image_path?: string;
  camera_id?: string;
}

export interface QueryParams {
  [key: string]: string | number | boolean | undefined;
}

export interface HealthStatus {
  status: string;
  timestamp: string;
  uptime?: number;
}

export interface DetailedHealth extends HealthStatus {
  database: {
    status: string;
    response_time?: number;
  };
  cache: {
    status: string;
  };
}
