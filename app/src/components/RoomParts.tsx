import { useCallback, useRef, useState } from 'react';
import { useEntity, useLightsOnCount, type HA } from '../hooks/useHomeAssistant';
import { useLiveSlider } from '../hooks/useLiveSlider';
import type { Light, Room, ShadeGroup } from '../config';
import { Icon } from './Icons';

export type Act = (action: Promise<unknown>, successMessage?: string) => Promise<boolean>;

export function RoomHeader({ room, ha }: { room: Room; ha: HA }) {
  const [ids] = useState(() => room.lights.map((l) => l.entity));
  const on = useLightsOnCount(ha, ids);
  return (
    <header className="head">
      <h1>{room.name}</h1>
      <p>{on ? `${on} of ${ids.length} lights on` : 'Lights off'}</p>
    </header>
  );
}

function LightRow({ light, ha, act, onManual }: { light: Light; ha: HA; act: Act; onManual?: () => void }) {
  const entity = useEntity(ha, light.entity);
  const live = entity?.state === 'on' ? Math.round((((entity.attributes.brightness as number) ?? 255) / 255) * 100) : 0;
  const { callService } = ha;
  const send = useCallback(
    (pct: number) =>
      act(
        pct > 0
          ? callService('light', 'turn_on', { brightness_pct: pct }, { entity_id: light.entity })
          : callService('light', 'turn_off', {}, { entity_id: light.entity })
      ),
    [act, callService, light.entity]
  );
  const [value, setValue] = useLiveSlider(live, send);
  const id = `light-${light.entity}`;
  return (
    <div className="row">
      <label className="name" htmlFor={id}>{light.label}</label>
      <input
        type="range"
        id={id}
        min="0"
        max="100"
        step="1"
        value={value}
        style={{ '--p': `${value}%` } as React.CSSProperties}
        onChange={(e) => {
          onManual?.();
          setValue(+e.target.value);
        }}
      />
      <span className="pct">{value ? `${value}%` : 'Off'}</span>
    </div>
  );
}

export function LightList({ room, ha, act, onManual }: { room: Room; ha: HA; act: Act; onManual?: () => void }) {
  return (
    <div className="list">
      {room.lights.map((l) => <LightRow key={l.entity} light={l} ha={ha} act={act} onManual={onManual} />)}
    </div>
  );
}

const SHADE_DONE = { up: 'Going up', stop: 'Stopped', down: 'Going down' };

function ShadeRow({ label, shadeNames, ha, act }: { label: string; shadeNames: string[]; ha: HA; act: Act }) {
  const [note, setNote] = useState('');
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const command = async (cmd: keyof typeof SHADE_DONE) => {
    const ok = await act(ha.callService('script', 'send_somfy_shade_command', { shade_names: shadeNames, command: cmd }));
    if (!ok) return;
    setNote(SHADE_DONE[cmd]);
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setNote(''), 2500);
  };
  return (
    <div className="row shade">
      <div className="name">{label}{note && <small>{note}</small>}</div>
      <div className="tri">
        <button aria-label={`${label} up`} onClick={() => command('up')}><Icon name="up" /></button>
        <button aria-label={`${label} stop`} onClick={() => command('stop')}><Icon name="stop" /></button>
        <button aria-label={`${label} down`} onClick={() => command('down')}><Icon name="down" /></button>
      </div>
    </div>
  );
}

function ShadeGroupRows({ group, split, ha, act }: { group: ShadeGroup; split: boolean; ha: HA; act: Act }) {
  const noun = group.label.replace(' shades', '').toLowerCase();
  return (
    <>
      <ShadeRow label={group.label} shadeNames={[group.left, group.right]} ha={ha} act={act} />
      {split && (
        <div className="sub">
          <ShadeRow label={`Left ${noun}`} shadeNames={[group.left]} ha={ha} act={act} />
          <ShadeRow label={`Right ${noun}`} shadeNames={[group.right]} ha={ha} act={act} />
        </div>
      )}
    </>
  );
}

export function ShadesSection({ room, ha, act }: { room: Room; ha: HA; act: Act }) {
  const [split, setSplit] = useState(false);
  return (
    <section>
      <div className="sec-h">
        <h2>Shades</h2>
        <button className="link" aria-expanded={split} onClick={() => setSplit(!split)}>
          {split ? 'Hide left and right' : 'Left and right'}
        </button>
      </div>
      <div className="list">
        {room.shades.map((g) => <ShadeGroupRows key={g.label} group={g} split={split} ha={ha} act={act} />)}
      </div>
    </section>
  );
}

export function RoomPage({ room, ha, act, hidden }: { room: Room; ha: HA; act: Act; hidden: boolean }) {
  return (
    <div className="page" hidden={hidden}>
      <RoomHeader room={room} ha={ha} />
      <section>
        <div className="sec-h"><h2>Lights</h2></div>
        <LightList room={room} ha={ha} act={act} />
      </section>
      <ShadesSection room={room} ha={ha} act={act} />
    </div>
  );
}
