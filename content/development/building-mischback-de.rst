
:layout: article
:summary: Describing the process of building this website from scratch.
:keywords: personal website,build log,webdesign,sphinx
:tubhrq: My general working style is to write everything first with pencil and
         paper, sitting beside a big wastebasket. Then I use Emacs to enter
         the text into my machine.
:tubhrq_origin: Donald Knuth

.. tags:: foo; bar;

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


2022-12-02
==========

``Jekyll`` let the user determine, which template (or *layout* in ``Jekyll``'s
terminology) is used to render the content.

``Sphinx`` on the other hand uses a hardcoded call which will use the template
``page.html`` for any user-provided content.

The fix is actually really easy. The custom theme will provide some logic in
its ``page.html``, which evaluates a meta variable specifying the desired
template to be used and then just includes that template.

.. note::
   ``Sphinx`` will treat any field before a document's first headline as
   `file-wide metadata <https://www.sphinx-doc.org/en/master/usage/restructuredtext/field-lists.html#file-wide-metadata>`_
   which is accessible from the rendering context in templates as ``meta``
   mapping/dictionary.

   This is comparable to ``Jekyll``'s *front matter*.

The implementation does provide a *fallback template*, if a document doesn't
specify the desired template. And for whatever it is worth, that fallback
template is provided as a theme option and configurable from ``Sphinx``'s
``conf.py``.


2022-12-03
==========

Time for some Continuous Integration!

I rely on GitHub Actions for all my repositories, so most of that code is
copied from other projects.

Instead of manually calling the linters in a job, I use
`pre-commit's action <https://github.com/pre-commit/action>`_ to run the whole
``pre-commit`` configuration.

.. note::
   *Anthony Sottile*, the developer of ``pre-commit`` and this action considers
   this action **deprecated** and recommends using **pre-commit.ci** instead.

   Fair advice, but I really like to have all my checks (meaning: the whole of
   my CI setup) on a single platform, *GitHub Actions* in this case.

The ``pre-commit`` action is really great, as it has caching built-in, making
``pre-commit`` runs really fast.

After *linting* the source code, CI will actually build the ``reST`` sources
using ``Sphinx``.


2022-12-09
==========

One thing I really wanted to have, is another method of categorizing content.
Usually, blogs have the concept of *tags*, which is something that Sphinx
doesn't provide out of the box.

A simple search yields
`a corresponding Stack Overflow question <https://stackoverflow.com/questions/18146107/how-to-add-blog-style-tags-in-restructuredtext-with-sphinx>`_
with two different hints:

#. Use
   `Sphinx's index directive <https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-index>`_
   and let Sphinx handle indices internally.
#. A custom directive that creates links to pages, that are automatically
   created with a *pre-processing script*.

I tried to use the first approach, but after reviewing
`Sphinx's tutorial that includes the use of indices <https://www.sphinx-doc.org/en/master/development/tutorials/recipe.html>`_
I figured that it would require to dynamically create indices for the tags.
**Meh.**

The second approach is sympathically hacky, but a more thorough implementation
would be required. **Meh.**

At this point I had a look at `ABlog <https://github.com/sunpy/ablog>`_, which
is a Sphinx extension that basically turns Sphinx into a blog. With tags.

But an actual blog was not what I wanted. I don't see the point in date-based
postings (for my intended content). I want the *blog-style tags* **without**
the *blog*. **Meh.**

Time to hitch up my knickers... I kluged a Sphinx extension that does provide
*tagging*, including internally tracked indices, a custom directive and
dedicated overview pages.


2022-12-15
==========

A common issue with all web frameworks is: using templates to generate the
actual HTML source code results in *ugly looking code*. After running Sphinx,
the build artifacts are post-processed using a custom wrapper around
`tidy-html5 <https://github.com/htacg/tidy-html5>`_ to clean and prettify the
source code.

The generated build artifacts are validated during CI, using several tools:

- `HTMLHint <https://github.com/htmlhint/HTMLHint>`_ catches several stylistic
  issues. It is not strictly validating the correctness of the (generated) HTML
  but can rather be considered a linter for HTML.
- `HTML-validate <https://html-validate.org/>`_ is an actual validator for
  HTML5 and it is really strict about it.
- `HTML5 validator <https://github.com/svenkreiss/html5validator>`_ is like a
  *frontend* for
  `The Nu Html Checker <https://github.com/validator/validator>`_, which is
  also used by W3C's validation service. It can check CSS and SVG, too.
- `HTMLProofer <https://github.com/gjtorikian/html-proofer>`_ is another
  validator, specifically geared towards testing generated HTML output. It
  includes checks for internal and external references.


2022-12-17
==========

The custom theme needs a custom stylesheet. SASS / SCSS source files are
compiled to actual CSS using
`libsass-python <https://sass.github.io/libsass-python/index.html>`_ with a
minimal wrapper script.

To keep the source as clean as possible,
`styleint <https://github.com/thibaudcolas/pre-commit-stylelint>`_ is used as
a ``pre-commit`` hook (with various plugins) to lint the source files.
