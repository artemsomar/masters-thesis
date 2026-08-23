import { useCallback, useEffect, useRef, useState } from 'react';
import { updateProject } from '../../api/projects';
import { documentToXml } from '../../lib/projects/xml';
import type { DiagramDocument } from '../../types/diagram';

export type SaveState = 'saved' | 'saving' | 'failed';

export type ProjectAutosave = {
  saveState: SaveState;
  retry: () => void;
};

export const useProjectAutosave = (
  projectId: string,
  projectToken: string,
  document: DiagramDocument,
  revision: number,
) => {
  const [saveState, setSaveState] = useState<SaveState>('saved');
  const previousRevision = useRef(revision);
  const latest = useRef({ document, revision });
  const saving = useRef(false);
  const mounted = useRef(true);

  const saveLatest = useCallback(async () => {
    if (saving.current) return;
    saving.current = true;
    const snapshot = latest.current;
    if (mounted.current) setSaveState('saving');
    try {
      await updateProject(projectId, projectToken, documentToXml(snapshot.document));
      if (latest.current.revision !== snapshot.revision) {
        saving.current = false;
        void saveLatest();
        return;
      }
      if (mounted.current) setSaveState('saved');
    } catch {
      if (latest.current.revision !== snapshot.revision) {
        saving.current = false;
        void saveLatest();
        return;
      }
      if (mounted.current) setSaveState('failed');
    }
    saving.current = false;
  }, [projectId, projectToken]);

  useEffect(() => {
    if (revision === previousRevision.current) return;
    previousRevision.current = revision;
    latest.current = { document, revision };
    const timer = window.setTimeout(() => void saveLatest(), 450);
    return () => window.clearTimeout(timer);
  }, [document, revision, saveLatest]);

  useEffect(
    () => () => {
      mounted.current = false;
    },
    [],
  );

  return { saveState, retry: () => void saveLatest() };
};
