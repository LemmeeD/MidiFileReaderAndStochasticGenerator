import mido


def print_midi_meta_messages(mid):
    for track in mid.tracks:
        for msg in track:
            if (isinstance(msg, mido.midifiles.meta.MetaMessage) or (isinstance(msg, mido.messages.messages.Message) and msg.type == "sysex")):
                print(msg)