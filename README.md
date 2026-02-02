fw-lab/
├── backend/
│   ├── main.py
│   ├── db.py
│   ├── models.py
│   ├── engine.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── api.js
│       └── components/
│           └── Topology.vue
│
└── docker-compose.yml


wyl@wyl-KVM:~/fw-lab-v1$ tree
.
├── backend
│   ├── data.db
│   ├── db.py
│   ├── __init__.py
│   ├── ipam.py
│   ├── main.py
│   ├── models.py
│   ├── orchestrator.py
│   ├── __pycache__
│   │   ├── db.cpython-310.pyc
│   │   ├── ipam.cpython-310.pyc
│   │   ├── main.cpython-310.pyc
│   │   ├── models.cpython-310.pyc
│   │   ├── orchestrator.cpython-310.pyc
│   │   └── webshell.cpython-310.pyc
│   ├── requirements.txt
│   └── webshell.py
├── docker-compose.yml
├── frontend
│   ├── Dockerfile
│   ├── index.html
│   ├── __init__.py
│   ├── node_modules
│   ├── package.json
│   ├── src
│   │   ├── api.js
│   │   ├── App.vue
│   │   ├── components
│   │   │   └── Topology.vue
│   │   └── main.js
│   └── vite.config.js
└── README.md
