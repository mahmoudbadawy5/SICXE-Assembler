# SICXE-Assembler

It's a 2-pass assembler for SIC/XE architicture I made as a project in college.

## Usage

You can run it by using:

``python3 phase2.py 'filename.asm'``

The assembler will then produce multiple files:

* **out.txt**: Contains pass1 output
* **loc.txt**: Contains the location counter after pass1.
* **out_pass2.txt**: Contains pass2 output.
* **HTE.txt**: Contains the HTE records of the program.


## Tests

Multiple tests are provided in the folder tests.

* **sheet8_prog{1,2,3}.asm**: A multi section program.

* **test2.asm**: Nearly contain all cases the program needs to handle.

* **test4.asm**: Contains tests for EQU operation with relative addressing.

* **test{1,3}.asm**: General tests.
