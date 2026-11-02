# Contributing

This is an experimental frontend. Keep the backend contract small and explicit.

Before submitting changes:

```sh
python3 -m py_compile src/main.py
sh -n alpine-desktop-center install.sh
```

Do not move Ansible roles into this repository. Changes to the stable backend
belong in [alpine-desktop](https://github.com/awsxo000/alpine).
