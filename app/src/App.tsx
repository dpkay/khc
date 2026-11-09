import { useCallback, useEffect, useRef, useState } from 'react';
import { BEDROOM, KIDS } from './config';
import { OFFLINE, useHomeAssistant } from './hooks/useHomeAssistant';
import { LivingPage } from './components/LivingPage';
import { RoomPage, type Act } from './components/RoomParts';
import './styles.css';

const ROOMS = ['Living', 'Bedroom', 'Kids'] as const;
const OFFLINE_BANNER_DELAY_MS = 2000;

export default function App() {
  const ha = useHomeAssistant();
  const [room, setRoom] = useState<(typeof ROOMS)[number]>('Living');
  const [toast, setToast] = useState<{ message: string; bad: boolean } | null>(null);
  const [showOffline, setShowOffline] = useState(false);
  const toastTimer = useRef<ReturnType<typeof setTimeout>>(undefined);

  // Brief drops (like the phone waking) reconnect on their own; don't flash a banner.
  useEffect(() => {
    const timer = setTimeout(() => setShowOffline(!ha.connected), ha.connected ? 0 : OFFLINE_BANNER_DELAY_MS);
    return () => clearTimeout(timer);
  }, [ha.connected]);

  const notify = useCallback((message: string, bad = false) => {
    setToast({ message, bad });
    clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 2000);
  }, []);

  const act: Act = useCallback(
    async (action, successMessage) => {
      try {
        await action;
        if (successMessage) notify(successMessage);
        return true;
      } catch (e) {
        notify((e as Error).message === OFFLINE ? 'Not sent. Home Assistant is offline.' : "That didn't work. Try again.", true);
        return false;
      }
    },
    [notify]
  );

  return (
    <div className="app">
      {showOffline && <div className="offline">Can't reach Home Assistant. Retrying now.</div>}
      <main className="scroll">
        <LivingPage ha={ha} act={act} notify={notify} hidden={room !== 'Living'} />
        <RoomPage room={BEDROOM} ha={ha} act={act} hidden={room !== 'Bedroom'} />
        <RoomPage room={KIDS} ha={ha} act={act} hidden={room !== 'Kids'} />
      </main>
      <nav aria-label="Rooms">
        {ROOMS.map((r) => (
          <button key={r} aria-current={r === room ? 'page' : undefined} onClick={() => setRoom(r)}>{r}</button>
        ))}
      </nav>
      {toast && <div className={`toast ${toast.bad ? 'bad' : ''}`} role="status">{toast.message}</div>}
    </div>
  );
}
