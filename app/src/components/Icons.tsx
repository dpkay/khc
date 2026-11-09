const PATHS = {
  up: <path d="M5 15l7-7 7 7" />,
  down: <path d="M5 9l7 7 7-7" />,
  left: <path d="M15 5l-7 7 7 7" />,
  right: <path d="M9 5l7 7-7 7" />,
  stop: <rect x="7" y="7" width="10" height="10" rx="1" />,
  prev: <path d="M6 5v14M19 6l-9 6 9 6z" />,
  next: <path d="M18 5v14M5 6l9 6-9 6z" />,
  play: <path d="M5 5l9 7-9 7zM17 6v12M21 6v12" />,
  back: <path d="M9 7L4 12l5 5M4 12h11a5 5 0 0 1 5 5" />,
  home: <path d="M4 11l8-7 8 7M6 10v10h12V10" />,
  more: <path d="M5 12h.01M12 12h.01M19 12h.01" strokeWidth="3" />,
  minus: <path d="M6 12h12" />,
  plus: <path d="M6 12h12M12 6v12" />,
};

export function Icon({ name }: { name: keyof typeof PATHS }) {
  return <svg viewBox="0 0 24 24" aria-hidden="true">{PATHS[name]}</svg>;
}
