# RPA Challenge Solver

The requirements of this example, written the way you fill in `requirements.md` in a new project (`kinenix init`). `flow.md` does what they ask; compare the two to see how each section becomes steps, settings in `config/config.json`, and error handling.

## Goal

Solve the RPA Challenge (https://rpachallenge.com/): enter the ten people from the challenge's Excel file into its web form, whose fields move to a new place after every submit, and show the result. Also list the people whose role is not Programmer, for a separate review.

## Steps

1. Open https://rpachallenge.com/.
2. Read the Excel file of the challenge (10 people: First Name, Last Name, Company Name, Role in Company, Address, Email, Phone Number).
3. Press Start to begin the timer.
4. For each person whose role is Programmer, fill the seven fields and press Submit. Find each field by its label, not by its position, because the fields move.
5. Add every person whose role is not Programmer to a list, with the first name and the role.
6. Save a screenshot of the result message.
7. Close the browser.
8. When asked to, e-mail the result with the screenshot attached and the list of people who are not programmers.

## Settings that must change without editing the flow

- The challenge URL
- The Excel file
- Where the screenshots are saved
- Whether to send the e-mail, its recipient and subject, and whether it is really sent (to test without sending)

## Secrets

- The Gmail account and its app password, only when the e-mail is sent

## Personal or confidential data

- none (the challenge data is made up); in a real form-filling task, the names, e-mails, and phone numbers would be listed here

## Output

- `output/screenshots/result_rpachallenge.png`: the challenge's result message
- The list of people who are not programmers, in the e-mail when it is sent

## Errors and exceptions

- If the Excel file is missing, stop and say which file.
- If a field cannot be found by its label, stop at that person and keep a screenshot.

## Schedule

By hand, as a demonstration and a benchmark.
