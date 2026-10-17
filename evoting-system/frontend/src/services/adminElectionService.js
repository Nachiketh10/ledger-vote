import api from "./api";

export async function adminListElections(status) {
  const { data } = await api.get("/elections/admin", { params: status ? { status } : {} });
  return data.data.items;
}

export async function adminGetElection(electionId) {
  const { data } = await api.get(`/elections/admin/${electionId}`);
  return data.data;
}

export async function createElection(payload) {
  const { data } = await api.post("/elections", payload);
  return data.data;
}

export async function updateElection(electionId, payload) {
  const { data } = await api.put(`/elections/${electionId}`, payload);
  return data.data;
}

export async function deleteElection(electionId) {
  await api.delete(`/elections/${electionId}`);
}

export async function electionAction(electionId, action) {
  // action: "start" | "pause" | "resume" | "close"
  const { data } = await api.post(`/elections/${electionId}/${action}`);
  return data.data;
}

export async function setEligibleVoters(electionId, voterIds) {
  const { data } = await api.put(`/elections/${electionId}/eligible-voters`, { voter_ids: voterIds });
  return data.data;
}

export async function addCandidate(electionId, payload) {
  const { data } = await api.post(`/elections/${electionId}/candidates`, payload);
  return data.data;
}

export async function updateCandidate(candidateId, payload) {
  const { data } = await api.put(`/candidates/${candidateId}`, payload);
  return data.data;
}

export async function deleteCandidate(candidateId) {
  await api.delete(`/candidates/${candidateId}`);
}

export async function listElectionAdmins() {
  const { data } = await api.get("/elections/election-admins");
  return data.data;
}

export async function assignElectionAdmin(electionId, electionAdminId) {
  const { data } = await api.post(`/elections/${electionId}/assign-admin`, {
    election_admin_id: electionAdminId,
  });
  return data.data;
}

export async function unassignElectionAdmin(electionId, electionAdminId) {
  const { data } = await api.post(`/elections/${electionId}/unassign-admin`, {
    election_admin_id: electionAdminId,
  });
  return data.data;
}
