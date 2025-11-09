const allowedDomain = process.env.REACT_APP_ALLOWED_DOMAIN || "example.com";

const adminEmails = (process.env.REACT_APP_ADMIN_EMAILS || "")
  .split(",")
  .map((email) => email.trim())
  .filter(Boolean);

export const authConfig = {
  allowedDomain,
  adminEmails,
  otpExpiryMinutes: Number(process.env.REACT_APP_OTP_EXPIRY_MIN || 5),
};

export const isEmailAllowed = (email) => {
  if (!email) return false;
  const normalized = email.trim().toLowerCase();
  const domain = normalized.split("@")[1];

  if (!domain) return false;
  if (authConfig.adminEmails.includes(normalized)) return true;

  return domain === authConfig.allowedDomain.toLowerCase();
};

const API_BASE_URL =
  process.env.NODE_ENV === "production"
    ? "http://backend:8080"  // Internal Docker service name
    : "http://localhost:8080";  // Local dev (non-Docker)

export const AUTH_CONFIG = {
  apiBaseUrl: API_BASE_URL,

  // Add any existing auth-related config here
  // For example:
  endpoints: {
    login: `${API_BASE_URL}/auth/login`,
    register: `${API_BASE_URL}/auth/register`,
    logout: `${API_BASE_URL}/auth/logout`,
  },
};

export default AUTH_CONFIG;