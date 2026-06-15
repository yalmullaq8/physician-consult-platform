export interface ApiError {
  code?: string;
  message: string;
}

export interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  error?: ApiError;
}

export interface AuthUser {
  id: number;
  email: string;
  full_name: string;
  phone_number: string;
  is_active: boolean;
  is_staff: boolean;
}

export interface Specialty {
  id: number;
  name: string;
  slug: string;
  description: string;
  display_order: number;
}

export interface PhysicianSummary {
  id: number;
  full_name: string;
  slug: string;
  specialties: Specialty[];
  professional_title: string;
  consultation_price: string | null;
  consultation_duration_minutes: number | null;
  bio: string;
  profile_photo: string | null;
  is_featured: boolean;
}

export interface PhysicianDetail {
  id: number;
  full_name: string;
  slug: string;
  specialties: Specialty[];
  subspecialty: string;
  professional_title: string;
  hospital_or_clinic: string;
  years_of_experience: number;
  consultation_price: string | null;
  consultation_duration_minutes: number | null;
  bio: string;
  profile_photo: string | null;
  is_featured: boolean;
}

export interface PaginatedResult<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface PhysicianListFilters {
  search?: string;
  specialty?: string;
  featured?: boolean;
}

export interface AvailableSlot {
  start: string;
  end: string;
}

export interface AvailableSlotsPayload {
  date: string;
  slots: AvailableSlot[];
}

export interface CreateBookingPayload {
  consulting_physician_id: number;
  scheduled_start: string;
  case_summary: string;
  requester_name: string;
  requester_specialization: string;
  requester_country_of_practice: string;
  requester_email: string;
  requester_whatsapp_number?: string;
  payment_method_id?: number;
}

export interface PaymentMethodOption {
  payment_method_id: number;
  payment_method_ar?: string;
  payment_method_en?: string;
  service_charge?: string | number;
  total_amount?: string | number;
  is_direct_payment?: boolean;
  image_url?: string;
}

export interface CreateBookingResult {
  booking_reference: string;
  payment_url: string;
}

export interface PaymentCallbackResult {
  booking_reference: string;
  payment_status: string;
  booking_status: string;
}

export interface BookingRecord {
  booking_reference: string;
  requesting_physician: number;
  requesting_physician_name: string;
  consulting_physician: number;
  consulting_physician_name: string;
  scheduled_start: string;
  scheduled_end: string;
  status: string;
  case_summary: string;
  meeting_url: string;
  cancellation_reason: string;
  cancelled_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface WeeklyAvailabilityBlock {
  id: string;
  weekday: number;
  startTime: string;
  endTime: string;
}

export interface AvailabilityExceptionDraft {
  id: string;
  date: string;
  startTime: string;
  endTime: string;
  exceptionType: "unavailable" | "extra_available";
  reason: string;
}

export interface AvailabilityBlockAPI {
  id: number;
  weekday: number;
  start_time: string;
  end_time: string;
  is_active: boolean;
}

export interface AvailabilityExceptionAPI {
  id: number;
  date: string;
  start_time: string;
  end_time: string;
  exception_type: "unavailable" | "extra_available";
  reason: string;
}

export interface MyAvailabilityPayload {
  blocks: AvailabilityBlockAPI[];
  exceptions: AvailabilityExceptionAPI[];
}
