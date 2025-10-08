# Backend

## Getting Started

```bash
git clone https://github.com/devcourse-de7-1-team-5/backend.git
uv sync

cd src
uv run python manage.py runserver
```

## Project Structure

```markdown
backend
├─ .venv
├─ manage.py
├─ docs # Documentation files
├─ src # Django Project Root
│  ├─ backend
│  │  ├─ settings.py
│  │  ├─ urls.py
│  │  └─ ...
│  ├─ todo # Example Django App
│  └─ django_apps ...
└─ README.md
```

### uv 사용법
> 이 프로젝트는 `uv`를 사용하여 Python 가상 환경과 Django 패키지를 관리합니다.

[uv](/docs/uv_usage.md) 사용법을 참고하세요.
