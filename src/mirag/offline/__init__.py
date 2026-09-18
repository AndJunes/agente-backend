"""Seeing the machine work without paying, and without it inventing answers.

With the offline lock on, only the model's DECISION is replaced, by a fixed script, and only
for the prepared demos. Any other question gets "no model" instead of a confident answer to
a different question: a fixture that answers the wrong question looks like a hallucination
of the model when it is a badly chosen fixture.
"""
