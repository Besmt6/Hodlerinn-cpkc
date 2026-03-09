import axios from "axios";

export const ADMIN_TOKEN_KEY = "adminToken";

export function getAdminToken() {
  return sessionStorage.getItem(ADMIN_TOKEN_KEY);
}

export function setAdminToken(token) {
  if (!token) return;
  sessionStorage.setItem(ADMIN_TOKEN_KEY, token);
}

export function clearAdminToken() {
  sessionStorage.removeItem(ADMIN_TOKEN_KEY);
  sessionStorage.removeItem("adminAuth");
}

export function initializeAdminAxiosAuth() {
  axios.interceptors.request.use((config) => {
    const token = getAdminToken();
    const url = config.url || "";

    if (token && url.includes("/api/admin") && !url.endsWith("/api/admin/login")) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  });

  axios.interceptors.response.use(
    (response) => response,
    (error) => {
      const status = error?.response?.status;
      const url = error?.config?.url || "";
      if (status === 401 && url.includes("/api/admin") && !url.endsWith("/api/admin/login")) {
        clearAdminToken();
        // Use hash-based routing
        if (!window.location.hash.includes("/admin")) {
          window.location.href = "/#/admin";
        }
      }
      return Promise.reject(error);
    },
  );
}
