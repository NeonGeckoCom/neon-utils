

def clean_quotes(raw_utt):
    """
    Method for stripping quotes from fully quoted strings in different languages
    :param raw_utt: Input string to be cleaned
    :return: string with all paired quote characters removed
    """
    chars_to_remove = ['“', '"', '«', u'\u201d', u'\u00bb', u'\u201e', '「', '」', u'u\xa0', u'\u00a0']
    raw_utt = raw_utt.strip()
    # LOG.debug(f"clean_utterance({raw_utt})")
    utt = raw_utt
    trailing_punctuation = False
    if utt.endswith("."):
        trailing_punctuation = True
        utt = utt.rstrip(".")
    quotes_cleaned = False
    try:
        # Checks if utterance starts AND ends with some form of quotations and removes them accordingly
        while (utt.startswith('“') or utt.startswith(u'\u201d') or utt.startswith('"') or utt.startswith('«')
               or utt.startswith(u'\u00bb') or utt.startswith(u'\u201e') or utt.startswith('「') or
               utt.startswith(u'u\xa0') or utt.startswith(u'\u00a0')) and \
                (utt.endswith('“') or utt.endswith(u'\u201d') or utt.endswith('"') or utt.endswith(u'\u00bb') or
                 utt.endswith(u'\u201e') or utt.endswith('」') or utt.endswith(u'u\xa0') or
                 utt.endswith(u'\u00a0') or utt.endswith('»')):
            # LOG.debug("DM: Handling Quotations")
            quotes_cleaned = True
            removed_left, removed_right = False, False
            for c in chars_to_remove:
                if not removed_left and utt.startswith(c):
                    utt = utt[1:]
                    removed_left = True
                if not removed_right and utt.endswith(c):
                    utt = utt[:-1]
                    removed_right = True
            # utt = raw_utt.lstrip('“').lstrip(u'\u201d').lstrip('"').lstrip('«') \
            #     .lstrip(u'\u00bb').lstrip(u'\u201e').rstrip('“').rstrip(u'\u201d').rstrip('"').rstrip('«') \
            #     .rstrip(u'\u00bb').rstrip(u'\u201e')
        # else:
        #     utt = raw_utt
        # LOG.debug(f"DM: {utt}")
        if quotes_cleaned:
            if trailing_punctuation:
                return f"{utt}."
            return utt
        else:
            return raw_utt
    except Exception as x:
        print(x)
        return raw_utt
