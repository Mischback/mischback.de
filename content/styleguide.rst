
:layout: article
:summary: Visualizes the pre-defined design elements
:keywords: sphinx theme,webdesign,visual design
:tubhrq: It's not an experiment if you know it's going to work.
:tubhrq_origin: Jeff Bezos
:published: 2023-01-25
:modified: 2023-02-09

.. tags:: internal; webdesign

##########
Styleguide
##########

This page doesn't really provide content. It is meant to include all
pre-defined *semantic elements* to demonstrate their styling. Having all of
them available in one document is meant as a reference aswell as the means to
create a coherent overall style.

This document may then act as the theme's styleguide.

The *top-level* headline is already included above, let's move to other the
other headlines.

*********
Headlines
*********

The headlines in the ``reST`` source files correspond to visual styling. But
most importantly they have semantic meaning aswell, as they control the
(internal) structure of the text content / documents.

.. note::
   Any document can have only one *main headline*, formatted using ``#`` as
   *overline* **and** *underline*.

   This will also determine the document's title, which is available for
   Sphinx's build process and will be used when linking to the document.

This block is a *second-level headline*, formatted using ``*`` as *overline*
**and** *underline*.

3rd-level Headline
==================

This is a *third-level headline*, formatted using ``=`` as *underline*.

Probably this is already the finest level of structure that is required for any
document.

**********************
Inline text formatting
**********************

In the actual text body, additional formatting is required and available. Don't
get this wrong: the additional formatting is meant to provide the visual
representation of *semantic meaning*. Text is not simply **bold**, instead, it
puts an emphasis on something, using HTML's ``<strong>`` tag, which is styled
as **bold text** in the theme's stylesheet.

Available formatting includes

* **bold text**, formatted using ``**`` to enclose the text, resulting in a
  ``<strong>`` tag
* *italic*, formatted using ``*`` to enclose the text, resulting in an ``<em>``
  tag

*****
Lists
*****

Lists are a great way to structure content. They are easy and fast to consume
by the reader and *may* provide additional semantic meaning when using
*ordered lists*.

* This is an **unordered list**;
* it is formatted using HTML's ``<ul>`` tag;

  * it may even contain another list...
  * ...creating some kind of hierarchy...

    * but this may be overdone!
    * Carefully evaluate how much nesting is really required!

* The top-level list may then be resumed;
* and may contain more elements!

******
Quotes
******

Quotes provide some kind of pseudo-scientific aestetics or may just be used to
create a valid reference.

If quotes are used as an actual reference to support the argumentation of the
article, carefully evaluate if an actual direct quote (using ``<blockquote>``)
is required or if the link to the source is more fitting and provides
additional context. **Use** ``<blockquote>`` **sparingly**, as a means for
really strong emphasis!

  My general working style is to write everything first with pencil and paper,
  sitting beside a big wastebasket. Then I use Emacs to enter the text into my
  machine.

  -- Donald E. Knuth

That quote is one of my all-time favorites! It pretty much describes my own
style, though I prefer ``vi``.

***********
Admonitions
***********

**Admonitions** translates to *Ermahnungen* in German, which is actually pretty
funny.

.. note::
   The **note** admonition is just that, a note.

   I like to use it to include additional context, that is highly related to
   the main text, but is kind of *over the top*. Consume it like a "Oh, that's
   interesting and nice to know!" information.

On the other hand, there is an *important admonition*:

.. important::
   This is really important! It strongly emphasizes an argument of the main
   text body or is an actual warning about something.

   The formatting must reflect the - well - importance!
