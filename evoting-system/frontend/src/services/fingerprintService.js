import api from "./api";
import { bufferToBase64url, base64urlToBuffer } from "../utils/webauthn";

export async function registerFingerprint() {
  const optResp = await api.post("/fingerprint/register/options");
  const options = JSON.parse(optResp.data.data.options);
  const state = optResp.data.data.state;

  const publicKey = {
    ...options,
    challenge: base64urlToBuffer(options.challenge),
    user: { ...options.user, id: base64urlToBuffer(options.user.id) },
    excludeCredentials: (options.excludeCredentials || []).map((c) => ({
      ...c,
      id: base64urlToBuffer(c.id),
    })),
  };

  const credential = await navigator.credentials.create({ publicKey });

  const credentialJson = JSON.stringify({
    id: credential.id,
    rawId: bufferToBase64url(credential.rawId),
    type: credential.type,
    response: {
      clientDataJSON: bufferToBase64url(credential.response.clientDataJSON),
      attestationObject: bufferToBase64url(credential.response.attestationObject),
    },
    clientExtensionResults: credential.getClientExtensionResults
      ? credential.getClientExtensionResults()
      : {},
  });

  const verifyResp = await api.post("/fingerprint/register/verify", {
    credential: credentialJson,
    state,
  });
  return verifyResp.data;
}

/**
 * Runs the WebAuthn authentication ceremony and returns the
 * {credential, state} pair the /vote endpoint expects — does NOT call
 * /fingerprint/verify/verify itself, since for voting the credential is
 * submitted together with the vote (see voteService.castVote).
 */
export async function getFingerprintAssertion() {
  const optResp = await api.post("/fingerprint/verify/options");
  const options = JSON.parse(optResp.data.data.options);
  const state = optResp.data.data.state;

  const publicKey = {
    ...options,
    challenge: base64urlToBuffer(options.challenge),
    allowCredentials: (options.allowCredentials || []).map((c) => ({
      ...c,
      id: base64urlToBuffer(c.id),
    })),
  };

  const assertion = await navigator.credentials.get({ publicKey });

  const credentialJson = JSON.stringify({
    id: assertion.id,
    rawId: bufferToBase64url(assertion.rawId),
    type: assertion.type,
    response: {
      clientDataJSON: bufferToBase64url(assertion.response.clientDataJSON),
      authenticatorData: bufferToBase64url(assertion.response.authenticatorData),
      signature: bufferToBase64url(assertion.response.signature),
      userHandle: assertion.response.userHandle
        ? bufferToBase64url(assertion.response.userHandle)
        : null,
    },
    clientExtensionResults: assertion.getClientExtensionResults
      ? assertion.getClientExtensionResults()
      : {},
  });

  return { credential: credentialJson, state };
}
