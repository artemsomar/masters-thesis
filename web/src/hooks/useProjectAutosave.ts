import { useEffect, useRef, useState } from 'react';
import { updateProject } from '../api/projects';
import { documentToXml } from '../lib/xml';
import type { DiagramDocument } from '../types/diagram';

export type SaveState = 'saved' | 'saving' | 'failed';

export const useProjectAutosave = (
  projectId: string,
  projectToken: string,
  document: DiagramDocument,
  revision: number,
) => {
  const [saveState, setSaveState] = useState<SaveState>('saved');
  const previousRevision = useRef(revision);

  useEffect(() => {
    if (revision === previousRevision.current) return;
    previousRevision.current = revision;
    const timer = window.setTimeout(async () => {
      setSaveState('saving');
      try {
        await updateProject(projectId, projectToken, documentToXml(document));
        setSaveState('saved');
      } catch {
        setSaveState('failed');
      }
    }, 450);
    return () => window.clearTimeout(timer);
  }, [document, projectId, projectToken, revision]);

  return saveState;
};
