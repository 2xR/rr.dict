=======
rr.dict
=======

Utility functions for working with dictionaries. Defines very useful ``merge()`` and ``diff()`` operations, as well as other utilities like ``extract()`` to create new dicts containing a subset of the original dict, and ``lookup()`` to attempt multiple keys before raising an exception.

There is also a ``rr.dict.nested`` module containing functions to create, manipulate and iterate over nested dictionaries.


Compatibility
=============

Developed and tested in Python 3.6+. The code may or may not work under earlier versions of Python 3 (perhaps back to 3.3).


Installation
============

From the github repo:

.. code-block:: bash

    pip install git+https://github.com/2xR/rr.dict.git


License
=======

This library is released as open source under the MIT License.

Copyright (c) 2017 Rui Rei
