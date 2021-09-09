import os
import mido
from fractions import Fraction
import utils


def clean_duplicate_tracks(mid):
    message_numbers = []
    duplicates = []
    for track in mid.tracks:
        if len(track) in message_numbers:
            duplicates.append(track)
        else:
            message_numbers.append(len(track))
    filename = os.path.basename(mid.filename)
    print("DEBUG: track duplicates found in " + filename + ": " + str(len(duplicates)))
    if len(duplicates) != 0:
        for track in duplicates:
            mid.tracks.remove(track)
        filename_no_extension = filename[:filename.find('.')]
        mid.save(filename_no_extension+"_NO_DUPLICATES.mid")
    return mid


def is_track_only_for_meta_data(track):
    for msg in track:
        if isinstance(msg, mido.messages.messages.Message) and (msg.type == "note_on" or msg.type == "note_off"):
            return False
    return True


def remove_meta_track(tracks):
    result = []
    for track in tracks:
        if not is_track_only_for_meta_data(track):
            result.append(track)
    return result


def get_first_time_signature(mid):
    for track in mid.tracks:
        for msg in track:
            if (isinstance(msg, mido.midifiles.meta.MetaMessage)):
                if msg.type == "time_signature":
                    return msg.numerator, msg.denominator


def get_first_instrument_set_of_track(track):
    for msg in track:
        if (isinstance(msg, mido.messages.messages.Message) and msg.type == "program_change"):
                return msg.program


def get_first_tempo_as_bpm(mid):
    for track in mid.tracks:
        for msg in track:
            if (isinstance(msg, mido.midifiles.meta.MetaMessage)):
                if msg.type == "set_tempo":
                    return int(mido.tempo2bpm(msg.tempo))



# the end of note can be an 'note_off' of the same note OR ANOTHER 'note_on' event of the same note but with velocity 0
def parse_note_duration(current_msg, index_current_msg, current_track, ticks_per_beat):     # as fraction as string
    ticks_elapsed = 0
    for j in range(index_current_msg + 1, len(current_track)):
        if isinstance(current_track[j], mido.messages.messages.Message) and (
            (current_track[j].type == 'note_off' and current_track[j].note) or
            (current_track[j].type == 'note_on' and current_msg.note == current_track[j].note and current_track[j].velocity == 0)
        ):
            ticks_elapsed = ticks_elapsed + current_track[j].time
            return str(Fraction(ticks_elapsed / ticks_per_beat).limit_denominator(32))
        else:
            ticks_elapsed = ticks_elapsed + current_track[j].time
    return None


def parse_note_attack_of_next_note(current_track, index_current_msg, ticks_per_beat):
    if index_current_msg <= len(current_track) - 2:
        tot_ticks_elapsed = 0
        for j in range(index_current_msg + 1, len(current_track)):
            if isinstance(current_track[j], mido.messages.messages.Message) and current_track[j].type == "note_on" and current_track[j].velocity > 0:  # time of a message is already a DELTA, implicitly calculating delta ticks of current note from the previous one
                # this note_on could have time related with an intermediate vent (maybe note_off)
                return utils.convert_ticks_to_fraction_string(current_track[j].time + tot_ticks_elapsed, ticks_per_beat)
            else:
                tot_ticks_elapsed = tot_ticks_elapsed + current_track[j].time


def parse_next_note_pitch(current_track, index_current_msg):
    for j in range(index_current_msg + 1, len(current_track)):
        if current_track[j].type == "note_on" and current_track[j].velocity > 0:
            return current_track[j].note
    return None


def parse_next_note_duration(current_track, index_current_msg, ticks_per_beat):
    for j in range(index_current_msg + 1, len(current_track)):
        if current_track[j].type == "note_on" and current_track[j].velocity > 0:
            return parse_note_duration(current_track[j], j, current_track, ticks_per_beat)
    return None


def parse_next_note_attack_of_the_next_note_again(current_track, index_current_msg, ticks_per_beat):
    for j in range(index_current_msg + 1, len(current_track)):
        if current_track[j].type == "note_on" and current_track[j].velocity > 0:
            return parse_note_attack_of_next_note(current_track, j, ticks_per_beat)
    return None


def get_noted_note(number, diesis=True):
    if diesis:
        map = {21: "A0", 22: "A#0", 23: "B0",
                 24: "C1", 25: "C#1", 26: "D1", 27: "D#1", 28: "E1", 29: "F1", 30: "F#1", 31: "G1", 32: "G#1",
                 33: "A1", 34: "A#1", 35: "B1",
                 36: "C2", 37: "C#2", 38: "D2", 39: "D#2", 40: "E2", 41: "F2", 42: "F#2", 43: "G2", 44: "G#2",
                 45: "A2", 46: "A#2", 47: "B2",
                 48: "C3", 49: "C#3", 50: "D3", 51: "D#3", 52: "E3", 53: "F3", 54: "F#3", 55: "G3", 56: "G#3",
                 57: "A3", 58: "A#3", 59: "B3",
                 60: "C4", 61: "C#4", 62: "D4", 63: "D#4", 64: "E4", 65: "F4", 66: "F#4", 67: "G4", 68: "G#4",
                 69: "A4", 70: "A#4", 71: "B4",
                 72: "C5", 73: "C#5", 74: "D5", 75: "D#5", 76: "E5", 77: "F5", 78: "F#5", 79: "G5", 80: "G#5",
                 81: "A5", 82: "A#5", 83: "B5",
                 84: "C6", 85: "C#6", 86: "D6", 87: "D#6", 88: "E6", 89: "F6", 90: "F#6", 91: "G6", 92: "G#6",
                 93: "A6", 94: "A#6", 95: "B6",
                 96: "C7", 97: "C#7", 98: "D7", 99: "D#7", 100: "E7", 101: "F7", 102: "F#7", 103: "G7",
                 104: "G#7", 105: "A7", 106: "A#7", 107: "B7",
                 108: "C8"}
    else:
        map = {21: "A0", 22: "Bb0", 23: "B0",
                 24: "C1", 25: "Db1", 26: "D1", 27: "Eb1", 28: "E1", 29: "F1", 30: "Gb1", 31: "G1",
                 32: "Ab1", 33: "A1", 34: "Bb1", 35: "B1",
                 36: "C2", 37: "Db2", 38: "D2", 39: "Eb2", 40: "E2", 41: "F2", 42: "Gb2", 43: "G2",
                 44: "Ab2", 45: "A2", 46: "Bb2", 47: "B2",
                 48: "C3", 49: "Db3", 50: "D3", 51: "Eb3", 52: "E3", 53: "F3", 54: "Gb3", 55: "G3",
                 56: "Ab3", 57: "A3", 58: "Bb3", 59: "B3",
                 60: "C4", 61: "Db4", 62: "D4", 63: "Eb4", 64: "E4", 65: "F4", 66: "Gb4", 67: "G4",
                 68: "Ab4", 69: "A4", 70: "Bb4", 71: "B4",
                 72: "C5", 73: "Db5", 74: "D5", 75: "Eb5", 76: "E5", 77: "F5", 78: "Gb5", 79: "G5",
                 80: "Ab5", 81: "A5", 82: "Bb5", 83: "B5",
                 84: "C6", 85: "Db6", 86: "D6", 87: "Eb6", 88: "E6", 89: "F6", 90: "Gb6", 91: "G6",
                 92: "Ab6", 93: "A6", 94: "Bb6", 95: "B6",
                 96: "C7", 97: "Db7", 98: "D7", 99: "Eb7", 100: "E7", 101: "F7", 102: "Gb7", 103: "G7",
                 104: "Ab7", 105: "A7", 106: "Bb7", 107: "B7",
                 108: "C8"}
    return map[number]