import api from "./api";

export async function listFraudLogs({ page = 1, severity, isResolved } = {}) {
  const { data } = await api.get("/fraud", {
    params: { page, severity: severity || undefined, is_resolved: isResolved },
  });
  return data.data;
}

export async function resolveFraudLog(fraudLogId, notes) {
  const { data } = await api.post(`/fraud/${fraudLogId}/resolve`, { notes });
  return data.data;
}
