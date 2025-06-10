# UPDATE THE DICTIONARY

## THINGS TO DO
1. Define postings
    - contains `doc_id`
    - `__repr__`
    - `<`, `>` and `==` comparisons with `@total_ordering`
    - ``from_corpus``: given docID get the document
2. Define postings list
    - create with `@classmethod`, constructor for different initialzation methods.
    - contain DocID of documents ordered by DocID
    - `AND`, `OR` and `NOT` functions
    - retrieve content from postings
3. Define terms
    - `term` contain term and `posting_list`
    - merge if terms are same
    - Unique word in the document
    - ordered by alphabetical order
    - print term followed by list of docIDs.
4. Inverted index:
    - b-tree or trie of terms.
    - `get`, `__repr__` and constructor
    - normalize (punctuation removal) and tokenize (break into words)
    - save to disk to save space
4. Corpus reader
    - based on the documents break into title and description
4. Scan the documents
5. Merge lists
    - update when grows too big

## WRTIE A BOOLEAN IR SYSTEM + PHRASE QUERIES
- IR system answers to boolean queries
- AND, OR, NOT
- phrase queries (maybe wildcard)
- normalization and stemming
- spelling correction

### Boolean retrieval
`t1 AND t2` for the intersection and `t1 OR t2` for intersection.  
Return all documents containing the terms in the query

### Inverted Index
Adjacency list: for each term the documents that contain it:
1. For each document extract terms
2. Tag each term with the DocID
3. Sort the terms in alphabetical order
4. Group terms and merge posting lists

With `AND` compare posting lists comparing the first element and then increas until you find a match in both and continue  
With `OR` compare posting lists comparing the first element and then increas until you find a match in any and continue  

1. Collect documents
2. Tokenize text -> list of tokens
3. Linguistic preprocessing
4. Index documents, inverted index (dictionary and postings)

### Tokenization
Break text into words  
Use stop list to remove stop words  
Can use:
- compression
- weighting
- limit runtime impact

### Normalization
**query expansion** list or **equivalence classes**

### Stemming and Lemmatization
**Porter stemmer** or **Wordnet lemmatizer** (requires POS tagging)
1. Document retrieval
2. Normalization
3. Stop words removal
4. Stemming/Lemmatization
5. Indexing

### Prhase Queries
Use *""* to make phrase queries  
Biwords indexes or **positional index**  
Biwords for common queries and positional for complex ones 

### Data Structures for IR
**Skip lists** for the Inverted index  
**B-trees** or **Tries** for the index. Make easier insertion and deletion. Tries use prefixes to access the dictionary.
Save to disk after making the index so don't need to make it again.

### Wildcard Queries
???

### Spelling correction
???

### Memory access
Select the order that reduces the opeartions to perform:
- For `AND` consider the terms with the smallest list first
- For `OR` consider that `|A OR B| ≤ |A + B|`

Read entire blocks of memory instead of single bytes. More work in memory to reduce disk access. 

### Dictionary and Index Compression
???

## ADD AND DELETE DOCUMENTS
### Storing Postings
Huge file is better than maney files

### Dynamic indexing
Maintain program online and keep the index as is.  
Create **auxiliary index** and **merge** when needed. Keep `log_2(T/n)` auxiliary indexes where `T` is the number of postings and `n` is the size of the smaller auxiliary index.
Deletions are performed with an **invalidation bit vector**.  
Merge with **logarithmic merging**:
- create index in memory
- when full save to disk and create new index with same size
- when full merge into index of size `2n` and create new index of size `n`
- when full create new index...

Most merges are of small indexes but more merge operations are necessary.

## ADDITION AND DELETION ARE EFFICIENT (ADDITIONAL INDEX + MERGES)

## TEST WITH SPLITS
