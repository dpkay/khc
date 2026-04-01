import { useEffect, useState, useRef } from 'react';
import { NUMPAD_TOPIC, SHIELD_KEY_TOPIC, DENON_ENTITY, DENON_MAX_VOLUME } from '../config';

type HA = {
  publishMqtt: (topic: string, payload: string) => Promise<unknown>;
  callService: (domain: string, service: string, data?: Record<string, unknown>, target?: Record<string, unknown>) => Promise<unknown>;
  subscribeState: (entityId: string, listener: (state: { state: string; attributes: Record<string, unknown> }) => void) => () => void;
  getState: (entityId: string) => Promise<{ state: string; attributes: Record<string, unknown> } | null>;
};

function numpad(key: string, modifiers: string[] = []) {
  return JSON.stringify({
    event_name: 'pressed',
    key,
    pressed_keys: [...modifiers, key],
  });
}

export function ShieldTab({ ha }: { ha: HA }) {
  const [volume, setVolume] = useState(0.4);
  const [rebootConfirm, setRebootConfirm] = useState(false);
  const rebootTimer = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => {
    ha.getState(DENON_ENTITY).then((s) => {
      if (s?.attributes?.volume_level != null) {
        setVolume(s.attributes.volume_level as number);
      }
    });
    return ha.subscribeState(DENON_ENTITY, (s) => {
      if (s.attributes?.volume_level != null) {
        setVolume(s.attributes.volume_level as number);
      }
    });
  }, [ha]);

  const shieldKey = (name: string) => {
    ha.publishMqtt(SHIELD_KEY_TOPIC, JSON.stringify({ name }));
  };

  const onVolumeChange = (val: number) => {
    setVolume(val);
    ha.callService('media_player', 'volume_set', { volume_level: val }, { entity_id: DENON_ENTITY });
  };

  const handleReboot = () => {
    if (!rebootConfirm) {
      setRebootConfirm(true);
      rebootTimer.current = setTimeout(() => setRebootConfirm(false), 3000);
    } else {
      ha.publishMqtt(NUMPAD_TOPIC, numpad('1_3', ['mod_left']));
      setRebootConfirm(false);
      clearTimeout(rebootTimer.current);
    }
  };

  return (
    <div className="tab-content">
      {/* Media Controls */}
      <div className="section">
        <div className="row">
          <button className="btn" onClick={() => shieldKey('prev')}>&#9198;</button>
          <button className="btn accent" onClick={() => shieldKey('play_pause')}>&#9199;</button>
          <button className="btn" onClick={() => shieldKey('next')}>&#9197;</button>
        </div>
      </div>

      {/* D-Pad */}
      <div className="section">
        <div className="dpad">
          <button className="btn dpad-up" onClick={() => shieldKey('up')}>&#9650;</button>
          <button className="btn dpad-left" onClick={() => shieldKey('left')}>&#9664;</button>
          <button className="btn dpad-center" onClick={() => shieldKey('center')}>OK</button>
          <button className="btn dpad-right" onClick={() => shieldKey('right')}>&#9654;</button>
          <button className="btn dpad-down" onClick={() => shieldKey('down')}>&#9660;</button>
        </div>
        <div className="row" style={{ marginTop: 12 }}>
          <button className="btn" onClick={() => shieldKey('back')}>&#8617; Back</button>
          <button className="btn" onClick={() => ha.publishMqtt(NUMPAD_TOPIC, numpad('4_3'))}>&#127968; Home</button>
        </div>
      </div>

      {/* Volume */}
      <div className="section">
        <div className="volume-row">
          <span className="label-dim">&#128265;</span>
          <input
            type="range"
            min="0"
            max={DENON_MAX_VOLUME}
            step="0.01"
            value={volume}
            onChange={(e) => onVolumeChange(parseFloat(e.target.value))}
            className="volume-slider"
          />
          <span className="label-dim">&#128266;</span>
        </div>
        <div className="volume-label">{Math.round(volume * 100)}%</div>
      </div>

      {/* TV Controls */}
      <div className="section">
        <div className="row">
          <button className="btn" onClick={() => ha.publishMqtt(NUMPAD_TOPIC, numpad('1_4'))}>
            &#128444; Ambient
          </button>
          <button className="btn danger" onClick={() => ha.publishMqtt(NUMPAD_TOPIC, numpad('1_4', ['mod_left']))}>
            &#9211; TV Off
          </button>
        </div>
        <div className="row">
          <button className="btn" onClick={() => ha.publishMqtt(NUMPAD_TOPIC, numpad('2_3', ['mod_left']))}>
            &#9881; Menu
          </button>
          <button className="btn" onClick={() => ha.publishMqtt(NUMPAD_TOPIC, numpad('2_3', ['mod_left']))}>
            Match FPS
          </button>
        </div>
      </div>

      {/* App Launchers */}
      <div className="section">
        <div className="section-title">Apps</div>
        <div className="row">
          <button className="btn" onClick={() => ha.publishMqtt(NUMPAD_TOPIC, numpad('4_2', ['mod_left']))}>
            Kodi
          </button>
          <button className="btn" onClick={() => ha.publishMqtt(NUMPAD_TOPIC, numpad('4_3', ['mod_left']))}>
            YouTube
          </button>
          <button className="btn" onClick={() => ha.publishMqtt(NUMPAD_TOPIC, numpad('4_1', ['mod_left']))}>
            Screensaver
          </button>
        </div>
        <div className="row">
          <button className={`btn ${rebootConfirm ? 'danger' : ''}`} onClick={handleReboot}>
            {rebootConfirm ? 'Tap again to reboot' : 'Reboot Shield'}
          </button>
        </div>
      </div>
    </div>
  );
}
