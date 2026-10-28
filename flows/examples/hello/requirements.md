# Hello Kinenix

The requirements of this example, written the way you fill in `requirements.md` in a new project (`kinenix init`). `flow.md` does what they ask; compare the two to see how each section becomes steps, settings in `config/config.json`, and error handling.

## Goal

Make a greeting for each person on a short list and save the greetings as a table, to check that Kinenix works on a new machine. It must run without a browser and without internet.

## Steps

1. Take the list of names.
2. For each name, make one greeting such as "Hello, Somchai!". Build one greeting in a separate, reusable piece, so the same piece can make greetings elsewhere.
3. Put the greetings in a table with two columns: Name and Greeting.
4. Save the table as a CSV file.

## Settings that must change without editing the flow

- The list of names
- The greeting word ("Hello")
- Where the CSV file is saved

## Secrets

- none

## Personal or confidential data

- none (the names are examples)

## Output

`output/greetings.csv` with the columns Name and Greeting, one row per name, in the order of the list:

| Name | Greeting |
| :--- | :--- |
| Somchai | Hello, Somchai! |

## Errors and exceptions

- If the list of names is empty, stop and say that there is nobody to greet, instead of saving an empty file.
- If a name is missing inside the reusable piece, stop and say so.

## Schedule

By hand, after installing Kinenix.
