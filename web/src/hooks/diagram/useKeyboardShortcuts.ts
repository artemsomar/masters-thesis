import { useEffect } from 'react';
import { useDiagramStore } from '../../store/diagram-store';
import { useEditorUiStore } from '../../store/editor-ui-store';

export const useKeyboardShortcuts = () => {
  const selectedIds = useEditorUiStore((state) => state.selectedIds);
  const clearSelection = useEditorUiStore((state) => state.clearSelection);
  const deleteElements = useDiagramStore((state) => state.deleteElements);
  const undo = useDiagramStore((state) => state.undo);
  const redo = useDiagramStore((state) => state.redo);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (target?.closest('input, textarea, select, [contenteditable="true"]')) return;
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'z') {
        event.preventDefault();
        if (event.shiftKey) redo();
        else undo();
        return;
      }
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'y') {
        event.preventDefault();
        redo();
        return;
      }
      if ((event.key === 'Backspace' || event.key === 'Delete') && selectedIds.length) {
        event.preventDefault();
        deleteElements(selectedIds);
        clearSelection();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [clearSelection, deleteElements, redo, selectedIds, undo]);
};
