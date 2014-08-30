{% for pkg in 'python-setuptools', 'python-pip', 'python-devel' %}
{{ pkg }}:
    pkg.installed
{% endfor %}

{% for pip in 'virtualenv', 'virtualenvwrapper' %}
{{ pip }}:
    pip.installed:
        - require:
            - pkg: python-pip
{% endfor %}

/etc/profile.d/python.sh:
    file.managed:
        - source: salt://python/python.profile.sh
        - mode: 00755
        - user: root
        - group: root
