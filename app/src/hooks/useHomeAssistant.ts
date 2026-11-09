import { useCallback, useEffect, useMemo, useRef, useState, useSyncExternalStore } from 'react';
import { HA_TOKEN } from '../config';

export type HAState = {
  entity_id: string;
  state: string;
  attributes: Record<string, unknown>;
};
type Pending = { resolve: (result: unknown) => void; reject: (error: Error) => void };

export const OFFLINE = 'offline';

export function useHomeAssistant() {
  const ws = useRef<WebSocket | null>(null);
  const authed = useRef(false);
  const msgId = useRef(1);
  const pending = useRef<Record<number, Pending>>({});
  const states = useRef<Record<string, HAState>>({});
  const listeners = useRef<Record<string, Set<() => void>>>({});
  const [connected, setConnected] = useState(false);

  const send = useCallback((msg: Record<string, unknown>): Promise<unknown> => {
    return new Promise((resolve, reject) => {
      const socket = ws.current;
      if (!socket || socket.readyState !== WebSocket.OPEN || !authed.current) {
        reject(new Error(OFFLINE));
        return;
      }
      const id = msgId.current++;
      pending.current[id] = { resolve, reject };
      socket.send(JSON.stringify({ ...msg, id }));
    });
  }, []);

  const callService = useCallback(
    (domain: string, service: string, data?: Record<string, unknown>, target?: Record<string, unknown>) =>
      send({ type: 'call_service', domain, service, service_data: data, target }),
    [send]
  );

  const publishMqtt = useCallback(
    (topic: string, payload: string) => callService('mqtt', 'publish', { topic, payload }),
    [callService]
  );

  const subscribeEntity = useCallback((entityId: string, listener: () => void) => {
    (listeners.current[entityId] ??= new Set()).add(listener);
    return () => {
      listeners.current[entityId]?.delete(listener);
    };
  }, []);

  const getEntity = useCallback((entityId: string): HAState | undefined => states.current[entityId], []);

  useEffect(() => {
    let reconnectTimer: ReturnType<typeof setTimeout>;
    let pongTimer: ReturnType<typeof setTimeout>;

    function failPending() {
      Object.values(pending.current).forEach((p) => p.reject(new Error(OFFLINE)));
      pending.current = {};
    }

    function dropSocket() {
      authed.current = false;
      setConnected(false);
      failPending();
      if (ws.current) {
        ws.current.onclose = null;
        ws.current.onerror = null;
        ws.current.close();
        ws.current = null;
      }
    }

    function publishAll(list: HAState[]) {
      for (const s of list) states.current[s.entity_id] = s;
      Object.values(listeners.current).forEach((set) => set.forEach((fn) => fn()));
    }

    function connect() {
      clearTimeout(reconnectTimer);
      const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
      const socket = new WebSocket(`${protocol}//${location.host}/api/websocket`);
      ws.current = socket;

      socket.onmessage = (event) => {
        const msg = JSON.parse(event.data);

        if (msg.type === 'auth_required') {
          socket.send(JSON.stringify({ type: 'auth', access_token: HA_TOKEN }));
        } else if (msg.type === 'auth_ok') {
          authed.current = true;
          setConnected(true);
          socket.send(JSON.stringify({ id: msgId.current++, type: 'subscribe_events', event_type: 'state_changed' }));
          send({ type: 'get_states' }).then((r) => publishAll((r as { result: HAState[] }).result));
        } else if (msg.type === 'auth_invalid') {
          console.error('HA auth failed');
          setConnected(false);
        } else if (msg.type === 'pong') {
          clearTimeout(pongTimer);
        } else if (msg.type === 'result' && msg.id in pending.current) {
          const p = pending.current[msg.id];
          delete pending.current[msg.id];
          if (msg.success === false) p.reject(new Error(msg.error?.message ?? 'failed'));
          else p.resolve(msg);
        } else if (msg.type === 'event' && msg.event?.event_type === 'state_changed') {
          const newState = msg.event.data.new_state as HAState | null;
          if (newState) {
            states.current[newState.entity_id] = newState;
            listeners.current[newState.entity_id]?.forEach((fn) => fn());
          }
        }
      };

      socket.onclose = () => {
        dropSocket();
        reconnectTimer = setTimeout(connect, 3000);
      };

      socket.onerror = () => socket.close();
    }

    // A phone that slept usually returns with a dead socket that still claims to
    // be open, so check it straight away instead of waiting for it to time out.
    function onVisible() {
      if (document.visibilityState !== 'visible') return;
      const socket = ws.current;
      if (socket?.readyState === WebSocket.OPEN && authed.current) {
        clearTimeout(pongTimer);
        pongTimer = setTimeout(() => {
          dropSocket();
          connect();
        }, 1500);
        socket.send(JSON.stringify({ id: msgId.current++, type: 'ping' }));
      } else if (!socket || socket.readyState !== WebSocket.CONNECTING) {
        dropSocket();
        connect();
      }
    }

    connect();
    document.addEventListener('visibilitychange', onVisible);
    return () => {
      document.removeEventListener('visibilitychange', onVisible);
      clearTimeout(reconnectTimer);
      clearTimeout(pongTimer);
      dropSocket();
    };
  }, [send]);

  return useMemo(
    () => ({ connected, callService, publishMqtt, subscribeEntity, getEntity }),
    [connected, callService, publishMqtt, subscribeEntity, getEntity]
  );
}

export type HA = ReturnType<typeof useHomeAssistant>;

export function useEntity(ha: HA, entityId: string) {
  const { subscribeEntity, getEntity } = ha;
  return useSyncExternalStore(
    useCallback((fn) => subscribeEntity(entityId, fn), [subscribeEntity, entityId]),
    () => getEntity(entityId)
  );
}

export function useLightsOnCount(ha: HA, entityIds: string[]) {
  const { subscribeEntity, getEntity } = ha;
  return useSyncExternalStore(
    useCallback(
      (fn) => {
        const stops = entityIds.map((id) => subscribeEntity(id, fn));
        return () => stops.forEach((stop) => stop());
      },
      [subscribeEntity, entityIds]
    ),
    () => entityIds.filter((id) => getEntity(id)?.state === 'on').length
  );
}
