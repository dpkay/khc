from datetime import datetime as dt
from datetime import timezone as timezone

cached_volume = None
volume_last_changed_datetime = None

MEDIA_PLAYER_ENTITY_PATH = "media_player.denon_avr_x4700h"
MEDIA_PLAYER_MAX_VOLUME = 0.91  # given by denon AVR
RESET_VOLUME_HIGH = 0.55
RESET_VOLUME_LOW = 0.4
VOLUME_INCREMENT = 0.03

def set_volume(volume):
  global cached_volume
  global volume_last_changed_datetime

  cached_volume = volume
  volume_last_changed_datetime = dt.now(tz=timezone.utc)

  media_player.volume_set(entity_id=MEDIA_PLAYER_ENTITY_PATH,
                          volume_level=cached_volume)

def change_volume(delta_volume):
  # Unfortunately, on our Denon AVR it takes forever for the volume_level
  # attribute to change after a set_volume call. As a result, calling this
  # functions many times in quick succession does not lead to the desired
  # result if just using volume_level. This is why we use a caching hack
  # here, so we don't have to rely on volume_level at a high frequency.
  global cached_volume

  # Refresh the cached volume if there is none yet, or if the last press was
  # too long ago for it to still be accurate.
  now = dt.now(tz=timezone.utc)
  if cached_volume == None or (now - volume_last_changed_datetime).total_seconds() > 3:
    cached_volume = state.get(f"{MEDIA_PLAYER_ENTITY_PATH}.volume_level")

  # Adjust cached volume and apply it to the media player. set_volume also
  # updates the timestamp, so the 3 seconds count from the most recent press.
  set_volume(min(max(cached_volume + delta_volume, 0.0),
                 MEDIA_PLAYER_MAX_VOLUME))

def increase_volume():
  change_volume(+VOLUME_INCREMENT)

def decrease_volume():
  change_volume(-VOLUME_INCREMENT)

def reset_volume_high():
  set_volume(RESET_VOLUME_HIGH)

def reset_volume_low():
  set_volume(RESET_VOLUME_LOW)
