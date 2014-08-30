bot:
    group.present:
        - system: False
    user.present:
        - fullname: Bot dev
        - shell: /bin/bash
        - home: /home/bot
        - groups:
            - bot

/home/bot/.virtualenvs:
    file.directory:
        - user: bot
        - group: bot
        - dir_mode: 00750
        - file_mode: 00640

{% for pkg in 'nano', 'vim-enhanced', 'wget', 'curl' %}
{{ pkg }}:
    pkg.installed
{% endfor %}
