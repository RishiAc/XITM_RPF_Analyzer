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