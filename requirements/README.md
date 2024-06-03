# Requirements

## How this works
The `.in` files specify only the direct dependencies. 

The `.txt` files are generated from `pip freeze` and include all dependencies (basically: they're the lock files).

## How to add a dependency

### Base dependency

1. add package name(s) to `base.in`
2. install packages `pip install -r requirements/base.in`
3. run `make lock`

### Dev dependency

1. add package name(s) to `dev.in`
2. install packages `pip install -r requirements/dev.in`
3. run `make lock-dev`

Note that the lock commands aren't intelligent at all - they simply generate the dependencies 
for their "group" (i.e. base or dev) by excluding the dependencies specified in the `.in` 
files of the other group. 

This means that you can add as many dependencies of the same group as you wish, but you should 
call the group's respective lock command before adding dependencies to the other group.

## How to update dependencies

Run `make update` or `make update-dev`.
