import denon_avr
import samsung_qn90a
import re

SPOTIFY_ENTITY_ID = "media_player.spotify"
SHIELD_CAST_ENTITY_ID = "media_player.shield_cast"
SHIELD_SPOTIFY_DEVICE_ID = "1b53f7563c30e386c72df35e6e394813ec7e173c"

# ------------------------------------------------------------------------------
# Classical.
# ------------------------------------------------------------------------------
BACH_WELL_TEMPERED_CLAVIER_BY_RICHTER = "https://open.spotify.com/playlist/4smx1d1hZQdLWemujTY4e0"

MOZART_PIANO_SONATAS = "https://open.spotify.com/playlist/14ztNfCM5P4k8Lp7TFJTaN?si=8abd02626c3045ab"

CHOPIN_PIANO_WORKS = "https://open.spotify.com/playlist/0CYIDTNpqFbW6nbHUcqKnm?si=08bd4a1a01d347c4"

RAVEL_PIANO_WORKS = "https://open.spotify.com/album/5Ui8Uj9oHn2yT7Duo0welM?si=tPY0dVMiSJiJTLLqiUvIfw"

JOHN_WILLIAMS_GREATEST_HITS = "https://open.spotify.com/album/3xeo92ykCYWfe32si3I6zF?si=zOsK5tfySvesBTJzfk2cBg"

# ------------------------------------------------------------------------------
# Jazz.
# ------------------------------------------------------------------------------
BILL_EVANS_SOLO_PIANO = "https://open.spotify.com/playlist/77Vn3VsZEk8u1EhacroNka?si=755c14c66cab43e3"

OSCAR_PETERSON_EXCLUSIVELY_FOR_MY_FRIENDS = "https://open.spotify.com/album/3spAipb0mLDUR1CJSG9P6W?si=853d4deaa7804f28"

KEITH_JARRETT_MELODY_AT_NIGHT_WITH_YOU = "https://open.spotify.com/album/2onXlqUvme77BeIcMIOz3M?si=57d6yKeHQQ2fpsFOmfKVRQ"

THIS_IS_CHARLIE_PARKER = "https://open.spotify.com/playlist/37i9dQZF1DZ06evO2TXsYJ?si=bd2790ac5bd94051"

# ------------------------------------------------------------------------------
# Pop.
# ------------------------------------------------------------------------------
SIXTIES_AND_SEVENTIES = "https://open.spotify.com/playlist/37i9dQZF1EIhdup1SOLFpO?si=d92cada98af749da"

EIGHTIES_AND_NINETIES = "https://open.spotify.com/playlist/141guhSLUNzE58MqlIC4zT?si=0b90c586f86641d2"

ELECTROSWING = "https://open.spotify.com/playlist/37i9dQZF1DX3bH0P2uDnWA?si=9b5d6d8aeca44168"

SIMONE_SOMMERLAND = "https://open.spotify.com/playlist/70qFH5gQ59Yk5rudxiYK4t?si=4fe37b386bc34067"

# ------------------------------------------------------------------------------
# Environments.
# ------------------------------------------------------------------------------
BIRDS = "https://open.spotify.com/playlist/0tvrfzljcgMqgTUAHVWxAt?si=3f5dd5461aa54f8e"

RAIN = "https://open.spotify.com/playlist/7cStudWJdRCpG1diX164Td?si=257908acac23425b"

JUNGLE_CANOPY_RAIN = "https://open.spotify.com/playlist/5CaRl6b2tbcihfxgzmiaGV?si=23d4f8e3f3bc46e2"

# ------------------------------------------------------------------------------
PROPS_BY_ID = {
  # (Shuffle, URL)
  1: (False, BACH_WELL_TEMPERED_CLAVIER_BY_RICHTER),
  2: (False, MOZART_PIANO_SONATAS),
  3: (True, CHOPIN_PIANO_WORKS),
  4: (True, JOHN_WILLIAMS_GREATEST_HITS),

  5: (True, THIS_IS_CHARLIE_PARKER),
  6: (True, OSCAR_PETERSON_EXCLUSIVELY_FOR_MY_FRIENDS),
  7: (True, BILL_EVANS_SOLO_PIANO),
  8: (True, KEITH_JARRETT_MELODY_AT_NIGHT_WITH_YOU),

  9: (True, SIXTIES_AND_SEVENTIES),
  10: (True, EIGHTIES_AND_NINETIES),
  11: (True, ELECTROSWING),
  12: (True, SIMONE_SOMMERLAND),

  13: (True, BIRDS),
  14: (True, RAIN),
  15: (True, JUNGLE_CANOPY_RAIN)
}

def uri_from_url(url):
  m = re.match(r".*open.spotify.com\/(\w*)\/(\w*)\??.*", url)
  content_type = m[1]  # e.g. "playlist"
  id = m[2]  # e.g. "4smx1d1hZQdLWemujTY4e0"
  return f"spotify:{content_type}:{id}"

def play_uri(uri=None, repeat=False, shuffle=False):
  spotcast.start(spotify_device_id=SHIELD_SPOTIFY_DEVICE_ID,
                 uri=uri,
                 random_song=shuffle,
                 shuffle=shuffle,
                 repeat=repeat)

def play(id):
  samsung_qn90a.maybe_enable_ambient_mode()
  shuffle, url = PROPS_BY_ID[id]
  media_player.media_pause(entity_id=SHIELD_CAST_ENTITY_ID)
  denon_avr.reset_volume_low()
  uri = uri_from_url(url)
  play_uri(uri, repeat=True, shuffle=shuffle)

