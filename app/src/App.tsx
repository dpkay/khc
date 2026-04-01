import { useState } from 'react';
import { useHomeAssistant } from './hooks/useHomeAssistant';
import { ShieldTab } from './components/ShieldTab';
import { LightsTab } from './components/LightsTab';
import { ShadesTab } from './components/ShadesTab';
import './styles.css';

const TABS = ['Shield', 'Lights', 'Shades'] as const;

export default function App() {
  const ha = useHomeAssistant();
  const [tab, setTab] = useState<(typeof TABS)[number]>('Shield');

  return (
    <div className="app">
      <div className={`status-bar ${ha.connected ? 'connected' : 'disconnected'}`}>
        {ha.connected ? 'Connected' : 'Connecting...'}
      </div>

      <div className="tabs">
        {TABS.map((t) => (
          <button key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
      </div>

      <div className="content">
        {tab === 'Shield' && <ShieldTab ha={ha} />}
        {tab === 'Lights' && <LightsTab ha={ha} />}
        {tab === 'Shades' && <ShadesTab ha={ha} />}
      </div>
    </div>
  );
}
