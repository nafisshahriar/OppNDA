REST API Reference
==================

This section documents the Flask REST API endpoints.

api
---
Main API endpoints for configuration and execution.

.. automodule:: app.api
   :members:
   :undoc-members:
   :show-inheritance:

routes
------
Web routes for serving the GUI.

.. automodule:: app.routes
   :members:
   :undoc-members:
   :show-inheritance:


API Endpoints Summary
---------------------

Configuration Endpoints
~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :widths: 20 10 70
   :header-rows: 1

   * - Endpoint
     - Method
     - Description
   * - ``/api/config/<name>``
     - GET
     - Get configuration file (analysis, averager, regression)
   * - ``/api/config/<name>``
     - POST
     - Save configuration file
   * - ``/api/save-all``
     - POST
     - Save all configurations and settings

Execution Endpoints
~~~~~~~~~~~~~~~~~~~

.. list-table::
   :widths: 20 10 70
   :header-rows: 1

   * - Endpoint
     - Method
     - Description
   * - ``/api/run-one``
     - POST
     - Run complete simulation pipeline
   * - ``/api/run-averager``
     - POST
     - Run report averaging only
   * - ``/api/run-analysis``
     - POST
     - Run analysis/visualization only
   * - ``/api/run-regression``
     - POST
     - Run ML regression only

Streaming Endpoints
~~~~~~~~~~~~~~~~~~~

.. list-table::
   :widths: 20 10 70
   :header-rows: 1

   * - Endpoint
     - Method
     - Description
   * - ``/api/stream-averager``
     - GET
     - Stream averager output (SSE)
   * - ``/api/stream-analysis``
     - GET
     - Stream analysis output (SSE)
   * - ``/api/stream-regression``
     - GET
     - Stream regression output (SSE)
