import type { DiagramNode, NodeStyle } from '../../../types/diagram';
import styles from './PropertiesPanel.module.scss';

type Props = { node: DiagramNode; onChange: (style: NodeStyle) => void };

export const VisualStyleFields = ({ node, onChange }: Props) => {
  const updateColor = (key: 'fill' | 'stroke' | 'textColor', value: string) =>
    onChange({ ...node.style, [key]: value });
  return (
    <fieldset className={styles.fieldset}>
      <legend>Visual style</legend>
      <label className={styles.field}>
        Font size (px)
        <input
          key={`font-${node.style.fontSize ?? (node.kind === 'boundary' ? 13 : 12)}`}
          type="number"
          min="6"
          max="96"
          step="1"
          defaultValue={node.style.fontSize ?? (node.kind === 'boundary' ? 13 : 12)}
          onBlur={(event) => {
            const value = Number(event.target.value);
            const fontSize =
              Number.isFinite(value) && value > 0
                ? Math.min(96, Math.max(6, value))
                : (node.style.fontSize ?? (node.kind === 'boundary' ? 13 : 12));
            event.target.value = String(fontSize);
            if (fontSize !== (node.style.fontSize ?? (node.kind === 'boundary' ? 13 : 12)))
              onChange({ ...node.style, fontSize });
          }}
        />
      </label>
      <label className={styles.colorField}>
        Stroke
        <input
          type="color"
          value={node.style.stroke}
          onChange={(event) => updateColor('stroke', event.target.value)}
        />
      </label>
      <label className={styles.colorField}>
        Fill
        <input
          type="color"
          value={node.style.fill}
          onChange={(event) => updateColor('fill', event.target.value)}
        />
      </label>
      <label className={styles.colorField}>
        Text
        <input
          type="color"
          value={node.style.textColor}
          onChange={(event) => updateColor('textColor', event.target.value)}
        />
      </label>
    </fieldset>
  );
};
