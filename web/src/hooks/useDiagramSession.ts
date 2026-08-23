import { useEffect, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getDiagramSessionStatus, openDiagramSessionStatusStream } from '../api/diagram-sessions';
import { queryKeys } from '../api/query-keys';
import type { DiagramSessionAccess, DiagramSessionStatusResponse } from '../types/api';

export const useDiagramSession = (session: DiagramSessionAccess) => {
  const queryClient = useQueryClient();
  const [streamConnected, setStreamConnected] = useState(false);
  const [reconnectAttempt, setReconnectAttempt] = useState(0);
  const status = useQuery({
    queryKey: queryKeys.diagramSessionStatus(session.sessionId),
    queryFn: () => getDiagramSessionStatus(session.sessionId, session.sessionToken),
    refetchInterval: streamConnected ? false : 2500,
  });

  useEffect(() => {
    let reconnectTimer: number | undefined;
    const closeStream = openDiagramSessionStatusStream(session.sessionId, session.sessionToken, {
      onOpen: () => setStreamConnected(true),
      onStatus: (event) => {
        queryClient.setQueryData<DiagramSessionStatusResponse>(
          queryKeys.diagramSessionStatus(session.sessionId),
          (current) =>
            current
              ? { ...current, status: event.status, errorCode: event.errorCode ?? null }
              : current,
        );
      },
      onDisconnect: () => {
        setStreamConnected(false);
        reconnectTimer = window.setTimeout(() => {
          setReconnectAttempt((attempt) => attempt + 1);
        }, 2000);
      },
    });
    return () => {
      closeStream();
      if (reconnectTimer) window.clearTimeout(reconnectTimer);
    };
  }, [queryClient, reconnectAttempt, session.sessionId, session.sessionToken]);

  return { ...status, streamConnected };
};
