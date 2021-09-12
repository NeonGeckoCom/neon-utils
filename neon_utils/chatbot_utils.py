from autocorrect import Speller
from nltk.translate.bleu_score import sentence_bleu
from nltk import word_tokenize


def find_closest_answer(algorithm: str = 'random', sentence: str = None, options: dict = None):
    """
        Handles an incoming shout into the current conversation
        :param algorithm: algorithm considered
        :param sentence: base sentence
        :param options: options to pick best one from
    """
    if not sentence:
        LOG.warning('Empty sentence supplied')
        return sentence
    if not options or len(options.keys()) == 0:
        LOG.warning('No options provided')
        return sentence
    if algorithm == 'random':
        closest_answer = random.choice(options)
    elif algorithm == 'bleu_score':
        bleu_scores = []
        response_tokenized = word_tokenize(sentence.lower())
        for option in options.keys():
            opinion_tokenized = word_tokenize(options[option].lower())
            if len(opinion_tokenized) > 0:
                if min(len(response_tokenized), len(opinion_tokenized)) < 4:
                    weighting = 1.0 / min(len(response_tokenized), len(opinion_tokenized))
                    weights = tuple([weighting] * min(len(response_tokenized), len(opinion_tokenized)))
                else:
                    weights = (0.25, 0.25, 0.25, 0.25)
                bleu_scores.append(
                    (option, sentence_bleu([response_tokenized], opinion_tokenized, weights=weights)))
        max_score = max([x[1] for x in bleu_scores]) if len(bleu_scores) > 0 else 0
        closest_answer = random.choice(list(filter(lambda x: x[1] == max_score, bleu_scores)))[0]
        LOG.info(f'Closest answer is {closest_answer}')
    elif algorithm == 'damerau_levenshtein_distance':
        closest_distance = None
        closest_answer = None
        try:
            for option in options.items():
                distance = jellyfish.damerau_levenshtein_distance(option[1], sentence)
                if not closest_distance or closest_distance > distance:
                    closest_distance = distance
                    closest_answer = option[0]
            LOG.info(f'Closest answer is {closest_answer}')
        except Exception as e:
            LOG.error(e)
    else:
        LOG.error(f'Unknown algorithm supplied:{algorithm}')
        return sentence
    return closest_answer


def grammar_check(func):
    """
    Checks grammar for output of passed function
    :param func: function to consider
    """
    spell = Speller()

    def wrapper(*args, **kwargs):
        LOG.debug("Entered decorator")
        output = func(*args, **kwargs)
        if output:
            LOG.debug(f"Received output: {output}")
            output = spell(output)
            LOG.debug(f"Processed output: {output}")
        return output

    return wrapper