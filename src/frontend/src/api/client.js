const apiBaseUrl =
  process.env.REACT_APP_API_URL ||
  process.env.REACT_APP_STAGING_BACKEND_URL ||
  "http://localhost:8080";

export const client = {
  apiBaseUrl: apiBaseUrl.replace(/\/$/, ""),
};