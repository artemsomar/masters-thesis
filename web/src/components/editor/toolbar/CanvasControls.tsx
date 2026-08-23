import { Minus, Plus } from 'lucide-react';
import { useEditorUiStore } from '../../../store/editor-ui-store';
import styles from './CanvasControls.module.scss';

export const CanvasControls = () => {
  const viewport = useEditorUiStore((state) => state.viewport);
  const setViewport = useEditorUiStore((state) => state.setViewport);
  const setScale = (scale: number) => setViewport({ ...viewport, scale });
  return (
    <div className={styles.controls}>
      <button aria-label="Zoom out" onClick={() => setScale(Math.max(0.6, viewport.scale - 0.1))}>
        <Minus size={15} />
      </button>
      <span>{Math.round(viewport.scale * 100)}%</span>
      <button aria-label="Zoom in" onClick={() => setScale(Math.min(1.8, viewport.scale + 0.1))}>
        <Plus size={15} />
      </button>
    </div>
  );
};
