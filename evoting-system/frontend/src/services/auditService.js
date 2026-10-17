import api from "./api";

export async function listAuditLogs({ page = 1, action } = {}) {
  const { data } = await api.get("/audit", { params: { page, action: action || undefined } });
  return data.data;
}
