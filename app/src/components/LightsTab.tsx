import { NUMPAD_TOPIC } from '../config';

type HA = {
  publishMqtt: (topic: string, payload: string) => Promise<unknown>;
};

function numpad(key: string, modifiers: string[] = []) {
  return JSON.stringify({
    event_name: 'pressed',
    key,
    pressed_keys: [...modifiers, key],
  });
}

const SCENES = [
  { label: 'All On', key: '2_1' },
  { label: 'All Off', key: '1_1' },
  { label: 'Dim', key: '1_2' },
  { label: 'Low', key: '1_3' },
  { label: 'Reading', key: '2_2' },
  { label: 'Dining', key: '2_3' },
  { label: 'LR Only On', key: '2_4' },
  { label: 'LR Only Dim', key: '3_4' },
];

export function LightsTab({ ha }: { ha: HA }) {
  return (
    <div className="tab-content">
      <div className="section">
        <div className="section-title">Scenes</div>
        <div className="grid-2">
          {SCENES.map((scene) => (
            <button
              key={scene.key}
              className="btn"
              onClick={() => ha.publishMqtt(NUMPAD_TOPIC, numpad(scene.key, ['mod_right']))}
            >
              {scene.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
