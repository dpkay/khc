from datetime import datetime as dt
from datetime import timezone as timezone

cached_volume = None
volume_last_changed_datetime = None

MEDIA_PLAYER_ENTITY_PATH = "media_player.denon_avr_x4700h"
MEDIA_PLAYER_MAX_VOLUME = 0.91  # given by denon AVR
RESET_VOLUME = 0.3
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
  global volume_last_changed_datetime

  # Determine whether we need to refresh the |cached_volume| variable.
  cached_volume_needs_refresh = False

  now = dt.now(tz=timezone.utc)
  if cached_volume == None:
    # If no volume is cached, we need to refresh.
    cached_volume_needs_refresh = True
  else:
    if volume_last_changed_datetime == None:
      volume_last_changed_datetime = now

      # If we don't know how old the cached volume is, we need to refresh.
      cached_volume_needs_refresh = True
    else:
      num_seconds_ago = (now - volume_last_changed_datetime).total_seconds()
      if num_seconds_ago > 3:
      # If the cached volume is too old, we need to refresh.
        cached_volume_needs_refresh = True

  # Now refresh the cached volume if necessary.
  if cached_volume_needs_refresh:
    cached_volume = state.get(f"{MEDIA_PLAYER_ENTITY_PATH}.volume_level")
    volume_last_changed_datetime = now

  # Adjust cached volume.
  cached_volume = min(max(cached_volume + delta_volume, 0.0),
                      MEDIA_PLAYER_MAX_VOLUME)

  # Apply new cached volume to the media player.
  media_player.volume_set(entity_id=MEDIA_PLAYER_ENTITY_PATH,
                          volume_level=cached_volume)

def increase_volume():
  change_volume(+VOLUME_INCREMENT)

def decrease_volume():
  change_volume(-VOLUME_INCREMENT)

def reset_volume():
  set_volume(RESET_VOLUME)
