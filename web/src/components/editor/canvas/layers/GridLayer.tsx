import { Layer, Line } from 'react-konva';

const gridStep = 24;

export const GridLayer = ({ width, height }: { width: number; height: number }) => {
  const lines = [];
  for (let x = 0; x < width; x += gridStep)
    lines.push(<Line key={`x-${x}`} points={[x, 0, x, height]} stroke="#e6e8ee" strokeWidth={1} />);
  for (let y = 0; y < height; y += gridStep)
    lines.push(<Line key={`y-${y}`} points={[0, y, width, y]} stroke="#e6e8ee" strokeWidth={1} />);
  return (
    <Layer name="grid-layer" listening={false}>
      {lines}
    </Layer>
  );
};
