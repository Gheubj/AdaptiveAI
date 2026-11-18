# Robust Fallback Analysis

The confidence rule uses the validation-selected gap between the top two MLP probabilities and
falls back to the train-selected Best Single. It changed 28.2% of proprietary ID decisions and
reached 0.6095 quality at cost 0.0575. On ARC it changed 12.8% and exactly matched Best Single at
0.4275. The disagreement rule (MLP versus Shared) changed 9.4% ID decisions, reached 0.6049, and
dropped to 0.4050 ARC.

Thus confidence fallback reduces some harmful ID decisions, but its apparent OOD robustness is
mostly increased selection of the strongest fixed model. Confidence is not validated as an OOD
detector; ARC ECE remains 0.249 for MLP versus 0.026 ID.
