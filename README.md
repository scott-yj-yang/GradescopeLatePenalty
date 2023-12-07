# Getting Started

<!-- WARNING: THIS FILE WAS AUTOGENERATED! DO NOT EDIT! -->

## Install

You can install via Pypi:

``` shell
pip install LatePenalty
```

Or alternatively, you can directly install from source

``` sh
pip install git+https://github.com/scott-yj-yang/LatePenalty.git
```

## How to use

View our tutorial:

### [Gradescope](./tutorial/gradescope%20late%20penalty%20tutorial.html)

### [nbgrader](./tutorial/nbgrader%20late%20penalty%20tutorial.html)

# FAQ

## Why do `LatePenalty` Exist?

This module supports both gradescope and nbgrader. Gradescope is an
interface where students can hand in their homework, programming
assignments, and even exams. Gradescope does accept late submission
after the official deadline, but it does not support well with the late
penalty of late submission, according to the course policy. In other
words, gradescope accepts late submission, but does nothing to
disincentive the late submissions. `LatePenalty` applies late penalty
for the late submissions when we publish grades from gradescope to
canvas, with custom messages for students about the allowance of the
penalty.

## Why not use `Post Grades to Canvas` on Gradescope?

- No Late Penalty

> Gradescope accepts late submissions from students, but the platform
> does not penalize late submissions. `Post Grades to Canvas` will post
> the raw score, shown on gradescope, to a specific assignment on
> canvas.

- No Support for Multiple Components of a Single Assignment

> Gradescope’s `Post Grades to Canvas` is a one-to-one mapping from
> gradescope’s assignment to canvas’ assignment. In certain cases, where
> an assignment has multiple components (auto-graded notebook and
> handwritten math work), gradescope cannot combine the score to a
> single assignment. For example, let’s say we have an assignment called
> `Assignment 1`, which has two components - `Assignment 1 - Autograder`
> and `Assignment 1 - Manual Grading` on gradescope. This package will
> combine two assignments into one and sync the canvas grade

## Late Policy

Some courses allow students to submit their work within a certain mercy
period of time, also called *slip days* or *slip hours*. Once

In this module, we the package `canvasapi` to

## How to set credentials

This package uses [canvas API](https://canvas.instructure.com/doc/api/)
and its wrapper package
[canvasapi](https://github.com/ucfopen/canvasapi) to post grades and
comments to your target course’s assignment. To do that, you’ll have to
provide the canvas credentials.

In order to interact with this software, you’ll have to create a
`credentials.json` file that is in the following format:

    {'GitHub Token': 'token', 'Canvas Token': 'token'}

Whenever you create an object, you will need to authenticate via this
`credentials.json` file through providing the file path to the object
initializer. It will test whether the credential you provided is
authenticate or not.

## How to obtain credentials

1.  Login to Canvas
2.  On the left menu bar, click `Account` -\> `Profile`
3.  At the profile page, click `Settings`
4.  Scroll down, at `Approved Integrations`, click `+ New Access Token`
5.  Name it, set expire date, and copy to the `credentials.json`

## Update Note:
- 11/01/2023: Added arguments to grade A1 and A1 GitHub part of COGS 108.
