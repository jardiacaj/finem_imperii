This document is based on the homonym text of the [OpenGovernment
project](https://github.com/opengovernment/opengovernment/blob/master/CONTRIBUTING.md)

# How to contribute

I'm really glad you're reading this, because we need volunteer
developers to help this project come to fruition.

If you haven't already, come find us in
[our Gitter chat](https://gitter.im/finemimperii/Lobby).
We want you working on things you're excited about.

Here are some important resources:

  * [The documentation](https://github.com/jardiacaj/finem_imperii/blob/master/README.md)
  is part of the Git repo.
  * [Our GitHub milestones](https://github.com/jardiacaj/finem_imperii/milestones)
  show our goals, both short- and long-term.
  * [GitHub issues](https://github.com/jardiacaj/finem_imperii/issues)
  show our open issues. Not only bugs, but also features and open
  discussions.
  * Bugs? [Create a new issue](https://github.com/jardiacaj/finem_imperii/issues/new).
  * Chat: [Gitter](https://gitter.im/finemimperii/Lobby). I check it out
  most days.

## Development

The project was originally created using the
[PyCharm IDE](https://www.jetbrains.com/pycharm/), which has a free
version available. In the Git repo there is some shared configuration
included, so using this IDE will allow you to use existing
configuration and share your changes back.

You may of course make your changes with any tools you like.

There is a short
[server setup guide](https://github.com/jardiacaj/finem_imperii/blob/master/docs/4-server_setup.md)
available in the documentation.

## Testing

We use the [Django testing framework](https://docs.djangoproject.com/en/1.11/topics/testing/)
for the Python code. There are unfortunately no tests for the frontend
yet.

## Submitting changes

Please send a
[GitHub Pull Request to finem_imperii](https://github.com/jardiacaj/finem_imperii/compare)
with a clear list of what you've done (read more about
[pull requests](http://help.github.com/pull-requests/)).
When you send a pull request, we will love you forever if you include
new tests. We can always use more test coverage. Please follow our
coding conventions (below) and make sure all of your commits are atomic
(one feature per commit).

Always write a clear log message for your commits. One-line messages are
fine for small changes, but bigger changes should look like this:

    $ git commit -m "A brief summary of the commit
    >
    > A paragraph describing what changed and its impact."

## Coding conventions

In Python, we follow PEP8. There are no hard conventions in other file
types, but in general:

  * We indent using four spaces.
  * This is open source software. Consider the people who will read your
   code, and make it look nice for them. It's sort of like driving a
   car: Perhaps you love doing donuts when you're alone, but with
   passengers the goal is to make the ride as smooth as possible.

Thanks!
