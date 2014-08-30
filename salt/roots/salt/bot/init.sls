{% for pkg in 'lua', 'lua-devel' %}
{{ pkg }}:
    pkg.installed
{% endfor %}

/home/bot/.virtualenvs/bot:
    virtualenv.managed:
        - requirements: /src/requirements.txt
        - user: bot
        - require:
            - pkg: lua
            - pkg: lua-devel
