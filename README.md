complexity
==========

Introduction
------------
In 2013 at the ScipPy conference, I got a preview copy of [Modeling Complexity by Maksim Tsvetovat, Alexander Kouznetsov](https://www.google.com/books/edition/Modeling_Complexity/GX3zmAEACAAJ?hl=en) and wanted to try out some of the algorithms presented there.  I started with their forest fire model and coded up version in Python with a GUI using Enthought's Traits/TraitsUI.  You can see the end result in `forest.py`.  That model and code ended up as the basis for a class I developed and subsequently taught for several years for Enthought on object-oriented programming.  You'll see pieces of it if you take their Python Foundations class.  I never got around to coding up any of the other examples in the book.

As of 2022, I still haven't updated the code to run in Python 3.

Getting Started
---------------

As a long-time Enthoughter, I'm most comfortable working with [EDM](https://assets.enthought.com/downloads/edm/), although I think the commands are pretty similar for `conda`.
- Clone the repo, using your preferred method.
- Create a Python 2 environment.
```
$ edm envs create --version '2.7' complexity
```
- Start a shell in the new environment.
```
edm shell -e complexity
```
- Install the dependencies
```
edm install numpy scipy traitsui chaco pyqt5
```
- Launch the app
```
$ python forest.py
```
<img width="814" alt="Screen Shot 2022-03-11 at 12 00 01" src="https://user-images.githubusercontent.com/852629/157924170-3f83760e-933e-402e-8afe-c4ff5e6eae36.png">

