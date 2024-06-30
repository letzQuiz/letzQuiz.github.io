---
title:  "Fun With Flags"
date: 2024-07-01
categories:
  - Questions
tags:
  - fun-with-flags
---
# Erik Pillon presents: Fun with Flags

The following questions were asked during the special round "Erik Pillon presents: Fun with Flags" of the pubquiz on the 9th of September, 2022.

<ul>
  {% assign questions = site.data.questions | where: "tags", "fun-with-flags" | where: "date", "2022-09-09" %}
  {% for question in questions %}
    <li>
      <strong>Question:</strong> {{ question.question }}<br>
      <strong>Answer:</strong> {{ question.answer }}
    </li>
  {% endfor %}
</ul>

