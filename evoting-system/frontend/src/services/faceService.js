import api from "./api";

export async function registerFace(images) {
  const { data } = await api.post("/face/register", { images });
  return data;
}

export async function verifyFace(images) {
  const { data } = await api.post("/face/verify", { images });
  return data.data;
}
