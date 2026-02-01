Installation
============

This guide covers detailed installation instructions for OppNDA.

Requirements
------------

- Python 3.8 or higher
- ONE Simulator (optional, for running simulations)

Python Dependencies
-------------------

Install all dependencies via pip:

.. code-block:: bash

    pip install -r requirements.txt

Core dependencies include:

- Flask (web framework)
- NumPy (numerical operations)
- Pandas (data manipulation)
- Matplotlib (visualization)
- Seaborn (statistical plots)
- scikit-learn (regression models)

Optional Dependencies
---------------------

For development and documentation:

.. code-block:: bash

    pip install sphinx sphinx-rtd-theme pytest pytest-cov

For optimal multiprocessing performance:

.. code-block:: bash

    pip install psutil

Building Documentation
----------------------

Build HTML documentation:

.. code-block:: bash

    cd docs
    sphinx-build -b html . _build/html

View documentation:

.. code-block:: bash

    # Windows
    start _build/html/index.html

    # Linux/Mac
    open _build/html/index.html
