import mido
import numpy as np
from midiutil import MIDIFile
from mido import MidiFile
from utils import gen_utils
from utils import midi_utils
from model import dtmc


# PARAMETERS: filepath and number of measures to simulate (T)
T = 8       # number of measures to simulate
# filepath = "tabs_&_midis/3rdmov_part_inverno.mid"
# filepath = "tabs_&_midis/1stmov_part_primavera.mid"
# filepath = "tabs_&_midis/arpeggio_chords.mid"
# filepath = "tabs_&_midis/arpeggio_chords_rings.mid"
# filepath = "tabs_&_midis/cave.mid"
# filepath = "tabs_&_midis/great_fairys_fountain.mid"
# filepath = "tabs_&_midis/intro_dsb.mid"
# filepath = "tabs_&_midis/lost_woods.mid"
filepath = "tabs_&_midis/riff_tfc.mid"
# filepath = "tabs_&_midis/underwater.mid"
# filepath = "tabs_&_midis/wood_carving_partita.mid"
# filepath = "tabs_&_midis/zeldas_lullaby.mid"

print("------- START -------")
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
work_with_ticks = True
new_mid = MIDIFile(num_of_tracks, deinterleave=False, file_format=original_midi_type, ticks_per_quarternote=ticks_per_beat, eventtime_is_ticks=work_with_ticks)
new_mid.addTempo(0, 0, bpm)

# analysis and simulation per track
for i, track in enumerate(tracks):
    print("DEBUG: ***** PARSING track "+str(i+1)+"/"+str(len(tracks))+" *****")
    pitches_sequence = []
    durations_sequence = []
    attacks_sequence = []
    instrument = midi_utils.get_first_instrument_set_of_track(track)
    for j, msg in enumerate(track):
        # get notes pitch
        if isinstance(msg, mido.messages.messages.Message) and msg.type == 'note_on' and msg.velocity > 0:
            pitches_sequence.append(msg.note)
            # get duration of note
            durations_sequence.append(midi_utils.parse_note_duration(msg, j, track, ticks_per_beat, as_ticks=work_with_ticks))
            # get next note attack
            attacks_sequence.append(midi_utils.parse_note_attack_of_next_note(track, j, ticks_per_beat, as_ticks=work_with_ticks))

    # removing duplicates
    #pitches_sequence = gen_utils.remove_None_elements_from_list(pitches_sequence)
    #durations_sequence = gen_utils.remove_None_elements_from_list(durations_sequence)
    attacks_sequence = gen_utils.remove_None_elements_from_list(attacks_sequence)

    # setting the framework
    tm_pitches, pitches = dtmc.create_transition_matrix_from_sequence(pitches_sequence)
    tm_durations, durations = dtmc.create_transition_matrix_from_sequence(durations_sequence)
    tm_attacks, attacks = dtmc.create_transition_matrix_from_sequence(attacks_sequence)

    # initial probabilities: the idea is to start from the same note of the original file. That means taking the first transition in the sequence
    initial_p = np.zeros(len(pitches)).tolist()
    initial_p[pitches.index(pitches_sequence[0])] = 1       # initial_p[0] = 1 directly
    initial_d = np.zeros(len(durations)).tolist()
    initial_d[0] = 1
    initial_a = np.zeros(len(attacks)).tolist()
    initial_a[0] = 1

    # setting track and heuristic
    print("DEBUG: starting track's simulation")
    track_name = "track_" + str(i+1)
    new_mid.addTrackName(i, 0, track_name)
    new_mid.addProgramChange(i, 0, 0, instrument)
    coeff_heuristic = dtmc.compute_heuristic_coeff(pitches_sequence)
    is_melody = dtmc.is_lead_melody(coeff_heuristic)
    print("DEBUG: computed coeff_heuristic =", coeff_heuristic, "==>", track_name, "is lead?", is_melody)

    # simulation
    p, p_index = dtmc.sample(pitches, initial_p)
    d, d_index = dtmc.sample(durations, initial_d)
    a = -1
    a_index = -1
    cursor = 0
    limit = midi_utils.compute_limit_from_parameter_T(T, ticks_per_beat, num, den, as_ticks=work_with_ticks)
    while cursor < limit:
        # writing
        new_mid.addNote(i, 0, p, cursor, d, 100)  # needs the GLOBAL cursor (int for ticks, float for beats) in which insert the note
        last_note_pitch = p
        # heuristic
        if is_melody:
            a = d       # if is_melody==True, a_index is useless
        else:
            a, a_index = dtmc.sample(attacks, tm_attacks[a_index])
        # sampling
        p, p_index = dtmc.sample(pitches, tm_pitches[p_index])
        d, d_index = dtmc.sample(durations, tm_durations[d_index])
        # cannot have the same note played in the same exact moment otherwise ERROR... = Interleaving
        while a == 0 and p == last_note_pitch:
            p, p_index = dtmc.sample(pitches, tm_pitches[p_index])
            a, a_index = dtmc.sample(attacks, tm_attacks[a_index])
        cursor = cursor + a
    print("DEBUG: ending track's simulation")

# write to file the final result
with open("output.mid", 'wb') as outf:
    new_mid.writeFile(outf)
print("------- END -------")
