import api from "./api";

export async function getVoteStatus(electionId) {
  const { data } = await api.get(`/elections/${electionId}/vote-status`);
  return data.data;
}

export async function castVote(electionId, payload) {
  // payload: { candidate_id, face_images }
  const { data } = await api.post(`/elections/${electionId}/vote`, payload);
  return data.data;
}

export async function getResults(electionId) {
  const { data } = await api.get(`/elections/${electionId}/results`);
  return data.data;
}
