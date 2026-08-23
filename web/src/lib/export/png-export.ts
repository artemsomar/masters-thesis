import type Konva from 'konva';

export const stageToPng = (stage: Konva.Stage): string => {
  const hiddenLayers = stage.find('.grid-layer, .interaction-layer');
  hiddenLayers.forEach((layer) => layer.hide());
  const result = stage.toDataURL({ mimeType: 'image/png', pixelRatio: 2 });
  hiddenLayers.forEach((layer) => layer.show());
  return result;
};
