---
title:  "Fun With Flags"
date: 2024-07-01
questions_date: "2022-09-09"
excerpt: "10 flag questions from the Fun with Flags special round of the 9 September 2022 pub quiz."
categories:
  - Questions
tags:
  - fun-with-flags
---
## Erik Pillon presents: Fun with Flags

The following questions were asked during the special round "Erik Pillon presents: Fun with Flags" of the pubquiz on the 9th of September, 2022.

{% assign questions = site.data.questions | where: "tags", "fun-with-flags" | where: "date", page.questions_date %}
{% include quiz-toolbar.html %}
<ol class="quiz-questions">
  {%- for question in questions %}
  {% include quiz-question.html entry=question %}
  {%- endfor %}
</ol>

