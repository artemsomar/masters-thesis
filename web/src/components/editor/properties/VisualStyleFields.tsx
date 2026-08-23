import type { DiagramNode, NodeStyle } from '../../../types/diagram';
import styles from './PropertiesPanel.module.scss';

type Props = { node: DiagramNode; onChange: (style: NodeStyle) => void };

export const VisualStyleFields = ({ node, onChange }: Props) => {
  const updateColor = (key: keyof NodeStyle, value: string) =>
    onChange({ ...node.style, [key]: value });
  return (
    <fieldset className={styles.fieldset}>
      <legend>Visual style</legend>
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
