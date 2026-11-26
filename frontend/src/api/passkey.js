// In demo mode there is no real passkey: we wait a moment and pretend the device said yes.
// With the real server these two become WebAuthn calls (navigator.credentials.get and .create).
const pretend = () => new Promise((resolve) => setTimeout(() => resolve('demo-passkey'), 900))

export const usePasskeyOnDevice = pretend
export const createPasskeyOnDevice = pretend
