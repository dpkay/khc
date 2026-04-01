declare const __HA_TOKEN__: string;

export const HA_TOKEN = __HA_TOKEN__;
export const NUMPAD_TOPIC = 'khc/livingroom/numpad';
export const SHIELD_KEY_TOPIC = 'kha/livingroom/shield/press_key';
export const DENON_ENTITY = 'media_player.denon_avr_x4700h';
export const DENON_MAX_VOLUME = 0.91;

export const SHADE_NAMES_BY_ROOM: Record<string, { label: string; name: string }[]> = {
  'Living Room': [
    { label: 'Solar Left', name: 'livingroom_solar_left' },
    { label: 'Solar Right', name: 'livingroom_solar_right' },
  ],
  'Bedroom': [
    { label: 'Blackout Left', name: 'bedroom_blackout_left' },
    { label: 'Blackout Right', name: 'bedroom_blackout_right' },
    { label: 'Solar Left', name: 'bedroom_solar_left' },
    { label: 'Solar Right', name: 'bedroom_solar_right' },
  ],
  'Kids Room': [
    { label: 'Blackout Left', name: 'kidsroom_blackout_left' },
    { label: 'Blackout Right', name: 'kidsroom_blackout_right' },
    { label: 'Solar Left', name: 'kidsroom_solar_left' },
    { label: 'Solar Right', name: 'kidsroom_solar_right' },
  ],
};
