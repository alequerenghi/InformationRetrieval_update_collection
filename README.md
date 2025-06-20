# Information Retrieval Project
Boolean information retrieval system project focused on the update of the collection allowing for addition and deletion of documents.  
### Features:
- `AND`, `OR` and `NOT` operators to combine terms in the query
- use of "`(`" and "`)`" in queries for more control on the documents retrieved
- allow for **phrase queries** with **biword index** <del>and positional index</del>
- intelligent **query optimization** to reduce operations on `AND`s
- **add** and **delete documents**
- **additional index** to keep the system running while adding documents
## How To
To load the program simply run the `main.py` script. It will ask for data to load:
```
load data/movie.metadata.tsv plot_summaries.txt
```
This will create the index and save it on disk for future uses.  

To add documents to the index run
```bash
add metadata_file.tsv plot_file.tsv # files containing new data
```
The added documents will be stored in an additional index until it will grow too big and merged in the main one.  
This operation runs on a different thread so queries can be executed in the meantime.

To delete documents run:
```bash
del 2 4-6 # and so on
```
Documents are deleted by DocID in a space separated list. To indicate ranges of documents to delete use the dash `-` as in `A-Z`. This will result in the removal of documents from `A` to `Z` (included).

Queries are performed by typing the words one is searching:
```
a AND b OR c NOT d
(a AND b) OR (c NOT d)
```

Phrase queries are performed by adding `"` at the end and at the beginning of the query:
```
"to be or not to be"
```

### Additional remarks
Operators are applied from left to right. `AND`s do not have precedence over `OR`s (e.g. "_dog OR cat AND water_" -> "_(dog OR cat) AND water_").  
`NOT` operator corresponds to `AND NOT` meaning that "_a NOT b_" `-> a - b`.  
Since **stop words are filtered out** by the system, it is advised to not include them in regular queries but to **perform phrase queries instead**.
