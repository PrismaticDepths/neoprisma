import pynput

def on_press(key):
    try:
        vk = key.vk if isinstance(key,pynput.keyboard.KeyCode) else key.value.vk
        print(vk)
    except AttributeError:
        pass

# Collect events until released
with pynput.keyboard.Listener(on_press=on_press) as listener:
    listener.join()
