export type ApiErrorResponse = { error?: { code?: string; message?: string } };

export type DiagramSessionStatus =
  | 'created'
  | 'analyzing'
  | 'awaiting_answers'
  | 'generating_diagram'
  | 'diagram_ready'
  | 'failed'
  | 'cancelled'
  | 'expired';

export type CreateDiagramSessionRequest = {
  description: string;
  language: string;
  clarificationsEnabled: boolean;
};

export type DiagramSessionAccess = {
  sessionId: string;
  sessionToken: string;
  status: DiagramSessionStatus;
  expiresAt: string;
};

export type DiagramSessionStatusResponse = {
  sessionId: string;
  status: DiagramSessionStatus;
  nextAction: 'wait' | 'get_questions' | 'get_diagram' | 'create_new_session';
  updatedAt: string;
  errorCode: string | null;
};

export type DiagramSessionStatusEvent = Pick<
  DiagramSessionStatusResponse,
  'status' | 'errorCode'
> & {
  correlationId?: string;
};

export type GeneratedActor = { id: string; name: string; type: 'primary' | 'secondary' };
export type GeneratedUseCase = { id: string; name: string };
export type GeneratedRelation = {
  type: 'association' | 'include' | 'extend' | 'generalization';
  sourceId: string;
  targetId: string;
};

export type GeneratedDiagram = {
  schemaVersion: '1.0';
  system: { id: string; name: string };
  actors: GeneratedActor[];
  useCases: GeneratedUseCase[];
  relations: GeneratedRelation[];
  assumptions: string[];
  warnings: string[];
};
