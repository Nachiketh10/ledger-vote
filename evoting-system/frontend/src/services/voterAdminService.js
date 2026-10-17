import api from "./api";

export async function listVoters({ page = 1, search, isVerified, isActive } = {}) {
  const { data } = await api.get("/admin/voters", {
    params: {
      page,
      search: search || undefined,
      is_verified: isVerified,
      is_active: isActive,
    },
  });
  return data.data;
}

export async function getVoter(voterId) {
  const { data } = await api.get(`/admin/voters/${voterId}`);
  return data.data;
}

export async function verifyVoter(voterId, note) {
  const { data } = await api.post(`/admin/voters/${voterId}/verify`, { note });
  return data.data;
}

export async function suspendVoter(voterId, reason) {
  const { data } = await api.post(`/admin/voters/${voterId}/suspend`, { reason });
  return data.data;
}

export async function reactivateVoter(voterId) {
  const { data } = await api.post(`/admin/voters/${voterId}/reactivate`);
  return data.data;
}

export async function revokeVoterSessions(voterId) {
  const { data } = await api.post(`/admin/voters/${voterId}/revoke-sessions`);
  return data.data;
}

export async function resetVoterBiometrics(voterId) {
  const { data } = await api.post(`/admin/voters/${voterId}/reset-biometrics`);
  return data.data;
}
