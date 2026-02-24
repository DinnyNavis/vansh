import axios from "axios";

// If production URL exists use it,
// otherwise use local backend
export const API_BASE =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:5007";

const api = axios.create({
  baseURL: `${API_BASE}/api`,
  timeout: 120000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Attach JWT
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("vansh_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("vansh_token");
      localStorage.removeItem("vansh_user");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;
