#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, getopt
import re
import random
import string
from collections import Counter, OrderedDict
import json
import math
import codecs
import traceback

pathname = os.path.dirname(os.path.abspath(__file__))
 
UPPERCASE_ASCII = unicode(string.ascii_uppercase)
UPPERCASE_ASCII_SET = set(UPPERCASE_ASCII)
LOWERCASE_ASCII = unicode(string.ascii_lowercase)
LOWERCASE_ASCII_SET = set(LOWERCASE_ASCII)

data_directory = os.path.join(pathname,'../data/')
corpus_path = os.path.join(data_directory, 'corpus-en.txt')
encrypted_text_path = os.path.join(data_directory,'encoded-en.txt')
decrypted_text_path = os.path.join(data_directory,'decoded-en.txt')
cipher_table_path = os.path.join(data_directory,'cipher-table.txt')
corpus_cache_path = os.path.join(data_directory,'corpus_dict_cache.json')
use_corpus_cache = False


class Text(dict):
   """ Text: class serves as base class inherited by Corpus and Encrypted_Text classes to provide common methods to both
    
    Inherits from built-in dict class which will be used by Corpus
   """
   def __init__(self, path= None):
      self.filepath = path
      self.raw_text = None
      self.normalized_text = None
      self.letters_by_frequency = None
      self.trigrams = None
      if self.filepath:
         self.read_textfile()
         self.normalize_text()

   def read_textfile(self):
      """ Reads in text files and sets the raw_text attrivbute

      This assumes all text files are encoded in utf-8
      """
      self.raw_text = read_textfile(self.filepath, encoding="utf-8-sig")


   def translate(self, map, normalize= False):
      if not normalize:
         return self.raw_text.translate(map)
      else:
         return self.normalized_text.translate(map)



   def split_into_words(self):
      """ Split the normalized_text string on whitespace and common punctiation marks
      and return as a list of strings
      """

      list_of_words = re.split(ur'[\s\.\,\-]*', self.normalized_text, flags=re.UNICODE)
      return list_of_words

   def build_letter_frequency_list(self):
      """  Return a list of letters in order of frequency in the text
      """

      frequency_counter = Counter(list(self.normalized_text)).most_common()
      letters_by_frequency = OrderedDict(frequency_counter).keys()
      # this filters out punctuation, white spaces and numbers
      letters_by_frequency = filter(lambda x: x in UPPERCASE_ASCII, letters_by_frequency)
      missing_letters = list(build_missing_letters(''.join(letters_by_frequency)))
      self.letters_by_frequency = letters_by_frequency + missing_letters
   
   def divide_ngrams(self, n):
      """ Returns counter object 

      Divides the normalized text into ngrams of length n and creates counter 

      Parameters
      ----------
      n : integer
      size of ngrams to divide text into, required
      """
      return divide_ngrams(self.normalized_text, n)

   def normalize_text(self):
      """ Sets the normalized text attribute by normalizing the string in the raw_text attribute
      """
      self.normalized_text =  normalize_text(self.raw_text)
      return True

class Corpus(Text):
   """ Corpus Class inherits from the Text class which inherits from the built-in dict class
   
   Corpus provides various methods for scoring relevance of other texts to the corpus

   """
   def __init__(self, filepath, use_cache = False, cache_path = corpus_cache_path):
      """ Read in the corpus and create the letter frequency list and fill the word count dictionary
      """
      self.filepath = filepath
      self.total_count = 0
      self.corpus_dict = {}
      self.corpus_cache_path = cache_path
      self.read_corpus(use_cache)
      self.build_letter_frequency_list()

      for word, count in self.corpus_dict.iteritems():
         self[word] = int(count)
         self.total_count += int(count)

   def __call__(self, key):
      return self.score_one_word(self, key)

   def score_one_word(self, key):
      """ Returns a score calculated as the square of the length of the key
      times its count in the corpus

      Parameters
      ----------
      key : string
      Word searched for in corpus and used to score
      """
      if key in self:
         return float(self[key]) * len(key) *len(key)
      else:
         return 0.0

   def normalize_text(self):
      """
      "Non-words" are removed in the Corpus version.  Especially important for removing urls and filenames

      """
      self.normalized_text =  normalize_text(remove_nonwords(self.raw_text))
      return True

   def score_word_list(self, word_list):
      """ Returns a score by iteratating over the word list and totaling all word scores
  
      Parameters
      ----------
      word_list : list of strings
      List of words searched for in corpus and used to score
      """
      return sum(self.score_one_word(word) for word in word_list)

   def score_trigrams(self, ngram_list):
      """ Returns a score based on the ratio of trigrams that are present in the corpus
          the score is based on the base-10 log of this ratio and is used to boost other scores
  
      Parameters
      ----------
      ngram_list: list of strings
      List of ngrams searched for in corpus and used to score
      """
      if not ngram_list: return None
      total = 0
      for fragment in ngram_list:
         if self.trigrams.has_key(fragment):
            total += self.trigrams[fragment]
      return  math.log10(0.0001+total/ len(ngram_list) )

   def read_corpus(self, use_cache=False):
      """ Reads the corpus, cleans and normalizes the text, and creates the corpus word counter dictionary, 
          trigrams Counter.
          If the use_cache flag is on values are read from the cache
      
      Parameters
      ----------
      use_cache: Boolean
      Default is False
      """
      if use_cache:
         cache = read_json(self.corpus_cache_path)
         self.raw_text = cache['raw_text']
         self.normalized_text = cache['normalized_text']
         self.trigrams = cache['trigrams']
         text_dict = cache['text_dict'] 
         self.corpus_dict = text_dict
      else:
         cache = {}
         self.read_textfile()
         self.normalize_text()
         self.trigrams = self.divide_ngrams(3)
         text_dict = {} 
         text_list = self.split_into_words()
         for word in text_list:
            if text_dict.has_key(word):
               text_dict[word] += 1
            else:
               text_dict[word] = 1
         cache['trigrams'] = self.trigrams
         cache['raw_text'] = self.raw_text 
         cache['normalized_text'] = self.normalized_text
         cache['text_dict'] = text_dict
         if self.corpus_cache_path:  write_json(cache, self.corpus_cache_path)
         self.corpus_dict = text_dict

   def ratio_of_words_found(self, word_list):
      """ Returns a floating-point numeral, the ratio of words in the word list that are in the corpus
      
      Parameters
      ----------
      word_list : list of strings
      List of words searched for in corpus and used to calculate ratio
      """
      if not word_list: return None
      total = 0
      for word in word_list:
         if self.corpus_dict.has_key(word):
            total += 1.0
      return total/ len(word_list)

class Encrypted_Text(Text):
   """ Encrypted_Text Class inherits from the Text class which inherits from the built-in dict class
   
   Provides methods for translating the text as well as creating ngrams using translation table
   """
   def __init__(self, path):
      self.raw_text = None
      self.normalized_text = None
      self.list_of_strings = None
      self.filepath = path
      self.read_encrypted()
      self.build_letter_frequency_list()

   def read_encrypted(self):
      """ Reads in encrypted text file, normalizes text and creates list of encrypted words
      """
      self.read_textfile()
      self.normalize_text()
      list_of_strings = self.split_into_words()
      list_of_strings.sort(key=len, reverse=False)
      self.list_of_strings = list_of_strings
      return True

   def translate(self, translation_map, raw = True):
      """ Returns decrypted version of the encrypted text
      using the translation map

      Parameters
      ----------
      translation_map: Dictionary
      mapping table for decryption
      
      raw: Boolean flag
      True: translate the raw text
      Otherwise: translate the normalized text
      """
      if raw:  return self.raw_text.translate(translation_map)
      else: return self.normalized_text.translate(translation_map)

   def divide_ngrams(self, n, translation_map = None):
      """ Returns Counter object

      Divide sthe normalized text into ngrams of length n and creates counter of
      ngram frequency
      IF there is a translation map, then translate before dividing

      Parameters
      ----------
      n : integer
      size of ngrams to divide text into, required

      translation_map: Dictionary
      mapping table for decryption
      """
      if translation_map:
         return divide_ngrams(self.translate(translation_map), n)
      else:
         return divide_ngrams(self.normalized_text, n)

   def write_decrypted(self, translation_map, filepath):
      return write_file(self.translate(translation_map), filepath, encoding="utf-8-sig")
      

# BEGIN Global Functions

def write_file(text, filepath, encoding="utf-8-sig"):
   try:
      f = codecs.open(filepath, "w", encoding = encoding)
      f.write(text)
      f.close()  
      return True    
   except:
      print "Error writing file to %s" % filepath
      return False

def read_textfile(filepath, encoding="utf-8-sig"):
      """ Reads in text files and sets the raw_text attrivbute

      Default encoding is utf-8
      """
      try:
         with open(filepath) as text_file:
            return text_file.read().decode('utf-8-sig')
      except:
         print "Error reading %s " % self.filepath
         return None

def read_json(path):
   """ reads in json file 
   returns the data used for reading cached data
   returns None if error

   Parameters
   ----------
   path : text
   path of json file to read

   """
   try:
      with open(path) as json_file:
         data = json.load(json_file)
      return(data)
   except:
      print "error reading in json file %s" %path
      return None

def write_json(data, path):
   """ writes a json file of the data
   returns True if no error encountered when writing;
   False otherwise
   
   Parameters
   ----------
   data: text
   data to be serialized to json and saved.  
   nust be serializable type such as dict, list, string, etc.

   path : string
   path of json file to write

   """
   try:
      print 'trying to write to', path
      with open(path,'w') as json_file:
         data = json.dump(data, json_file)
      print 'JSON written to', path
      return True
   except:
      print 'Failure writing json to', path
      traceback.print_stack()
      return False


def make_dir(directory_path):
   """
   Returns True if directory is created
   Returns False if directory already exists

   Creates a directory.  This does not handle recursive directory creation.

   directory_path : string
   path of directory to be created
   """
   if not os.path.exists(directory_path):
      os.makedirs(directory_path)
      print "creating directory %s" % directory_path
      return True
   return False

def write_decryption_cipher(decrypt_map, filepath):
   buffer_lines = []
   for letter in LOWERCASE_ASCII:
      buffer_lines.append("%s -> %s" % (letter, letter.translate(decrypt_map) ))
   buffer = '\r\n'.join(buffer_lines)
   try:
      with open(filepath,'w') as file:
         file.write(buffer)
      print 'decryption cipher written', filepath
      return True
   except:
      print 'Failure writing decryption cipher to', filepath
      return False


def divide_ngrams(text, n):
   """ Returns Counter object pf frequency of ngrams

   Divides the normalized text into ngrams of length n and creates counter object
   
   adapted from from https://jeremykun.com/2012/02/03/cryptanalysis-with-n-grams/

   Parameters
   ----------
   text: string
   text to be split up into ngrams, required

   n : integer
   size of ngrams to divide text into, required
   """
   return Counter([text[i:i+n] for i in range(len(text) - (n-1))])

def build_missing_letters(text):
   """ Returns set of letters not contained in the text, normalized to capital letters

   Parameters
   ----------
   text: string
   text to be analyzed for missing letters

   """
   return UPPERCASE_ASCII_SET - set(list(text.upper()))

def remove_nonwords(text):
   """ Returns text with "non-words" removed.  Here non-words include any string with
    including numerals, or the the following punctionation marks .:_

    This means stand-alone numerals such as 1 or 1.2 will also be removed.

    Removal of strings will create multiple spaces in a row.   That is non-addressed by this 
    function.  

   Parameters
   ----------
   text: string
   text to be analyzed for missing letters

   """
   text = re.sub(ur'[\S]*[\.\:\_0-9]+[\S]*', '', text, flags=re.UNICODE|re.MULTILINE)
   return text

def normalize_text(text):
   """ Returns normalized text
   normalization includes the following
      1) all letters are capitalized
      2) removes numbers and punctuation which we aren't using for word splitting
      3) replaces punctuation and whitespace with a single space

      apostrophes are left in

   Parameters
   ----------
   text: string
   text to be normalized

   """
   text =  text.upper()
   text = re.sub(u"[^a-z,^A-Z,\s\.\,\-^'^’]", ' ', text, flags=re.UNICODE)
   text = re.sub(u"[\s,\.\|_]+",' ', text)
   text = re.sub(ur'([^\s\w])+', '',text)
   text = text.strip()
   return text

def filter_by_size(word_counts, word_length, top_n=None):
   """Returns counter object of freqeuncy counts of words, filtered by words of specified word_length
   and optionally returning top N words by frequency

   Parameters
   ----------
   word_counts: Counter object 
   Counter(dict) of words and their frequencies

   word_length: integer
   The length of words to filter counter object by

   top_n: integer, optional
   If specified, only the top N by frequency of the Counter object will be returned

   """
   return_counter = Counter({word: count for word, count in word_counts.iteritems() if (len(word) == word_length)})
   if top_n:
      most_common = [word_tuple[0] for word_tuple in return_counter.most_common(top_n)]
      return_counter = Counter({word: count for word, count in word_counts.iteritems() if (word in most_common)})
   return return_counter

def build_decrypt_map(input_list, output_list):
   """ returns translation table that is a mapping of 2 lists of letters, 
   Mapping is done in order of the letters in each list.  Assumes both lists are of uppercase letters.
   This function adds lowercase versions of those letters.

   Parameters
   ----------
   input_list:  list of single-character strings
   List of letters that are being mapped from

   output_list: list of single-character strings
   List of letters that will be mapped to

   """
   # http://stackoverflow.com/questions/1324067/how-do-i-get-str-translate-to-work-with-unicode-strings
   input_list = input_list + list(''.join(input_list).lower())
   output_list = output_list + list(''.join(output_list).lower())
   input_list_ords = [ord(char) for char in input_list]
   translate_table = dict(zip(input_list_ords, u''.join(output_list)))
   return translate_table

def build_list_unique_letters(text_list):
   """Returns list of unique characters in the list of strings

   Parameters:
   text_list: list of strings
   """
   return list(set(''.join(text_list)))

def shuffle_keys(key_list, base_list, candidates= None, base_candidates=None):
   """returns a copy of key_list after 2 letters have been shuffled
   
   If there is a candidates list and a base_candidates list then one character in the
   candidates list will be randomly selected from the base list to determine the first position in the
   key_list that will be swapped.  The base_candidates will be used to randomly select the from the base_list
   to determine the second position in key_list that will be swapped,. 

   Parameters
   ----------
   key_list: list of single-character strings, in order of encrypted part of decryption table
   candidates: list of single-character strings, the letters which are up for swapping
   base_list: list of single-character strings, in order for decrypted part of decryption table
   base_candidates: list of single-character strings

   """
   key_list_tmp = key_list [ : ]
   if base_list:
      candidates = build_list_unique_letters(candidates)
      [item1] = random.sample(candidates,1)
      index1 = base_list.index(item1)
      if base_candidates: 
         base_candidates = build_list_unique_letters(base_candidates)
         [item2] = random.sample(base_candidates,1)
         index2 = base_list.index(item2)
      else:
         [index2] = random.sample(range(len(base_list)), 1)
   else:
      raise ValueError('If a candidates list is passed in, then a base_list is also required')
   key_list_tmp[index1], key_list_tmp[index2] = key_list_tmp[index2], key_list_tmp[index1]
   return key_list_tmp

def score_decryption(corpus_obj, encrypted_text_obj, decrypt_map):
   """
   Returns a tuple containing two floating point numerals: 
       1) composite score and 2) the ratio of words found in the corpus

   The composite score is calculated as score by words found multiplied by the trigrams score

   See score_trigrams, score_word_list for details on how those scores are calculated

   Parameters
   ----------
   corpus_obj: object of Corpus class

   encrypted_text_obj: object of Encrypted_Text Class

   decrypt_map: translation table

   """
   decrypted_text_list =  [word.translate(decrypt_map) for word in encrypted_text_obj.list_of_strings] 
   trigrams = divide_ngrams(encrypted_text_obj.translate(decrypt_map, False),3)
   trigrams_boost = corpus_obj.score_trigrams(trigrams)
   ratio_of_words_found = corpus_obj.ratio_of_words_found(decrypted_text_list)
   composite_score = corpus_obj.score_word_list(decrypted_text_list) * trigrams_boost
   return composite_score, ratio_of_words_found

def build_decryption_tests(corpus_obj, encrypted_text_obj,config_list_of_tuples):
   """Returns a list of tuples
   Each tuple has 3 items:
     item 1: list of unique characters in the subset of the encrypted text strings we are working with
     item 2: list of unique characters in the subset of the corpus strings we are working with
     item 3: number of shuffles to be iterated through with the 2 lists of characters above

   Parameters
   ----------
   corpus_obj: object of Corpus class

   encrypted_text_obj: object of Encrypted_Text Class

   config_list_of_tuples: 
   """
   return_list = []
   for config_tuple in config_list_of_tuples:
      if config_tuple[0]:
         corpus_candidate_dict = filter_by_size(corpus_obj.corpus_dict,config_tuple[0], config_tuple[1])
         corpus_candidate_letters = build_list_unique_letters(corpus_candidate_dict.keys())
         cipher_candidate_dict = filter_by_size(Counter(encrypted_text_obj.list_of_strings),config_tuple[0])
         cipher_candidate_letters = build_list_unique_letters(cipher_candidate_dict.keys())
         number_of_shuffles = len(corpus_candidate_letters)*len(cipher_candidate_letters)*2
         return_list.append((cipher_candidate_letters,corpus_candidate_letters, number_of_shuffles))
      else:
         return_list.append((cipher_candidate_letters, None, math.pow(len(UPPERCASE_ASCII),2) ))
   return return_list

def decrypt(corpus_obj, encrypted_text_obj):
   """ Returns a tuple of:
          item 1: a dictionary of our best fitting decryption table 
          item 2: ratio of words in our decrypted text found in the corpus
      
      A best fit ratio over 0.95 will return out of the function witout further iterations
      This 0.95 ratio is hardcoded but should be made into a configurable parameter
   
   Parameters
   ----------
   corpus_obj: object of Corpus class

   encrypted_text_obj: object of Encrypted_Text Class
   """
   cypher_key_alphabet_list = encrypted_text_obj.letters_by_frequency 
   corpus_alphabet_list = corpus_obj.letters_by_frequency
   decrypt_map = build_decrypt_map(cypher_key_alphabet_list,corpus_alphabet_list)

   best_score, ratio_of_words_found = score_decryption(corpus_obj, encrypted_text_obj, decrypt_map)
   decryption_tests = build_decryption_tests(corpus_obj, encrypted_text_obj, [(1,2),(2,30),(3,30),(4,200),(5,300)])
   i = 0
   for decryption_test in decryption_tests:
      for t in range(decryption_test[2]):
         test_corpus_alphabet_list = shuffle_keys(corpus_alphabet_list[ : ], cypher_key_alphabet_list, decryption_test[0], decryption_test[1])
         test_decrypt_map = build_decrypt_map(cypher_key_alphabet_list, test_corpus_alphabet_list)
         score_test, ratio_of_words_found_test = score_decryption(corpus_obj, encrypted_text_obj, test_decrypt_map)
         if score_test > best_score:
            decrypt_map = test_decrypt_map
            best_score = score_test
            corpus_alphabet_list = test_corpus_alphabet_list
            ratio_of_words_found = ratio_of_words_found_test
            if ratio_of_words_found > 0.96:
               return decrypt_map, ratio_of_words_found
         i += 1
         if i % 1000 == 0: print "progress: ", encrypted_text_obj.translate(decrypt_map, False)[:50]     
   return decrypt_map, ratio_of_words_found

def run_decryption_iterations(encrypted_text_obj, corpus_obj, tolerance=0.98):   
   for i in range(200): 
      print "try # %d "  % (i+1)
      if i == 0:
         decrypt_map, ratio_of_words_found_best = decrypt(corpus_obj, encrypted_text_obj)
      else:
         decrypt_map_candidate, ratio_of_words_found_candidate = decrypt(corpus_obj, encrypted_text_obj)
         if ratio_of_words_found_candidate > ratio_of_words_found_best:
            decrypt_map = decrypt_map_candidate
            ratio_of_words_found_best = ratio_of_words_found_candidate
      if ratio_of_words_found_best > tolerance: 
         print "high ratio of recognized words: %.2f%% , breaking from loop: " % (ratio_of_words_found_best *100)
         return decrypt_map
         break
   return None

def main(argv):
   """ Corpus and encrypted text objects are created and we iterate of trials to find a decrytion key
   until a good fit is found.  This "good fit" is hardcoded to be over 95% of words in the decrypted text
   existing in the corpus.  It should be made into a configurable parameter

   200 trials will be performed if a good fit is not found and the best fit will be returned.
   The 200 trial limit is an arbitrary and has never been reached in testing.


   Parameters to set input and output file, all optional
   _______________________________________
    -c <corpus_path>  

    -e <encrypted_text_path> 

    -d <decrypted_text_path>  

    -u   
    If the u flag (usecache flag) is present the cached versions of parsed corpus data will be "u"sed instead of reparsing the corpus
    If not set then corpus data will be reparsed from raw corpus text

   """
   global corpus_path, corpus_cache_path, encrypted_text_path, decrypted_text_path, use_corpus_cache
   try:
      opts, args = getopt.getopt(sys.argv[1:], 'hc:e:d:u', ["corpus=","encrypted=","decrypted=","use_cache"])
   except getopt.GetoptError:
      print 'decipher.py -c <corpus_path> -e <encrypted_text_path> -d <decrypted_text_path> -u '
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print 'decipher.py -c <corpus_path> -e <encrypted_text_path> -d <decrypted_text_path> -u '
         sys.exit()
      elif opt in ("-e", "--encrypted"):
         encrypted_text_path = arg
      elif opt in ("-d", "--decrypted"):
         decrypted_text_path = arg
      elif opt in ("-c", "--corpus"):
         corpus_path = arg
      elif opt in ("-u", "--useCache"):
         use_corpus_cache = True

   make_dir(data_directory)

   encrypted_text_obj = Encrypted_Text(encrypted_text_path)
   corpus_obj = Corpus(corpus_path, use_corpus_cache)
   decrypt_map = run_decryption_iterations(encrypted_text_obj, corpus_obj)

   if decrypt_map:
      print encrypted_text_obj.translate(decrypt_map)
      encrypted_text_obj.write_decrypted(decrypt_map, decrypted_text_path) 
      write_decryption_cipher(decrypt_map, cipher_table_path )
   else:
      print "unsuccessful decryption"
 

if __name__ == "__main__":
    main(sys.argv)