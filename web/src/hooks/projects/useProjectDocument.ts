import { useEffect } from 'react';
import { xmlToDocument } from '../../lib/projects/xml';
import { useDiagramStore } from '../../store/diagram-store';

export const useProjectDocument = (documentXml: string): void => {
  const setDocument = useDiagramStore((state) => state.setDocument);
  useEffect(() => {
    setDocument(xmlToDocument(documentXml));
  }, [documentXml, setDocument]);
};
