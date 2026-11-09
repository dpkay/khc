import { useCallback, useEffect, useRef, useState } from 'react';
import { AMBIENT_ENTITY, DENON_ENTITY, DENON_MAX_VOLUME, LIVING, NUMPAD_TOPIC, SCENES, SHIELD_ENTITY, SHIELD_KEY_TOPIC, TV_ENTITY, numpad } from '../config';
import { useEntity, type HA } from '../hooks/useHomeAssistant';
import { useLiveSlider } from '../hooks/useLiveSlider';
import { Icon } from './Icons';
import { LightList, RoomHeader, ShadesSection, type Act } from './RoomParts';

type Mode = 'ambient' | 'youtube' | 'kodi' | 'off' | 'stargazing';
const MODE_BUTTONS: Mode[] = ['ambient', 'youtube', 'kodi'];
const LABEL: Record<Mode, string> = { ambient: 'Ambient', youtube: 'YouTube', kodi: 'Kodi', off: 'Screen off', stargazing: 'Stargazing' };
const NOTE: Record<Mode, string> = {
  ambient: 'Showing artwork',
  youtube: 'Open on the Shield',
  kodi: 'Open on the Shield',
  off: 'Pick a mode to wake it',
  stargazing: 'Screen and lights off',
};
const SWITCH_TIMEOUT_MS = 20000;

function Stars() {
  const canvas = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const c = canvas.current!;
    const rect = c.getBoundingClientRect();
    const dpr = devicePixelRatio || 1;
    c.width = rect.width * dpr;
    c.height = rect.height * dpr;
    const ctx = c.getContext('2d')!;
    let seed = 7;
    const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    for (let i = 0; i < 150; i++) {
      ctx.fillStyle = `rgba(240,232,218,${0.25 + rnd() * 0.75})`;
      ctx.beginPath();
      ctx.arc(rnd() * c.width, rnd() * c.height, (0.3 + rnd()) * dpr, 0, 7);
      ctx.fill();
    }
  }, []);
  return <canvas ref={canvas} />;
}

function TvPanel({ ha, act, notify, onMore, request, setRequest }: {
  ha: HA; act: Act; notify: (m: string, bad?: boolean) => void; onMore: () => void;
  request: { mode: Mode; timedOut: boolean } | null;
  setRequest: React.Dispatch<React.SetStateAction<{ mode: Mode; timedOut: boolean } | null>>;
}) {
  const tv = useEntity(ha, TV_ENTITY);
  const ambient = useEntity(ha, AMBIENT_ENTITY);
  const shield = useEntity(ha, SHIELD_ENTITY);
  const appId = String(shield?.attributes.app_id ?? '');

  let live: Mode | null = null;
  if (tv && tv.state !== 'on') live = 'off';
  else if (ambient?.state === 'on') live = 'ambient';
  else if (appId.includes('youtube')) live = 'youtube';
  else if (appId === 'org.xbmc.kodi') live = 'kodi';

  const reached = !!request && (live === request.mode || (request.mode === 'stargazing' && live === 'off'));
  const switching = !!request && !reached && !request.timedOut;
  const reachedRef = useRef(reached);
  useEffect(() => {
    reachedRef.current = reached;
  }, [reached]);

  useEffect(() => {
    if (!request || request.timedOut) return;
    const timer = setTimeout(() => {
      setRequest((r) => (r ? { ...r, timedOut: true } : r));
      if (!reachedRef.current) notify("The TV didn't confirm the change. Try again.", true);
    }, SWITCH_TIMEOUT_MS);
    return () => clearTimeout(timer);
  }, [request, setRequest, notify]);

  const shown: Mode | null = switching ? request.mode : live === 'off' && request?.mode === 'stargazing' && reached ? 'stargazing' : live;
  const wall = shown ? `wall-${shown}` : 'wall-other';
  const caption = shown ? LABEL[shown] : tv ? String(shield?.attributes.app_name ?? 'TV on') : '';
  const note = shown ? NOTE[shown] : '';

  const choose = async (mode: Mode) => {
    if (mode === live) {
      notify(`${LABEL[mode]} is already on`);
      return;
    }
    setRequest({ mode, timedOut: false });
    if (!(await act(ha.callService('pyscript', 'set_tv_mode', { mode })))) setRequest(null);
  };

  const key = (name: string) => act(ha.publishMqtt(SHIELD_KEY_TOPIC, JSON.stringify({ name })));
  const home = () => act(ha.publishMqtt(NUMPAD_TOPIC, numpad('4_3')));

  return (
    <>
      <div className="wall">
        <div className={`screen ${wall}`}>
          {shown === 'stargazing' && <Stars />}
          {shown === 'ambient' && <div className="frame"><i /></div>}
          <div className="cap">
            <b>{switching ? 'Switching…' : caption}</b>
            <span>{switching ? `To ${LABEL[request.mode]}` : note}</span>
          </div>
        </div>
        <div className="modes">
          {MODE_BUTTONS.map((m) => (
            <button key={m} className="mode" aria-pressed={shown === m} onClick={() => choose(m)}>{LABEL[m]}</button>
          ))}
        </div>
      </div>

      <div className="pad">
        <div className="side">
          <button className="key" aria-label="Previous" onClick={() => key('prev')}><Icon name="prev" /></button>
          <button className="key" aria-label="Play or pause" onClick={() => key('play_pause')}><Icon name="play" /></button>
          <button className="key" aria-label="Next" onClick={() => key('next')}><Icon name="next" /></button>
        </div>
        <div className="ring">
          <button className="w up" aria-label="Up" onClick={() => key('up')}><Icon name="up" /></button>
          <button className="w dn" aria-label="Down" onClick={() => key('down')}><Icon name="down" /></button>
          <button className="w lf" aria-label="Left" onClick={() => key('left')}><Icon name="left" /></button>
          <button className="w rt" aria-label="Right" onClick={() => key('right')}><Icon name="right" /></button>
          <button className="ok" onClick={() => key('center')}>OK</button>
        </div>
        <div className="side">
          <button className="key" onClick={() => key('back')}><Icon name="back" />Back</button>
          <button className="key" onClick={home}><Icon name="home" />Home</button>
          <button className="key" onClick={onMore}><Icon name="more" />More</button>
        </div>
      </div>
    </>
  );
}

function decibels(level: number) {
  const db = Math.round((level * 100 - 80) * 2) / 2;
  return `${db < 0 ? '−' : '+'}${Math.abs(db).toFixed(1)} dB`;
}

function Volume({ ha, act }: { ha: HA; act: Act }) {
  const denon = useEntity(ha, DENON_ENTITY);
  const { callService } = ha;
  const send = useCallback(
    (v: number) => act(callService('media_player', 'volume_set', { volume_level: v }, { entity_id: DENON_ENTITY })),
    [act, callService]
  );
  const [value, setValue] = useLiveSlider((denon?.attributes.volume_level as number) ?? 0, send);
  const step = (delta: number) => setValue(Math.min(DENON_MAX_VOLUME, Math.max(0, Math.round((value + delta) * 200) / 200)));
  return (
    <div className="vol">
      <button className="step" aria-label="Volume down" onClick={() => step(-0.03)}><Icon name="minus" /></button>
      <input
        type="range"
        id="volume"
        aria-label="Receiver volume"
        min="0"
        max={DENON_MAX_VOLUME}
        step="0.005"
        value={value}
        style={{ '--p': `${(value / DENON_MAX_VOLUME) * 100}%` } as React.CSSProperties}
        onChange={(e) => setValue(parseFloat(e.target.value))}
      />
      <button className="step" aria-label="Volume up" onClick={() => step(0.03)}><Icon name="plus" /></button>
      <span className="db">{decibels(value)}</span>
    </div>
  );
}

function MoreSheet({ ha, act, onClose, chooseMode }: { ha: HA; act: Act; onClose: () => void; chooseMode: (m: Mode) => void }) {
  const [armed, setArmed] = useState(false);
  useEffect(() => {
    if (!armed) return;
    const timer = setTimeout(() => setArmed(false), 3000);
    return () => clearTimeout(timer);
  }, [armed]);

  const numpadAction = (message: string, key: string, modifiers: string[] = []) => {
    onClose();
    act(ha.publishMqtt(NUMPAD_TOPIC, numpad(key, modifiers)), message);
  };
  const restart = () => {
    if (armed) numpadAction('Restarting Shield', '1_3', ['mod_left']);
    else setArmed(true);
  };

  return (
    <div className="veil" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="sheet" role="dialog" aria-label="More TV options">
        <h2>More for the TV</h2>
        <button className="opt" onClick={() => chooseMode('stargazing')}><b>Stargazing</b><span>Turns the screen and living area lights off</span></button>
        <button className="opt" onClick={() => chooseMode('off')}><b>Turn screen off</b><span>The screen stays dark until you pick a mode</span></button>
        <button className="opt" onClick={() => numpadAction('Starting screensaver', '4_1', ['mod_left'])}><b>Screensaver</b><span>Starts the Shield screensaver</span></button>
        <button className="opt" onClick={() => numpadAction('Opening Shield settings', '2_3')}><b>Shield settings</b><span>Opens the settings screen</span></button>
        <button className="opt" onClick={() => numpadAction('Running frame rate shortcut', '2_3', ['mod_left'])}><b>Match frame rate</b><span>Runs the settings shortcut on the Shield</span></button>
        <button className={`opt ${armed ? 'arm' : ''}`} onClick={restart}><b>{armed ? 'Tap again to restart' : 'Restart Shield'}</b><span>Cuts power to the Shield for 2 seconds</span></button>
      </div>
    </div>
  );
}

export function LivingPage({ ha, act, notify, hidden }: { ha: HA; act: Act; notify: (m: string, bad?: boolean) => void; hidden: boolean }) {
  const [scene, setScene] = useState<string | null>(null);
  const [eachLight, setEachLight] = useState(false);
  const [more, setMore] = useState(false);
  const [request, setRequest] = useState<{ mode: Mode; timedOut: boolean } | null>(null);
  const clearScene = useCallback(() => setScene(null), []);

  const applyScene = async (s: (typeof SCENES)[number]) => {
    const message = s.id === 'off' ? 'Living area lights off' : `${s.label} lights on`;
    if (await act(ha.publishMqtt(NUMPAD_TOPIC, numpad(s.key, ['mod_right'])), message)) setScene(s.id);
  };

  const chooseFromSheet = async (mode: Mode) => {
    setMore(false);
    setRequest({ mode, timedOut: false });
    if (!(await act(ha.callService('pyscript', 'set_tv_mode', { mode })))) setRequest(null);
    else if (mode === 'stargazing') setScene('off');
  };

  return (
    <div className="page" hidden={hidden}>
      <RoomHeader room={LIVING} ha={ha} />
      <TvPanel ha={ha} act={act} notify={notify} onMore={() => setMore(true)} request={request} setRequest={setRequest} />
      <Volume ha={ha} act={act} />
      <section>
        <div className="sec-h">
          <h2>Lights</h2>
          <button className="link" aria-expanded={eachLight} onClick={() => setEachLight(!eachLight)}>
            {eachLight ? 'Hide each light' : 'Each light'}
          </button>
        </div>
        <div className="scenes">
          {SCENES.map((s) => (
            <button
              key={s.id}
              className={`scene ${s.level > 60 ? 'bright' : ''}`}
              style={{ '--l': s.level } as React.CSSProperties}
              aria-pressed={scene === s.id}
              onClick={() => applyScene(s)}
            >
              {s.label}
            </button>
          ))}
        </div>
        {eachLight && <LightList room={LIVING} ha={ha} act={act} onManual={clearScene} />}
      </section>
      <ShadesSection room={LIVING} ha={ha} act={act} />
      {more && <MoreSheet ha={ha} act={act} onClose={() => setMore(false)} chooseMode={chooseFromSheet} />}
    </div>
  );
}
