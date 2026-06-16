export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
export const TOKEN_KEY = "student_mobile_token";

interface ApiResponse<T> {
  code?: number;
  message?: string;
  detail?: string;
  data?: T;
}

type Method = "GET" | "POST" | "PUT" | "DELETE";

function authHeader() {
  const token = uni.getStorageSync(TOKEN_KEY);
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function parsePayload<T>(payload: unknown): ApiResponse<T> {
  if (typeof payload === "string") {
    return JSON.parse(payload) as ApiResponse<T>;
  }
  return payload as ApiResponse<T>;
}

function unwrap<T>(response: UniApp.RequestSuccessCallbackResult): T {
  const data = parsePayload<T>(response.data);
  const errorMessage = data?.message || data?.detail;
  if (response.statusCode < 200 || response.statusCode >= 300) {
    throw new Error(errorMessage || `HTTP ${response.statusCode}`);
  }
  if (typeof data.code === "number" && data.code !== 0) {
    throw new Error(errorMessage || "Request failed");
  }
  return data.data as T;
}

export function request<T>(options: { url: string; method?: Method; data?: unknown; header?: Record<string, string> }) {
  return new Promise<T>((resolve, reject) => {
    uni.request({
      url: `${API_BASE_URL}${options.url}`,
      method: options.method || "GET",
      data: options.data,
      header: {
        "Content-Type": "application/json",
        ...authHeader(),
        ...options.header
      },
      success: (response) => {
        try {
          resolve(unwrap<T>(response));
        } catch (error) {
          reject(error);
        }
      },
      fail: (error) => reject(new Error(error.errMsg || "Network request failed"))
    });
  });
}

export function upload<T>(options: { url: string; filePath: string; formData?: Record<string, string | number> }) {
  return new Promise<T>((resolve, reject) => {
    uni.uploadFile({
      url: `${API_BASE_URL}${options.url}`,
      filePath: options.filePath,
      name: "file",
      formData: options.formData,
      header: authHeader(),
      success: (response) => {
        try {
          resolve(unwrap<T>(response as UniApp.RequestSuccessCallbackResult));
        } catch (error) {
          reject(error);
        }
      },
      fail: (error) => reject(new Error(error.errMsg || "Upload failed"))
    });
  });
}
