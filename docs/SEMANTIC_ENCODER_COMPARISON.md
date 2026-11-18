# Semantic Encoder Comparison

MiniLM-L6-v2 was selected over BGE-small-en-v1.5 for the initial controlled experiment. Both are
English 384-dimensional encoders; MiniLM is Apache-2.0 and about 22.7M parameters, while BGE-small
is MIT-licensed and about 33.4M parameters. Evaluating both would have doubled representation
degrees of freedom without independent validation. The selected Hugging Face revision and cache
SHA-256 are recorded in `data/processed/minilm_embeddings.json`; weights plus the 37 MB embedding
cache remained below the 500 MB download limit. The encoder was frozen and truncated at 128 tokens.

MiniLM did not establish an ID advantage over TF-IDF. Its best semantic head (MLP 0.6042) was below
TF-IDF (0.6155), but was much less brittle on ARC-AGI (0.4210 vs 0.2525). This is a representation
robustness signal, not evidence that MiniLM is the generally superior router.
