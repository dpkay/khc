"""
Single entry point for what the living room TV should be doing.

The web remote calls pyscript.set_tv_mode with the mode it wants. Unlike the
ambient toggle on the numpad, every mode can be requested from any starting
state: the TV is woken if needed, and asking for the current mode does nothing.
"""

import livingroom_lights
import nvidia_shield_tv
import samsung_qn90a


@service
def set_tv_mode(mode=None):
  """Web remote calls this service to change the TV mode."""
  task.unique("set_tv_mode")  # If taps overlap, the latest one wins.

  if mode == "ambient":
    samsung_qn90a.show_ambient()
  elif mode == "youtube":
    samsung_qn90a.wake_and_settle()
    nvidia_shield_tv.start_youtube()
  elif mode == "kodi":
    samsung_qn90a.wake_and_settle()
    nvidia_shield_tv.start_kodi()
  elif mode == "off":
    samsung_qn90a.turn_off()
  elif mode == "stargazing":
    samsung_qn90a.turn_off()
    livingroom_lights.scene_all_off()
