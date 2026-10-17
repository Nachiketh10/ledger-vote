import api from "./api";

export async function listBlocks(page = 1) {
  const { data } = await api.get("/blockchain", { params: { page } });
  return data.data;
}

export async function verifyChain() {
  const { data } = await api.get("/blockchain/verify");
  return data.data;
}

export async function searchBlocks(params) {
  // params: { transaction_id } | { hash } | { election_id }
  const { data } = await api.get("/blockchain/search", { params });
  return data.data;
}
