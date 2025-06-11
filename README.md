# Project Starter

This repository provides:
1. The necessary environment to run your interpreter solution inside of
2. A local autograder script supplied with 20% of the Gradescope test cases for you to test your program

## Notes

- To do the project, you must have a top-level, versioned interpretervX.py file (where X is the current project number) that exports the Interpreter class. If not, your code will not run on our autograder.
- Your Gradescope submission should contain `interpretervX.py` and optionally any additional files YOU wrote (not the base files) that it rely on to run.
- You should maintain a copy of your local git history and commit to it regularly as you work. Although this is not required for submission, we reserve the right to ask you to submit this at any time if we suspect foul play.
- A few days after each project deadline, we will upload a reference solution to THIS repository. We recommend you do the next part building on your own code, but you are free to build on the reference solution from the previous project if you wish.
- Use Python>=3.12, or you will very likely run into weird issues!

### For These Files:
```
ply/lex.py
ply/yacc.py
brewlex.py
brewparse.py
element.py
intbase.py
```

- You do NOT need to understand these files to do the project (other than knowing how to invoke certain methods defined in them, which is outlined in the spec)
- You should NOT modify these files under any circumstance

## Local Autograder

To test your solution against the local autograder (again, this is 20% of the total Gradescope test cases), simply run:
```
python tester.py <project number>
```

This will run all the `tests` and `fails` tests in directory `v<project number>` against your interpreter.

You are free to write additional tests and add them to the corresponding directory, the local autograder will automatically test your code against any additional tests you write.

## Licensing and Attribution

This is an unlicensed repository; even though the source code is public, it is **not** governed by an open-source license.

This code was primarily written by [Carey Nachenberg](http://careynachenberg.weebly.com/) with support from his TAs.


