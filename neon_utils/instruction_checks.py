# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2022 Neongecko.com Inc.
# Contributors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3 License
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from word2number import w2n
from neon_utils.logger import LOG
import re

LOG.warning("This module will be deprecated in neon_utils 1.0.0")


class Check:
    """

    Parameters:
        question_id (int): number of question in instructions
        prev_answer (str): user's previous answer
        question (str): current question from instructions according to question_id
        answer_list (list): list of all user's answers during instructions handling

    """
    def __init__(self, question_id: int, prev_answer: str, question: str, answer_list: list):
        self.question_id = int(question_id)
        self.prev_answer = prev_answer
        self.question = question
        self.answer_list = answer_list


    def answer_num_range(self, answer: str):
        """
        Converts word to number in user's answer
        Sums digits if there are several of them in the answer
        Checks that number is in range (1,10)
        if condition is satisfied: adding +1 to the question id

        Parameters:
            answer (str): user's answer

        Return:
            if condition is satisfied: question_id (int), numbers (int)
            else: question_id (int), numbers (int)
            on ValueError: question_id (int), answer (str)

        """
        try:
            numbers = w2n.word_to_num(answer)
            LOG.info('numbers: '+str(numbers))
            if numbers in range(1, 11):
                return self.question_id+1, numbers
            else:
                return self.question_id, numbers
        except ValueError:
            LOG.info('no numbers in the answer')
            return self.question_id, answer


    def is_even_number(self, answer: str):
        """
        Converts word to number in user's answer
        Sums digits if there are several of them in the answer
        Checks that number is an even number
        if condition is satisfied:  return next question id

        Parameters:
            answer (str): user's answer

        Return:
            if condition is satisfied: question_id (int), numbers (int)
            else: question_id (int), numbers (int)
            on ValueError: question_id (int), answer (str)

        """
        try:
            numbers = w2n.word_to_num(answer)
            if numbers >= 2 and (numbers % 2) == 0:
                return self.question_id+1, numbers
            else:
                return self.question_id, numbers
        except ValueError:
            LOG.info('no numbers in the answer')
            return self.question_id, answer


    def is_number(self, answer: str):
        """
        Converts word to number in user's answer
        Sums digits if there are several of them in the answer
        If there is no numbers in the string raises ValueError
        Else returns next question id

        Parameters:
            answer (str): user's answer

        Return:
            if there are numbers in the user's answer: question_id (int), numbers (int)
            on  ValueError: question_id (int), answer (str)

        """
        try:
            numbers = w2n.word_to_num(answer)
            return self.question_id+1, numbers
        except ValueError:
            LOG.info('no numbers in the answer')
            return self.question_id, answer


    def not_empty(self, answer: str):
        """
        Checks that yser's answer is not an empty string
        if condition is satisfied:  return next question id

        Parameters:
            answer (str): user's answer

        Return:
                question_id (int): current question_id or next question_id
                answer (str): user's current answer
        """

        if str(answer) != '':
            return self.question_id+1, answer
        else:
            return self.question_id, answer


    def replace_question(self):
        """
        replaces the word REPLACE in the question
        with the word from previous user's answer

        Return:
            new_question (str): transformed question for skill to ask
        """

        LOG.info("User's previous answer: "+str(self.prev_answer))
        new_question = re.sub('REPLACE', str(self.prev_answer), str(self.question))
        return new_question


    def check_answer(self, answer: str):
        """
        Converts word to number in user's answer
        Sums digits if there are several of them in the answer
        Checks that number from the answer dived by 2 equals numbers from user's answer #2
        if condition is satisfied:  return next question id (question_id+1)
        else: return  question_id+2

        Parameters:
            answer (str): user's answer

        Return:
            question_id (int), numbers (int)
            on ValueError: question_id (int), answer (str)
        """

        try:
            answer_2 = 1
            numbers = w2n.word_to_num(answer)
            for answer in self.answer_list:
                if answer[0] == 2:
                    answer_2 = answer[1]/2
                if numbers == answer_2:
                    return self.question_id+1, numbers
                else:
                    return self.question_id+2, numbers
        except ValueError:
            LOG.info('no numbers in the answer')
            return self.question_id+2, answer
