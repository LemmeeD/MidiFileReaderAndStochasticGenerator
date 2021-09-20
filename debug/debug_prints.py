import mido
from utils import midi_utils
from utils import gen_utils


def print_midi_meta_messages(mid):
    for track in mid.tracks:
        for msg in track:
            if (isinstance(msg, mido.midifiles.meta.MetaMessage) or (isinstance(msg, mido.messages.messages.Message) and msg.type == "sysex")):
                print(msg)


def print_midi_tracks(mid):
    counter_trax = 0
    for track in mid.tracks:
        counter_msg = 0
        is_only_for_metadata = True
        for msg in track:
            counter_msg = counter_msg + 1
            if (isinstance(msg, mido.messages.messages.Message)):
                is_only_for_metadata = False
        counter_trax = counter_trax + 1
        if is_only_for_metadata:
            print("<midi track["+str(counter_trax)+"]: '"+track.name+"', "+str(counter_msg)+" messages only for metadata>")
        else:
            print("<midi track["+str(counter_trax)+"]: '"+track.name+"', "+str(counter_msg)+" messages>")


def print_messages(track, ticks_per_beat):
    for msg in track:
        if (msg.type == 'note_on' or msg.type == 'note_off') and msg.velocity > 0:      # velocity?
            print("<" + msg.type +" note=" + str(msg.note) +"(" + midi_utils.get_noted_note(msg.note) + ")" + " delta_time=" + str(msg.time) + "(" + gen_utils.convert_ticks_to_fraction_string(msg.time, ticks_per_beat) + ")>")