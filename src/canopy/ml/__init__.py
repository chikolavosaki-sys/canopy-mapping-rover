"""Machine learning: classify every LiDAR point as ground, stem, shrub, crown or rock.

``features`` describes each point's local shape, ``dataset`` builds labelled
training data from simulated forests, and ``point_classifier`` trains and
evaluates a Random Forest. Run ``python scripts/train_point_classifier.py``.
Needs the optional extra: ``pip install -e ".[ml]"``.
"""
