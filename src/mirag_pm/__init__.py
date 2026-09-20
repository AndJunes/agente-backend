"""The Product Manager agent: its corpus, its vocabulary and its skills.

A sibling package of ``mirag``, not a fork of it. The code that retrieves, ranks, calls the
model and streams the answer stays in ``mirag``; what lives here is everything that makes
this agent a different agent — a different body of knowledge, a different vocabulary, a
different set of things it is allowed to do.

The two never meet inside a process. One process holds one container, one container holds
one ``I18n``, and that object is told at construction which corpus to read. Keeping them
apart is therefore a property of how the processes are started, not of anyone remembering to
be careful.
"""
