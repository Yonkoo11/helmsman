import React from 'react';
import { Composition } from 'remotion';
import { HelmsmanDemo, HOOK_FRAMES, RUN_FRAMES } from './HelmsmanDemo';

export const RemotionRoot: React.FC = () => (
  <Composition
    id="HelmsmanDemo"
    component={HelmsmanDemo}
    durationInFrames={HOOK_FRAMES + RUN_FRAMES}
    fps={30}
    width={1920}
    height={1080}
  />
);
