import api from "./api";

export async function listPublicElections(status) {
  const { data } = await api.get("/elections", { params: status ? { status } : {} });
  return data.data.items;
}

export async function getElection(electionId) {
  const { data } = await api.get(`/elections/${electionId}`);
  return data.data;
}

export async function listCandidates(electionId) {
  const { data } = await api.get(`/elections/${electionId}/candidates`);
  return data.data;
}
