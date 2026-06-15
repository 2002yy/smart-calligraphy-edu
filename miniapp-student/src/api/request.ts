export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
export const TOKEN_KEY = "student_mobile_token";

interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

type Method = "GET" | "POST" | "PUT" | "DELETE";

function authHeader() {
  const token = uni.getStorageSync(TOKEN_KEY);
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function unwrap<T>(response: UniApp.RequestSuccessCallbackResult): T {
  const payload = response.data as ApiResponse<T> | string;
  const data = typeof payload === "string" ? JSON.parse(payload) as ApiResponse<T> : payload;
  if (response.statusCode < 200 || response.statusCode >= 300) {
    throw new Error(data?.message || `HTTP ${response.statusCode}`);
  }
  if (data.code !== 0) {
    throw new Error(data.message || "请求失败");
  }
  return data.data;
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
      fail: (error) => reject(new Error(error.errMsg || "网络请求失败"))
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
      fail: (error) => reject(new Error(error.errMsg || "上传失败"))
    });
  });
}
