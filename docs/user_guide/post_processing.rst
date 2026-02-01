Post-Processing Guide
=====================

This guide explains the OppNDA post-processing pipeline.

Pipeline Overview
-----------------

OppNDA processes simulation results in three stages:

1. **Averager** - Groups and averages report files
2. **Analysis** - Generates visualizations
3. **Regression** - Trains ML models (optional)

Running Post-Processing
-----------------------

Via GUI
~~~~~~~

Click the respective buttons in the Settings page:

- "Run Averager" - Average reports
- "Run Analysis" - Generate plots
- "Run Regression" - Train models
- "Run All" - Execute complete pipeline

Via Command Line
~~~~~~~~~~~~~~~~

.. code-block:: bash

    python core/averager.py
    python core/analysis.py
    python core/regression.py

Output
------

- Averaged reports: ``reports/*_average.txt``
- Visualizations: ``plots/*.png``
- Regression models: ``regression_results/``
