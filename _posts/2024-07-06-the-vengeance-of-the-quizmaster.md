---
layout: normal-quiz
title:  "The Vengeance of the Quizmaster"
date: "2024-07-06"
categories:
  - Questions
---

{% assign date = page.date | date: "%Y-%m-%d" %}


{% assign files = site.data %}
{% assign all_entries = "" | split: "" %}

{% for file in site.data %}
  {% if file[0] contains "questions" %}
    {% assign entries = file[1] %}
    {% assign all_entries = all_entries | concat: entries %}
  {% endif %}
{% endfor %}

{% assign filtered_entries = all_entries | where: "date", date %}

{% assign general_knowledge = filtered_entries | where: "tags", "general knowledge" %}
{% assign sport = filtered_entries | where: "tags", "sport" %}

{% assign books_games = "" | split: "" %}

{% assign tv_entries = filtered_entries | where: "tags", "TV" %}
{% assign books_entries = filtered_entries | where: "tags", "books" %}
{% assign movies_entries = filtered_entries | where: "tags", "movies" %}
{% assign games_entries = filtered_entries | where: "tags", "games" %}

{% assign books_games = books_games | concat : tv_entries | concat : books_entries | concat : movies_entries | concat : games_entries %}

{% assign miscellaneous = filtered_entries | where_exp: "entry", "entry.tags != 'general knowledge'" | where_exp: "entry", "entry.tags != 'TV'" | where_exp: "entry", "entry.tags != 'books'" | where_exp: "entry", "entry.tags != 'movies'" | where_exp: "entry", "entry.tags != 'games'" | where_exp: "entry", "entry.tags != 'sport'" %}

<h2>General Knowledge</h2>
<ul>
  {% for entry in general_knowledge %}
    <li>
      <strong>Question:</strong> {{ entry.question }}<br>
      <strong>Answer:</strong> {{ entry.answer }}
    </li>
  {% endfor %}
</ul>

<h2>Books, TV Series and Boardgames </h2>
<ul>
  {% for entry in books_games %}
    <li>
      <strong>Question:</strong> {{ entry.question }}<br>
      <strong>Answer:</strong> {{ entry.answer }}
    </li>
  {% endfor %}
</ul>

<h2>Sport</h2>
<ul>
  {% for entry in sport %}
    <li>
      <strong>Question:</strong> {{ entry.question }}<br>
      <strong>Answer:</strong> {{ entry.answer }}
    </li>
  {% endfor %}
</ul>

<h2>Miscellaneous</h2>
<ul>
  {% for entry in miscellaneous %}
    <li>
      <strong>Question:</strong> {{ entry.question }}<br>
      <strong>Answer:</strong> {{ entry.answer }}
    </li>
  {% endfor %}
</ul>



