import React from 'react';
import { Series, useCurrentFrame, interpolate } from 'remotion';
import { Terminal } from './Terminal';

const GREEN = '#3fb950';
const CYAN = '#56d4c4';
const YELLOW = '#d29922';
const GREY = '#6e7681';
const WHITE = '#f0f6fc';
const FG = '#c9d1d9';

export const HOOK_FRAMES = 130;
export const RUN_FRAMES = 360;

const Scene: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 6], [0.35, 1], { extrapolateRight: 'clamp' });
  return <div style={{ width: '100%', height: '100%', backgroundColor: '#0d1117', opacity }}>{children}</div>;
};

const Hook: React.FC = () => (
  <Scene>
    <Terminal
      lines={[
        { text: '# would you hand a trading bot your private keys?', color: GREY, delay: 6 },
        { text: '', delay: 40 },
        { text: '# helmsman never asks. it signs every trade itself.', color: GREY, delay: 52 },
      ]}
    />
  </Scene>
);

const Run: React.FC = () => (
  <Scene>
    <Terminal
      command="python -m agent.runner"
      typingSpeed={0.9}
      lines={[
        { text: '', delay: 6 },
        { text: '[signal]  FG=22 (Fear)   mom7d=+3.4%   mcap24h=+0.52%', color: CYAN, delay: 12 },
        { text: '[regime]  risk-on   score=+0.239', color: YELLOW, delay: 26 },
        { text: '[state]   equity=$12.85   peak=$12.89   drawdown=0.3%', color: FG, delay: 40 },
        { text: '[decide]  propose swap  $1.03  USDT -> ETH', color: FG, delay: 56 },
        { text: '[guard]   ALLOW: per-trade, daily, concentration, slippage, gas', color: GREEN, delay: 74 },
        { text: '[x402]    paid CMC for live DEX data   (spend $0.01)', color: CYAN, delay: 92 },
        { text: '[exec]    TWAK signed locally, submitted to BNB Chain', color: WHITE, delay: 110 },
        { text: '[proof]   bscscan.com/tx/0xff1a49c4...938d7cbbf', color: GREEN, delay: 128 },
        { text: '', delay: 142 },
        { text: '$ twak tx 0xff1a49c4   (bsc mainnet)', color: FG, delay: 156 },
        { text: '  confirmed: true    failed: false', color: GREEN, delay: 176 },
        { text: '', delay: 190 },
        { text: '# keys never left the wallet.', color: GREY, delay: 206 },
        { text: '# self-custody trader, unattended-safe.', color: GREEN, delay: 222 },
      ]}
    />
  </Scene>
);

export const HelmsmanDemo: React.FC = () => (
  <Series>
    <Series.Sequence durationInFrames={HOOK_FRAMES}><Hook /></Series.Sequence>
    <Series.Sequence durationInFrames={RUN_FRAMES}><Run /></Series.Sequence>
  </Series>
);
