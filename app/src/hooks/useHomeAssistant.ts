import { useEffect, useRef, useState, useCallback } from 'react';
import { HA_TOKEN } from '../config';

type HAState = {
  entity_id: string;
  state: string;
  attributes: Record<string, unknown>;
};

export function useHomeAssistant() {
  const ws = useRef<WebSocket | null>(null);
  const msgId = useRef(1);
  const callbacks = useRef<Record<number, (result: unknown) => void>>({});
  const stateListeners = useRef<Record<string, Set<(state: HAState) => void>>>({});
  const [connected, setConnected] = useState(false);

  const send = useCallback((msg: Record<string, unknown>): Promise<unknown> => {
    return new Promise((resolve) => {
      const id = msgId.current++;
      callbacks.current[id] = resolve;
      ws.current?.send(JSON.stringify({ ...msg, id }));
    });
  }, []);

  const callService = useCallback(
    (domain: string, service: string, data?: Record<string, unknown>, target?: Record<string, unknown>) => {
      return send({ type: 'call_service', domain, service, service_data: data, target });
    },
    [send]
  );

  const publishMqtt = useCallback(
    (topic: string, payload: string) => {
      return callService('mqtt', 'publish', { topic, payload });
    },
    [callService]
  );

  const subscribeState = useCallback(
    (entityId: string, listener: (state: HAState) => void) => {
      if (!stateListeners.current[entityId]) {
        stateListeners.current[entityId] = new Set();
      }
      stateListeners.current[entityId].add(listener);
      return () => {
        stateListeners.current[entityId]?.delete(listener);
      };
    },
    []
  );

  const getState = useCallback(
    async (entityId: string): Promise<HAState | null> => {
      const result = (await send({ type: 'get_states' })) as { result: HAState[] } | undefined;
      if (!result?.result) return null;
      return result.result.find((s) => s.entity_id === entityId) ?? null;
    },
    [send]
  );

  useEffect(() => {
    let reconnectTimer: ReturnType<typeof setTimeout>;

    function connect() {
      const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
      const socket = new WebSocket(`${protocol}//${location.host}/api/websocket`);
      ws.current = socket;

      socket.onmessage = (event) => {
        const msg = JSON.parse(event.data);

        if (msg.type === 'auth_required') {
          socket.send(JSON.stringify({ type: 'auth', access_token: HA_TOKEN }));
        } else if (msg.type === 'auth_ok') {
          setConnected(true);
          // Subscribe to state changes
          const subId = msgId.current++;
          socket.send(JSON.stringify({ id: subId, type: 'subscribe_events', event_type: 'state_changed' }));
        } else if (msg.type === 'auth_invalid') {
          console.error('HA auth failed');
          setConnected(false);
        } else if (msg.type === 'result' && msg.id in callbacks.current) {
          callbacks.current[msg.id](msg);
          delete callbacks.current[msg.id];
        } else if (msg.type === 'event' && msg.event?.event_type === 'state_changed') {
          const newState = msg.event.data.new_state as HAState;
          if (newState) {
            const listeners = stateListeners.current[newState.entity_id];
            listeners?.forEach((fn) => fn(newState));
          }
        }
      };

      socket.onclose = () => {
        setConnected(false);
        reconnectTimer = setTimeout(connect, 3000);
      };

      socket.onerror = () => socket.close();
    }

    connect();
    return () => {
      clearTimeout(reconnectTimer);
      ws.current?.close();
    };
  }, []);

  return { connected, callService, publishMqtt, subscribeState, getState };
}
