```
data
│   README.md
└───dataset: This folder contains the dataset used by CLAMS.  
│   └───calls: These files are actually created by CLAMS
│   │   andengine.arff
│   │   ...
│   └───source: This folder includes any source code files, ie. client files and examples used by CLAMS
│   │   └───java_libraries: Includes client files for each project
│   │   │   └───andengine
│   │   │   │   AntiFrogActivity.java
│   │   │   │   ...
│   │   └───java_libraries_examples: Includes examples files for each project
│   │   │   └───andengine
│   │   │   │   AnalogOnScreenControlExample.java
│   │   │   │   ...
│   │   └───namespaces: For best performance, CLAMS' API call extractor  requires a folder of namespaces used in the libraries so that it can resolve wildcarded namespaces.
│   │   │   └───class
│   │   │   │   com.webobjects.appserver
│   │   │   │   ...
│   │   │   └───method
│   │   │   │   io.netty.channel.Channels
│   │   │   │   ...
└───results: This folder contains the results from CLAMS, MAPO, and UP-Miner systems.
│   └───clams: CLAMS results for each project
│   │   └───camel: 
│   │   │   └───HDBSCANSum: Version that uses the HDBSCAN clustering algorithm and the summariser
│   │   │   │   └───methodFiles:  ASTs in xml format for the client methods where the target API is being called. Filenames are in the form <classname>_<methodname>.xml and are extracted by the asts.xml file.
│   │   │   │   └───patternFiles: Summarised ASTs for the top N files of each cluster.
│   │   │   │   └───medoids: Summarised Java versions for the most representative file of each cluster as this is selected by the Snippet Selector.
│   │   │   │   └───ranked: Ranked version of the medoids folder, based on support.
│   │   │   │   callers_info.json: Contains info about callers
│   │   │   │   clusters.json: Clusters with their associated callers (i.e. client files)
│   │   │   │   top_files.json: Top N callers for each cluster, with their associated file's id and their distance from the medoid
│   │   │   │   medoids_map.json: Info, i.e. filename and API calls, for the medoid (most representative snippet) of each cluster.
│   │   │   │   ranked_files.json: Info, i.e. name (in the form <clusterid>_<classname>_<methodname>.xml), API calls and support for each of the ranked files.
│   │   │   │   readability.json: Readability for each of the ranked files.
│   │   │   │   locs.json: Physical lines of code for each of the ranked files.
│   │   │   │   precision.json: Precision for each of the ranked files using the library's examples dir.
│   │   │   │   coverage.json: Methods covered at top k results.
│   │   │   │   tokens: Number of sequence-tokens and snippet-tokens matched with examples tokens
│   │   │   │   evaluation.json: Brief evaluation summary.
│   │   │   │   summary.txt: Log file.
│   │   │   │   mapo_top_calls: Top API calls for MAPO.
│   │   │   │   upminer_top_calls: Top API calls for UP-Miner.
│   │   │   └───KeepUniqeNaiveSum:  Version that uses the naive clustering algorithm and the summariser, while keeping unique sequences during the preprocessing stage
│   │   │   └───KMedoidsSum: Version that uses the k-medoids clustering algorithm and the summariser
│   │   │   ...
│   │   │   └───NaiveNoSum: Version that uses the naive clustering algorithm, and the summariser while removing unique sequences during the preprocessing stage
│   │   │   ...
│   │   │   └───NaiveSum: Version that uses the naive clustering algorithm and the summariser while removing unique sequences during the preprocessing stage
│   │   │   ...
│   │   │   └───shared:  This includes files and folders that are shared between all the different versions. These are stored in a shared folder to avoid duplication and to reduce the size of the compressed folder.
│   │   │   │   └───srcFiles: Client source code files.
│   │   │   │   └───xmlFiles: ASTs of srcFiles, in xml format.
│   │   │   │   asts.xml: Aggregated xml with ASTs extracted from srcFiles.
│   └───mapo_upminer: Mapo and UP-Miner results
│   │   ...
└───user_survey: This folder contains the responses form the user survey conducted at Hotels.com.  
```