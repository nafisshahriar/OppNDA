Developer Guide
===============

This guide explains OppNDA's architecture and how to extend it.

Architecture Overview
---------------------

OppNDA follows a modular architecture with clear separation of concerns:

.. code-block:: text

    +-------------------------------------------------------------+
    |                         GUI Layer                           |
    |  +--------------+  +--------------+  +-------------------+  |
    |  | settings.html|  |   nda.html   |  |     config.js     |  |
    |  |  (Config UI) |  |  (Results)   |  | (Frontend Logic)  |  |
    |  +------+-------+  +------+-------+  +---------+---------+  |
    +---------|-----------------|-----------------------|----------+
              |                 |                       |
              v                 v                       v
    +-------------------------------------------------------------+
    |                     Flask Application                       |
    |  +-------------------------------------------------------+  |
    |  |                    app/api.py                         |  |
    |  |  * Configuration endpoints                            |  |
    |  |  * Execution endpoints (run-one, run-averager, etc)   |  |
    |  |  * Streaming endpoints (SSE for real-time output)     |  |
    |  +---------------------------+---------------------------+  |
    +------------------------------|------------------------------+
                                   |
                                   v
    +-------------------------------------------------------------+
    |                      Core Modules                           |
    |  +----------------+  +----------------+  +---------------+  |
    |  |   averager.py  |  |  analysis.py   |  | regression.py |  |
    |  | (Data Avg)     |  | (Visualization)|  | (ML Models)   |  |
    |  +-------+--------+  +-------+--------+  +------+--------+  |
    |          +-------------------+-------------------+          |
    |                              |                              |
    |  +-------------------------------------------------------+  |
    |  |              resource_manager.py                      |  |
    |  |   Dynamic memory/CPU management for multiprocessing   |  |
    |  +-------------------------------------------------------+  |
    +-------------------------------------------------------------+
                                   |
                                   v
    +-------------------------------------------------------------+
    |                    Configuration                            |
    |  +----------------+  +----------------+  +---------------+  |
    |  |averager_config |  |analysis_config |  |regression_cfg |  |
    |  |     .json      |  |     .json      |  |    .json      |  |
    |  +----------------+  +----------------+  +---------------+  |
    +-------------------------------------------------------------+


Data Flow
---------

The typical data flow through OppNDA:

1. **ONE Simulator** generates report files (``*.txt``) in ``reports/``
2. **Averager** groups and averages reports by configuration parameters
3. **Analysis** generates visualizations from averaged data
4. **Regression** (optional) trains ML models on the data

.. code-block:: text

    ONE Simulator
         |
         v (report files)
    +-------------+     +-------------+     +-------------+
    |  Averager   |---->|  Analysis   |---->|  Regression |
    |             |     |             |     |   (ML)      |
    +-------------+     +-------------+     +-------------+
         |                    |                   |
         v                    v                   v
    averaged_*.txt       plots/*.png       regression_results/


Module Descriptions
-------------------

averager.py
~~~~~~~~~~~

Groups report files by configurable parameters and calculates averages.

**Key Classes:**

- ``ReportAverager``: Main orchestrator
- Uses multiprocessing for parallel file reading

**Configuration:** ``config/averager_config.json``

.. code-block:: json

    {
        "folder": "reports",
        "filename_pattern": {...},
        "average_groups": [...]
    }

analysis.py
~~~~~~~~~~~

Generates visualizations from processed data.

**Key Classes:**

- ``SmartFileParser``: Parses averaged and raw files
- ``DataOrganizer``: Prepares data for plotting
- ``PlotStrategy``: Determines which plots to generate
- ``PlotGenerator``: Creates matplotlib visualizations

**Supported Plot Types:**

- Line plots (metric vs parameter)
- 3D surface plots
- Violin plots
- Correlation heatmaps
- Pairplots

resource_manager.py
~~~~~~~~~~~~~~~~~~~

Optimizes multiprocessing based on available system resources.

**Key Features:**

- Dynamic worker count based on RAM
- Memory estimation for batch processing
- Prevents system thrashing

**Mathematical Model:**

.. code-block:: text

    P_opt = max{p in Z+ | M(t)|P=p <= eta * M_RAM}

    Where:
    - P_opt: Optimal worker count
    - eta: RAM utilization threshold (default 85%)
    - M_RAM: Available system RAM


Configuration Guide
-------------------

All configurations are in ``config/`` directory:

averager_config.json
~~~~~~~~~~~~~~~~~~~~

Controls how reports are grouped and averaged.

.. code-block:: json

    {
        "folder": "reports",
        "filename_pattern": {
            "delimiter": "_",
            "components": {
                "router": 1,
                "ttl": 2,
                "buffer": 3
            }
        },
        "average_groups": [
            {
                "name": "By TTL",
                "group_by": ["router", "buffer"],
                "output_template": "{report_type}_{router}_{ttl}_average.txt"
            }
        ]
    }

analysis_config.json
~~~~~~~~~~~~~~~~~~~~

Controls visualization settings.

.. code-block:: json

    {
        "directories": {
            "report_dir": "reports",
            "plots_dir": "plots"
        },
        "metrics": {
            "include": ["delivery_prob", "latency_avg"],
            "ignore": ["sim_time"]
        },
        "enabled_plots": {
            "line_plots": true,
            "3d_surface": true,
            "violin_plots": true
        }
    }


Extending OppNDA
----------------

Adding a New Plot Type
~~~~~~~~~~~~~~~~~~~~~~

1. Add method to ``PlotGenerator`` class in ``analysis.py``:

.. code-block:: python

    def create_custom_plot(self, job_data):
        """Create custom plot type."""
        grouping_type, df, metric, settings = job_data
        
        fig, ax = plt.subplots(figsize=tuple(settings['size']))
        # Your plotting logic here
        
        output_path = os.path.join(self.output_dir, f"{metric}_custom.png")
        fig.savefig(output_path, dpi=150)
        plt.close(fig)
        
        print(f"  [OK] Custom: {metric}")
        return True

2. Add to ``execute_plot_job`` dispatcher:

.. code-block:: python

    elif job_type == 'custom':
        return generator.create_custom_plot(job_data)

3. Add to ``enabled_plots`` in config and main job queue.

Adding a New API Endpoint
~~~~~~~~~~~~~~~~~~~~~~~~~

1. Add route in ``app/api.py``:

.. code-block:: python

    @api_bp.route('/custom-endpoint', methods=['POST'])
    def custom_endpoint():
        """
        Custom endpoint description.
        
        Request:
            JSON with parameters
            
        Returns:
            JSON response
        """
        data = request.get_json() or {}
        # Your logic here
        return jsonify({'success': True, 'data': result})

2. Add streaming version if needed (using SSE pattern).


Testing
-------

Run tests with pytest:

.. code-block:: bash

    # Run all tests
    pytest tests/

    # Run with coverage
    pytest --cov=core --cov=app tests/

    # Run specific module tests
    pytest tests/test_averager.py
