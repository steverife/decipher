#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import decipher

import os, shutil, sys, random
from collections import Counter

TEST_DATA_DIR = 'tmp_tests'


def build_test_dir_path():
   pathname = os.path.dirname(os.path.abspath(__file__))
   test_data_path = os.path.join(pathname,TEST_DATA_DIR)
   return test_data_path


def setup():
   """ setup() sets up the environment
   this should be executed before tests are performed

   the test data directory is deleted so that making a directory can be tested

   """
   test_data_path = build_test_dir_path()
   if os.path.exists(test_data_path):
   	  shutil.rmtree(test_data_path)
   	  print "deleted directory %s" % test_data_path



class TestDecipherMethods(unittest.TestCase):
   # 
   '''
build_decryption_tests
decrypt
score_decryption
write_decryption_cipher

   '''
   def test_build_decrypt_map(self):
      actual_result = decipher.build_decrypt_map(['Y','Q','I','D'],['W','H','E','N'])
      expected_result = {100: u'n', 68: u'N', 81: u'H', 73: u'E', 113: u'h', 105: u'e', 121: u'w', 89: u'W'}
      self.assertEqual(actual_result, expected_result)

   def test_build_list_unique_letters(self):
      result = decipher.build_list_unique_letters(['test','one'])
      result.sort()
      self.assertEqual(result, ['e', 'n', 'o', 's', 't'])

   def test_remove_nonwords(self):
	  test_string = decipher.remove_nonwords('Test https://www.wikipedia.org test,one two file.txt 2.2')
	  expected_result = 'Test  test,one two  '
	  self.assertEqual(decipher.remove_nonwords(test_string), expected_result)

   def test_normalize_text(self):
   	  test_string = u'TEST 2 test.html comma,comma   under_under pipe|pipe'
   	  expected_result = u'TEST TEST HTML COMMA COMMA UNDER UNDER PIPE PIPE'
   	  self.assertEqual(decipher.normalize_text(test_string), expected_result)

   def test_divide_ngrams_2(self):
      test_string = 'test'
      expected_result = {'te': 1, 'es': 1, 'st': 1}
      self.assertEqual(dict(decipher.divide_ngrams(test_string,2)), expected_result)

   def test_divide_ngrams_3(self):
      test_string = 'test'
      expected_result = {'tes': 1, 'est': 1}
      self.assertEqual(dict(decipher.divide_ngrams('test',3)), expected_result)

   def test_make_dir(self):
   	  test_data_path = build_test_dir_path()
   	  decipher.make_dir(test_data_path)
   	  expected_result = True
   	  actual_result = os.path.exists(test_data_path)
   	  self.assertEqual(actual_result,expected_result)

   def test_json_read_write(self):
   	  test_data_dir = build_test_dir_path()
   	  test_data_path = os.path.join(test_data_dir,'test.json')
   	  decipher.make_dir(test_data_dir)
   	  test_dict = {'a':1,u'日本語':3}
   	  decipher.write_json(test_dict, test_data_path)
   	  result = decipher.read_json(test_data_path)
   	  self.assertEqual(test_dict, result)

   def test_filter_by_size(self):
   	  test_data= Counter({'one':1, 'two':33, 'three':2})
   	  result = decipher.filter_by_size(test_data,3)
   	  expected_result = Counter({'one':1, 'two':33})
   	  self.assertEqual(result, expected_result) 

   def test_shuffle_keys(self):
   	  key_list = ['a','b','c','d','e']
   	  candidates = ['a']
   	  base_list = ['b', 'c', 'd', 'e','a']
   	  base_candidates = ['d','e'] 
   	  expected_result = ['d', 'b', 'c', 'a','e']
   	  actual_result = decipher.shuffle_keys(key_list,base_list,candidates,base_candidates)
   	  
   	  self.assertTrue(actual_result[base_list.index('a')] in ['c','d']) 

   def test_divide_ngrams(self):
      actual_result = decipher.divide_ngrams('huehuetenango', 3)
      expected_result = Counter({'hue': 2, 'ehu': 1, 'ueh': 1, 'ten': 1, 'ena': 1, 'ngo': 1, 'nan': 1, 'ang': 1, 'ete': 1, 'uet': 1})
      self.assertEqual(actual_result, expected_result)

   def test_build_missing_letters(self):
      text = 'A bird in the hand is worth two in the bush.  Zebras, yaks and cougars.'
      expected_result = set([u'F', u'J', u'M', u'L', u'Q', u'P', u'V', u'X'])
      actual_result = decipher.build_missing_letters(text)
      self.assertEqual(actual_result, expected_result) 

class TestEncryptedTextObjectMethods(unittest.TestCase):
   def setUp(self):
       self.encrypted_text_obj = decipher.Encrypted_Text(os.path.join(decipher.data_directory,'tests','test_quotes.txt-123'))

   '''
   read_encrypted
   read_textfile

   '''
   def test_build_letter_frequency_list(self):
       actual_result = self.encrypted_text_obj.letters_by_frequency[:5]
       expected_result = [u'I', u'K', u'R', u'V', u'Z']
       self.assertEqual(actual_result, expected_result) 

   def test_split_into_words(self):
       actual_result = self.encrypted_text_obj.split_into_words()
       actual_result = actual_result[:5]
       expected_result = [u'YQID', u'CRA', u'HRUI', u'KR', u'Z']
       self.assertEqual(actual_result, expected_result) 

   def test_translate(self):
       translate_map =  decipher.build_decrypt_map(['Y','Q','I','D'],['W','H','E','N'])
       actual_result = self.encrypted_text_obj.translate(translate_map, raw = False)
       actual_result = actual_result[:4]
       expected_result = 'WHEN'
       self.assertEqual(actual_result, expected_result) 


if __name__ == '__main__':
   setup()
   unittest.main()
