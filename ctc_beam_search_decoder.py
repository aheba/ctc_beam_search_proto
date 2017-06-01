## This is a prototype of ctc beam search decoder

import copy
import random
import numpy as np

# vocab = blank + space + English characters
#vocab = ['-', ' '] + [chr(i) for i in range(97, 123)]

vocab = ['-', '_', 'a']

def ids_str2list(ids_str):
    ids_str = ids_str.split(' ')
    ids_list = [int(elem) for elem in ids_str]
    return ids_list

def ids_list2str(ids_list):
    ids_str = [str(elem) for elem in ids_list]
    ids_str = ' '.join(ids_str)
    return ids_str

def ids_id2token(ids_list):
    ids_str = ''
    for ids in ids_list:
	ids_str += vocab[ids]
    return ids_str

def ctc_beam_search_decoder(
    input_probs_matrix,
    beam_size,
    max_time_steps=None,
    lang_model=None,
    alpha=1.0,
    beta=1.0,
    blank_id=0,
    space_id=1,
    num_results_per_sample=None):

    '''
    beam search decoder for CTC-trained network, called outside of the recurrent group. 
    adapted from Algorithm 1 in https://arxiv.org/abs/1408.2873.

    param input_probs_matrix: probs matrix for input sequence, row major
    type input_probs_matrix: 2D matrix. 
    param beam_size: width for beam search
    type beam_size: int
    max_time_steps: maximum steps' number for input sequence, <=len(input_probs_matrix)
    type max_time_steps: int
    lang_model: language model for scoring
    type lang_model: function

    ......

    '''
    if num_results_per_sample is None:
        num_results_per_sample = beam_size
    assert num_results_per_sample <= beam_size
	
    if max_time_steps is None:
        max_time_steps = len(input_probs_matrix)
    else:
        max_time_steps = min(max_time_steps, len(input_probs_matrix))
    assert  max_time_steps > 0
    
    vocab_dim = len(input_probs_matrix[0])
    assert blank_id < vocab_dim
    assert space_id < vocab_dim
    
    ## initialize 
    start_id = -1
    # the set containing selected prefixes 
    prefix_set_prev = {str(start_id):1.0}
    probs_b, probs_nb = {str(start_id):1.0}, {str(start_id):0.0}

    ## extend prefix in loop 
    for time_step in range(max_time_steps):
        # the set containing candidate prefixes
        prefix_set_next = {}
        probs_b_cur, probs_nb_cur = {}, {}
        for (l, prob_) in prefix_set_prev.items():
            prob = input_probs_matrix[time_step]

            # convert ids in string to list
            ids_list = ids_str2list(l)
            end_id = ids_list[-1]
            if not probs_b_cur.has_key(l):
                probs_b_cur[l], probs_nb_cur[l] = 0.0, 0.0

            # extend prefix by travering vocabulary
            for c in range(0, vocab_dim):
                if c == blank_id:
	            probs_b_cur[l] += prob[c] * (probs_b[l] + probs_nb[l])
		else:
	            l_plus = l + ' ' + str(c)
                    if not probs_b_cur.has_key(l_plus):
                        probs_b_cur[l_plus], probs_nb_cur[l_plus] = 0.0, 0.0

		    if c == end_id:
		        probs_nb_cur[l_plus] += prob[c] * probs_b[l]
			probs_nb_cur[l] += prob[c] * probs_nb[l]
                    elif c == space_id:
                        lm = 1.0 if lang_model is None \
                               else np.power(lang_model(ids_list), alpha)
                        probs_nb_cur[l_plus] +=  lm * prob[c] * (probs_b[l]+probs_nb[l])
                    else:
                        probs_nb_cur[l_plus] += prob[c] * (probs_b[l]+probs_nb[l])
                    # add l_plus into prefix_set_next
                    prefix_set_next[l_plus] = probs_nb_cur[l_plus]+probs_b_cur[l_plus]
            # add l into prefix_set_next
            prefix_set_next[l] = probs_b_cur[l]+probs_nb_cur[l]
        # update probs
        probs_b, probs_nb = copy.deepcopy(probs_b_cur), copy.deepcopy(probs_nb_cur)
        
        ## store top beam_size prefixes 
	prefix_set_prev = sorted(prefix_set_next.iteritems(), 
                                key = lambda asd:asd[1], 
                                reverse=True)
	if beam_size < len(prefix_set_prev):
	    prefix_set_prev = prefix_set_prev[:beam_size]
	prefix_set_prev = dict(prefix_set_prev)
    
    beam_result = []
    for (seq, prob) in prefix_set_prev.items():
        if prob > 0.0:
            ids_list = ids_str2list(seq)
            log_prob = np.log(prob)
	    beam_result.append([log_prob, ids_list[1:]])

    ## output top beam_size decoding results
    beam_result = sorted(beam_result, 
                        key = lambda asd:asd[0], 
                        reverse=True)
    if num_results_per_sample < beam_size:
        beam_result = beam_result[:num_results_per_sample]
    return beam_result
				
def language_model(input):
    # TODO
    return random.uniform(0, 1)

def simple_test():

    input_probs_matrix = [[0.1, 0.3, 0.6],
                          [0.2, 0.1, 0.7],
                          [0.5, 0.2, 0.3]]

    beam_result = ctc_beam_search_decoder(
			input_probs_matrix=input_probs_matrix,
			beam_size=20,
                        blank_id=0,
                        space_id=1,
			)

    print "\nbeam search output:"
    for result in beam_result:
        print("%6f\t%s"%(result[0], ids_id2token(result[1])))

if __name__ == '__main__':
	simple_test() 
