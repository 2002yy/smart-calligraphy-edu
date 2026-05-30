import axios, { AxiosError } from "axios";

type ApiResponse<T> = {
  code: number;
  message: string;
  data: T;
};

function normalizeHttpError(error: unknown): Error {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiResponse<unknown> | { message?: string }>;
    const status = axiosError.response?.status;
    const responseData = axiosError.response?.data;
    const serverMessage =
      typeof responseData === "object" && responseData
        ? "message" in responseData && typeof responseData.message === "string"
          ? responseData.message
          : undefined
        : undefined;

    if (serverMessage) {
      return new Error(serverMessage);
    }

    if (axiosError.code === "ECONNABORTED") {
      return new Error("请求超时，请确认后端服务已启动并稍后重试。");
    }

    if (!axiosError.response) {
      return new Error("无法连接到后端接口，请检查 api-server 是否已启动。");
    }

    if (status === 400) {
      return new Error("请求参数不完整或格式错误，请检查输入内容。");
    }

    if (status === 401) {
      return new Error("登录状态已失效，请重新登录学生账号。");
    }

    if (status === 403) {
      return new Error("当前账号暂无此操作权限。");
    }

    if (status === 404) {
      return new Error("请求的接口或数据不存在，请确认后端路由是否正确。");
    }

    if (status && status >= 500) {
      return new Error("后端服务发生异常，请查看 api-server 控制台日志。");
    }
  }

  if (error instanceof Error) {
    return new Error(error.message || "请求失败，请稍后重试。");
  }

  return new Error("请求失败，请稍后重试。");
}

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
  timeout: 10000
});

request.interceptors.request.use((config) => {
  const token = window.localStorage.getItem("student_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

request.interceptors.response.use(
  (response) => {
    const payload = response.data as ApiResponse<unknown>;
    if (payload.code !== 0) {
      return Promise.reject(new Error(payload.message || "接口返回失败，请稍后重试。"));
    }
    return payload.data;
  },
  (error) => Promise.reject(normalizeHttpError(error))
);

export default request;
