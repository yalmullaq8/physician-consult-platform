import {
  AvailableSlotsPayload,
  AvailabilityBlockAPI,
  AvailabilityExceptionAPI,
  ApiEnvelope,
  AuthUser,
  BookingRecord,
  CreateBookingPayload,
  CreateBookingResult,
  MyAvailabilityPayload,
  PaginatedResult,
  PaymentMethodOption,
  PaymentCallbackResult,
  PhysicianDetail,
  PhysicianListFilters,
  PhysicianSummary,
  Specialty,
} from "@/types/api";

const RAW_API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

const API_BASE_URL = RAW_API_BASE_URL.replace(/\/$/, "");

function buildUrl(path: string): string {
  return `${API_BASE_URL}${path.startsWith("/") ? "" : "/"}${path}`;
}

function extractErrorMessage(body: unknown, fallback: string): string {
  if (!body || typeof body !== "object") {
    return fallback;
  }

  const candidate = body as {
    error?: { message?: string };
    detail?: string;
    message?: string;
    [key: string]: unknown;
  };

  if (candidate.error?.message) {
    return candidate.error.message;
  }

  if (typeof candidate.detail === "string" && candidate.detail.trim()) {
    return candidate.detail;
  }

  if (typeof candidate.message === "string" && candidate.message.trim()) {
    return candidate.message;
  }

  const firstEntry = Object.values(candidate).find((value) => {
    if (typeof value === "string" && value.trim()) {
      return true;
    }
    if (Array.isArray(value) && value.length > 0 && typeof value[0] === "string") {
      return true;
    }
    return false;
  });

  if (typeof firstEntry === "string") {
    return firstEntry;
  }

  if (Array.isArray(firstEntry) && firstEntry.length > 0 && typeof firstEntry[0] === "string") {
    return firstEntry[0];
  }

  return fallback;
}

function getCookie(name: string): string | null {
  if (typeof document === "undefined") {
    return null;
  }

  const cookies = document.cookie ? document.cookie.split(";") : [];
  for (const rawCookie of cookies) {
    const cookie = rawCookie.trim();
    if (cookie.startsWith(`${name}=`)) {
      return decodeURIComponent(cookie.slice(name.length + 1));
    }
  }

  return null;
}

async function fetchCsrfToken(): Promise<string | null> {
  // In a decoupled setup the frontend and backend can live on different
  // domains, so JavaScript cannot read the csrftoken cookie set by the
  // backend. The csrf endpoint returns the token in the body for this reason.
  try {
    const response = await fetch(buildUrl("/auth/csrf/"), {
      credentials: "include",
      cache: "no-store",
    });

    if (response.ok) {
      try {
        const body = (await response.json()) as ApiEnvelope<{ csrf_token?: string }>;
        if (body?.success && body.data?.csrf_token) {
          return body.data.csrf_token;
        }
      } catch {
        // Ignore body parse errors and fall back to the cookie.
      }
    }
  } catch {
    return getCookie("csrftoken");
  }

  return getCookie("csrftoken");
}

export async function loginUser(payload: {
  email: string;
  password: string;
}): Promise<{ success: boolean; data?: AuthUser; errorMessage?: string }> {
  const csrfToken = await fetchCsrfToken();
  if (!csrfToken) {
    return {
      success: false,
      errorMessage: "Could not initialize login session. Please refresh and try again.",
    };
  }

  try {
    const response = await fetch(buildUrl("/auth/login/"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      credentials: "include",
      cache: "no-store",
      body: JSON.stringify({
        email: payload.email.trim().toLowerCase(),
        password: payload.password,
      }),
    });

    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      body = null;
    }

    const envelope = body as ApiEnvelope<AuthUser> | null;
    if (!response.ok || !envelope?.success || !envelope?.data) {
      return {
        success: false,
        errorMessage: extractErrorMessage(body, "Login failed."),
      };
    }

    return { success: true, data: envelope.data };
  } catch {
    return {
      success: false,
      errorMessage: "Unable to reach authentication service.",
    };
  }
}

export async function logoutUser(): Promise<{ success: boolean; errorMessage?: string }> {
  const csrfToken = await fetchCsrfToken();
  if (!csrfToken) {
    return {
      success: false,
      errorMessage: "Could not initialize logout session.",
    };
  }

  try {
    const response = await fetch(buildUrl("/auth/logout/"), {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken,
      },
      credentials: "include",
      cache: "no-store",
    });

    if (!response.ok) {
      let body: unknown = null;
      try {
        body = await response.json();
      } catch {
        body = null;
      }

      return {
        success: false,
        errorMessage: extractErrorMessage(body, "Logout failed."),
      };
    }

    return { success: true };
  } catch {
    return {
      success: false,
      errorMessage: "Unable to reach authentication service.",
    };
  }
}

export async function getCurrentUser(): Promise<{
  success: boolean;
  data?: AuthUser;
  errorMessage?: string;
}> {
  try {
    const response = await fetch(buildUrl("/auth/me/"), {
      credentials: "include",
      cache: "no-store",
    });

    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      body = null;
    }

    const envelope = body as ApiEnvelope<AuthUser> | null;
    if (!response.ok || !envelope?.success || !envelope?.data) {
      return {
        success: false,
        errorMessage: extractErrorMessage(body, "Not authenticated."),
      };
    }

    return { success: true, data: envelope.data };
  } catch {
    return {
      success: false,
      errorMessage: "Unable to reach authentication service.",
    };
  }
}

async function request<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(buildUrl(path), {
      next: { revalidate: 60 },
    });

    if (!response.ok) {
      return null;
    }

    const body: ApiEnvelope<T> = await response.json();
    if (!body.success) {
      return null;
    }

    return body.data;
  } catch {
    return null;
  }
}

export async function getSpecialties(): Promise<Specialty[]> {
  const data = await request<Specialty[]>("/specialties/");
  return data ?? [];
}

export async function getPhysicians(
  filters: PhysicianListFilters = {},
): Promise<PhysicianSummary[]> {
  const params = new URLSearchParams();

  if (filters.search) {
    params.set("search", filters.search);
  }

  if (filters.specialty) {
    params.set("specialty", filters.specialty);
  }

  if (filters.featured) {
    params.set("featured", "true");
  }

  const queryString = params.toString();
  const endpoint = queryString
    ? `/physicians/?${queryString}`
    : "/physicians/";

  const data = await request<PaginatedResult<PhysicianSummary> | PhysicianSummary[]>(
    endpoint,
  );

  if (!data) {
    return [];
  }

  if (Array.isArray(data)) {
    return data;
  }

  return data.results;
}

export async function getPhysicianBySlug(
  slug: string,
): Promise<PhysicianDetail | null> {
  if (!slug) {
    return null;
  }

  return request<PhysicianDetail>(`/physicians/${slug}/`);
}

export async function getPhysicianAvailableSlots(
  slug: string,
  date: string,
): Promise<AvailableSlotsPayload | null> {
  if (!slug || !date) {
    return null;
  }

  const encodedDate = encodeURIComponent(date);

  try {
    const response = await fetch(
      buildUrl(`/physicians/${slug}/available-slots/?date=${encodedDate}`),
      { cache: "no-store" },
    );

    if (!response.ok) {
      return null;
    }

    const body = (await response.json()) as ApiEnvelope<AvailableSlotsPayload>;
    if (!body.success) {
      return null;
    }

    return body.data;
  } catch {
    return null;
  }
}

export async function createBooking(payload: CreateBookingPayload): Promise<{
  success: boolean;
  data?: CreateBookingResult;
  errorMessage?: string;
}> {
  const csrfToken = await fetchCsrfToken();
  if (!csrfToken) {
    return {
      success: false,
      errorMessage: "Could not initialize booking session. Please refresh and try again.",
    };
  }

  try {
    const response = await fetch(buildUrl("/bookings/"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      credentials: "include",
      cache: "no-store",
      body: JSON.stringify(payload),
    });

    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      body = null;
    }

    const envelope = body as ApiEnvelope<CreateBookingResult> | null;
    if (!response.ok || !envelope?.success || !envelope?.data) {
      return {
        success: false,
        errorMessage: extractErrorMessage(body, "Unable to create booking."),
      };
    }

    return { success: true, data: envelope.data };
  } catch {
    return {
      success: false,
      errorMessage: "Unable to reach booking service. Please try again.",
    };
  }
}

export async function verifyMyFatoorahCallback(
  paymentIdentifier: string,
  bookingReference?: string,
): Promise<{ success: boolean; data?: PaymentCallbackResult; errorMessage?: string }> {
  if (!paymentIdentifier) {
    return {
      success: false,
      errorMessage: "Missing payment identifier.",
    };
  }

  const params = new URLSearchParams({ paymentId: paymentIdentifier });
  if (bookingReference) {
    params.set("bookingReference", bookingReference);
  }
  const query = params.toString();
  const endpoint = buildUrl(`/payments/myfatoorah/confirm/?${query}`);

  const attemptVerification = async () => {
    const response = await fetch(endpoint, { cache: "no-store" });

    let body: ApiEnvelope<PaymentCallbackResult> | null = null;
    try {
      body = (await response.json()) as ApiEnvelope<PaymentCallbackResult>;
    } catch {
      body = null;
    }

    if (!response.ok || !body?.success || !body?.data) {
      const fallback =
        response.status >= 500
          ? "Payment verification is temporarily unavailable. Please refresh in a moment."
          : "Payment verification failed.";
      return {
        success: false,
        errorMessage: body?.error?.message ?? fallback,
      };
    }

    return { success: true as const, data: body.data };
  };

  try {
    const firstAttempt = await attemptVerification();
    if (firstAttempt.success) {
      return firstAttempt;
    }

    // Retry once for transient provider/network conditions.
    if ((firstAttempt.errorMessage ?? "").toLowerCase().includes("temporarily unavailable")) {
      const secondAttempt = await attemptVerification();
      if (secondAttempt.success) {
        return secondAttempt;
      }
      return secondAttempt;
    }

    return firstAttempt;
  } catch {
    return {
      success: false,
      errorMessage:
        "Payment verification is temporarily unavailable. Please refresh in a moment.",
    };
  }
}

export async function getMyFatoorahPaymentMethods(
  amount: number,
): Promise<{ success: boolean; data: PaymentMethodOption[]; errorMessage?: string }> {
  const normalizedAmount = Number.isFinite(amount) && amount > 0 ? amount : 1;

  try {
    const query = new URLSearchParams({ amount: String(normalizedAmount) }).toString();
    const response = await fetch(buildUrl(`/payments/myfatoorah/methods/?${query}`), {
      cache: "no-store",
    });

    const body = (await response.json()) as ApiEnvelope<PaymentMethodOption[]>;
    if (!response.ok || !body.success || !Array.isArray(body.data)) {
      return {
        success: false,
        data: [],
        errorMessage: body.error?.message ?? "Could not load payment methods.",
      };
    }

    return { success: true, data: body.data };
  } catch {
    return {
      success: false,
      data: [],
      errorMessage: "Could not reach payment service.",
    };
  }
}

export async function getMyBookings(): Promise<{
  success: boolean;
  data: BookingRecord[];
  errorMessage?: string;
}> {
  try {
    const response = await fetch(buildUrl("/me/bookings/"), {
      credentials: "include",
      cache: "no-store",
    });

    const body = (await response.json()) as ApiEnvelope<BookingRecord[]>;
    if (!response.ok || !body.success || !Array.isArray(body.data)) {
      return {
        success: false,
        data: [],
        errorMessage: body.error?.message ?? "Could not load dashboard bookings.",
      };
    }

    return { success: true, data: body.data };
  } catch {
    return {
      success: false,
      data: [],
      errorMessage: "Could not reach booking service.",
    };
  }
}

export async function getMyAvailability(): Promise<{
  success: boolean;
  data: MyAvailabilityPayload;
  errorMessage?: string;
}> {
  try {
    const response = await fetch(buildUrl("/me/availability/"), {
      credentials: "include",
      cache: "no-store",
    });

    const body = (await response.json()) as ApiEnvelope<MyAvailabilityPayload>;
    if (!response.ok || !body.success || !body.data) {
      return {
        success: false,
        data: { blocks: [], exceptions: [] },
        errorMessage: body.error?.message ?? "Could not load availability.",
      };
    }

    return { success: true, data: body.data };
  } catch {
    return {
      success: false,
      data: { blocks: [], exceptions: [] },
      errorMessage: "Could not reach availability service.",
    };
  }
}

export async function createAvailabilityBlock(payload: {
  weekday: number;
  start_time: string;
  end_time: string;
  is_active?: boolean;
}): Promise<{ success: boolean; data?: AvailabilityBlockAPI; errorMessage?: string }> {
  const csrfToken = await fetchCsrfToken();
  if (!csrfToken) {
    return {
      success: false,
      errorMessage: "Could not initialize availability session. Please refresh and try again.",
    };
  }

  try {
    const response = await fetch(buildUrl("/me/availability/blocks/"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      credentials: "include",
      cache: "no-store",
      body: JSON.stringify({ ...payload, is_active: payload.is_active ?? true }),
    });

    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      body = null;
    }

    const envelope = body as ApiEnvelope<AvailabilityBlockAPI> | null;
    if (!response.ok || !envelope?.success || !envelope?.data) {
      return {
        success: false,
        errorMessage: extractErrorMessage(body, "Could not create availability block."),
      };
    }
    return { success: true, data: envelope.data };
  } catch {
    return { success: false, errorMessage: "Could not reach availability service." };
  }
}

export async function deleteAvailabilityBlock(
  id: number,
): Promise<{ success: boolean; errorMessage?: string }> {
  const csrfToken = await fetchCsrfToken();
  if (!csrfToken) {
    return {
      success: false,
      errorMessage: "Could not initialize availability session. Please refresh and try again.",
    };
  }

  try {
    const response = await fetch(buildUrl(`/me/availability/blocks/${id}/`), {
      method: "DELETE",
      headers: {
        "X-CSRFToken": csrfToken,
      },
      credentials: "include",
      cache: "no-store",
    });

    if (!response.ok) {
      let body: unknown = null;
      try {
        body = await response.json();
      } catch {
        body = null;
      }

      return {
        success: false,
        errorMessage: extractErrorMessage(body, "Could not delete availability block."),
      };
    }

    return { success: true };
  } catch {
    return { success: false, errorMessage: "Could not reach availability service." };
  }
}

export async function updateAvailabilityBlock(
  id: number,
  payload: Partial<{
    weekday: number;
    start_time: string;
    end_time: string;
    is_active: boolean;
  }>,
): Promise<{ success: boolean; data?: AvailabilityBlockAPI; errorMessage?: string }> {
  const csrfToken = await fetchCsrfToken();
  if (!csrfToken) {
    return {
      success: false,
      errorMessage: "Could not initialize availability session. Please refresh and try again.",
    };
  }

  try {
    const response = await fetch(buildUrl(`/me/availability/blocks/${id}/`), {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      credentials: "include",
      cache: "no-store",
      body: JSON.stringify(payload),
    });

    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      body = null;
    }

    const envelope = body as ApiEnvelope<AvailabilityBlockAPI> | null;
    if (!response.ok || !envelope?.success || !envelope?.data) {
      return {
        success: false,
        errorMessage: extractErrorMessage(body, "Could not update availability block."),
      };
    }
    return { success: true, data: envelope.data };
  } catch {
    return { success: false, errorMessage: "Could not reach availability service." };
  }
}

export async function createAvailabilityException(payload: {
  date: string;
  start_time: string;
  end_time: string;
  exception_type: "unavailable" | "extra_available";
  reason?: string;
}): Promise<{ success: boolean; data?: AvailabilityExceptionAPI; errorMessage?: string }> {
  const csrfToken = await fetchCsrfToken();
  if (!csrfToken) {
    return {
      success: false,
      errorMessage: "Could not initialize availability session. Please refresh and try again.",
    };
  }

  try {
    const response = await fetch(buildUrl("/me/availability/exceptions/"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      credentials: "include",
      cache: "no-store",
      body: JSON.stringify(payload),
    });

    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      body = null;
    }

    const envelope = body as ApiEnvelope<AvailabilityExceptionAPI> | null;
    if (!response.ok || !envelope?.success || !envelope?.data) {
      return {
        success: false,
        errorMessage: extractErrorMessage(body, "Could not create availability exception."),
      };
    }
    return { success: true, data: envelope.data };
  } catch {
    return { success: false, errorMessage: "Could not reach availability service." };
  }
}

export async function deleteAvailabilityException(
  id: number,
): Promise<{ success: boolean; errorMessage?: string }> {
  const csrfToken = await fetchCsrfToken();
  if (!csrfToken) {
    return {
      success: false,
      errorMessage: "Could not initialize availability session. Please refresh and try again.",
    };
  }

  try {
    const response = await fetch(buildUrl(`/me/availability/exceptions/${id}/`), {
      method: "DELETE",
      headers: {
        "X-CSRFToken": csrfToken,
      },
      credentials: "include",
      cache: "no-store",
    });

    if (!response.ok) {
      let body: unknown = null;
      try {
        body = await response.json();
      } catch {
        body = null;
      }

      return {
        success: false,
        errorMessage: extractErrorMessage(body, "Could not delete availability exception."),
      };
    }

    return { success: true };
  } catch {
    return { success: false, errorMessage: "Could not reach availability service." };
  }
}

export async function updateAvailabilityException(
  id: number,
  payload: Partial<{
    date: string;
    start_time: string;
    end_time: string;
    exception_type: "unavailable" | "extra_available";
    reason: string;
  }>,
): Promise<{ success: boolean; data?: AvailabilityExceptionAPI; errorMessage?: string }> {
  const csrfToken = await fetchCsrfToken();
  if (!csrfToken) {
    return {
      success: false,
      errorMessage: "Could not initialize availability session. Please refresh and try again.",
    };
  }

  try {
    const response = await fetch(buildUrl(`/me/availability/exceptions/${id}/`), {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      credentials: "include",
      cache: "no-store",
      body: JSON.stringify(payload),
    });

    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      body = null;
    }

    const envelope = body as ApiEnvelope<AvailabilityExceptionAPI> | null;
    if (!response.ok || !envelope?.success || !envelope?.data) {
      return {
        success: false,
        errorMessage: extractErrorMessage(body, "Could not update availability exception."),
      };
    }
    return { success: true, data: envelope.data };
  } catch {
    return { success: false, errorMessage: "Could not reach availability service." };
  }
}
