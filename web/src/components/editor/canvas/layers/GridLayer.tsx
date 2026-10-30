import { Layer, Line } from 'react-konva';

const gridStep = 24;

type Props = { x: number; y: number; width: number; height: number };

export const GridLayer = ({ x, y, width, height }: Props) => {
  const lines = [];
  for (let column = Math.floor(x / gridStep) * gridStep; column <= x + width; column += gridStep)
    lines.push(
      <Line
        key={`x-${column}`}
        points={[column, y, column, y + height]}
        stroke="#e6e8ee"
        strokeWidth={1}
      />,
    );
  for (let row = Math.floor(y / gridStep) * gridStep; row <= y + height; row += gridStep)
    lines.push(
      <Line key={`y-${row}`} points={[x, row, x + width, row]} stroke="#e6e8ee" strokeWidth={1} />,
    );
  return (
    <Layer name="grid-layer" listening={false}>
      {lines}
    </Layer>
  );
};
