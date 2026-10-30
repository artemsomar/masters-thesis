let context: CanvasRenderingContext2D | null = null;

export const getTextLayout = (name: string, textWidth: number, fontSize = 12) => {
  const lineHeight = (fontSize * 4) / 3;
  context ??= document.createElement('canvas').getContext('2d');
  if (!context) throw new Error('Canvas text measurement is unavailable.');
  context.font = `${fontSize}px Arial`;
  const measure = (text: string) => context!.measureText(text).width;
  const lines: string[] = [];
  for (const paragraph of name.split(/\r?\n/)) {
    let line = '';
    for (const word of paragraph.trim().split(/\s+/)) {
      if (line && measure(`${line} ${word}`) > textWidth) {
        lines.push(line);
        line = '';
      }
      for (const character of line ? ` ${word}` : word) {
        if (line && measure(line + character) > textWidth) {
          lines.push(line);
          line = '';
        }
        line += character;
      }
    }
    lines.push(line);
  }
  return { text: lines.join('\n'), textHeight: lines.length * lineHeight, fontSize, lineHeight };
};

export const getUseCaseLayout = (
  name: string,
  size?: { width: number; height: number },
  fontSize = 12,
) => {
  const width = Math.max(size?.width ?? 156, fontSize * 2);
  // Keep the text rectangle inside the curved sides of the ellipse.
  const textWidth = Math.floor(width * 0.7);
  const text = getTextLayout(name, textWidth, fontSize);
  return {
    ...text,
    width,
    height: Math.max(size?.height ?? 62, text.textHeight * 1.5 + 12),
    textWidth,
  };
};
