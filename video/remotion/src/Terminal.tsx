import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';

export interface TermLine {
  text: string;
  color?: string;
  delay?: number;
}

interface TerminalProps {
  command?: string;
  lines: TermLine[];
  typingSpeed?: number;
  lineRevealRate?: number;
  title?: string;
}

const FG = '#c9d1d9';

export const Terminal: React.FC<TerminalProps> = ({
  command,
  lines,
  typingSpeed = 0.8,
  lineRevealRate = 8,
  title = 'helmsman : agent',
}) => {
  const frame = useCurrentFrame();

  const hasCommand = !!(command && command.length > 0);
  const commandChars = hasCommand ? Math.floor(frame / typingSpeed) : 999;
  const typedCommand = hasCommand ? command!.slice(0, commandChars) : '';
  const commandDone = !hasCommand || commandChars >= (command?.length ?? 0);
  const commandEndFrame = hasCommand ? (command?.length ?? 0) * typingSpeed : 0;
  const outputFrame = commandDone ? frame - commandEndFrame : -1;

  return (
    <div style={{
      width: '100%', height: '100%', backgroundColor: '#0d1117',
      display: 'flex', flexDirection: 'column', padding: '46px 60px',
      fontFamily: 'Menlo, Monaco, "Courier New", monospace',
      // Disable ligatures so "--chain" and "->" never render as an em-dash/arrow.
      fontVariantLigatures: 'none',
      fontFeatureSettings: '"liga" 0, "calt" 0, "dlig" 0',
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10,
        paddingBottom: 16, borderBottom: '1px solid #21262d', marginBottom: 28,
      }}>
        <div style={{ width: 16, height: 16, borderRadius: '50%', backgroundColor: '#ed6a5e' }} />
        <div style={{ width: 16, height: 16, borderRadius: '50%', backgroundColor: '#f5bf4f' }} />
        <div style={{ width: 16, height: 16, borderRadius: '50%', backgroundColor: '#62c554' }} />
        <span style={{ marginLeft: 'auto', marginRight: 'auto', color: '#6e7681', fontSize: 22 }}>{title}</span>
      </div>

      {hasCommand && (
        <div style={{ fontSize: 34, lineHeight: 1.5, marginBottom: 10 }}>
          <span style={{ color: '#6e7681' }}>$ </span>
          <span style={{ color: FG }}>{typedCommand}</span>
          {!commandDone && (
            <span style={{
              display: 'inline-block', width: 16, height: 30,
              backgroundColor: FG, marginLeft: 2,
              opacity: Math.sin(frame * 0.3) > 0 ? 1 : 0,
            }} />
          )}
        </div>
      )}

      {(commandDone || !hasCommand) && (
        <div style={{ marginTop: hasCommand ? 12 : 0, fontSize: 34, lineHeight: 1.55 }}>
          {lines.map((line, i) => {
            const lineDelay = line.delay ?? i * lineRevealRate;
            const effectiveFrame = hasCommand ? outputFrame : frame;
            const visible = effectiveFrame >= lineDelay;
            if (!visible) return null;
            const fadeIn = interpolate(effectiveFrame - lineDelay, [0, 6], [0, 1], { extrapolateRight: 'clamp' });
            return (
              <div key={i} style={{
                color: line.color || FG, opacity: fadeIn,
                transform: `translateY(${(1 - fadeIn) * 8}px)`,
                minHeight: line.text === '' ? 22 : undefined,
                whiteSpace: 'pre',
              }}>
                {line.text}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
