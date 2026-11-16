# Judging guidelines (`manual` test set)

You judge whether a Wikinews article satisfies the **information need** written under the query,
not whether it contains the query words. An article can match every word and still be grade 0,
or share no word with the query and be grade 2.

Run the tool with `uv run python -m evaluation.judge --judge <your name>`. It shows one article at
a time and saves each grade immediately: you can stop with `q` and resume later.

## Grades

| grade | meaning |
|---|---|
| **2** relevant | The article is **mainly about** what the need asks: a user with this need would be glad to have found it. |
| **1** partly relevant | The article is **related** or covers the need **substantially but not as its main subject**: one section or several sentences, a closely connected event, a follow-up. |
| **0** not relevant | The article is about something else, or mentions the subject only in passing (one name in a list, a line in a round-up). |

## Rules

1. **Judge the article, not the snippet.** Decide from the title and the lead shown by the tool;
   when they are not enough, press `o` and read the article (about 10 seconds a document is the
   target; take longer only when in doubt).
2. **Judge each article on its own.** Do not lower a grade because a better article for the same
   need was shown before: two articles on the same event can both be 2.
3. **Time matters when the need says so.** For a `time` query, an article on the right subject
   but clearly in another period is at most 1 (0 if the period is the point of the need).
4. **Pages that are not news** (tables, specials, lottery draws, drafts) are judged like any
   article: a standings table is 2 only if the need asks for those results.
5. **When in doubt between two grades, give the lower one**, and go on. Consistency matters more
   than any single judgment: the same kind of article should always get the same grade.
6. Do not look at which configuration retrieved a document (the tool does not show it, on
   purpose) and do not discuss your grades with the others before everyone has finished: queries
   1-10 are judged by two people to measure agreement (Cohen's kappa).

## Examples

Illustrative query (not in the test set): **"terremoto in Abruzzo"**, need: *"The user wants news
about the April 2009 earthquake in Abruzzo: victims, damage, rescue operations."*

| article | grade | why |
|---|---|---|
| Report on the victims and the collapsed buildings in L'Aquila the day after the quake | 2 | mainly about what the need asks |
| Report on the tent camps and the rescue teams at work in the Abruzzo villages | 2 | rescue operations are part of the need |
| Article on the government decree for the reconstruction, with a paragraph on the damage | 1 | connected follow-up, the damage is covered but is not the subject |
| Article on the G8 summit moved to L'Aquila, mentioning the earthquake as the reason | 1 | substantial mention, different main subject |
| Article on an earthquake in the Marche or in Sicily | 0 | another event |
| Round-up of the week's news with one line on the earthquake | 0 | mention in passing |

Illustrative `vague` query: **"incidente in una miniera di carbone"**, need: *"The user wants news
about accidents in coal mines (explosions, collapses), anywhere in the world."*

| article | grade | why |
|---|---|---|
| Methane explosion in a coal mine in China, dozens of miners dead | 2 | exactly the need, even without the word "incidente" |
| Rescue of miners trapped after a collapse, the mine type not stated | 1 | likely related, not clearly a coal mine |
| Strike of coal miners in Poland | 0 | coal mines, but no accident |
