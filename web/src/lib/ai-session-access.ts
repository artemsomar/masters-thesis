import type { DiagramSessionAccess } from '../types/api';

const storageKey = 'blueprint-uc.ai-session-access';

export const saveAiSessionAccess = (session: DiagramSessionAccess): void => {
  sessionStorage.setItem(storageKey, JSON.stringify(session));
};

export const getAiSessionAccess = (sessionId: string): DiagramSessionAccess | null => {
  const raw = sessionStorage.getItem(storageKey);
  if (!raw) return null;
  try {
    const session = JSON.parse(raw) as DiagramSessionAccess;
    return session.sessionId === sessionId && new Date(session.expiresAt).getTime() > Date.now()
      ? session
      : null;
  } catch {
    return null;
  }
};

export const clearAiSessionAccess = (): void => sessionStorage.removeItem(storageKey);
