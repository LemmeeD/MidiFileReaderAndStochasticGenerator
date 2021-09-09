import mido
import numpy as np
from midiutil import MIDIFile
from mido import MidiFile
import utils
import midi_utils
import model.dtmc


T = 16       # number of measures to simulate
# filepath = "midis/temp.mid"
# filepath = "midis\Videogames OST\Zelda's Lullaby.mid"
# filepath = "midis/Videogames OST/Song of Storms.mid"
# filepath = "midis/Videogames OST/Sm1cave.mid"
filepath = "midis/Videogames OST/Smbwater.mid"
# filepath = "midis/Beethoven/symphony_9_1_(c)cvikl.mid"
# filepath = "midis/Mozart/symphony_550_1_(c)ishii.mid"
# filepath = "midis/Vivaldi/vivaldi_4_stagioni_estate_1_(c)pollen.mid"
mid = MidiFile(filepath, clip=True)
ticks_per_beat = mid.ticks_per_beat
num_of_tracks = len(mid.tracks)
original_midi_type = mid.type
bpm = midi_utils.get_first_tempo_as_bpm(mid)
num, den = midi_utils.get_first_time_signature(mid)
print("<filename="+filepath+", type="+str(mid.type)+", ticks_per_beat="+str(mid.ticks_per_beat)+", num_of_tracks="+str(num_of_tracks)+">")

# 'cleaning'
mid = midi_utils.clean_duplicate_tracks(mid)
num_of_tracks = len(mid.tracks)
print("DEBUG: num_of_tracks after cleaning duplicates =", num_of_tracks)
tracks = midi_utils.remove_meta_track(mid.tracks)
num_of_tracks = len(tracks)
print("DEBUG: num_of_tracks after removing 'meta' tracks =", num_of_tracks)

# instantiating new midi file
new_mid = MIDIFile(num_of_tracks, deinterleave=False, file_format=original_midi_type, ticks_per_quarternote=ticks_per_beat)
new_mid.addTempo(0, 0, bpm)

# analysis
for i, track in enumerate(tracks):
    print("DEBUG: ******** PARSING track "+str(i+1)+"/"+str(len(tracks))+" ********")
    pitches_sequence = []
    durations_sequence = []
    attacks_sequence = []
    instrument = midi_utils.get_first_instrument_set_of_track(track)
    for j, msg in enumerate(track):
        # get notes pitch
        if isinstance(msg, mido.messages.messages.Message) and msg.type == 'note_on' and msg.velocity > 0:
            pitches_sequence.append(msg.note)
            # get duration of note
            durations_sequence.append(midi_utils.parse_note_duration(msg, j, track, ticks_per_beat))
            # get next note attack
            attacks_sequence.append(midi_utils.parse_note_attack_of_next_note(track, j, ticks_per_beat))

    # removing duplicates
    pitches_sequence = utils.remove_None_elements_from_list(pitches_sequence)
    durations_sequence = utils.remove_None_elements_from_list(durations_sequence)
    attacks_sequence = utils.remove_None_elements_from_list(attacks_sequence)

    # setting the framework
    tm_pitches, pitches = model.dtmc.create_transition_matrix_from_sequence(pitches_sequence)
    tm_durations, durations = model.dtmc.create_transition_matrix_from_sequence(durations_sequence)
    tm_attacks, attacks = model.dtmc.create_transition_matrix_from_sequence(attacks_sequence)

    # initial probabilities: the idea is to start from the same note of the original file. That means taking the first transition in the sequence
    initial_p = np.zeros(len(pitches)).tolist()
    initial_p[pitches.index(pitches_sequence[0])] = 1       # initial_p[0] = 1 directly
    initial_d = np.zeros(len(durations)).tolist()
    initial_d[0] = 1
    initial_a = np.zeros(len(attacks)).tolist()
    initial_a[0] = 1

    print("DEBUG: starting track's simulation")
    new_mid.addTrackName(i, 0, "track_" + str(i))
    new_mid.addProgramChange(i, 0, 0, instrument)
    # sampling
    p = np.random.choice(a=pitches, p=initial_p)
    d = utils.get_note_duration_as_number(np.random.choice(a=durations, p=initial_d))
    a = utils.get_note_duration_as_number(np.random.choice(a=attacks, p=initial_a))
    cursor = 0
    while cursor <= T * ((4 / den) * num):
        # print("NOTE", n, "with d =", d, "WRITTEN at tempo =", cursor)
        new_mid.addNote(i, 0, p, cursor, d, 100)  # needs the GLOBAL beat in which insert the note
        last_note_pitch = p
        # sampling
        attacks.index(utils.get_note_duration_as_string_fraction(a))
        p, d, a = model.dtmc.sample_pitch_duration_attack(pitches, tm_pitches[pitches.index(p)],
                         durations, tm_durations[durations.index(utils.get_note_duration_as_string_fraction(d))],
                         attacks, tm_attacks[attacks.index(utils.get_note_duration_as_string_fraction(a))])
        # cannot have the same note played in the same exact moment otherwise ERROR...
        while a == 0 and p == last_note_pitch:
            p, d, a = model.dtmc.sample_pitch_duration_attack(pitches, tm_pitches[pitches.index(p)],
                             durations, tm_durations[durations.index(utils.get_note_duration_as_string_fraction(d))],
                             attacks, tm_attacks[attacks.index(utils.get_note_duration_as_string_fraction(a))])
        cursor = cursor + a
    print("DEBUG: ending track's simulation")

# write to file the final result
with open("output.mid", 'wb') as outf:
    new_mid.writeFile(outf)

print("------- END -------")
