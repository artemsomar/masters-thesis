import { ApiError, request } from './client';
import type {
  CreateDiagramSessionRequest,
  DiagramSessionAccess,
  DiagramSessionStatusEvent,
  DiagramSessionStatusResponse,
  GeneratedDiagram,
} from '../types/api';

const apiBase = import.meta.env.VITE_API_URL ?? '';

const authorization = (sessionToken: string): HeadersInit => ({
  Authorization: `Bearer ${sessionToken}`,
});

export const createDiagramSession = (
  payload: CreateDiagramSessionRequest,
): Promise<DiagramSessionAccess> =>
  request('/api/v1/diagram-sessions', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

export const getDiagramSessionStatus = (
  sessionId: string,
  sessionToken: string,
): Promise<DiagramSessionStatusResponse> =>
  request(`/api/v1/diagram-sessions/${sessionId}`, { headers: authorization(sessionToken) });

export const getGeneratedDiagram = (
  sessionId: string,
  sessionToken: string,
): Promise<GeneratedDiagram> =>
  request(`/api/v1/diagram-sessions/${sessionId}/diagram`, {
    headers: authorization(sessionToken),
  });

type StatusStreamHandlers = {
  onOpen: () => void;
  onStatus: (event: DiagramSessionStatusEvent) => void;
  onDisconnect: () => void;
};

const dispatchEvent = (frame: string, onStatus: StatusStreamHandlers['onStatus']): void => {
  const dataLine = frame
    .split('\n')
    .find((line) => line.startsWith('data:'))
    ?.slice('data:'.length)
    .trim();
  if (!dataLine) return;
  onStatus(JSON.parse(dataLine) as DiagramSessionStatusEvent);
};

export const openDiagramSessionStatusStream = (
  sessionId: string,
  sessionToken: string,
  { onOpen, onStatus, onDisconnect }: StatusStreamHandlers,
): (() => void) => {
  const controller = new AbortController();

  void (async () => {
    try {
      const response = await fetch(`${apiBase}/api/v1/diagram-sessions/${sessionId}/events`, {
        headers: authorization(sessionToken),
        signal: controller.signal,
      });
      if (!response.ok || !response.body) {
        throw new ApiError('Could not connect to generation status updates.', response.status);
      }
      onOpen();
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      while (!controller.signal.aborted) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const frames = buffer.split('\n\n');
        buffer = frames.pop() ?? '';
        frames.forEach((frame) => dispatchEvent(frame, onStatus));
      }
    } catch {
      // The polling fallback provides status while the stream reconnects.
    } finally {
      if (!controller.signal.aborted) onDisconnect();
    }
  })();

  return () => controller.abort();
};
