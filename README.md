# Decipher

decipher.py decrypts text which has been encrypted using a simple substitution cipher.
It uses a corpus which is a text file configurable by the user.  


## How to use:

The first run using a corpus
```
code/decipher.py -c <corpus_path> -e <encrypted_text_path> -d <decrypted_text_path>
```

Eg.
 ```
 ./code/decipher.py -c data/corpus-bartlebys.txt -e data/encrypted.txt  -d ./data/decrypted.txt
 ```

decipher.py assumes that the language of the corpus and the ciphered text are the same and that language uses spaces to segment words.

The first run without the -u flag will build a cache of the corpus so on subsequent runs this expensive step can be skipped. 

Use the -u flag on second or subsequent runs assuming you are using the same corpus.

```
code/decipher.py -c <corpus_path> -e <encrypted_text_path> -d <decryp
ted_text_path> -u 
```

## Other code
```
./code/download_test_data.py
```

Downloads a corpus of English texts in the public domain.  

It also used to encrypt test data. (A list of Yogi Berra quotes data/tests/test_quotes.txt )

```
./code/tests.py 
```










