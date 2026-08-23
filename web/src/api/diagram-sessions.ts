import { ApiError, request } from './client';
import type {
  CreateDiagramSessionRequest,
  ClarificationQuestionsResponse,
  DiagramSessionAccess,
  DiagramSessionStatusEvent,
  DiagramSessionStatusResponse,
  GeneratedDiagram,
  SubmitClarificationAnswersRequest,
  SubmitClarificationAnswersResponse,
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
  signal?: AbortSignal,
): Promise<DiagramSessionStatusResponse> =>
  request(`/api/v1/diagram-sessions/${sessionId}`, {
    headers: authorization(sessionToken),
    signal,
  });

export const getGeneratedDiagram = (
  sessionId: string,
  sessionToken: string,
): Promise<GeneratedDiagram> =>
  request(`/api/v1/diagram-sessions/${sessionId}/diagram`, {
    headers: authorization(sessionToken),
  });

export const getClarificationQuestions = (
  sessionId: string,
  sessionToken: string,
): Promise<ClarificationQuestionsResponse> =>
  request(`/api/v1/diagram-sessions/${sessionId}/questions`, {
    headers: authorization(sessionToken),
  });

export const submitClarificationAnswers = (
  sessionId: string,
  sessionToken: string,
  payload: SubmitClarificationAnswersRequest,
): Promise<SubmitClarificationAnswersResponse> =>
  request(`/api/v1/diagram-sessions/${sessionId}/answers`, {
    method: 'POST',
    headers: authorization(sessionToken),
    body: JSON.stringify(payload),
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
  try {
    onStatus(JSON.parse(dataLine) as DiagramSessionStatusEvent);
  } catch {
    // Ignore a malformed frame; the status query remains the source of recovery.
  }
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
