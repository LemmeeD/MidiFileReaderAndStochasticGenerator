import mido
import numpy as np
from mido import Message, MidiFile, MidiTrack
from mido import MetaMessage
from mido import bpm2tempo
from utils import gen_utils
from utils import midi_utils
from model import uniformized_dtmc


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
# filepath = "tabs_&_midis/moonlight_sonata.mid"
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
print("<filename="+filepath+", type="+str(mid.type)+", ticks_per_beat="+str(mid.ticks_per_beat)+", num_of_tracks="+str(num_of_tracks)+", bpm="+str(bpm)+", time_signature="+str(num)+"/"+str(den)+">")

# 'cleaning'
mid = midi_utils.clean_duplicate_tracks(mid)
num_of_tracks = len(mid.tracks)
print("DEBUG: num_of_tracks after cleaning duplicates =", num_of_tracks)
tracks = midi_utils.remove_meta_track(mid.tracks)
num_of_tracks = len(tracks)
print("DEBUG: num_of_tracks after removing 'meta' tracks =", num_of_tracks)

# instantiating new midi file
new_midi = MidiFile(type=original_midi_type, ticks_per_beat=ticks_per_beat)
meta_track = MidiTrack()
meta_track.append(MetaMessage('set_tempo', tempo=bpm2tempo(bpm), time=0))
meta_track.append(MetaMessage('time_signature', numerator=num, denominator=den, time=0))
new_midi.tracks.append(meta_track)

# analysis and simulation per track
for i, track in enumerate(tracks):
    print("DEBUG: ******** PARSING track "+str(i+1)+"/"+str(len(tracks))+" ********")
    pitches_sequence = []
    durations_sequence = []
    instrument = midi_utils.get_first_instrument_set_of_track(track)

    for j, msg in enumerate(track):
        # get notes pitch
        if isinstance(msg, mido.messages.messages.Message) and msg.type == 'note_on' and msg.velocity > 0:
            pitches_sequence.append(msg.note)
            # get duration of note
            durations_sequence.append(midi_utils.parse_note_duration(msg, j, track, ticks_per_beat, as_ticks=True))

    # removing duplicates
    #pitches_sequence = gen_utils.remove_None_elements_from_list(pitches_sequence)
    #durations_sequence = gen_utils.remove_None_elements_from_list(durations_sequence)
    pitches = gen_utils.remove_duplicates_from_list(pitches_sequence)
    durations = gen_utils.remove_duplicates_from_list(durations_sequence)

    # time unit
    dt = np.amin(durations)

    # setting the framework
    Q = np.zeros((len(pitches), len(pitches)))
    occurrences = np.zeros((len(pitches), len(pitches), len(pitches_sequence)))     # of q_ij
    for j in range(len(pitches_sequence)-1):
        current_pitch = pitches_sequence[j]
        index_current_pitch = pitches.index(current_pitch)
        next_pitch = pitches_sequence[j+1]
        index_next_pitch = pitches.index(next_pitch)
        duration_current_pitch = durations_sequence[j]      # in dt units of time
        if current_pitch == next_pitch:
            durations_sequence[j+1] += durations_sequence[j]
        else:
            third_dim_index = gen_utils.find_first_uninitialized_element_index(occurrences[index_current_pitch, index_next_pitch, :])
            occurrences[index_current_pitch, index_next_pitch, third_dim_index] = dt / duration_current_pitch       #occurrences[index_current_pitch, index_next_pitch, :]
    # weighted average of all q_ij per transition
    for j in range(len(pitches)):
        for l in range(len(pitches)):
            if l != j:
                sum = 0
                count = 0
                for k in range(len(pitches_sequence)):
                    if occurrences[j, l, k] != 0:
                        sum = sum + occurrences[j, l, k]
                        count = count + 1
                if count == 0:
                    Q[j, l] = 0
                else:
                    Q[j, l] = sum / count
    # Q[j, j] = -exit_rate
    for j in range(Q.shape[0]):
        row_tot = 0
        for l in range(Q.shape[1]):
            row_tot += Q[j, l]
        Q[j, j] = - row_tot
    PI = uniformized_dtmc.get_uniformized_transition_matrix(Q)

    # initial probabilities: the idea is to start from the same note of the original file. That means taking the first transition in the sequence
    initial_p = np.zeros(len(pitches)).tolist()
    initial_p[pitches.index(pitches_sequence[0])] = 1       # initial_p[0] = 1 directly
    initial_d = np.zeros(len(durations)).tolist()
    initial_d[0] = 1

    # setting track
    new_track = MidiTrack()
    new_track.append(MetaMessage('track_name', name="track_"+str(i), time=0))
    new_track.append(Message('program_change', program=instrument, time=0))

    # simulation
    last_note_pitch = pitches_sequence[0]
    index_p0 = pitches.index(last_note_pitch)
    t = 0
    x, index_x = uniformized_dtmc.sample_from_uniformized_transition_matrix(pitches, initial_p)
    new_track.append(Message('note_on', note=x, velocity=100, time=0))
    last_event_time = t
    while t < T* midi_utils.get_ticks_per_measure(ticks_per_beat, num, den):
        t = t + dt
        x, index_x = uniformized_dtmc.sample_from_uniformized_transition_matrix(pitches, PI[index_x, :])
        if x != last_note_pitch:
            new_track.append(Message('note_off', note=last_note_pitch, velocity=100, time=t-last_event_time))
            new_track.append(Message('note_on', note=x, velocity=100, time=0))
            last_event_time = t
            last_note_pitch = x

    new_track.append(MetaMessage('end_of_track', time=t))
    new_midi.tracks.append(new_track)
    print("DEBUG: ending track's simulation")

# write to file the final result
new_midi.save('output.mid')
print("------- END -------")
