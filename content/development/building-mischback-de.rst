#####################
Building mischback.de
#####################

Building my personal website has been on my bucket list for quite a while. But
actually it is not that easy.

Creating the website just for the sake of *having a website* seems like a waste
of time (in the sense of *"I could be doing cooler things right now!"*).

So, the very first step **should** be: Defining the type of content and
building the actual website from there on.

However, this is not really what I'm doing right now.


******************
The starting point
******************

Ok, I **have** a rough idea about the content. I want a place to document my
very own projects from my own perspective. That is, not only the technical
documentation, that accompanies programming projects, but also the
non-technical aspects that went into the projects.

Furthermore, I have some stuff going on beside / along the programming
projects and I want to show that off, too (:wikipedia:`Narcissism <narcissism>`
is always part of personal websites, isn't it?).


The content
===========

**Bottom line up front**: mischback.de's content will be text-heavy. Be it
additional information about one of my
`open-source projects <https://github.com/Mischback/>`_, maybe some (technical)
tutorials / guides or stuff like build logs / presentations of non-programming
projects.

*Text-heaviness* *may* (and probably *should*) be broken / augmented by some
images. These may be pictures or other graphics.

.. note::
   Embedding videos is neither intended nor desired.

   It's not that I don't like video content. But I feel like that medium is not
   really suited for technical stuff (and yes, I'm feeling old writing this
   down).

The content will not be *bloggish*, meaning it will be ordered by topics rather
than dates.


The visual presentation
=======================

With that rough understanding about the content, I developed a first draft of
the visual presentation. It was focused on text-heavy content, with clear
typographic rules and high contrast to enhance readability.

Having a custom-made, individual layout was **a given**. I don't necessarily
want the layout to be outstanding and cutting-edge, but it should be
individual and presenting myself.

Modern web technologies should be applied where possible. Semantic markup is
highly desired, incorporating Javascript where necessary to provide additional
functionality.


The technical implementation
============================

And now the truth: Yes, I had a (vague) idea about the content. But I had more
than just an idea about the technical implementation.

I was looking at the vast ecosystem of **Static Site Generators**, with its
most promising candidates, *Next.js*, *Gatsby*, *Jekyll* and *Hugo*.

.. note::
   I just address the site generation here.

   For the whole web stack, I will rely on the existing setup of my server,
   which is - as of now - running Nginx as webserver.

*Next.js* and *Gatsby* were ruled out fast. While I acknowledge Javascript as
a valid general-purpose programming language, I simply don't like it and could
not imagine building my personal website with that technology stack.

I've never worked with Go nor Ruby, so *Hugo* and *Jekyll* would mean new
technology stacks.

I settled with *Jekyll*, mainly because it is developed by GitHub's folks and
powers GitHub Pages. I even started a first try to get this going, when I got
distratcted by other projects.

I liked the concepts of *Jekyll*. Providing meta information directly within
the actual content (source) files allows a great amount of control. Templating
(and thus: visual layout development) is easy but powerful. And there is a
vast ecosystem of plugins and guides around it.

But there was a break. And I was working on different projects, some Python,
some DevOps stuff. And I was - not for the first time - working with *Sphinx*.

When I returned to mischback.de, I reconsidered the *Jekyll* choice. I feel
most comfortable around Python, so why not use a Python-based SSG?

**Hell**, why not using **Sphinx**?

And this is, where we start this journey.


******************
Implementation Log
******************

The following wall of text describes and documents the actual (technical)
implementation of *mischback.de*.

It is meant as a log, so mistakes and dead-ends may (will) happen.


2022-11-24
==========

Starting from scratch. As usual, building the foundation of a repository is
some effort. Setting up the infrastructure of ``tox``, ``make``, ``pre-commit``
and providing the general configurations for these tools.

Researching stuff around ``Sphinx``. There are some guides about using
``Sphinx`` for personal websites, but it is not the prominent choice.


2022-11-26
==========

Getting ``Sphinx`` going. The first real task is finding ways to structure the
content to make it work with ``Sphinx``'s internal logic:

``Sphinx`` does expect a clear hierachical structure of the content. At this
point (with virtually no content available), this is easily done. Can this
clear structure be maintained?

My (probably too naive) solution: I set
`root_doc <https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-root_doc>`_
to ``sitemap`` and create a ``sitemap.rst`` which will provide a full TOC for
the whole website. The main categories (as of now only ``development``) have
a TOC that includes all documents of that category.

*Most likely* this means, that the actual navigation has to be built by hand.
But let's solve that problem later.
