import axios from "axios";

export const ADMIN_TOKEN_KEY = "adminToken";
export const ADMIN_TOKEN_EXPIRY_KEY = "adminTokenExpiry";

export function getAdminToken() {
  const token = localStorage.getItem(ADMIN_TOKEN_KEY);
  const expiry = localStorage.getItem(ADMIN_TOKEN_EXPIRY_KEY);
  
  // If no token, return null
  if (!token) {
    return null;
  }
  
  // If we have expiry, check if token is expired
  if (expiry) {
    const expiryTime = new Date(expiry).getTime();
    if (Date.now() >= expiryTime) {
      // Token expired, clear it
      clearAdminToken();
      return null;
    }
  }
  
  // Return token (even without expiry for backwards compatibility)
  return token;
}

export function setAdminToken(token, expiresAt = null) {
  if (!token) return;
  localStorage.setItem(ADMIN_TOKEN_KEY, token);
  if (expiresAt) {
    localStorage.setItem(ADMIN_TOKEN_EXPIRY_KEY, expiresAt);
  }
}

export function clearAdminToken() {
  localStorage.removeItem(ADMIN_TOKEN_KEY);
  localStorage.removeItem(ADMIN_TOKEN_EXPIRY_KEY);
  // Also clear old sessionStorage keys for backwards compatibility
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
