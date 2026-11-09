declare const __HA_TOKEN__: string;

export const HA_TOKEN = __HA_TOKEN__;
export const NUMPAD_TOPIC = 'khc/livingroom/numpad';
export const SHIELD_KEY_TOPIC = 'kha/livingroom/shield/press_key';

export const DENON_ENTITY = 'media_player.denon_avr_x4700h';
export const DENON_MAX_VOLUME = 0.91;
export const TV_ENTITY = 'media_player.livingroom_qn90a';
export const SHIELD_ENTITY = 'media_player.shield_androidtv';
export const AMBIENT_ENTITY = 'input_boolean.livingroom_qn90a_ambient_mode';

export type Light = { label: string; entity: string };
export type ShadeGroup = { label: string; left: string; right: string };
export type Room = { name: string; lights: Light[]; shades: ShadeGroup[] };

const shades = (prefix: string, type: string, label: string): ShadeGroup => ({
  label,
  left: `${prefix}_${type}_left`,
  right: `${prefix}_${type}_right`,
});

export const LIVING: Room = {
  name: 'Living',
  lights: [
    { label: 'Living main', entity: 'light.living_room_main_lights' },
    { label: 'Living cove', entity: 'light.living_room_cove_lights' },
    { label: 'Sconces', entity: 'light.living_room_sconces' },
    { label: 'Dining cove', entity: 'light.dining_room_cove_lights' },
    { label: 'Chandelier', entity: 'light.dining_room_chandelier' },
    { label: 'Kitchen', entity: 'light.kitchen_main_lights' },
    { label: 'Under cabinet', entity: 'light.kitchen_under_cabinet' },
    { label: 'Hallway', entity: 'light.hallway_main_lights' },
    { label: 'Foyer', entity: 'light.front_foyer_main_lights' },
  ],
  shades: [shades('livingroom', 'solar', 'Solar shades')],
};

export const BEDROOM: Room = {
  name: 'Bedroom',
  lights: [
    { label: 'Ceiling', entity: 'light.master_bedroom_cove_lights' },
    { label: 'Closet', entity: 'light.walkin_closet_main_lights' },
  ],
  shades: [shades('bedroom', 'blackout', 'Blackout'), shades('bedroom', 'solar', 'Solar')],
};

export const KIDS: Room = {
  name: 'Kids',
  lights: [
    { label: 'Main', entity: 'light.luca_bedroom_main_lights' },
    { label: 'Cove', entity: 'light.luca_bedroom_cove_lights' },
  ],
  shades: [shades('kidsroom', 'blackout', 'Blackout'), shades('kidsroom', 'solar', 'Solar')],
};

// `level` tints the button by how much light the scene gives. `key` is the
// numpad key for the scene, so the app and the numpad share main.py's dispatch.
export const SCENES = [
  { id: 'bright', label: 'Bright', level: 90, key: '2_1' },
  { id: 'reading', label: 'Reading', level: 32, key: '2_2' },
  { id: 'dining', label: 'Dining', level: 24, key: '2_3' },
  { id: 'living', label: 'Living only', level: 28, key: '2_4' },
  { id: 'low', label: 'Low', level: 16, key: '1_3' },
  { id: 'dim', label: 'Dim', level: 10, key: '1_2' },
  { id: 'lrdim', label: 'Living dim', level: 7, key: '3_4' },
  { id: 'off', label: 'Off', level: 0, key: '1_1' },
];

// Payload that makes pyscript treat this like a press on the physical numpad.
export function numpad(key: string, modifiers: string[] = []) {
  return JSON.stringify({ event_name: 'pressed', key, pressed_keys: [...modifiers, key] });
}
