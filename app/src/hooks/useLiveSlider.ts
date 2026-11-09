import { useState } from 'react';

// How long after the last command we ignore what the device reports. Devices
// report old values while catching up, and those shouldn't move the slider.
const HOLD_MS = 3000;

// Slider for a device that's slower than a finger. Only the latest value is
// sent, one command at a time, so commands can't pile up behind a drag.
// `send` must be stable for the lifetime of the component.
export function useLiveSlider(live: number, send: (value: number) => Promise<unknown>) {
  const [held, setHeld] = useState<number | null>(null);
  const [change] = useState(() => {
    let latest: number | null = null;
    let inFlight = false;
    let release: ReturnType<typeof setTimeout>;

    const hold = () => {
      clearTimeout(release);
      release = setTimeout(() => setHeld(null), HOLD_MS);
    };
    const pump = () => {
      if (inFlight || latest === null) return;
      const value = latest;
      latest = null;
      inFlight = true;
      send(value)
        .catch(() => {})
        .finally(() => {
          inFlight = false;
          hold();
          pump();
        });
    };
    return (value: number) => {
      setHeld(value);
      latest = value;
      hold();
      pump();
    };
  });

  return [held ?? live, change] as const;
}
