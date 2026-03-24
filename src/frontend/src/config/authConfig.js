const allowedDomain = process.env.REACT_APP_ALLOWED_DOMAIN;
const allowedDomainNormalized = allowedDomain
  ? allowedDomain.trim().toLowerCase()
  : null;

const approvedEmails = (process.env.REACT_APP_APPROVED_EMAILS || "")
  .split(",")
  .map((email) => email.trim().toLowerCase())
  .filter(Boolean);

const adminEmails = (process.env.REACT_APP_ADMIN_EMAILS || "")
  .split(",")
  .map((email) => email.trim().toLowerCase())
  .filter(Boolean);

const approvedEmailSet = new Set(approvedEmails);
const adminEmailSet = new Set(adminEmails);

export const authConfig = {
  allowedDomain,
  approvedEmails,
  adminEmails,
  otpExpiryMinutes: Number(process.env.REACT_APP_OTP_EXPIRY_MIN || 5),
};

export const isEmailAllowed = (email) => {
  if (!email) return false;
  const normalized = email.trim().toLowerCase();
  const domain = normalized.split("@")[1];

  if (!domain) return false;
  if (adminEmailSet.has(normalized)) return true;

  // If explicit approved list exists, only those emails can access.
  if (approvedEmailSet.size > 0) return approvedEmailSet.has(normalized);

  if (allowedDomainNormalized) return domain === allowedDomainNormalized;
  return false;
};

const API_BASE_URL =
  process.env.REACT_APP_API_URL ||
  process.env.REACT_APP_STAGING_BACKEND_URL ||
  "http://localhost:8080";

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
