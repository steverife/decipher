#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests, requests_cache
import lxml.html
from HTMLParser import HTMLParser
import os, codecs
from urlparse import urljoin
import re
import time
import decipher as dc
import random, string

pathname = os.path.dirname(os.path.abspath(__file__))
data_directory = os.path.join(pathname,'../data/tests/')
test_corpus = os.path.join(data_directory,'test_corpus.txt')
tests_cache = os.path.join(data_directory,'tests_cache')
test_text_unencoded = os.path.join(data_directory,'test_quotes.txt')

requests_cache.install_cache(tests_cache)

LINK_URLS = ['http://www.bartleby.com/hc/', 'http://www.bartleby.com/237/', 'http://www.bartleby.com/fiction/','http://www.bartleby.com/185/']
BARTLEBY_GENERAL_LINK_PATTERN = re.compile(r'(http://www.bartleby.com/[0-9]+/[0-9]+[\S]*)')
BARTLEBY_BOOK_LINK_PATTERN = re.compile(r'(http://www.bartleby.com/[0-9]+/[0-9]+[/]?)$')
BARTLEBY_CHAPTER_LINK_PATTERN = re.compile(r'(http://www.bartleby.com/[0-9]+/[0-9\/]+\.html)$')
BARTLEBY_BOOK_BODY_PATTERN = re.compile(r'BEGIN CHAPTER -->(.*)<!-- END CHAPTER',flags=re.MULTILINE| re.DOTALL)

urls_visited = []
chapter_links = []
book_links = []

#  build_decrypt_map([u'\x92',u'\x93',u'\x94', u'\xa0'],[u"'",u'"',u'"',u' '])
punctuation_map = {160: u' ', 146: u"'", 147: u'"', 148: u'"'}


def encode_test_text(path = test_text_unencoded, seed=None):
   unencoded_text = dc.Text(test_text_unencoded)
   uppercase_letters_list = list(unicode(string.ascii_uppercase))
   if seed: 
      random.seed(seed)
      shuffled_letters_list = uppercase_letters_list[:]
      random.shuffle(shuffled_letters_list)
      translation_map = dc.build_decrypt_map(uppercase_letters_list,shuffled_letters_list)
      encoded_text = unencoded_text.translate(translation_map)
      write_text(encoded_text, '-'.join([test_text_unencoded,str(seed)]))

def get_text_from_url(url):
   global urls_visited
   if not url in urls_visited:
      try:
         resp = requests.get(url)
         urls_visited.append(url)
         if not resp.from_cache:  
            time.sleep(2)
            print 'not from cache', url
         else:
            print 'from cache', url
         return resp.text
      except:
      	 time.sleep(10)
      	 print "skipping %s " % url 
   else:
   	  print 'already visited'
   return ''

def get_test_corpus_links(url, pattern, text= None):
   link_list = []
   if not text:
      text = get_text_from_url(url)
   if text:
      dom =  lxml.html.fromstring(text)
      for link in dom.xpath('//a/@href'):
   	     if not link.startswith('http'):
   	  	    absolute_link = urljoin(url, link)
   	  	    matched = pattern.match(absolute_link)
   	  	    if matched:
   	  	 	   absolute_link = matched.group(1)
   	  	 	   if not absolute_link in link_list:
   	  	 	      link_list.append(absolute_link)
   	  	 	      print "found link %s" % absolute_link
   return link_list

def normalize_text(text):
   text = HTMLParser().unescape(text).translate(punctuation_map)# replace html encoded apostrophe
   return text

def get_book_and_parse(url, chapter_pattern=None):
   text = get_text_from_url(url) 
   pattern_hit = chapter_pattern.search(text)
   text = pattern_hit.group(1)
   document = lxml.html.document_fromstring(text)
   text = document.text_content()
   text = normalize_text(text)
   try:
      text = pattern_hit.group(1)
      document = lxml.html.document_fromstring(text)
      text = document.text_content()
      text = normalize_text(text)
      return text
   except:
      print 'get_book_and_parse error'
      document = lxml.html.document_fromstring(text)
      text = document.text_content()
      return ''

def write_text(text, filepath):
	f = codecs.open(filepath, "w", encoding="utf-8-sig")
	f.write(text)
	f.close()  

def is_chapter_link(link):
	return True if BARTLEBY_CHAPTER_LINK_PATTERN.match(link) else False

def is_book_link(link):
	return True if BARTLEBY_BOOK_LINK_PATTERN.match(link) else False

			
def download_corpus():
   # links = get_test_corpus_links(LINKS_URL, BARTLEBY_BOOK_LINK_PATTERN)
   buffer_list = []
   links = []
   book_links = []
   for link in LINK_URLS:
   	  if not is_book_link(link):
   	  	 links += get_test_corpus_links(link, BARTLEBY_GENERAL_LINK_PATTERN)
   	  else:
   	  	 book_links.append(link)  
   book_links += [link for link in links if is_book_link(link)]
   book_links = list(set(book_links))
   print 'book_links', book_links
   for link in book_links:
   	  print "parsing", link
   	  links += get_test_corpus_links(link, BARTLEBY_GENERAL_LINK_PATTERN)
   chapter_links = [link for link in links if is_chapter_link(link)]
   chapter_links = list(set(chapter_links))
   print 'chapter_links', chapter_links
   links_count = len(chapter_links)
   for i in range(links_count):
   	  link = chapter_links[i]
   	  print i, links_count, link
   	  buffer_list.append("*** from %s ****" % link)
   	  buffer_list.append("")
   	  buffer_list.append(get_book_and_parse(link, BARTLEBY_BOOK_BODY_PATTERN))
   	  buffer_list.append("")
   write_text('\n\r'.join(buffer_list), test_corpus)

def main():
   download_corpus()
   seeds = [123, 23556, 455454, 55555]
   for seed in seeds:
      encode_test_text(test_text_unencoded, seed= seed)


if __name__ == "__main__":
   main()



