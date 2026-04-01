import { SHADE_NAMES_BY_ROOM } from '../config';

type HA = {
  callService: (domain: string, service: string, data?: Record<string, unknown>, target?: Record<string, unknown>) => Promise<unknown>;
};

function shadeCommand(ha: HA, shadeNames: string[], command: string) {
  ha.callService('script', 'send_somfy_shade_command', {
    shade_names: shadeNames,
    command,
  });
}

export function ShadesTab({ ha }: { ha: HA }) {
  return (
    <div className="tab-content">
      {Object.entries(SHADE_NAMES_BY_ROOM).map(([room, shades]) => (
        <div className="section" key={room}>
          <div className="section-title">{room}</div>
          {shades.map((shade) => (
            <div className="shade-row" key={shade.name}>
              <span className="shade-label">{shade.label}</span>
              <div className="shade-buttons">
                <button className="btn-sm" onClick={() => shadeCommand(ha, [shade.name], 'up')}>&#9650;</button>
                <button className="btn-sm" onClick={() => shadeCommand(ha, [shade.name], 'stop')}>&#9724;</button>
                <button className="btn-sm" onClick={() => shadeCommand(ha, [shade.name], 'down')}>&#9660;</button>
              </div>
            </div>
          ))}
          <div className="row" style={{ marginTop: 8 }}>
            <button className="btn-sm" onClick={() => shadeCommand(ha, shades.map((s) => s.name), 'up')}>
              All &#9650;
            </button>
            <button className="btn-sm" onClick={() => shadeCommand(ha, shades.map((s) => s.name), 'stop')}>
              All &#9724;
            </button>
            <button className="btn-sm" onClick={() => shadeCommand(ha, shades.map((s) => s.name), 'down')}>
              All &#9660;
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
