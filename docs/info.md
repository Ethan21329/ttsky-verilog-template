<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

My Mini Cryptography engine takes in an 8 bit message, 7 bit key, and a 1 bit mode select signal, outputting the original input message scrambled into an 8 bit code. 

For encrypting, input your message, a custom 7 bit password key, and set the mode to 1 for encryption. The module will then output your encrypted message.

For decrypting, input your encrypted message, your password key, and set mode to 0 for decryption. The modole will then output your original message.

## How to test

Since tiny tapeout has very limited I/O it's feasable to brute force every single possible input pattern for testing. This is what the testbench tb.v does.

Run make sim to test within the test directory.

## Use of Gen AI

I used AI to help me debug any issues I ran in with my project. I also used it to come up with different types of reversable scrambling sequences I could apply to input.